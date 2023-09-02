import os
import json
import argparse
import threading
import subprocess
import bittensor as bt

def get_config() -> bt.config:
    parser = argparse.ArgumentParser(description="Rebase the database based on available memory and also")
    parser.add_argument("--only_hash", action='store_true', default=False, help="Only hash the db.")
    parser.add_argument("--restart", action='store_true',  default=False, help="Restart the db.")
    parser.add_argument("--db_path", required=False, default="~/bittensor-db", help="Path to the data database.")
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
    # Get the partition fill and load it.
    bt.logging( config = config )
    parition_path = f"{os.path.expanduser( config.db_path )}/{config.wallet.name}/{config.wallet.hotkey}/partition.json"
    bt.logging.info(f"Loading partition from: {parition_path}")
    with open( parition_path, 'r' ) as fp:
        partition = json.load(fp)
    threads = []
    for db in partition:
        thread = threading.Thread(target=run_cargo_command, args=(db,False,config.restart))
        thread.start()
        threads.append(thread)
        if not config.only_hash:
            thread = threading.Thread(target=run_cargo_command, args=(db,True,config.restart))
            thread.start()
            threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

        

if __name__ == "__main__":
    main( get_config() )
