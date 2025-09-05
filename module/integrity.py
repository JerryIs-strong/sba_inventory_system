import hashlib
import json
import datetime
import pytz

timezone = pytz.timezone('Asia/Hong_Kong')

def writeMD5():
    db_hash = hashlib.md5(open('data/inventoryDB.json', 'rb').read()).hexdigest()
    
    with open('data/system.json', 'r') as system_file:
            data = json.load(system_file)

    data['hash'] = db_hash
    
    with open('data/system.json', 'w') as system_file:
        json.dump(data, system_file)

def sysInfo():
    with open('data/system.json') as system_file:
        data = json.load(system_file)
    return data

def verifyMD5():
    db_hash = hashlib.md5(open('data/inventoryDB.json', 'rb').read()).hexdigest()
    with open('data/system.json') as system_file:
        hash_record = json.load(system_file)["hash"]

    if db_hash == hash_record:
        return True
    else:
        return False
    
def initLogService():
    current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
    lid = datetime.datetime.now(timezone).strftime("%Y%m%d%H%M%S")
    with open(f"log/system_log_{current_date}.txt", "a") as f:
        f.write(f'LID: {lid} start\n')
    return lid

def log(message, transaction = False):
    current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
    if transaction:
        folder = "log/transaction"
        file_name = f"log_{current_date}.txt"
    else:
        folder = "log"
        file_name = f"system_log_{current_date}.txt"
    with open(f"{folder}/{file_name}", "a", encoding='utf-8') as f:
        f.write(f'{datetime.datetime.now(timezone)} {message}\n')