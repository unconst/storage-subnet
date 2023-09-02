
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
# Partitioning

To allocate your available space fun the following command, this does not create data but instead determines the correct allocation of space on your machine based on your choosed threshold and the stake of other participants in the network.
```bash
python partition/allocate.py 
    --netuid <OPTIONAL: the subnet netuid, defualt = 1> # This is the netuid of the storage subnet you are serving on.
    --threshold <OPTIONAL: threshold i.e. 0.0001, default =  0.0001>  # The threshold for the partitioning algorithm which is the maximum amount of space the miner can use based on available.
    ---db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-db>  # This is where the partition will be created storing network data.
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli, btcli new_hotkey
# Outputs the following file under your wallet path.
>> /Users/user/<db_path> # The root DB directory.
>> └── <wallet_name> # The wallet name of your miner/validator.
>>     └── <wallet_hotkey> # The hotkey of your miner/validator.
>>         └── partition.json # The file containing the allocation details.
```

You can view the created partition by running the following command.
```bash
cat ~/{db_path}/{wallet_name}{hotkey_name}/partition.json 
# Example output.
>> 
    {
        "i": 0, # The index of the allocation
        "block": 1737, # The block at which the allocation was created.
        "netuid": 1, # The netuid of the subnet.
        "subtensor": "ws://127.0.0.1:9946", # The chain endpoint.
        "wallet_name": "my_wallet", # The name of the wallet.
        "wallet_hotkey": "my_hotkey", # The hotkey of the wallet.
        "path": "/Users/user/db_path/wallet_name/hotkey_name", # The path of the partition.
        "owner": "5CSkJdaN1HxDHsVev1BfzDkknGYg8Hxnsokio26m4GCPNcHQ", # The owner ss58 address of the partition.
        "validator": "5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1", # The validator ss58 address of the partition.
        "stake": 0, # The stake of the validator.
        "size": 17503128, # The size of the partition (bytest)
        "h_size": "16.69 MB", # The size of the partition (human readable)
        "threshold": 0.0001, # The threshold of the partition (i.e. the maximum amount of space the miner can use based on available)
        "threshold_space": 35006255, # The threshold of the partition (i.e. the maximum amount of space the miner can use based on available)
        "h_threshold_space": "33.38 MB", # The human readable threshold of the partition (i.e. the maximum amount of space the miner can use based on available)
        "threshold_percent": 50.000001279771276, # The percent of the threshold of the partition (i.e. the maximum amount of space the miner can use based on available)
        "availble_space": 350062551040, # The total available space on the partition.
        "h_available_space": "326.02 GB", # The total available space on the partition (human readable)
        "available_percent": 0.005000000127977128, # The proportion of spaces used based on available.
        "n_chunks": 350, # The number of chunks in the partition.
        "chunk_size": 100000, # The size of each chunk.
        "seed": "5CSkJdaN1HxDHsVev1BfzDkknGYg8Hxnsokio26m4GCPNcHQ5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1" # The DB seed used to generate the partition.
    },
```

To fill the partition, i.e. generate the random data on your machine, you need to first build the rust script under `scripts/generate_db` by running the following command.
```bash
cd partition/generate_db
cargo build --release
```

Once this script is built you can fill all your paritition files in parallel by running the following command. 
```bash
python partition/generate.py 
    --db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-db>  # This is where the partition will be created storing network data.
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli wallet new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli btcli wallet new_hotkey
    --only_hash <OPTIONAL: only hash the data i.e. for validation, default = False> # If true, only hashes the data, otherwise creates the data too, validators should use this.
    --restart <OPTIONAL: restart the fill process from the beginning, otherwise restarts from the last created chunk. default = False> # If true, the hashes and data creation process restarts instead using a checkpoint.

# Should create the files like the following.
>> /Users/user/<path>
>> └── <wallet_name>
>>     └── <wallet_hotkey>
>>         ├── data-5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1
>>         ├── data-5GZCGWuJgx3wGERm36WAV2cwS4D1KqpaYHg1ArGWDMoHvvNf
>>         ├── hashes-5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1
>>         ├── hashes-5GZCGWuJgx3wGERm36WAV2cwS4D1KqpaYHg1ArGWDMoHvvNf
>>         └── partition.json
```

