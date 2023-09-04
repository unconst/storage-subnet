import bittensor as bt
import allocate
import os
import json
import sqlite3
import hashlib

bt.trace()
mw = bt.wallet(hotkey = 'miner')
vm = bt.wallet(hotkey = 'validator')
print (f"miner: {mw}")
print (f"validator: {vm}")


v_path = f"/Users/napoli/bittensor-db/default/validator/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"
v_allocations = [
    {
        'path': v_path,
        'n_chunks': 110,
        'seed': f"{mw.hotkey.ss58_address}{vm.hotkey.ss58_address}",
        'miner': mw.hotkey.ss58_address,
        'validator': vm.hotkey.ss58_address,
        'hash': True,
    }
]
m_path = f"/Users/napoli/bittensor-db/default/miner/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"
m_allocations = [
    {
        'path': m_path,
        'n_chunks': 110,
        'seed': f"{mw.hotkey.ss58_address}{vm.hotkey.ss58_address}",
        'miner': mw.hotkey.ss58_address,
        'validator': vm.hotkey.ss58_address,
        'hash': False,
    }
]
allocate.generate( v_allocations, no_prompt = True, workers = 10, restart = False )
allocate.generate( m_allocations, no_prompt = True, workers = 10, restart = False )
allocate.verify( m_allocations, v_allocations )


# # Generate allocations for the validator.
# v_path = f"/Users/napoli/bittensor-db/default/validator/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"
# v_allocations_1 = [
#     {
#         'path': v_path,
#         'n_chunks': 100,
#         'seed': f"{mw.hotkey.ss58_address}{vm.hotkey.ss58_address}",
#         'miner': mw.hotkey.ss58_address,
#         'validator': vm.hotkey.ss58_address,
#         'hash': True,
#     }
# ]

# allocate.generate( v_allocations_1, no_prompt = True, workers = 10, restart = True )
# import sqlite3
# conn = sqlite3.connect(v_allocations_1[0]['path'])
# cursor = conn.cursor()
# cursor.execute(f"SELECT data FROM DB{v_allocations_1[0]['seed']} WHERE id=?", (str(1),))
# stored_data = cursor.fetchone()
# cursor.execute(f"SELECT hash FROM DB{v_allocations_1[0]['seed']} WHERE id=?", (str(1),))
# stored_hash = cursor.fetchone()
# print (f"stored_data: {stored_data[0][-10:]}, {stored_hash}")

# # Generate allocations for the validator.
# v_path = f"/Users/napoli/bittensor-db/default/validator/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"
# v_allocations_2 = [
#     {
#         'path': v_path,
#         'n_chunks': 100,
#         'seed': f"{mw.hotkey.ss58_address}{vm.hotkey.ss58_address}",
#         'miner': mw.hotkey.ss58_address,
#         'validator': vm.hotkey.ss58_address,
#         'hash': False,
#     }
# ]

# allocate.generate( v_allocations_2, no_prompt = True, workers = 10, restart = True )
# import sqlite3
# conn = sqlite3.connect(v_allocations_2[0]['path'])
# cursor = conn.cursor()
# cursor.execute(f"SELECT data FROM DB{v_allocations_2[0]['seed']} WHERE id=?", (str(1),))
# stored_data = cursor.fetchone()
# cursor.execute(f"SELECT hash FROM DB{v_allocations_2[0]['seed']} WHERE id=?", (str(1),))
# stored_hash = cursor.fetchone()
# computed_hash = hashlib.sha256(stored_data[0].encode('utf-8')).hexdigest()
# print (f"stored_data: {stored_data[0][-10:]}, {stored_hash} {computed_hash}")

# # Generate allocations for the miner.
# m_path = f"/Users/napoli/bittensor-db/default/miner/DB-5F46RtCpDtdg9Dp29oiwZzFhMJjYhFZVZQTS18H1FjAhMZZo-5FWxgnZx4FjjfASTxGd11W8w7WVtWSXXvKd9G6UTjyoqyNhh"
# m_allocations = [
#     {
#         'path': m_path,
#         'n_chunks': 100,
#         'seed': f"{mw.hotkey.ss58_address}{vm.hotkey.ss58_address}",
#         'miner': mw.hotkey.ss58_address,
#         'validator': vm.hotkey.ss58_address,
#         'hash': False,
#     }
# ]
# allocate.generate( m_allocations, no_prompt = True, workers = 10, restart = True )
# import sqlite3
# conn = sqlite3.connect(m_allocations[0]['path'])
# cursor = conn.cursor()
# cursor.execute(f"SELECT data FROM DB{m_allocations[0]['seed']} WHERE id=?", (str(1),))
# stored_data = cursor.fetchone()
# cursor.execute(f"SELECT hash FROM DB{m_allocations[0]['seed']} WHERE id=?", (str(1),))
# stored_hash = cursor.fetchone()
# computed_hash = hashlib.sha256(stored_data[0].encode('utf-8')).hexdigest()
# print (f"stored_data: {stored_data[0][-10:]}, {stored_hash} {computed_hash}")


# allocate.verify(m_allocations, v_allocations_2 )
# allocate.verify(m_allocations, v_allocations_1 )

# allocate.generate( 
#     allocations = v_allocations,
#     no_prompt = False,  # If True, no prompt will be shown
#     workers = 10,  # The number of concurrent workers to use for generation. Default is 10.
#     only_hash = True, # The validator only generates hashes
#     restart = True # Dont restart the generation from empty files.
# )

# db = sqlite3.connect(f"/Users/napoli/bittensor-db/default/validator/hashes-{mw.hotkey.ss58_address}-{vm.hotkey.ss58_address}")
# cursor = db.cursor()
# cursor.execute(f"SELECT id FROM DB{v_allocations[0]['seed']}")
# all_ids = cursor.fetchall()
# bt.logging.error(f"Available ids: {all_ids}")

