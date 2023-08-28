import rocksdb
import asyncio
import argparse
import hashlib
from tqdm import tqdm

async def verify_hashes(data_path, hashes_path):
    data_db = rocksdb.RocksDB(db_path=data_path, options=rocksdb.Options(create_if_missing=True))
    hashes_db = rocksdb.RocksDB(db_path=hashes_path, options=rocksdb.Options(create_if_missing=True))

    # Assuming keys are strings "0", "1", "2", ...
    i = 0
    pbar = tqdm(desc="Verifying", unit="keys", dynamic_ncols=True)
    while True:
        data_key = str(i)
        data_value = (await data_db.get(rocksdb.ReadOptions(), data_key)).value
        stored_hash = (await hashes_db.get(rocksdb.ReadOptions(), data_key)).value
        if not data_value:
            break  # Exit loop if key not found

        computed_hash = hashlib.sha256(data_value.encode('utf-8')).hexdigest()
        if computed_hash != stored_hash:
            print(f"Hash mismatch for key {i}!")
            return

        i += 1
        pbar.update(1)  # Update the progress bar by one step

    print("All hashes verified successfully!")
    await data_db.close()
    await hashes_db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify hashes between two RocksDB databases.")
    parser.add_argument("--path_to_data", required=True, help="Path to the data database.")
    parser.add_argument("--path_to_hashes", required=True, help="Path to the hashes database.")
    args = parser.parse_args()

    asyncio.run(verify_hashes(args.path_to_data, args.path_to_hashes))
