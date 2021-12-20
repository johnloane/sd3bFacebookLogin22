import hashlib
import string

from flask import Flask, render_template, session, url_for, redirect, flash
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

import random

import json
import os
import time, threading

from . import my_db, PB


app = Flask(__name__)

mysql_password = os.getenv('mysql_password';)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:'+mysql_password+'@localhost/sd3biot22'
app.config['SQL_TRACK_MODIFICATONS'] = False

db = SQLAlchemy(app)

facebook_app_id = os.getenv('FACEBOOK_APP')
print("Facebook app id is " + str(facebook_app_id))
facebook_app_secret = os.getenv('FACEBOOK_SECRET')

test = os.getenv('TEST')
print("Test is " + str(test))

facebook_blueprint = make_facebook_blueprint(client_id = facebook_app_id, client_secret = facebook_app_secret, redirect_url='/facebook_login')
app.register_blueprint(facebook_blueprint, url_prefix='/facebook_login')

PB.grant_access("johns-pi", True, True)

alive = 0
data = {}


@app.route('/')
def index():
    return render_template("login.html")


@app.route('/facebook_login')
def facebook_login():
    if not facebook.authorized:
        # This will redirect to facebook login
        return redirect(url_for('facebook.login'))
    account_info = facebook.get('/me')
    if account_info.ok:
        print("Access token", facebook.access_token)
        me = account_info.json()
        session['logged_in'] = True
        session['facebook_token'] = facebook.access_token
        session['user'] = me['name']
        session['user_id'] = me['id']
        print("Logged in as " + me['name'] + " redirecting to main")
        return redirect(url_for('main'))
    print("Account info is not ok")
    return redirect(url_for('login'))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "logged_in" in session:
            if session["logged_in"]:
                return f(*args, **kwargs)

        flash("Please login first")
        return redirect(url_for('login'))
    return wrapper


@app.route('/main')
#@login_required
def main():
    session['facebook_token'] = '123234asdfbgfhfsgh'
    session['user'] = 'John'
    session['user_id'] = '326681429269251'
    flash(session['user'])
    my_db.add_user_and_login(session['user'], int(session['user_id']))
    my_db.view_all()
    return render_template("index.html", user_id=session['user_id'], online_users = my_db.get_all_logged_in_users())

def clear_user_session():
    session['facebook_token'] = None
    session['user'] = None
    session['user_id'] = None

@app.route('/login')
def login():
    clear_user_session()
    return render_template('login.html')

@app.route('/logout')
def logout():
    flash("You just logged out")
    my_db.user_logout(session['user_id'])
    my_db.view_all()
    clear_user_session()
    return redirect(url_for('login'))


@app.route('/keep_alive')
def keep_alive():
    global alive, data
    alive += 1
    keep_alive_count = str(alive)
    data['keep_alive'] = keep_alive_count
    parsed_json = json.dumps(data)
    return str(parsed_json)


def str_to_bool(s):
    if 'true' in str(s):
        return True
    elif 'false' in str(s):
        return False
    else:
        raise ValueError


@app.route('/grant-<who>-<key_or_id>-<read>-<write>', methods=['GET', 'POST'])
def grant_access(who, key_or_id, read, write):
    if int(session['user_id']) == 326681429269251:
        print("Granting " + key_or_id + " read:"+read +", write:"+write+" permission")
        my_db.add_user_permission(key_or_id, read, write)
        auth_key = my_db.get_auth_key(key_or_id)
        PB.grant_access(auth_key, str_to_bool(read), str_to_bool(write))
    else:
        print("Non admin trying to grant privileges")
        return json.dumps({"access" : "denied"})
    return json.dumps({"access": "granted"})


def salt(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def create_auth_key():
    s = salt(10)
    hash_string = str(session['facebook_token']) + s
    hashing = hashlib.sha256(hash_string.encode('utf-8'))
    return hashing.hexdigest()

@app.route('/get_auth_key', methods=['GET', 'POST'])
def get_auth_key():
    print("Creating authkey for: " + session['user'])
    auth_key = create_auth_key()
    my_db.add_auth_key(int(session['user_id']), auth_key)
    (read, write) = my_db.get_user_access(int(session['user_id']))
    PB.grant_access(auth_key, read, write)
    auth_response = {'auth_key' : auth_key, 'cipher_key' : PB.cipher_key}
    json_response = json.dumps(auth_response)
    return str(json_response)


if __name__ == '__main__':
    app.run()





