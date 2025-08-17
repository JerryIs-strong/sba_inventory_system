from flask import Flask, request, jsonify, session, redirect, render_template, url_for, flash
import json, os
import pandas as pd
from datetime import datetime
import pytz
import time

import module.integrity as itg
from module.userManagement import UserManager

app = Flask(__name__)
app.secret_key = 'super_inventorrrrrry_system'

inventory = {}
timezone = pytz.timezone('Asia/Hong_Kong')
um = UserManager()
version_info = itg.sysInfo()

@app.route('/', methods=['GET'])
def home():
    from_admin = session.get("group") == "Admin"
    if session.get("integrity"):
        if session.get("username"):  
            if 'page' in request.args:
                page = request.args['page']
                return render_template("index.html", version=version_info, username=session["username"], from_admin=from_admin, re_dir=page)
            else:
                return render_template("index.html", version=version_info, username=session["username"], from_admin=from_admin)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('suspend'))
    
@app.route('/dashboard')
def dashboard():
    if session.get("username"):
        return render_template("dashboard.html")
    else:
        return redirect(url_for('login'))

@app.route('/iManagement')
def iManagement():
    if session.get("username"):
        return render_template("iManagement.html")
    else:
        return redirect(url_for('login'))

@app.route('/iView')
def iView():
    if session.get("username"):
        return render_template("iView.html")
    else:
        return redirect(url_for('login'))

@app.route('/search')
def search():
    if session.get("username"):
        return render_template("search.html")
    else:
        return redirect(url_for('login'))
    
@app.route('/export')
def export():
    if session.get("username"):
        return render_template("export.html")
    else:
        return redirect(url_for('login'))
    
@app.route('/admin')
def admin():
    if session.get("username"):
        if session.get("group") != "Admin":
            return(redirect(url_for('/')))
        else:
            return render_template("admin.html")
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
            if itg.verifyMD5():
                itg.log(f'[{session["username"]}] User "{username}" success to sign-in system')
                return redirect(url_for('home'))
            else:
                flash("Database integrity not pass. System ended", 'error')
                itg.log(f'[{session["username"]}] system quit due to database integrity test fail')
                return redirect(url_for('suspend'))
        else:
            itg.log(f'[Guest] User "{username}" try to signin into system')
            flash('Username/Password incorrect. Please try again', 'error')
        return redirect(url_for('login'))
    return render_template('login.html', version=version_info)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    from_admin = session.get("group") == "Admin"
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        group = request.form['group'] if from_admin else "User"
        if um.userNameVerify(username):
            if um.passwordVerify(password):
                um.createUser(username, password, group)
                return redirect(url_for('login'))
            else:
                flash("Weak password is not allowed. Try to set up a <a href='{}'>strong password</a>".format(url_for('static', filename='password_policy.txt')), 'error')
        else:
            flash("Require Username already exists", 'error')
        return redirect(url_for('signup'))
    return render_template('signup.html', from_admin=from_admin)


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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/suspend')
def suspend():
    session.clear()
    session["integrity"] = False
    return render_template("danger.html")

@app.route('/system/integrity/unlock')
def unlock():
    if itg.verifyMD5():
        session["integrity"] = True
        itg.log(f'[Admin] System unlocked')
        return redirect(url_for('home'))
    else:
        print("unlock fail")
        return redirect(url_for('suspend'))


if __name__ == "__main__":
    app.run(debug=True)
