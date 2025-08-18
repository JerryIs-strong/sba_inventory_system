from flask import Flask, request, session, redirect, render_template, url_for, flash, abort, send_file
import json, os
import pandas as pd
from datetime import datetime
import pytz
import datetime

import module.integrity as itg
from module.userManagement import UserManager

app = Flask(__name__)
app.secret_key = 'super_inventorrrrrry_system'

inventory = {}
timezone = pytz.timezone('Asia/Hong_Kong')
um = UserManager()
sys_version, p_version = itg.sysInfo()
from_admin = False

def loadDB():
    global inventory
    with open('./data/inventoryDB.json', 'r') as file:
        inventory = json.load(file)

def getItems():
    result = []
    for item, quantity in inventory.items():
        result.append([item, quantity])
    return result

@app.route('/', methods=['GET'])
def home():
    global from_admin
    from_admin = session.get("group") == "Admin"
    if itg.verifyMD5():
        if session.get("username"):  
            if 'page' in request.args:
                page = request.args['page']
                return render_template("index.html", version=sys_version, p_version=p_version, username=session["username"], from_admin=from_admin, re_dir=page)
            else:
                return render_template("index.html", version=sys_version, p_version=p_version, username=session["username"], from_admin=from_admin)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('suspend'))
    
@app.route('/dashboard')
def dashboard():
    if session.get("username"):
        print(from_admin)
        return render_template("dashboard.html", username=session['username'], from_admin=from_admin)
    else:
        return redirect(url_for('login'))

@app.route('/iManagement/')
def iManagement():
    if session.get("username"):
        return render_template("iManagement.html", inventory_data=getItems())
    else:
        return redirect(url_for('login'))


@app.route('/iView', methods=['GET', 'POST'])
def iView():
    if session.get("username"):
        if request.method == 'POST':
            flash("Success to get inventory data", "success")
            return render_template("iView.html", inventory_data=getItems())
        return render_template("iView.html")
    else:
        return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if session.get("username"):
        if request.method == 'POST':
            item_name = request.form['product_search']
            total_inventory = getItems()
            result = [item for item in total_inventory if item_name.lower() == item[0].lower()]

            if result:
                return render_template("search.html", inventory_data=result)
            else:
                return render_template("search.html", inventory_data=False)
        
        return render_template("search.html")
    else:
        return redirect(url_for('login'))
    
@app.route('/export', methods=['GET','POST'])
def export():
    if session.get("username"):
        if request.method == 'POST':
            try:
                df = pd.DataFrame(list(inventory.items()), columns=['Item_name', 'Quantity'])
                current_date = datetime.datetime.now(timezone).strftime("%d_%m_%Y")
                file_name = f'exported_data_{current_date}.csv'
                file_path = os.path.join('exports', file_name)
                df.to_csv(file_path, index=False)
                flash(f"Successfully to export data at {file_path}", 'success')
                itg.log(f"[{session["username"]}] Inventory exported")
                return redirect(url_for('export'))
            except Exception as e:
                flash(f"Error exporting data: {str(e)}", 'error')
                return redirect(url_for('export'))
        return render_template("export.html", exportData=os.listdir("exports/"))
    else:
        return redirect(url_for('login'))
    
