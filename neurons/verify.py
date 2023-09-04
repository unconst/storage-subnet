import sqlite3


M = {
    "hash": False,
    "miner": "5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo",
    "n_chunks": 175,
    "path": "/Users/napoli/bittensor-db/default/miner/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh",
    "seed": "5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh",
    "validator": "5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"
}
V = 100

# Connect to the SQLite databases for data and hashes.
data_conn = sqlite3.connect(M)
hashes_conn = sqlite3.connect(V)
data_cursor = data_conn.cursor()
hashes_cursor = hashes_conn.cursor()

i = 0
while True:
    data_key = str(i)
            
    # Fetch data from the data database using the current key.
    data_cursor.execute(f"SELECT data FROM DB{data_alloc['seed']} WHERE id=?", (data_key,))
    data_value = data_cursor.fetchone()

    # Fetch the corresponding hash from the hashes database.
    hashes_cursor.execute(f"SELECT hash FROM DB{hash_allocs['seed']} WHERE id=?", (data_key,))
    stored_hash = hashes_cursor.fetchone()

    # If no data is found for the current key, exit the loop.
    if not data_value:
        break

    # Compute the hash of the fetched data.
    computed_hash = hashlib.sha256(data_value[0].encode('utf-8')).hexdigest()

    # Check if the computed hash matches the stored hash.
    if computed_hash != stored_hash[0]:
        bt.logging.error(f"Hash mismatch for key {i}!, computed hash: {computed_hash}, stored hash: {stored_hash[0]}")
        return
    else:
        bt.logging.success(f"Hash match for key {i}! computed hash: {computed_hash}, stored hash: {stored_hash[0]}")


    # Increment the key for the next iteration.
    i += 1

# Log the successful verification of the data.
bt.logging.success(f"Verified {data_alloc['path']} with hashes from {hash_allocs['path']}")

# Close the database connections.
data_conn.close()
hashes_conn.close()
