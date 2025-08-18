from module.userManagement import UserManager
import module.integrity as itg
import json

um=UserManager()
inventory = {}

def loadDB():
    global inventory
    with open('./data/inventoryDB.json', 'r') as file:
        inventory = json.load(file)

def getItems():
    result = []
    for item_code, item_detail in inventory.items():
        result.append([item_code, item_detail["name"], item_detail["quantity"]])
    return result

loadDB()
itg.writeMD5()
