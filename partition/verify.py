import os
import json
import hashlib
import sqlite3
import argparse
from tqdm import tqdm
import bittensor as bt

def get_config() -> bt.config:
    parser = argparse.ArgumentParser(description="Rebase the database based on available memory and also")
    parser.add_argument("--db_path", required=False, default="~/bittensor-db", help="Path to the data database.")
    bt.wallet.add_args(parser)
    bt.logging.add_args(parser)
    return bt.config( parser )

def main( config ):

    # Get the partition fill and load it.
    bt.logging( config = config )
    parition_path = f"{os.path.expanduser( config.db_path )}/{config.wallet.name}/{config.wallet.hotkey}/partition.json"
    bt.logging.info(f"Verifying partitios from: {parition_path}")
    with open( parition_path, 'r' ) as fp:
        partition = json.load(fp)

    for db in partition:
        data_path = f"{ db['path'] }/data-{db['validator']}"
        hashes_path = f"{ db['path'] }/hashes-{db['validator']}"
        bt.logging.info(f"Verifying: \n\tData {data_path}\n\tHashes: {hashes_path}")

        # Connect to SQLite databases
        data_conn = sqlite3.connect(data_path)
        data_cursor = data_conn.cursor()
        hashes_conn = sqlite3.connect(hashes_path)
        hashes_cursor = hashes_conn.cursor()

        i = 0
        while True:
            data_key = str(i)
            
            # Fetch data from SQLite databases
            data_cursor.execute("SELECT data FROM DB{} WHERE id=?".format(db['seed']), (data_key,))
            data_value = data_cursor.fetchone()

            hashes_cursor.execute("SELECT data FROM DB{} WHERE id=?".format(db['seed']), (data_key,))
            stored_hash = hashes_cursor.fetchone()

            if not data_value:
                break  # Exit loop if key not found

            computed_hash = hashlib.sha256(data_value[0].encode('utf-8')).hexdigest()
            if computed_hash != stored_hash[0]:
                bt.logging.error(f"Hash mismatch for key {i}!")
                return

            i += 1

        bt.logging.success("All hashes verified successfully!\n")
        data_conn.close()
        hashes_conn.close()
        

if __name__ == "__main__":
    main( get_config() )
