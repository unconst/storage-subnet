import os
import torch
import argparse
import subprocess
import bittensor as bt

def get_available_space(path):
    """Return the available space in bytes."""
    stat = os.statvfs(path)
    return stat.f_frsize * stat.f_bavail

def calculate_number_of_chunks(available_space, chunk_size, threshold=0.0001):
    """Calculate the number of chunks that can be created without exceeding the threshold."""
    total_space = available_space * threshold
    return int(total_space / chunk_size)

def human_readable_size(size):
    """Convert a size in bytes to a human-readable format."""
    
    # Define the thresholds and units
    thresholds = [1<<30, 1<<20, 1<<10]  # GB, MB, KB thresholds in bytes
    units = ["GB", "MB", "KB", "bytes"]

    for threshold, unit in zip(thresholds, units):
        if size >= threshold:
            return f"{size / threshold:.2f} {unit}"

    return f"{size} bytes"

def get_config() -> bt.config:
    parser = argparse.ArgumentParser(description="Rebase the database based on available memory and also")
    parser.add_argument("--netuid", type=int, default=1, required=False, help="Netuid to rebase into")
    parser.add_argument("--threshold", type=float, default=0.0001, required=False, help="Size of path to fill")
    parser.add_argument("--chunk_size", type=float, default=100000, required=False, help="Size of data chunks to rebase.")
    parser.add_argument("--db_path", required=False, default="~/bittensor-db", help="Path to the data database.")
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    return bt.config( parser )    

def main( config ):

    config.db_path = os.path.expanduser( config.db_path )
    bt.logging( config = config )
    bt.logging.info( config  )
    sub = bt.subtensor( config = config )
    wallet = bt.wallet( config = config )
    metagraph = sub.metagraph( netuid = config.netuid )

    bt.logging.info( f'Partitioning path:{config.db_path} at threshold: {config.threshold}' )

    available_space = get_available_space( config.db_path )
    filling_space = available_space * config.threshold
    bt.logging.info( f'Available space: {human_readable_size(available_space)}' )
    bt.logging.info( f'Using: {human_readable_size(filling_space)} bytes' )

    num_dbs = metagraph.n.item()
    bt.logging.info( f'Creating: {num_dbs} databases with under paths and sizes' )
    paths = []
    sizes = []
    chunks = []
    for i in range( num_dbs ):
        denom = (metagraph.S + torch.ones_like(metagraph.S)).sum()
        size = ((metagraph.S[i] + 1)/denom) * filling_space
        n_chunks = calculate_number_of_chunks( available_space, config.chunk_size, config.threshold )
        path = f"{config.db_path}/DB-{wallet.hotkey.ss58_address[:5]}-{metagraph.hotkeys[i][:5]}"
        bt.logging.info( f'   size: {human_readable_size(size)} --- n_chunks: {n_chunks} --- path: {path}' )
        paths.append( path )
        sizes.append( size )
        chunks.append( n_chunks )
    
    for i in range( num_dbs ):
        path = paths[i]
        size = sizes[i]
        n_chunks = chunks[i]
        seed = f"{wallet.hotkey.ss58_address}{metagraph.hotkeys[i]}"
        bt.logging.info( f'Creating DB with: \nsize: {size} \nn_chunks: {n_chunks} \nseed: {seed} \npath: {path}' )
        cmd = [
            "cargo", "run", "--",
            "--path", path,
            "--n", str(n_chunks),
            "--size", str(config.chunk_size),
            "--seed", seed,
            "--delete"
        ]
        env = {
            **dict(os.environ),
            "RUST_LOG": "info"
        }
        cargo_directory = os.path.join(os.getcwd(), "generate_db")
        result = subprocess.run(cmd, env=env, cwd=cargo_directory, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

if __name__ == "__main__":
    main( get_config() )
