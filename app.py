from flask import Flask, request, jsonify, session, redirect, template_rendered, url_for, flash
import json, os
import pandas as pd
from datetime import datetime
import pytz

import module.integrity as itg
from module.userManagement import UserManager

app = Flask(__name__)

inventory = {}
timezone = pytz.timezone('Asia/Hong_Kong')
um = UserManager()

@app.route('/')
def home():
    if session.get("username"):
        return template_rendered("index.html", version=itg.sysInfo())
    else:
        return redirect(url_for('login'), version=itg.sysInfo())
    
@app.route('/login', method=['GET', 'POST'])
def login():
    if request.method == 'GET':
        username = request.form['username']
        password = request.form['password']

        if um.logIn(username, password):
            return redirect(url_for(home))
        else:
            flash('Username/Password incorrect. Please try again')
    return template_rendered('login.html')


if __name__ == "__main__":
    app.run(debug=True)
