from flask import Flask, request, session, redirect, render_template, url_for, flash, abort, send_file, jsonify
import json, os
import pandas as pd
import datetime
import pytz
import module.integrity as itg
from module.userManagement import UserManager
import time
from threading import Thread
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_inventory_system'
inventory = {}
timezone = pytz.timezone('Asia/Hong_Kong')
um = UserManager()
sys_version = itg.sysInfo()["version"]
from_admin = False
low_level = itg.sysInfo()['sys_setting']['low_quantity']

def loadDB():
    global inventory
    with open('./data/inventoryDB.json', 'r') as file:
        inventory = json.load(file)

def getItems():
    result = []
    for item_code, item_detail in inventory.items():
        state = []
        quantity = item_detail['quantity']
        if quantity <= 0:
            state.append("out_of_stock")
            if quantity == -999:
                state.append("Out of stock(Stop Supply)")
            else:
                state.append("Out of stock")
        elif quantity <= itg.sysInfo()['sys_setting']['low_quantity']:
            state.append("low")
            state.append("Low Quantity")
        else:
            state.append("available")
            state.append("Available")
        result.append([item_code, item_detail["name"], item_detail["quantity"], item_detail["price"], state])
    return result

def inventoryMonitor():
    while True:
        total_inventory = getItems()
        file_path = 'static/low_inventory.json'
        low_quantity = []
        for item in total_inventory:
            if item[2] <= low_level and item[2] != -999:
                low_quantity.append(item[0])
        with open(file_path, "w") as f:
            if len(low_quantity) > 0:
                json.dump(low_quantity, f)
                low_quantity = []
            else:
                json.dump({}, f)
        time.sleep(3600)

#---------------
#  Page Router
#--------------- 

@app.route('/', methods=['GET'])
def home():
    global from_admin
    from_admin = session.get("group") == "Admin"
    if itg.verifyMD5():
        if session.get('username'):  
            if 'page' in request.args:
                page = request.args['page']
                return render_template("index.html", version=sys_version, username=session["username"], from_admin=from_admin, re_dir=page)
            else:
                return render_template("index.html", version=sys_version, username=session["username"], from_admin=from_admin)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('suspend'))
    
@app.route('/dashboard')
def dashboard():
    if session.get('username'):
        print(from_admin)
        return render_template("dashboard.html", username=session['username'], from_admin=from_admin)
    else:
        return redirect(url_for('login'))

@app.route('/iManagement')
def iManagement():
    if session.get('username'):
        return render_template("iManagement.html", inventory_data=getItems())
    else:
        return redirect(url_for('login'))

@app.route('/iView')
def iView():
    if session.get('username'):
        total_value = 0
        for item in getItems():
            if item[2] != -999:
                total_value += (item[2] * item[3])
        return render_template("iView.html", inventory_data=getItems(), total_value=total_value)
    else:
        return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if session.get('username'):
        if request.method == 'POST':
            item_target = request.form['product_search'].lower()
            total_inventory = getItems()
            result = []
            for item in total_inventory:
                if item_target in item[0].lower() or item_target in item[1].lower():
                    result.append(item)
            if result:
                return render_template("search.html", inventory_data=result)
            else:
                return render_template("search.html", inventory_data=False)
        return render_template("search.html", inventory_data=False)
    else:
        return redirect(url_for('login'))
    
