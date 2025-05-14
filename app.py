from tabulate import tabulate

inventory = {
    "We are": 100,
    "HER": 100,
    "I SWAY": 100,
    "YUQ1": -999
}

def menu():
    print("[1] Inventory Management")
    print("[2] View Inventory")
    print("[3] Update Inventory")
    print("[4] Exit")

def management():
    print("[1] Add item")
    print("[2] Remove item")
    action = int(input("Choose an action: "))
    if action == 1:
        item_name = input("Which item do you want to add: ")
        if item_name in inventory:
            print("[Info] Item already exit.")
        else:
            inventory[item_name] = -999
            print(f'[Info] Added item {item_name} with quantity 0.')
    elif action == 2:
        for item, quantity in inventory.items():
            print(item)
        item_name = input("Which item do you want to remove: ")
        if item_name in inventory:
            del inventory[item_name]
            print(f"[Info] {item_name} have been removed.")
        else:
            print("[Error] The item is not exit.")
    main()

def view():
    total_inventory = []
    header = ["Item", "Quantity"]
    for item, quantity in inventory.items():
        if quantity > 0:
            total_inventory.append([item,quantity])
        else:
            total_inventory.append([item, "SOLD OUT"])
    print(tabulate(total_inventory, headers=header))

def main():
    while True:
        menu()
        action = int(input("Choose an action: "))
        if action == 1:
            management()
        elif action == 2:
            view()
        elif action == 3:
            update()
        elif action == 4:
            break
        else:
            print("Invalid action.")
            action = int(input("Choose an action: "))

if __name__ == '__main__':
    main()