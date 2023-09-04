
<div align="center">

# **Bittensor Storage Subnet Prototype** <!-- omit in toc -->
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

---

### The Incentivized Internet <!-- omit in toc -->

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper)

</div>

---

This is a prototype incentive mechanism for storage where miners serve their harddrive space onto the network and prove its existence to validators. Miners are rewarded proportionally to the amount of space they can prove they have, and also allow encrypted data to be stored there by validators. The amount of space available to each validator is proportional to the amount of stake they have on the network.

---
Installing

Installs the python package and the rust binary.
```bash
python -m pip install -e # Installs the python package.
cd neurons/generate_db; cargo build --release # Builds the rust binary.
```

---
# Mining

To run the miner
```bash
python neurons/miner.py
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli wallet new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli btcli wallet new_hotkey
    --db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-db>  # This is where the partition will be created storing network data.
    --logging.debug # Run in debug mode, alternatively --logging.trace for trace mode
    --threshold <OPTIONAL: threshold i.e. 0.0001, default =  0.0001>  # The threshold for the partitioning algorithm which is the maximum amount of space the miner can use based on available.
    --netuid <OPTIONAL: the subnet netuid, defualt = 1> # This is the netuid of the storage subnet you are serving on.
    --subtensor.network <OPTIONAL: the bittensor chain endpoint, default = finney, local, test> # The chain endpoint to use to generate the partition.
    --restart <OPTIONAL: restart the partitioning process from the beginning, otherwise restarts from the last created chunk. default = False> # If true, the partitioning process restarts instead using a checkpoint.
    --steps_per_reallocate <OPTIONAL: the number of steps before reallocating, default = 1000> # The number of steps before reallocating.
```

---
# Validating

To run the validator
```bash
python neurons/validator.py
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli wallet new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli btcli wallet new_hotkey
    --db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-db>  # This is where the partition will be created storing network data.
    --logging.debug # Run in debug mode, alternatively --logging.trace for trace mode
    --netuid <OPTIONAL: the subnet netuid, defualt = 1> # This is the netuid of the storage subnet you are serving on.
    --subtensor.network <OPTIONAL: the bittensor chain endpoint, default = finney, local, test> # The chain endpoint to use to generate the partition.
```

---
# Allocating 

Allocates space on your machine based on the amount of stake other neurons have on the network. The allocation process is done by partitioning the space on your machine into chunks and assigning each chunk to a validator. The amount of space allocated to each validator is proportional to the amount of stake they have on the network. The allocation process is done by running the following command.

```bash
cd neurons/ # Navigate to the neurons directory.
cd generate_db; cargo build --release # Builds the rust binary.
python allocate.py # Runs the partitioning process.
    --db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-db>  # This is where the partition will be created storing network data.
    --netuid <OPTIONAL: the subnet netuid, defualt = 1> # This is the netuid of the storage subnet you are serving on.
    --threshold <OPTIONAL: threshold i.e. 0.0001, default =  0.0001>  # The threshold for the partitioning algorithm which is the maximum amount of space the miner can use based on available.
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli, btcli new_hotkey
    --no_prompt <OPTIONAL: does not wait for user input to confirm the allocation, default = False> # If true, the partitioning process will not wait for user input to confirm the allocation.
    --restart <OPTIONAL: restart the partitioning process from the beginning, otherwise restarts from the last created chunk. default = False> # If true, the partitioning process restarts instead using a checkpoint.
    --workers <OPTIONAL: number of concurrent workers to use, default = 10> # The number of concurrent workers to use to generate the partition.
    --subtensor.network <OPTIONAL: the bittensor chain endpoint, default = finney, local, test> # The chain endpoint to use to generate the partition.
    --logging.debug <OPTIONAL: run in debug mode, default = False> # If true, the partitioning process will run in debug mode.
    --validator <OPTIONAL: run the partitioning process as a validator, default = False> # If true, the partitioning process will run as a validator.

# Should create the files like the following, if --validator is set you will only see hash files.
>> /Users/user/<path>
>> └── <wallet_name>
>>     └── <wallet_hotkey>
>>         ├── data-5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1
>>         ├── data-5GZCGWuJgx3wGERm36WAV2cwS4D1KqpaYHg1ArGWDMoHvvNf
>>         ├── hashes-5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1
>>         ├── hashes-5GZCGWuJgx3wGERm36WAV2cwS4D1KqpaYHg1ArGWDMoHvvNf
>>         └── partition.json
```
All allocation details are stored in the `partition.json` file. You can view the contents of the file by running the following command.
```bash
cat ~/{db_path}/{wallet_name}{hotkey_name}/partition.json 
# Example output.
>> 
    {
        "path": "/Users/user/db_path/wallet_name/hotkey_name", # The path of the partition.
        "owner": "5CSkJdaN1HxDHsVev1BfzDkknGYg8Hxnsokio26m4GCPNcHQ", # The owner ss58 address of the partition.
        "validator": "5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1", # The validator ss58 address of the partition.
        "size": 17503128, # The size of the partition (bytest)
        "n_chunks": 350, # The number of chunks in the partition.
        "seed": "5CSkJdaN1HxDHsVev1BfzDkknGYg8Hxnsokio26m4GCPNcHQ5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1" # The DB seed used to generate the partition.
    },
```


---
# Frontend

You can bridge access to your validator via a frontend, this allows you to set values and retrieve them from the miners. To run the frontend, run the following command.
```bash
cd frontend # Navigate to the frontend directory.
npm install # Install the dependencies.
python bridge.py # Runs the bridge using the same key as your validator to get network access.
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli wallet new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli btcli wallet new_hotkey
yarn start # Starts the frontend server.
```
Then navigate to the localhost address in your browser http://localhost:3000/.

---

## License
This repository is licensed under the MIT License.
```text
# The MIT License (MIT)
# Copyright © 2023 Yuma Rao

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
```
