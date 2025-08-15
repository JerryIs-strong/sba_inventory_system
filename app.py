from tabulate import tabulate
import json
import module.integrity as itg
import pandas as pd
from datetime import datetime
import os
from module.userManagement import UserManager
import getpass
import pytz
from colorama import Fore, Style, Back, init
import os

inventory = {}
current_user_name = ''
timezone = pytz.timezone('Asia/Hong_Kong')
um = UserManager()
init(autoreset=True)
admin = False
firstLogIn = True
lid = None

def loadDB():
    global inventory
    with open('./data/inventoryDB.json', 'r') as file:
        inventory = json.load(file)

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def echoMessage(action, message):
    if action == 'error':
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
    elif action == 'info':
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")
    elif action == 'success':
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def menu():
    global admin
    command = [[0, "Help: Print out this menu again"], [1,"Inventory Management: add, remove or update item(s) inside this system\n- type item_name:quantity for adding item and quantity\n- use ' ' to split for batch update"],[2,"View Inventory: Check the inventory quantity of each item"],[3,"Search: Searching a specific item from inventory"],[4, "Export: Export data as .csv"],[5,"Dashboard: User settings"],[6,"Log Out: Log out current account"],[7,"Admin Menu: Control panel for admin"]]
    if(not admin):
        command.pop()
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
    cls()
    print(f"{Back.GREEN}PAGE / INVENTORY MANAGEMENT\n")
    print("[1] Add item")
    print("[2] Remove item")
    print("[3] Update Inventory")
    print("[4] Exit this page")
    while True:
        action = int(input("\nChoose an action: "))
        match action:
            case 1:
                item = input("Which item do you want to add: ")
                items = item.split()
                for i in range(len(items)):
                    if ':' in items[i]:
                        if items[i] in inventory:
                            echoMessage('error', "Item already exit")
                        else:
                            item_name, quantity = items[i].split(':')
                            inventory[item_name] = quantity
                            echoMessage('info', f"Added item {item_name} with quantity {quantity}")
                            itg.log(f"[{current_user_name}] Added item {item_name} with quantity {quantity}(TEMP)")
                    else:
                        if items[i] in inventory:
                            echoMessage('error', f"Item already exit")
                        else:
                            inventory[items[i]] = 0
                            echoMessage('info', f"Added item {items[i]} with quantity 0")
                            itg.log(f"[{current_user_name}] Added item {items[i]} with quantity 0(TEMP)")
            case 2:
                total_inventory = getItems(False)
                print(tabulate(total_inventory, headers=["Code", "Item name"], tablefmt="simple_grid"))
                try:
                    item_code = input("Which item do you want to remove: ")
                    item_codes = item_code.split()
                    if len(item_codes) > 0:
                        for i in range(len(item_codes)):
                            item_name = total_inventory[int(item_codes[i])][1]
                            del inventory[item_name]
                            echoMessage('info', f"{item_name} have been removed")
                            itg.log(f"[{current_user_name}] {item_name} have been removed(TEMP)")
                except IndexError:
                    echoMessage('error', "Value out of range")
            case 3:
                total_inventory = getItems(False)
                print(tabulate(total_inventory, headers=["Code", "Item name"], tablefmt="simple_grid"))  
                try:
                    item_code = int(input("Which item do you want to update: "))
                    item_name = total_inventory[item_code][1]
                    type = input("Which info you want to update [N]Item name [Q]Quantity: ")
                    match type.lower():
                        case "n":
                            new_name = input("Updated item name: ")
                            inventory[new_name] = inventory.pop(item_name)
                            echoMessage('info', f"Updated the name of {item_name} to {new_name}")
                            itg.log(f"[{current_user_name}] Updated the name of {item_name} to {new_name}(TEMP)")
                        case "q":
                            new_quantity = int(input("Updated quantity: "))
                            inventory[item_name] = new_quantity
                            echoMessage('info', f"Item already exit")
                            itg.log(f"[{current_user_name}] Updated the quantity of {item_name} to {new_quantity}(TEMP)")
                        case _:
                            echoMessage('error', "Invalid option")
                except IndexError:
                    echoMessage('error', "Value out of range")
            case 4:
                break
            case _:
                echoMessage('error', "Invalid option")