@app.route('/admin')
def admin():
    if session.get("username"):
        if session.get("group") != "Admin":
            return(redirect(url_for('/')))
        else:
            current_date = datetime.datetime.now(timezone).strftime("%d_%m_%Y")
            with open(f'log/transaction/log_{current_date}.txt', 'r', encoding='utf-8') as f:
                transactions = f.readlines()
                transactions.reverse()
            return render_template("admin.html", user_list=um.getUserList(), transactions=transactions)
    else:
        return redirect(url_for('login'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if um.logIn(username, password):
            session["username"] = username
            session["group"] = um.getUserGroup(username)
            itg.log(f'[{session["username"]}] User "{username}" success to sign-in system')
            return redirect(url_for('home'))
        else:
            itg.log(f'[Guest] User "{username}" try to signin into system')
            flash('Username/Password incorrect. Please try again', 'error')
        return redirect(url_for('login'))
    return render_template('login.html', version=sys_version)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        group = request.form['group'] if from_admin else "User"
        if um.userNameVerify(username):
            if um.passwordVerify(password):
                um.createUser(username, password, group)
                if from_admin:
                    flash(f"Success to add user {username}[{group}]", 'success')
                    return redirect(url_for('admin'))
                else:
                    flash(f"Success to create your account", 'success')
                    return redirect(url_for('login'))
            else:
                flash("Weak password is not allowed. Try to set up a <a href='{}'>strong password</a>".format(url_for('static', filename='password_policy.txt')), 'error')
        else:
            flash("Require Username already exists", 'error')
        if from_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('login'))
    return render_template('signup.html', from_admin=from_admin, version=sys_version)


#---------------
#     API
#--------------- 
@app.route('/api/account/update/<type>', methods=['POST'])
def update_account(type):
    if type == "username":
        username = request.form['username']
        current_user_name = session["username"]
        if um.userNameVerify(current_user_name):
            um.updateUser("user_name", current_user_name, username)
            session["username"] = username
            flash("Successful to update username", 'success')
        else:
            flash("Require Username already exists", 'error')
    else:
        old_password = request.form['password_old']
        current_user_name = session["username"]
        new_user_password = request.form['password']
        if um.logIn(current_user_name, old_password):
            if um.passwordVerify(new_user_password):
                um.updateUser("user_password", current_user_name, new_user_password)
                flash("Success to update account password", 'success')
            else:
                flash("Weak password is not allowed. Try to set up a <a href='{}'>strong password</a>".format(url_for('static', filename='password_policy.txt')), 'error')
        else:
            flash("Old Password incorrect", 'error')
    return redirect(url_for('dashboard'))

@app.route('/api/inventory/<type>', methods=['POST'])
def manageInventory(type):
    if type == "add":
        item = request.form.get("product_add")
        items = item.split()
        for i in range(len(items)):
            if ':' in items[i]:
                item_name, quantity = items[i].split(':')
                if item_name in inventory:
                    flash("Item already exit", 'error')
                else:
                    inventory[item_name] = int(quantity)
                    flash(f"Added item {item} with quantity {quantity}", 'info')
                    itg.log(f"[{item}] New item with init quantity {quantity} --> 🔼{quantity}", True)
            else:
                if items[i] in inventory:
                    flash("Item already exit", 'error')
                else:
                    inventory[items[i]] = 0
                    flash(f"Added item {item} with quantity 0", 'info')
                    itg.log(f"[{item}] New item with init quantity 0 --> 🔼0", True)
    elif type == "remove":
        item = request.form.get("product_remove")
        init_quantity = inventory[item]
        del inventory[item]
        itg.log(f"[{item}] Item removed from system --> 🔽{init_quantity}", True)
        flash(f'Success to delete item "{item}"', 'success')
    elif type == "update":
        item = request.form.get("product_modify")
        modify_type = request.form.get("product_modify_type")
        modify_data = request.form.get("product_modify_data")
        if modify_type == "name":
            new_name = modify_data
            inventory[new_name] = inventory.pop(item)
            flash(f"Updated the name of {item} to {new_name}", 'info')
            itg.log(f"[{new_name}] {item} now is {new_name} --> 🟡 maintain", True)
        elif modify_type == "quantity":
            new_quantity = int(modify_data)
            init_quantity = inventory[item]
            inventory[item] = new_quantity
            if (init_quantity - new_quantity) > 0:
                itg.log(f"[{item}] Goods have been sold --> 🔽{init_quantity - new_quantity}", True)
            else:
                itg.log(f"[{item}] Goods arrival --> 🔼{new_quantity - init_quantity}", True)
            flash(f"Updated the quantity of {item} to {new_quantity}", 'info')
    with open('./data/inventoryDB.json', 'w') as file:
        json.dump(inventory, file)
    itg.writeMD5()
    return redirect(url_for("iManagement"))
    

@app.route('/api/account/delete', methods=['POST'])
def deleteAcc():
    if from_admin:
        username = request.form.get('username')
    else:
        username = session['username']
    passkey = request.form.get('confirm')
    if passkey == f'Confirm to delete "{username}"':
        um.deleteUser(username)
        flash(f'Success to delete user "{username}"', 'success')
        if from_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('logout'))
    else:
        flash("Passkey validation fail", 'error')
        if from_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('dashboard'))
        
@app.route('/api/download/attachment/<file_name>', methods=['GET', 'POST'])
def downloadAttch(file_name):
    file_path = f'exports/{file_name}'    
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/suspend')
def suspend():
    session.clear()
    return render_template("danger.html")

if __name__ == "__main__":
    loadDB()
    app.run(debug=True)
