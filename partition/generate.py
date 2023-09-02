import os
import json
import argparse
import threading
import subprocess
import bittensor as bt
from concurrent.futures import ThreadPoolExecutor

def get_config() -> bt.config:
    parser = argparse.ArgumentParser(description="Rebase the database based on available memory and also")
    parser.add_argument("--only_hash", action='store_true', default=False, help="Only hash the db.")
    parser.add_argument("--restart", action='store_true',  default=False, help="Restart the db.")
    parser.add_argument("--db_path", required=False, default="~/bittensor-db", help="Path to the data database.")
    parser.add_argument("--workers", required=False, default=10, help="Number of concurrent workers to use.")

    bt.wallet.add_args(parser)
    bt.logging.add_args(parser)
    return bt.config( parser )

def run_cargo_command(db, hash = False, restart:bool = False):
    db_path = db['path']
    if not os.path.exists(db_path):
        os.makedirs(db_path)
    if hash:
        file_path = f"{db_path}/hashes-{db['validator']}"
    else:
        file_path = f"{db_path}/data-{db['validator']}"
    cmd = [
        "./target/release/storer_db_project",
        "--path", file_path,
        "--n", str(db['n_chunks']),
        "--size", str(db['chunk_size']),
        "--seed", db['seed'],
    ]
    if hash:
        cmd.append("--hash")
    if restart:
        cmd.append("--delete")
        
    cargo_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_db")
    result = subprocess.run(cmd, cwd=cargo_directory, capture_output=False, text=True)
    if result.stderr:
        bt.logging.error(f"Failed: {file_path}")

def main( config ):

    # Get the partition fill and load it.
    bt.logging( config = config )
    parition_path = f"{os.path.expanduser( config.db_path )}/{config.wallet.name}/{config.wallet.hotkey}/partition.json"
    bt.logging.info(f"Loading partition from: {parition_path}")
    with open( parition_path, 'r' ) as fp:
        partition = json.load(fp)

    # Use ThreadPoolExecutor to manage the threads
    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        futures = []
        for db in partition:
            # Submit tasks to the thread pool
            future = executor.submit(run_cargo_command, db, True, config.restart)
            futures.append(future)
            if not config.only_hash:
                future = executor.submit(run_cargo_command, db, False, config.restart)
                futures.append(future)
        

if __name__ == "__main__":
    main( get_config() )
