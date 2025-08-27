from flask import Flask, request, session, redirect, render_template, url_for, flash, abort, send_file, jsonify
import json, os
import pandas as pd
from datetime import datetime
import pytz
import datetime
import module.integrity as itg
from module.userManagement import UserManager

app = Flask(__name__)
app.secret_key = 'super_inventory_system'

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
    for item_code, item_detail in inventory.items():
        state = []
        quantity = item_detail['quantity']
        if quantity <= 0:
            state.append("out_of_stock")
            if quantity == -999:
                state.append("Out of stock(Stop Supply)")
            else:
                state.append("Out of stock")
        elif quantity <= 20:
            state.append("low")
            state.append("Low Quantity")
        else:
            state.append("available")
            state.append("Available")
        result.append([item_code, item_detail["name"], item_detail["quantity"], item_detail["price"], state])
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

@app.route('/iView')
def iView():
    if session.get("username"):
        return render_template("iView.html", inventory_data=getItems())
    else:
        return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if session.get("username"):
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
    if session.get("username"):
        if request.method == 'POST':
            try:
                df = pd.DataFrame([ {"Product Code": code, "Product Name": item["name"], "Quantity": item["quantity"]} for code, item in inventory.items() ])
                current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
                file_name = f'exported_data_{current_date}.csv'
                file_path = os.path.join('exports', file_name)
                df.to_csv(file_path, index=False)
                flash(f"Successfully to export data at exports/{file_name}", 'success')
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
            current_date = datetime.datetime.now(timezone).strftime("%Y_%m_%d")
            if os.path.exists(f'log/transaction/log_{current_date}.txt'):
                with open(f'log/transaction/log_{current_date}.txt', 'r', encoding='utf-8') as f:
                    transactions = f.readlines()
                    transactions.reverse()
            else:
                transactions = False
            if os.path.exists(f'log/system_log_{current_date}.txt'):
                with open(f'log/system_log_{current_date}.txt', 'r', encoding='utf-8') as f:
                    syslog = f.readlines()
                    syslog.reverse()
            else:
                syslog = False
            return render_template("admin.html", user_list=um.getUserList(), transactions=transactions, syslog=syslog)
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
            "price": int(price)
        }
        flash(f"Added item {code} with quantity {quantity} amd price ${price}", 'info')
        itg.log(f"[{code}] ⭕{name} 🔼{quantity} 🔼${price}", True)
    elif type == "remove":
        code = request.form.get("product_remove")
        name = inventory[code]['name']
        del inventory[code]
        itg.log(f"[{code}] ❌{name}", True)
        flash(f'Success to delete item "{code}"', 'success')
    elif type == "update":
        code = request.form.get("product_code")
        modify_type = request.form.get("product_type")
        modify_data = request.form.get("product_data")
        if modify_type == "name":
            inventory[code] = {
                "name": modify_data,
                "quantity": inventory[code]['quantity'],
                "price": inventory[code]['price']
            }
            flash(f"Updated the name of {code} to {modify_data}", 'info')
            itg.log(f"[{code}] ⭕{inventory[code]['name']} 🟡{inventory[code]['quantity']} 🟡${inventory[code]['price']}", True)
        elif modify_type == "quantity":
            init_quantity = inventory[code]["quantity"]
            inventory[code]["quantity"] = int(modify_data)
            if init_quantity > int(modify_data):
                itg.log(f"[{code}] 🟡{inventory[code]['name']} 🔽{init_quantity - int(modify_data)} --> {int(modify_data)} 🟡${inventory[code]['price']}", True)
            elif init_quantity < int(modify_data):
                itg.log(f"[{code}] 🟡{inventory[code]['name']} 🔼{int(modify_data) - init_quantity} --> {int(modify_data)} 🟡${inventory[code]['price']}", True)
            else:
                itg.log(f"[{code}] 🟡{inventory[code]['name']} 🟡{inventory[code]['quantity']} 🟡${int(modify_data)}", True)
            flash(f"Updated the quantity of {code} to {int(modify_data)}", 'info')
        elif modify_type == "price":
            init_price = inventory[code]['price']
            inventory[code]['price'] = int(modify_data)
            if init_price > int(modify_data):
                itg.log(f"[{code}] 🟡{inventory[code]['name']} 🟡{inventory[code]['quantity']} 🔽${init_price - int(modify_data)} --> ${int(modify_data)}", True)
            elif init_price < int(modify_data):
                itg.log(f"[{code}] 🟡{inventory[code]['name']} 🟡{inventory[code]['quantity']} 🔼${init_price - int(modify_data)} --> ${int(modify_data)}", True)
            else:
                itg.log(f"[{code}] 🟡{inventory[code]['name']} 🟡{inventory[code]['quantity']} 🟡${int(modify_data)}", True)
            flash(f"Updated the quantity of {code} to {int(modify_data)}", 'info')
    with open('./data/inventoryDB.json', 'w') as file:
        json.dump(inventory, file)
    itg.writeMD5()
    return redirect(url_for("iManagement"))

@app.route('/api/inventory/checkState')
def checkState():
    total_inventory = getItems()
    result = False
    item_name = []
    for item in total_inventory:
        if item[2] <= 20 and item[2] != -999:
            result = True
            item_name.append(item[0])
    return jsonify({"result": result, "list": item_name})

@app.route('/api/account/delete', methods=['POST'])
def deleteAcc():
    username = request.form.get('username')
    passkey = request.form.get('confirm')
    if passkey == f'Confirm to delete "{username}"':
        um.deleteUser(username)
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

@app.route('/signout')
def signout():
    global from_admin
    session.clear()
    from_admin = False
    return redirect(url_for('login'))

@app.route('/suspend')
def suspend():
    session.clear()
    return render_template("danger.html")

if __name__ == "__main__":
    loadDB()
    app.run(debug=True)
