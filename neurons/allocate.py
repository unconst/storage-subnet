import os
import json
import torch
import shutil
import sqlite3
import hashlib
import argparse
import subprocess
import bittensor as bt
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

CHUNK_SIZE = 100000

def get_config() -> bt.config:
    parser = argparse.ArgumentParser(description="Rebase the database based on available memory and also")
    parser.add_argument("--db_path", required=False, default="~/bittensor-db", help="Path to the data database.")
    parser.add_argument("--netuid", type=int, default=1, required=False, help="Netuid to rebase into")
    parser.add_argument("--threshold", type=float, default=0.0001, required=False, help="Size of path to fill")
    parser.add_argument("--validator", action='store_true', default=False, help="Allocate as a validator")
    parser.add_argument("--no_prompt", action='store_true', default=False, help="Does not wait for user input to confirm the allocation.")
    parser.add_argument("--restart", action='store_true',  default=False, help="Restart the db.")
    parser.add_argument("--workers", required=False, default=10, help="Number of concurrent workers to use.")
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    return bt.config( parser )   

def get_available_space(path: str) -> int:
    """
    Calculate the available space in a given directory.

    Args:
    - path (str): The directory path.

    Returns:
    - int: Available space in bytes.
    """
    stat = os.statvfs(path)
    return stat.f_frsize * stat.f_bavail

def confirm_generation(allocations, directory: str) -> bool:
    """
    Prompt the user to confirm the deletion of a directory.

    Args:
    - directory (str): The directory to be deleted.

    Returns:
    - bool: True if user confirms deletion, False otherwise.
    """
    total_dbs = len(allocations)
    total_size = sum([alloc['size'] for alloc in allocations])
    if os.path.exists(directory):
        bt.logging.warning(f"NOTE: confirming this generation will delete the data already stored unde {directory}" )
    bt.logging.info(f'Are you sure you want to partition {total_dbs} databases with total size {human_readable_size(total_size)} under : {directory}? (yes/no)')
    response = input()
    return response.lower() in ['yes', 'y']

def human_readable_size(size: int) -> str:
    """
    Convert a size in bytes to a human-readable format.

    Args:
    - size (int): Size in bytes.

    Returns:
    - str: Human-readable size.
    """
    thresholds = [1<<30, 1<<20, 1<<10]  # GB, MB, KB thresholds in bytes
    units = ["GB", "MB", "KB", "bytes"]

    for threshold, unit in zip(thresholds, units):
        if size >= threshold:
            return f"{size / threshold:.2f} {unit}"

    return f"{size} bytes"

def run_cargo_command(alloc, hash=False, restart=False):
    """
    Run the rust script to generate the data and hashes DBs.

    Args:
    - alloc (dict): Allocation details.
    - hash (bool): If True, generate hash. Default is False.
    - restart (bool): If True, restart the database. Default is False.
    """
    db_path = alloc['path']
    if not os.path.exists(db_path):
        os.makedirs(db_path)
        print ('made dires')
    
    file_path = f"{db_path}/hashes-{alloc['miner']}-{alloc['validator']}" if hash else f"{db_path}/data-{alloc['miner']}-{alloc['validator']}"
    cmd = [
        "./target/release/storer_db_project",
        "--path", file_path,
        "--n", str(alloc['n_chunks']),
        "--size", str(CHUNK_SIZE),
        "--seed", alloc['seed'],
    ]
    if hash:
        cmd.append("--hash")
    if restart:
        cmd.append("--delete")
    cargo_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_db")
    result = subprocess.run(cmd, cwd=cargo_directory, capture_output=False, text=True)
    if result.stderr:
        bt.logging.error(f"Failed: {file_path}")

def generate(config, allocations, no_prompt=False):
    """
    Generate data and hashes DBs using multi-threading.

    Args:
    - config (bt.config): Configuration object.
    - allocations (list): List of allocation details.
    """
    # Confirm the allocation step.
    allocation_dir = os.path.join(config.db_path, config.wallet.name, config.wallet.hotkey)
    if not config.no_prompt and not no_prompt:
        if not confirm_generation(allocations, allocation_dir):
            exit()

    # Check and potentially delete existing allocation directory.
    # if os.path.exists(allocation_dir):
    #     shutil.rmtree(allocation_dir)
      
    # Create the directory for the allocation file.
    os.makedirs(allocation_dir, exist_ok=True)

    # Write the allocations to a JSON file.
    allocation_file = os.path.join(allocation_dir, "allocation.json")
    bt.logging.debug(f'Writing allocations to {allocation_file}')
    with open(allocation_file, 'w') as f:
        json.dump(allocations, f, indent=4)

    # Run the generation
    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        for alloc in allocations:
            executor.submit(run_cargo_command, alloc, True, config.restart)
            if not config.validator:
                executor.submit(run_cargo_command, alloc, False, config.restart)

