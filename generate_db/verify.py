import sqlite3
import argparse
import hashlib
from tqdm import tqdm

def verify_hashes(seed, data_path, hashes_path):
    # Connect to SQLite databases
    data_conn = sqlite3.connect(data_path)
    data_cursor = data_conn.cursor()
    
    hashes_conn = sqlite3.connect(hashes_path)
    hashes_cursor = hashes_conn.cursor()

    i = 0
    pbar = tqdm(desc="Verifying", unit="keys", dynamic_ncols=True)
    while True:
        data_key = str(i)
        
        # Fetch data from SQLite databases
        data_cursor.execute("SELECT data FROM {} WHERE id=?".format(seed), (data_key,))
        data_value = data_cursor.fetchone()

        hashes_cursor.execute("SELECT data FROM {} WHERE id=?".format(seed), (data_key,))
        stored_hash = hashes_cursor.fetchone()

        if not data_value:
            break  # Exit loop if key not found

        computed_hash = hashlib.sha256(data_value[0].encode('utf-8')).hexdigest()
        if computed_hash != stored_hash[0]:
            print(f"Hash mismatch for key {i}!")
            return

        i += 1
        pbar.update(1)  # Update the progress bar by one step

    print("All hashes verified successfully!")
    data_conn.close()
    hashes_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify hashes between two SQLite databases.")
    parser.add_argument("--seed", type=str, required=True, help="Seed to verify.")
    parser.add_argument("--path_to_data", required=True, help="Path to the data database.")
    parser.add_argument("--path_to_hashes", required=True, help="Path to the hashes database.")
    args = parser.parse_args()

    verify_hashes(args.seed, args.path_to_data, args.path_to_hashes)
