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

def management():
    print("[1] Add item")
    print("[2] Remove item")
    action = int(input("Choose an action: "))
    if action == 1:
        item_name = input("Which item do you want to add: ")
        inventory[item_name] = 0
        print(inventory)
    elif action == 2:
        for item, quantity in inventory.items():
            print(item)
        item_name = input("Which item do you want to remove: ")

def view():
    for item, quantity in inventory.items():
        if quantity > 0:
            print(f"{item}: {quantity}")
        else:
            print(f"{item}: SOLD OUT")

def main():
    menu()
    action = int(input("Choose an action: "))
    if action == 1:
        management()
    elif action == 2:
        view()
    elif action == 3:
        update()

if __name__ == '__main__':
    main()