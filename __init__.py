#Something
from flask import Flask, render_template, session, url_for, redirect, flash
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

import json
import os
import time, threading

from . import my_db


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Mysql1234!@localhost/sd3biot22'
app.config['SQL_TRACK_MODIFICATONS'] = False

db = SQLAlchemy(app)

facebook_app_id = os.getenv('FACEBOOK_APP')
print("Facebook app id is " + str(facebook_app_id))
facebook_app_secret = os.getenv('FACEBOOK_SECRET')

test = os.getenv('TEST')
print("Test is " + str(test))

facebook_blueprint = make_facebook_blueprint(client_id = facebook_app_id, client_secret = facebook_app_secret, redirect_url='/facebook_login')
app.register_blueprint(facebook_blueprint, url_prefix='/facebook_login')

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
@login_required
def main():
    flash(session['user'])
    my_db.add_user_and_login(session['user'], int(session['user_id']))
    my_db.view_all()
    return render_template("index.html")

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


if __name__ == '__main__':
    app.run()





