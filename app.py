from tabulate import tabulate

inventory = {
    "We are": 100,
    "HER": 100,
    "I SWAY": 100,
    "YUQ1": -999
}

def menu():
    command = [[1,"Inventory Management: add or remove item(s) inside this system"],[2,"View Inventory: Check the inventory quantity of each item"],[3,"Update the inventory quantity of a specific item"],[4,"Exit"]]
    print(tabulate(command, headers=["code","describe"], tablefmt="simple_grid"))

def getItems(detail = False):
    result = []
    index = 0
    for item, quantity in inventory.items():
        if detail:
            result.append([index, item, quantity])
            index += 1
        else:
            result.append([index, item])
            index += 1
    return result

def management():
    print("[1] Add item")
    print("[2] Remove item")
    action = int(input("Choose an action: "))
    if action == 1:
        item_name = input("Which item do you want to add: ")
        if item_name in inventory:
            print("[Info] Item already exit.")
        else:
            inventory[item_name] = 0
            print(f'[Info] Added item {item_name} with quantity 0.')
    elif action == 2:
        total_inventory = getItems(False)
        print(tabulate(total_inventory, headers=["code", "Item name"], tablefmt="simple_grid"))
        item_code = int(input("Which item do you want to remove: "))
        item_name = total_inventory[item_code][1]
        del inventory[item_name]
        print(f"[Info] {item_name} have been removed.")
    main()

def view():
    print(tabulate(getItems(True), headers=["Item", "Quantity"], tablefmt="psql"))

def update():
    total_inventory = getItems(False)
    print(tabulate(total_inventory, headers=["code", "Item name"], tablefmt="simple_grid"))
    item_code = int(input("Which item do you want to update: "))
    item_name = total_inventory[item_code][1]
    type = int(input("Which info you want to update [0]Item name [1]Quantity: "))
    match type:
        case 0:
            new_name = input("Updated item name: ")
            inventory[new_name] = inventory.pop(item_name)
            print(f"[Info] Updated the name of {item_name} to {new_name}.")
        case 1:
            new_quantity = int(input("Updated quantity: "))
            inventory[item_name] = new_quantity
            print(f"[Info] Updated the quantity of {item_name} to {new_quantity}.")
        case _:
            print("[Error] Invalid option.")

def main():
    while True:
        menu()
        action = int(input("Choose an action: "))
        match action:
            case 1:
                management()
            case 2:
                view()
            case 3:
                update()
            case 4:
                break
            case _:
                print("Invalid action.")

if __name__ == '__main__':
    main()