If you generated both the data and hashes you can verify them by running the following command.
```bash
python partition/verify.py 
    --db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-dbn>  # This is where the partition will be created storing network data.
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli wallet new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli btcli wallet new_hotkey

#Example output
>> 2023-09-02 12:01:06.548 |       INFO       | Verifying partitios from: /Users/napoli/bittensor-db/default/default/partition.json
>> 2023-09-02 12:01:06.550 |       INFO       | Verifying: 
>>         Data /Users/napoli/bittensor-db/default/default/data-5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1
>>         Hashes: /Users/napoli/bittensor-db/default/default/hashes-5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1
>> 2023-09-02 12:01:06.626 |     SUCCESS      | All hashes verified successfully!
>> 2023-09-02 12:01:06.627 |       INFO       | Verifying: 
>>         Data /Users/napoli/bittensor-db/default/default/data-5GZCGWuJgx3wGERm36WAV2cwS4D1KqpaYHg1ArGWDMoHvvNf
>>         Hashes: /Users/napoli/bittensor-db/default/default/hashes-5GZCGWuJgx3wGERm36WAV2cwS4D1KqpaYHg1ArGWDMoHvvNf
>> 2023-09-02 12:01:06.698 |     SUCCESS      | All hashes verified successfully!
```
</div>

--- 
### Running the Miner

To run a miner follow the instruction from above to generate your parition. Once your parition is verified and created your miner can serve it onto the network. To run the miner run the following command.
```bash
python neurons/miner.py
    --wallet.name <OPTIONAL: your miner wallet, default = default> # Must be created using the bittensor-cli, btcli wallet new_coldkey
    --wallet.hotkey <OPTIONAL: your validator hotkey, defautl = default> # Must be created using the bittensor-cli btcli wallet new_hotkey
    --db_path <OPTIONAL: path where you want the DB files stored, default = ~/bittensor-db>  # This is where the partition will be created storing network data.

---

# Installation
This repository requires python3.8 or higher. To install, simply clone this repository and install the requirements.
```bash
git clone https://github.com/opentensor/bittensor-subnet-template.git
cd bittensor-subnet-template
python -m pip install -r requirements.txt
python -m pip install -e .
```

</div>

---

Once you have installed this repo and attained your subnet via the instructions in the nested docs (staging, testing, or main) you can run the miner and validator with the following commands.
```bash
# To run the miner
python -m neurons/miner.py 
    --netuid <your netuid>  # Must be attained by following the instructions in the docs/running_on_*.md files
    --subtensor.chain_endpoint <your chain url>  # Must be attained by following the instructions in the docs/running_on_*.md files
    --wallet.name <your miner wallet> # Must be created using the bittensor-cli
    --wallet.hotkey <your validator hotkey> # Must be created using the bittensor-cli
    --logging.debug # Run in debug mode, alternatively --logging.trace for trace mode

# To run the validator
python -m neurons/validator.py 
    --netuid <your netuid> # Must be attained by following the instructions in the docs/running_on_*.md files
    --subtensor.chain_endpoint <your chain url> # Must be attained by following the instructions in the docs/running_on_*.md files
    --wallet.name <your validator wallet>  # Must be created using the bittensor-cli
    --wallet.hotkey <your validator hotkey> # Must be created using the bittensor-cli
    --logging.debug # Run in debug mode, alternatively --logging.trace for trace mode
```

</div>

---

# Updating the template
The code contains detailed documentation on how to update the template. Please read the documentation in each of the files to understand how to update the template. There are multiple TODOs in each of the files which you should read and update.

</div>

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