def view():
    cls()
    print(f"{Back.GREEN}PAGE / VIEW INVENTORY\n")
    print(tabulate(getItems(True), headers=["Item", "Quantity"], tablefmt="psql"))
    itg.log(f"[{current_user_name}] Get inventory")
    while True:
        action = input("\nPress Enter to exit...")
        match action:
            case "":
                break
            case _:
                echoMessage('error', "Invalid option")

def search():
    cls()
    print(f"{Back.GREEN}PAGE / SEARCH ITEM")
    total_inventory = getItems(True)
    found = False
    while True:
        action = input("\nType name of the product (or press Enter to exit...): ")
        if action == "":
            break
        found = False
        for item in total_inventory:
            if action.lower() == item[0].lower():
                print(tabulate([item], headers=["Item", "Quantity"], tablefmt="psql"))
                found = True
        if not found:
            print("Not found")

def export():
    cls()
    print(f"{Back.GREEN}PAGE / EXPORT DATA\n")
    while True:
        try:
            df = pd.DataFrame(list(inventory.items()), columns=['Item_name', 'Quantity'])
            current_date = datetime.now(timezone).strftime("%d_%m_%Y")
            file_name = f'exported_data_{current_date}.csv'
            file_path = os.path.join('exports', file_name)
            df.to_csv(file_path, index=False)
            echoMessage('success', f"Successfully to export data at {file_path}")
            itg.log(f"[{current_user_name}] Inventory exported")
        except Exception:
            echoMessage('error', Exception)
        action = input("\nPress Enter to exit...")
        match action:
            case "":
                break
            case _:
                echoMessage('error', "Invalid option")

def quitNow():
    cls()
    global lid
    aka = input("Would you like to save the change Yes[Y] No[N]: ")
    match aka.lower():
        case "y":
            with open('./data/inventoryDB.json', 'w') as file:
                json.dump(inventory, file)
            echoMessage('success', "Update database successfully")
            itg.log(f"[{current_user_name}] Inventory updated")
            itg.writeMD5()
            itg.endLogService(lid, True)
        case "n":
            itg.endLogService(lid)
            return

def addUser(group = "User"):
    cls()
    print("\nPlease follow this role to setup your password:")
    print("- MUST include at least ONE Number & Uppercase Letter & Lowercase Letter & Symbol\n- Should between 8 - 32 latter")
    while True:
        user_name = input("[1/3]: Type your user name: ")
        while True:
                if um.userNameVerify(user_name) == "OK":
                    user_password = getpass.getpass("[2/3]: Type your password: ")
                    if(um.passwordVerify(user_password) == "OK"):
                        user_password_confirm = getpass.getpass("[3/3]: Type your password again to confirm: ")
                        if user_password == user_password_confirm:
                            um.createUser(user_name, user_password, group)
                            echoMessage('success', f'Successful to create user "{user_name}"\n')
                            return
                        else:
                            echoMessage('error', "The two inputs do not match")
                    else:
                        echoMessage('error', "Try to set up a secure password")
                else:
                    echoMessage('error', "Username already exists")
                    break

def dashboard():
    global current_user_name
    while True:
        cls()
        print(f"{Back.GREEN}PAGE / DASHBOARD [{current_user_name}]\n")
        print("[1] Account Information")
        print("[2] Preference")
        print("[3] Exit Control Panel")
        action = int(input("\nChoose an action: "))
        match action:
            case 1:
                cls()
                print("[1] Account Name")
                print("[2] Account Password")
                print("[3] Exit this page")
                while True:
                    action_info = int(input("\nChoose an action: "))
                    match action_info:
                        case 1:
                            new_user_name = input("Type your new account name: ")
                            um.updateUser("user_name", current_user_name, new_user_name)
                            echoMessage("success", f'Successful update user name from "{current_user_name}" to "{new_user_name}"')
                            current_user_name = new_user_name
                            exit_action = input("Press Enter to exit...")
                            match exit_action:
                                case "":
                                    break
                        case 2:
                            old_password = getpass.getpass("Type your current user password: ")
                            if um.logIn(current_user_name, old_password):
                                print("\nPlease follow this role to setup your password:")
                                print("- MUST include at least ONE Number & Uppercase Letter & Lowercase Letter & Symbol\n- Should between 8 - 32 latter")
                                new_user_password = getpass.getpass("Type your new password: ")
                                if um.passwordVerify(new_user_password) == "OK":
                                    user_password_confirm = getpass.getpass("Type your password again to confirm: ")
                                    if new_user_password == user_password_confirm:
                                        result = um.updateUser("user_password", current_user_name, new_user_password)
                                        if result == "OK":
                                            echoMessage('success', "Successful to update your password.")
                                            exit_action = input("Press Enter to exit...")
                                            match exit_action:
                                                case "":
                                                    break
                                    else:
                                        echoMessage('error', "The two inputs do not match")
                                else:
                                    echoMessage('error', "Try to set up a secure password")
                            else:
                                echoMessage('error', "Password incorrect")
                        case 3:
                            break
            case 2:
                echoMessage('info', "OK")
            case 3:
                break

