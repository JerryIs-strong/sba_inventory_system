import hashlib
import json

def writeMD5():
    db_hash = hashlib.md5(open('data/inventoryDB.json', 'rb').read()).hexdigest()
    
    with open('data/system.json', 'r') as system_file:
            data = json.load(system_file)

    data['hash'] = db_hash
    
    with open('data/system.json', 'w') as system_file:
        json.dump(data, system_file)

def verifyMD5():
    db_hash = hashlib.md5(open('data/inventoryDB.json', 'rb').read()).hexdigest()
    with open('data/system.json') as system_file:
        hash_record = json.load(system_file)["hash"]

    if db_hash == hash_record:
        return True
    else:
        return False