@app.route('/export', methods=['GET','POST'])
def export():
    if session.get('username'):
        if request.method == 'POST':
            try:
                df = pd.DataFrame([ {"Product Code": code, "Product Name": item["name"], "Quantity": item["quantity"]} for code, item in inventory.items() ])
                current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
                file_name = f'exported_data_{current_date}.csv'
                file_path = os.path.join('exports', file_name)
                df.to_csv(file_path, index=False)
                flash(f"Successfully to export data at exports/{file_name}", 'success')
                itg.log(f"[{session["username"]}] Inventory exported as {file_name}")
                return redirect(url_for('export'))
            except Exception as e:
                flash(f"Error exporting data: {str(e)}", 'error')
                return redirect(url_for('export'))
        return render_template("export.html", exportData=[f for f in os.listdir("exports/") if not f.startswith('.')])
    else:
        return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if session.get('username'):
        if session.get("group") != "Admin":
            return(redirect(url_for('/')))
        else:
            current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
            retrieve = []
            if os.path.exists(f'log/transaction/log_{current_date}.txt'):
                with open(f'log/transaction/log_{current_date}.txt', 'r', encoding='utf-8') as f:
                    transactions = f.readlines()
                    transactions.reverse()
                    for transaction in transactions:
                        if "#sales" in transaction:
                            retrieve.append([transaction.replace(" #sales", ""), "sales"])
                        elif "#purchase" in transaction:
                            retrieve.append([transaction.replace(" #purchase", ""), "purchase"])
                        else:
                            retrieve.append([transaction, "other"])
            else:
                transactions = False
            if os.path.exists(f'log/system_log_{current_date}.txt'):
                with open(f'log/system_log_{current_date}.txt', 'r', encoding='utf-8') as f:
                    syslog = f.readlines()
                    syslog.reverse()
            else:
                syslog = False
            return render_template("admin.html", user_list=um.getUserList(), transactions=retrieve, syslog=syslog, low_level=low_level, sys_running_info=itg.sysInfo())
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
            itg.log(f'[{session["group"]}] Success to sign-in system')
            return redirect(url_for('home'))
        else:
            itg.log(f'[Guest] Try to signin into system')
            flash('Username/Password incorrect. Please try again', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

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
                    itg.log(f'[{session["group"]}] User "{username}"[{group}] added')
                    return redirect(url_for('admin'))
                else:
                    flash(f"Success to create your account", 'success')
                    itg.log(f'[Guest] User "{username}" added')
                    return redirect(url_for('login'))
            else:
                flash("Weak password is not allowed. Try to set up a <a href='{}' style='color: var(--message-error-font) !important;'>strong password</a>".format(url_for('static', filename='password_policy.txt')), 'error')
        else:
            flash("Require Username already exists", 'error')
        if from_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('login'))
    return render_template('signup.html')

#---------------
#     API
#--------------- 

@app.route('/api/account/update/<type>', methods=['POST'])
def update_account(type):
    update_state = False
    signout = False
    if type == "username":
        username = request.form['username']
        current_user_name = session["username"]
        if um.userNameVerify(username):
            um.updateUser("user_name", current_user_name, username)
            session["username"] = username
            flash("Successful to update username", 'success')
            update_state = True
            signout = False
            itg.log(f'[{session["group"]}] "{current_user_name}" changed user name to "{username}"')
        else:
            flash("Require Username already exists", 'error')
            update_state = False
            signout = False
    elif type == "password":
        old_password = request.form['password_old']
        current_user_name = session["username"]
        new_user_password = request.form['password']
        if um.logIn(current_user_name, old_password):
            if um.passwordVerify(new_user_password):
                um.updateUser("user_password", current_user_name, new_user_password)
                flash("Success to update account password, system will signout in 3s automatically.", 'success')
                update_state = True
                signout = True
            else:
                flash("Weak password is not allowed. Try to set up a <a href='{}'>strong password</a>".format(url_for('static', filename='password_policy.txt')), 'error')
                update_state = False
                signout = False
        else:
            flash("Old Password incorrect", 'error')
            update_state = False
            signout = False
    return render_template("dashboard.html", username=session['username'], from_admin=from_admin, update_state=update_state, signout=signout)