def adminMenu():
    cls()
    print(f"{Back.GREEN}PAGE / ADMIN CONTROL PANEL\n")
    print("[1] User Management")
    print("[2] View User")
    print("[3] Exit Control Panel\n")
    while True:
        aka = int(input("Choose an action: "))
        match aka:
            case 1:
                print("\n[1] Create user")
                print("[2] Remove user")
                action = int(input("Choose an action: "))
                if action == 1:
                    user_group = int(input("User group [1]Admin [2]User (With great power comes great responsibility): "))
                    if user_group == 1:
                        addUser("Admin")
                    elif user_group == 2:
                        addUser()
                elif action == 2:
                    try:
                        index = 0
                        user_list = []
                        for user in um.getUserList():
                            user_list.append([index, user])
                            index += 1
                        print(tabulate(user_list, headers=["Code", "User Name"], tablefmt="simple_grid"))
                        user_code = int(input("Which user you want to delete: "))
                        print(f'Type(Confirm to delete "{user_list[user_code][1]}") to delete this account')
                        confirm = input("Type confirm passkey here: ")
                        if confirm == f'Confirm to delete "{user_list[user_code][1]}"':
                            um.deleteUser(user_list[user_code][1])
                            echoMessage('success', f"Successful delete user {user_list[user_code][1]}")  
                    except IndexError:
                        echoMessage('error', "Value out of range")
            case 2:
                user_list = []
                for user in um.getUserList():
                    user_list.append([user])
                print(tabulate(user_list, headers=["User Name"], tablefmt="psql"))
            case 3:
                break
            case _:
                print("Invalid action")

def main():
    loadDB()
    global firstLogIn
    while True:
        cls()
        if firstLogIn: 
            echoMessage('success', f"Welcome {current_user_name} [{um.getUserGroup(user_name)}]")
            firstLogIn = False
        menu()
        action = int(input("Choose an action: "))
        match action:
            case 0:
                menu()
            case 1:
                management()
            case 2:
                view()
            case 3:
                search()
            case 4:
                export()
            case 5:
                dashboard()
            case 6:
                itg.log(f"[{current_user_name}] sign-out system")
                quitNow()
                break
            case 7:
                if admin:
                    adminMenu()
                else:
                    print("Invalid action")
            case _:
                print("Invalid action")

if __name__ == '__main__':
    while True:
        cls()
        firstLogIn = True
        command = [[1,"Sign In: Log in to this system"],[2, "Sign Up: Create a new user account"] , [3,"Exist: Quit this system"]]
        print(tabulate(command, headers=["Code","Describe"], tablefmt="simple_grid"))
        aka = int(input("Choose an action: "))
        match aka:
            case 1:
                while True:
                    user_name = input("\nUSER NAME: ")
                    if user_name in um.getUserList():
                        current_user_name = user_name
                        user_password = getpass.getpass('PASSWORD:')
                        if um.logIn(user_name, user_password):
                            lid = itg.initLogService()
                            itg.log(f'[{current_user_name}] User "{user_name}" success to sign-in system')
                            if itg.verifyMD5():
                                if um.getUserGroup(user_name) == "Admin":
                                    admin = True
                                main()
                            else:
                                echoMessage('error', "Database integrity not pass. System ended")
                                itg.log(f'[{current_user_name}] system quit due to database integrity test fail')
                            break
                        else:
                            echoMessage('error', "Password incorrect")
                            itg.log(f'[{current_user_name}] User "{user_name}" fail to sign-in system')
                    else:
                        echoMessage('error', "User not exit")
            case 2:
                addUser()
            case 3:
                break
            case _:
                print("Invalid action")
