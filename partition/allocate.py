import os
import json
import torch
import shutil
import argparse
import subprocess
import bittensor as bt

def get_available_space(path):
    """Return the available space in bytes."""
    stat = os.statvfs(path)
    return stat.f_frsize * stat.f_bavail

def confirm_directory_deletion(directory):
    print(f"Are you sure you want to delete the previous partition files (data and hashes) under : {directory}? (yes/no)")
    response = input()
    if response.lower() in ['yes', 'y']:
        return True
    return False

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
    partitions = []
    for i in range( num_dbs ):
        denom = (metagraph.S + torch.ones_like(metagraph.S)).sum()
        db_size = ((metagraph.S[i] + 1)/denom) * filling_space
        n_chunks = int( db_size / int(config.chunk_size ) ) + 1
        path = f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}"
        seed = f"{wallet.hotkey.ss58_address}{metagraph.hotkeys[i]}"
        partition = {
            "i": i,
            "block": metagraph.block.item(),
            "subtensor": sub.chain_endpoint,
            "wallet_name": config.wallet.name,
            "wallet_hotkey": config.wallet.hotkey,
            "netuid": config.netuid,
            "path": path,
            "owner": wallet.hotkey.ss58_address,
            "validator": metagraph.hotkeys[i],
            "stake": int(metagraph.S[i].item()),
            "size": int(db_size),
            "h_size": human_readable_size(db_size),
            "threshold": config.threshold,
            "threshold_space": int(filling_space),
            "h_threshold_space": human_readable_size(filling_space),
            "threshold_percent": 100 * (float(db_size) / float(filling_space)),
            "availble_space": int(available_space),
            "h_available_space": human_readable_size(available_space),
            "available_percent": 100 * (float(db_size) / float(available_space)),
            "n_chunks": int(n_chunks),
            "chunk_size": int(config.chunk_size),
            "seed": seed,
        }
        bt.logging.info( f'   partition_{i}: {str(json.dumps(partition, indent=4))}' )
        partitions.append(partition)
    partition_file = f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}/partition.json"
    if os.path.exists(f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}"):
        if confirm_directory_deletion(f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}"):
            shutil.rmtree(f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}")
        else:
            exit()
    if not os.path.exists(f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}"):
        os.makedirs(f"{config.db_path}/{config.wallet.name}/{config.wallet.hotkey}")
    bt.logging.info( f'Writing partitions to {partition_file}' )
    with open(partition_file, 'w') as f:
        json.dump(partitions, f, indent=4)

if __name__ == "__main__":
    main( get_config() )
