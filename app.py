from tabulate import tabulate
import json
import module.integrity as itg
import pandas as pd
from datetime import datetime
import os
from module.userManagement import UserManager as um
import getpass

inventory = {}
current_user_name = ''

def loadDB():
    global inventory
    with open('./data/inventoryDB.json', 'r') as file:
        inventory = json.load(file)

def menu():
    command = [[1,"Inventory Management: add or remove item(s) inside this system\n- type item_name:quantity for adding item and quantity\n- use ' ' to split for batch update"],[2,"View Inventory: Check the inventory quantity of each item"],[3,"Update Inventory: Update the inventory quantity of a specific item"],[4,"Search: Searching a specific item from inventory"],[5, "Export: Export data as .csv"],[6,"Log Out: Log out current account"]]
    print(tabulate(command, headers=["Code","Describe"], tablefmt="simple_grid"))

def getItems(detail = False):
    result = []
    index = 0
    for item, quantity in inventory.items():
        if detail:
            result.append([item, quantity])
        else:
            result.append([index, item])
            index += 1
    return result

def management():
    print("[1] Add item")
    print("[2] Remove item")
    action = int(input("Choose an action: "))
    if action == 1:
        item = input("Which item do you want to add: ")
        items = item.split()
        for i in range(len(items)):
            if ':' in items[i]:
                if items[i] in inventory:
                    print("[Info] Item already exit.")
                else:
                    item_name, quantity = items[i].split(':')
                    inventory[item_name] = quantity
                    print(f'[Info] Added item {item_name} with quantity {quantity}.')
                    itg.log(f"[{current_user_name}] [Inventory Management]: Added item {item_name} with quantity {quantity}")
            else:
                if items[i] in inventory:
                    print("[Info] Item already exit.")
                else:
                    inventory[items[i]] = 0
                    print(f'[Info] Added item {items[i]} with quantity 0')
                    itg.log(f"[{current_user_name}] [Inventory Management]: Added item {items[i]} with quantity 0")

    elif action == 2:
        total_inventory = getItems(False)
        print(tabulate(total_inventory, headers=["Code", "Item name"], tablefmt="simple_grid"))
        try:
            item_code = input("Which item do you want to remove: ")
            item_codes = item_code.split()
            if len(item_codes) > 0:
                for i in range(len(item_codes)):
                    item_name = total_inventory[int(item_codes[i])][1]
                    del inventory[item_name]
                    print(f"[Info] {item_name} have been removed.")
                    itg.log(f"[{current_user_name}] [Inventory Management]: {item_name} have been removed")
        except IndexError:
            print("[Error] Value out of range.")

def view():
    print(tabulate(getItems(True), headers=["Item", "Quantity"], tablefmt="psql"))
    itg.log(f"[{current_user_name}] [View Inventory]: get inventory")

def update():
    total_inventory = getItems(False)
    print(tabulate(total_inventory, headers=["Code", "Item name"], tablefmt="simple_grid"))  
    try:
        item_code = int(input("Which item do you want to update: "))
        item_name = total_inventory[item_code][1]
        type = int(input("Which info you want to update [0]Item name [1]Quantity: "))
        match type:
            case 0:
                new_name = input("Updated item name: ")
                inventory[new_name] = inventory.pop(item_name)
                print(f"[Info] Updated the name of {item_name} to {new_name}.")
                itg.log(f"[{current_user_name}] [Update Inventory]: Updated the name of {item_name} to {new_name}")
            case 1:
                new_quantity = int(input("Updated quantity: "))
                inventory[item_name] = new_quantity
                print(f"[Info] Updated the quantity of {item_name} to {new_quantity}.")
                itg.log(f"[{current_user_name}] [Update Inventory]: Updated the quantity of {item_name} to {new_quantity}")
            case _:
                print("[Error] Invalid option.")
    except IndexError:
        print("[Error] Value out of range.")

def search():
    total_inventory = getItems(True)
    aka = input("Which item you want to search: ")
    for i in range(len(total_inventory)):
        if aka in total_inventory[i][0]:
            return tabulate([total_inventory[i]], headers=["Item", "Quantity"], tablefmt="psql")
    return "Not found."

def export():
    df = pd.DataFrame(list(inventory.items()), columns=['Item_name', 'Quantity'])
    current_date = datetime.now().strftime("%d_%m_%Y")
    file_name = f'exported_data_{current_date}.csv'
    file_path = os.path.join('exports', file_name)
    df.to_csv(file_path, index=False)
    itg.log(f"[{current_user_name}] [Export Inventory]: Inventory exported")

def quitNow():
    aka = input("Would you like to save the change Yes[Y] No[N]: ")
    match aka.lower():
        case "y":
            with open('./data/inventoryDB.json', 'w') as file:
                json.dump(inventory, file)
            print("[Info]: Update database successfully.")
            itg.log(f"[{current_user_name}] [Update Inventory]: Inventory updated")
            itg.writeMD5()
        case "n":
            return

def main(admin):
    loadDB()
    menu()
    while True:
        action = int(input("Choose an action: "))
        match action:
            case 1:
                management()
            case 2:
                view()
            case 3:
                update()
            case 4:
                print(search())
            case 5:
                export()
            case 6:
                quitNow()
                break
            case 7:
                if admin:
                    adminMenu()
                else:
                    print("Invalid action.")
            case _:
                print("Invalid action.")

if __name__ == '__main__':
    while True:
        command = [[1,"Log In: Log in to this system"], [2,"Exist: Quit this system"]]
        print(tabulate(command, headers=["Code","Describe"], tablefmt="simple_grid"))
        aka = int(input("Choose an action: "))
        match aka:
            case 1:
                while True:
                    user_name = input("\nUSER NAME: ")
                    if user_name in um().getUserList():
                        user_password = getpass.getpass('PASSWORD:')
                        if um().verifyUser(user_name, user_password):
                            if itg.verifyMD5():
                                if um().getUserGroup(user_name) == "Admin":
                                    print(f"\nWelcome {user_name}[{um().getUserGroup(user_name)}]")
                                    main(True)
                                else:
                                    print(f"Welcome {user_name}")
                                    main(False)
                            else:
                                print("[Error]: Database integrity not pass. System ended.")
                            break
                        else:
                            print(f"[Error]: Password incorrect")
                    else:
                        print("[Error]: User not exit")
            case 2:
                break
            case _:
                print("Invalid action.")
