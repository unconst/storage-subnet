# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Bittensor Validator Template:
# TODO(developer): Rewrite based on protocol defintion.

# Step 1: Import necessary libraries and modules
import os
import typing
import time
import random
import uvicorn
import argparse
import hashlib
import sqlite3
import secrets
import bittensor as bt
import database
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile
from pathlib import Path

# Import this repo
import storage

LIMIT_LOOP_COUNT = 3 # Maximum loop_count for every loop
CHUNK_STORE_COUNT = 1 # Number of chunks to store
CHUNK_SIZE = 1 << 22    # 1 MB
MIN_N_CHUNKS = 1 << 8  # the minimum number of chunks a miner should provide at least is 1GB (CHUNK_SIZE * MIN_N_CHUNKS)
TB_NAME = "saved_data"

# Create a database to store the given file
def create_database_for_file(db_name):
    db_base_path = f"{config.db_root_path}/{config.wallet.name}/{config.wallet.hotkey}/data"
    if not os.path.exists(db_base_path):
        os.makedirs(db_base_path, exist_ok=True)

    conn = sqlite3.connect(f"{db_base_path}/{db_name}.db")
    cursor = conn.cursor()
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {TB_NAME} (chunk_id INTEGER PRIMARY KEY, miner_hotkey TEXT, miner_key INTEGER)")
    conn.close()

# Save the chunk(index : chunk_number) to db_name
def save_chunk_location(db_name, chunk_number, store_resp_list):
    conn = sqlite3.connect(f"{config.db_root_path}/{config.wallet.name}/{config.wallet.hotkey}/data/{db_name}.db")
    cursor = conn.cursor()

    for store_resp in store_resp_list:
        cursor.execute(f"INSERT INTO {TB_NAME} (chunk_id, miner_hotkey, miner_key) VALUES (?, ?, ?)", (chunk_number, store_resp['hotkey'], store_resp['key']))
    conn.commit()
    conn.close()

# Update the hash value of miner table
def update_miner_hash(validator_hotkey, store_resp_list):
    for store_resp in store_resp_list:
        miner_hotkey = store_resp['hotkey']
        db_path = f"{config.db_root_path}/{config.wallet.name}/{config.wallet.hotkey}/DB-{miner_hotkey}-{validator_hotkey}"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        update_request = f"UPDATE DB{miner_hotkey}{validator_hotkey} SET hash = ? where id = ?"
        cursor.execute(update_request, (store_resp['hash'], store_resp['key']))
        conn.commit()
        conn.close()

# Hash the given data
def hash_data(data):
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.digest()

# Generate random hash string
def generate_random_hash_str():
    random_bytes = secrets.token_bytes(32)  # 32 bytes for SHA-256
    hashed = hashlib.sha256(random_bytes).hexdigest()
    return str(hashed)

# Get config.
def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_root_path",
        default=os.path.expanduser("~/bittensor-db"),
        help="Validator hashes",
    )
    parser.add_argument(
        "--no_bridge", action="store_true", help="Run without bridging to the network."
    )
    # Adds override arguments for network and netuid.
    parser.add_argument("--netuid", type=int, default=7, help="The chain subnet uid.")
    # Adds subtensor specific arguments i.e. --subtensor.chain_endpoint ... --subtensor.network ...
    bt.subtensor.add_args(parser)
    # Adds logging specific arguments i.e. --logging.debug ..., --logging.trace .. or --logging.logging_dir ...
    bt.logging.add_args(parser)
    # Adds wallet specific arguments i.e. --wallet.name ..., --wallet.hotkey ./. or --wallet.path ...
    bt.wallet.add_args(parser)
    # Parse the config (will take command-line arguments if provided)
    config = bt.config(parser)
    return config

app = FastAPI()