def verify(config, allocations):
    """
    Verify the integrity of the generated data and hashes.

    Args:
    - config (bt.config): Configuration object.
    - allocations (list): List of allocation details.
    """

    for alloc in allocations:
        # Construct paths for data and hashes based on the allocation details.
        data_path = os.path.join(alloc['path'], f"data-{alloc['miner']}-{alloc['validator']}")
        hashes_path = os.path.join(alloc['path'], f"hashes-{alloc['miner']}-{alloc['validator']}")

        # Connect to the SQLite databases for data and hashes.
        data_conn = sqlite3.connect(data_path)
        data_cursor = data_conn.cursor()
        hashes_conn = sqlite3.connect(hashes_path)
        hashes_cursor = hashes_conn.cursor()

        i = 0
        while True:
            data_key = str(i)
            
            # Fetch data from the data database using the current key.
            data_cursor.execute(f"SELECT data FROM DB{alloc['seed']} WHERE id=?", (data_key,))
            data_value = data_cursor.fetchone()

            # Fetch the corresponding hash from the hashes database.
            hashes_cursor.execute(f"SELECT data FROM DB{alloc['seed']} WHERE id=?", (data_key,))
            stored_hash = hashes_cursor.fetchone()

            # If no data is found for the current key, exit the loop.
            if not data_value:
                break

            # Compute the hash of the fetched data.
            computed_hash = hashlib.sha256(data_value[0].encode('utf-8')).hexdigest()

            # Check if the computed hash matches the stored hash.
            if computed_hash != stored_hash[0]:
                bt.logging.error(f"Hash mismatch for key {i}!")
                return

            # Increment the key for the next iteration.
            i += 1

        # Log the successful verification of the data.
        bt.logging.success(f"Verified {data_path}")

        # Close the database connections.
        data_conn.close()
        hashes_conn.close()

def allocate(config):
    """
    Allocate space and generate allocation details based on the configuration.

    Args:
    - config (bt.config): Configuration object.

    Returns:
    - list: List of allocation details.
    """

    # Expand user home directory in the path if it exists.
    config.db_path = os.path.expanduser(config.db_path)

    # Initialize subtensor, wallet, and metagraph.
    sub = bt.subtensor(config=config)
    wallet = bt.wallet(config=config)
    metagraph = sub.metagraph(netuid=config.netuid)

    # Log the partitioning details.
    bt.logging.info(f'Partitioning path:{config.db_path} at threshold: {config.threshold}')

    # Create the directory if it doesn't exist.
    os.makedirs(config.db_path, exist_ok=True)

    # Calculate available and filling space.
    available_space = get_available_space(config.db_path)
    filling_space = available_space * config.threshold

    # Log space details.
    bt.logging.info(f'Available space: {human_readable_size(available_space)}')
    bt.logging.info(f'Using: {human_readable_size(filling_space)} bytes')

    # Calculate the number of databases.
    num_dbs = metagraph.n.item()
    bt.logging.info(f'Creating: {num_dbs} databases with under paths and sizes')

    allocations = []

    # Calculate allocation details for each database.
    for i in range(num_dbs):
        denom = (metagraph.S + torch.ones_like(metagraph.S)).sum()
        db_size = (((metagraph.S[i] + 1) / denom) * filling_space).item()
        n_chunks = int(db_size / CHUNK_SIZE) + 1
        path = os.path.join(config.db_path, config.wallet.name, config.wallet.hotkey)

        # Determine miner and validator keys based on the validator flag.
        miner_key = metagraph.hotkeys[i] if config.validator else wallet.hotkey.ss58_address
        validator_key = wallet.hotkey.ss58_address if config.validator else metagraph.hotkeys[i]

        seed = f"{miner_key}{validator_key}"

        # Create the allocation dictionary.
        alloc = {
            "i": i,
            "block": metagraph.block.item(),
            "subtensor": sub.chain_endpoint,
            "wallet_name": config.wallet.name,
            "wallet_hotkey": config.wallet.hotkey,
            "netuid": config.netuid,
            "path": path,
            "miner": miner_key,
            "validator": validator_key,
            "stake": int(metagraph.S[i].item()),
            "size": int(db_size),
            "h_size": human_readable_size(db_size),
            "threshold": config.threshold,
            "threshold_space": int(filling_space),
            "h_threshold_space": human_readable_size(filling_space),
            "threshold_percent": 100 * (db_size / filling_space),
            "availble_space": int(available_space),
            "h_available_space": human_readable_size(available_space),
            "available_percent": 100 * (db_size / available_space),
            "n_chunks": n_chunks,
            "chunk_size": int(CHUNK_SIZE),
            "seed": seed,
        }
        bt.logging.debug(f'partition_{i}: {json.dumps(alloc, indent=4)}')
        allocations.append(alloc)

    return allocations 

def main( config ):
    bt.logging( config = config )
    bt.logging.info( config  )
    allocations = allocate( config )
    generate( config, allocations )
    if not config.validator:
        verify( config, allocations )

if __name__ == "__main__":
    main( get_config() )
