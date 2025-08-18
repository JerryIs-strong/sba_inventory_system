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
        version = data["version"]
        pversion = data["p_version"]
    return version, pversion

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

def endLogService(lid, save = False):
    current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
    log_start = None
    log_end = None

    with open(f"log/system_log_{current_date}.txt", "a") as f:
        f.write(f'LID: {lid} end\n')

    with open(f"log/system_log_{current_date}.txt", "r") as f:
        log_content = f.readlines()

    for i in range(0, len(log_content)):
        if f"LID: {lid} start" in log_content[i]:
            log_start = i
        elif f"LID: {lid} end\n" in log_content[i]:
            log_end = i

    if save:
        for i in range(log_start + 1, log_end - 1):
            log_content[i] = log_content[i].replace("(TEMP)", "").strip() + "\n"

    log_content.pop(log_end)
    log_content.pop(log_start)
    
    with open(f"log/system_log_{current_date}.txt", "w") as f:
        f.writelines(log_content)