def main( config ):

    # The wallet holds the cryptographic key pairs for the validator.
    wallet = bt.wallet( config = config )
    bt.logging.info(f"Wallet: {wallet}")

    # Dendrite is the RPC client; it lets us send messages to other nodes (axons) in the network.
    dendrite = bt.dendrite( wallet = wallet )
    bt.logging.info(f"Dendrite: {dendrite}")

    # The subtensor is our connection to the Bittensor blockchain.
    subtensor = bt.subtensor( config = config )
    bt.logging.info(f"Subtensor: {subtensor}")

    # The metagraph holds the state of the network, letting us know about other miners.
    metagraph = subtensor.metagraph( config.netuid )
    bt.logging.info(f"Metagraph: {metagraph}")

    app = FastAPI()

    origins = [
        "http://localhost:3000",  # React app's address
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/store/")
    async def store( file: UploadFile = File(...) ):
        # Find all active nodes
        ping_response = await dendrite.forward(
            metagraph.axons,
            storage.protocol.Ping(),
            deserialize=True,
        )
        
        active_axons = [axon for i, axon in enumerate(metagraph.axons) if ping_response[i] == "OK"]

        db_name = generate_random_hash_str()
        create_database_for_file(db_name)
        # Number of miners
        axon_count = len(active_axons)
        
        chunk_number = 0
        while chunk := await file.read(CHUNK_SIZE):
            hex_representation = ''.join([f'\\x{byte:02x}' for byte in chunk])

            # Construct the desired string
            chunk = f"b'{hex_representation}'"
            store_resp_list = []
            index_list = []
            loop_count = 0
            while len(store_resp_list) < CHUNK_STORE_COUNT and loop_count < LIMIT_LOOP_COUNT:
                loop_count = loop_count + 1
                #Generate list of miners who will receive chunk, count: CHUNK_STORE_COUNT
                store_count = min(CHUNK_STORE_COUNT * 2, axon_count - len(index_list))
                for i in range(axon_count):
                    while True:
                        chunk_i = random.randint(0, axon_count - 1)
                        if chunk_i in index_list:
                            continue
                        index_list.append(chunk_i)
                        break
                
                #Transfer the chunk to selected miners
                axons_list = []
                for index in index_list:
                    axons_list.append(active_axons[index])

                store_response = await dendrite.forward(
                    axons_list,
                    storage.protocol.Store(data = chunk),
                    deserialize=True,
                )
                
                for index, key in enumerate(store_response):
                    if key != -1: #Miner saved the chunk
                        store_resp_list.append({"key": key, "hotkey": axons_list[index].hotkey, "hash": hash_data(chunk.encode('utf-8'))})

            if not store_resp_list:
                return {"status": False, "error_msg" : "NETWORK IS BUSY"}
            
            #Save the key to db
            save_chunk_location(db_name, chunk_number, store_resp_list)
            
            #Update the hash value of the key that miner responded
            update_miner_hash(wallet.hotkey.ss58_address, store_resp_list)

            chunk_number += 1
        database.save_file_info(file.filename, db_name)
        return {"status": True, "hash":db_name}

    @app.get("/retrieve/")
    async def retrieve( hash: str ) -> str:
        db_name = hash
        output_filename = time.time()
        db_path = f"{config.db_root_path}/{config.wallet.name}/{config.wallet.hotkey}/data/{db_name}.db"

        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Invalid hash value")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {TB_NAME}")
        rows = cursor.fetchall()

        chunk_size = max(rows, key=lambda obj: obj[0])[0] + 1
        
        hotkey_axon_dict = {}
        for axon in metagraph.axons:
            hotkey_axon_dict[axon.hotkey] = axon

        file_path = str(time.time())

        validator_hotkey = wallet.hotkey.ss58_address

        with open(file_path, 'wb') as output_file:
            for id in range(chunk_size):
                cursor.execute(f"SELECT * FROM {TB_NAME} where chunk_id = {id}")
                rows = cursor.fetchall()
                hotkey_list = [row[1] for row in rows]
                key_list = {row[1]:row[2] for row in rows}
                axons_list = [hotkey_axon_dict[hotkey] for hotkey in hotkey_list]

                miner_hotkey = axons_list[0].hotkey
                db = sqlite3.connect( f"{config.db_root_path}/{config.wallet.name}/{config.wallet.hotkey}/DB-{miner_hotkey}-{validator_hotkey}")
                validation_hash = (
                    db.cursor()
                    .execute(
                        f"SELECT hash FROM DB{miner_hotkey}{validator_hotkey} WHERE id=?", (key_list[miner_hotkey],)
                    )
                    .fetchone()[0]
                )
                db.close()
                
                chunk_data = ''
                loop_count = 0
                while not chunk_data and loop_count < LIMIT_LOOP_COUNT:
                    loop_count = loop_count + 1
                    retrieve_response = await dendrite.forward(
                        axons_list,
                        storage.protocol.Retrieve(key_list = key_list),
                        deserialize=True,
                    )
                    for index, retrieve_resp in enumerate(retrieve_response):
                        if retrieve_resp and hash_data(retrieve_resp.encode('utf-8')) == validation_hash:
                            chunk_data = retrieve_resp
                            break
                if not chunk_data:
                    raise HTTPException(status_code=404, detail=f"Chunk_{id} is missing!")
                else:
                    hex_representation = chunk_data.split("'")[1]
                    clean_hex_representation = ''.join(c for c in hex_representation if c in '0123456789abcdefABCDEF')
                    # Convert the cleaned hexadecimal representation back to bytes
                    chunk_data = bytes.fromhex(clean_hex_representation)
                    output_file.write(chunk_data)
        conn.close()
        path = Path(file_path)
        filename = database.get_filename_for_hash(hash)
        try:
            return StreamingResponse(open(path, "rb"), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")
    # Run front end.
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
if __name__ == "__main__":
    config = get_config()
    main( config )
