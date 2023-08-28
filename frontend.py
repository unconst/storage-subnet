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
import uvicorn
import argparse
import threading
import bittensor as bt
from fastapi import FastAPI

# Import this repo
import storage

# Get config.
def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument( '--netuid', type = int, default = 1, help = "The chain subnet uid." )
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)
    bt.subtensor.add_args(parser)
    config =  bt.config(parser)
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

    @app.get("/store/")
    def store( key: str, data: str ):
        dendrite.query(
            # Send the query to all axons in the network.
            metagraph.axons,
            # Construct a dummy query.
            storage.protocol.Store( key = key, data = data ), # Construct a dummy query.
            # All responses have the deserialize function called on them before returning.
            deserialize = True, 
        )

    @app.get("/retrieve/")
    def retrieve( key: str ):
        retrieve_responses = dendrite.query(
            # Send the query to all axons in the network.
            metagraph.axons,
            # Construct a dummy query.
            storage.protocol.Retrieve( key = key ), # Construct a dummy query.
            # All responses have the deserialize function called on them before returning.
            deserialize = True, 
        )
        return {"data": f"Data for key: {retrieve_responses}"}
    
    # Run front end.
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
if __name__ == "__main__":
    main( get_config() )