@app.route('/api/inventory/<type>', methods=['POST'])
def manageInventory(type):
    if type == "add":
        code = request.form.get("product_code")
        name = request.form.get("product_name")
        quantity = request.form.get("product_quantity")
        price = request.form.get("product_price")
        inventory[code] = {
            "name": name,
            "quantity": int(quantity),
            "price": float(price)
        }
        flash(f"Added item {code} with quantity {quantity} amd price ${price}", 'info')
        itg.log(f"[{code}] +{name} | +{quantity} | +${price}", True)
    elif type == "remove":
        code = request.form.get("product_remove")
        name = inventory[code]['name']
        itg.log(f"[{code}] X{name} | -{inventory[code]['quantity']} | -${inventory[code]['price']}", True)
        del inventory[code]
        flash(f'Success to delete item "{code}"', 'success')
    elif type == "update":
        code = request.form.get("product_code")
        name = inventory[code]['name']
        modify_type = request.form.get("product_type")
        modify_data = request.form.get("product_data")
        if modify_type == "name":
            inventory[code] = {
                "name": modify_data,
                "quantity": inventory[code]['quantity'],
                "price": inventory[code]['price']
            }
            flash(f"Updated the name of {code} to {modify_data}", 'info')
            itg.log(f"[{code}] ※{name} | +0 | +$0", True)
        elif modify_type == "quantity":
            init_quantity = inventory[code]["quantity"]
            inventory[code]["quantity"] = int(modify_data)
            invoiceNote = request.form.get("invoice_data")
            if init_quantity > int(modify_data):
                itg.log(f"[{code}(#{invoiceNote})] {name} | -{init_quantity - int(modify_data)} | +$0 #sales", True)
            elif init_quantity < int(modify_data):
                itg.log(f"[{code}(#{invoiceNote})] {name} | +{int(modify_data) - init_quantity} | +$0 #purchase", True)
            else:
                itg.log(f"[{code}(#{invoiceNote})] {name} | +0 | +$0", True)
            flash(f"Updated the quantity of {code} to {int(modify_data)}", 'info')
        elif modify_type == "price":
            init_price = inventory[code]['price']
            current_price = float(modify_data)
            inventory[code]['price'] = current_price
            if init_price > current_price:
                itg.log(f"[{code}] {name} | +0 | -${init_price - current_price}", True)
            elif init_price < current_price:
                itg.log(f"[{code}] {name} | +0 | +${current_price - init_price}", True)
            else:
                itg.log(f"[{code}] {name} | +0 | +$0", True)
            flash(f"Updated the price of {code} to ${current_price}", 'info')
    with open('./data/inventoryDB.json', 'w') as file:
        json.dump(inventory, file)
    itg.writeMD5()
    return redirect(url_for("iManagement"))

@app.route('/api/account/delete', methods=['POST'])
def deleteAcc():
    username = request.form.get('username')
    passkey = request.form.get('confirm')
    if passkey == f'Confirm to delete "{username}"':
        um.deleteUser(username)
        itg.log(f'[{session["group"]}] User "{username}" deleted')
        flash(f'Success to delete user "{username}"', 'success')
        return redirect(url_for('admin'))
    else:
        flash("Passkey validation fail", 'error')
        return redirect(url_for('admin'))
        
@app.route('/api/download/attachment/<file_name>', methods=['GET', 'POST'])
def downloadAttch(file_name):
    file_path = f'exports/{file_name}'    
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/api/fileManager/remove/<file_name>')
def removeFile(file_name):
    file_name = secure_filename(file_name)
    print(file_name)
    file_path = f'exports/{file_name}'
    try:
        os.remove(file_path)
        itg.log(f'[{session["group"]}] Removed file {file_name}')
        flash(f"Sucess to remove file {file_name}", 'success')
        return(redirect(url_for('export')))
    except Exception:
        flash("Error removing file", 'error')
        return(redirect(url_for('export')))

@app.route('/api/system/setting', methods=['POST'])
def updateSysSetting():
    global low_level
    if request.method == 'POST':
        with open('data/system.json', 'r') as f:
            sysData = json.load(f)
        new_level = request.form.get("lowInvRange")
        sysData["sys_setting"]["low_quantity"] = int(new_level)
        low_level = int(new_level)
        with open('data/system.json', 'w') as f:
            json.dump(sysData, f)
            flash(f"Success to update low quantity level to {new_level} unit", "success")
    return redirect(url_for('admin'))

@app.route('/signout')
def signout():
    global from_admin
    itg.log(f'[{session["group"]}] User "{session["username"]}" signout the system')
    session.clear()
    from_admin = False
    flash("Signout sucess", "info")
    return redirect(url_for('login'))

@app.route('/suspend')
def suspend():
    if not itg.verifyMD5():
        if session.get('username'):
            itg.log(f'[{session["group"]}] System suspend')
        else:
            itg.log(f'[Gust] System suspend')
        session.clear()
        return render_template("danger.html")
    else:
        return redirect(url_for('home'))

if __name__ == "__main__":
    loadDB()
    monitor_thread = Thread(target=inventoryMonitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    app.run(port=5500)