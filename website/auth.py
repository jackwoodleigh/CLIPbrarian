from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from functools import wraps
import pandas as pd
from .models import User
from .database_manager import DatabaseManager
import requests, json, os

auth = Blueprint('auth', __name__)
def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' in session:
            #flash('Please logout to access this page.', category='success')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session: 
            #flash('Please login to access this page.', category='success')  # Modify the flash message
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function



#############################################################################################


@auth.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password1')

        user = current_app.config['DBM'].SF.query_all("SELECT Id, Email__c, FirstName__c, LastName__c, Password__c FROM CLIPAccount__c WHERE Email__c = '{}'".format(email))
        
    
        if user['records']:
            user = pd.DataFrame(user['records']).loc[0]
            if check_password_hash(user['Password__c'], password):
                session['user'] = {'id': user['Id'], 'email': user['Email__c'], 'first_name': user['FirstName__c'], 'last_name': user['LastName__c'], 'password': user['Password__c']}
                return redirect(url_for('views.home'))
            else:
                pass
        else:
            pass
        return redirect(url_for('views.home'))

    return render_template("login.html", session=session)




@auth.route('/sign-up', methods=['GET', 'POST']) # home page aka website {domain}/ 
@logout_required
def sign_up():
    
    if request.method == 'POST':
        print("yo")
        email = request.form.get('email')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = current_app.config['DBM'].SF.query_all("SELECT Email__c FROM CLIPAccount__c WHERE Email__c = '{}'".format(email))
        
        if user['records']:
            print('Email already Exists')
        elif len(email) < 4:
            print('Email must be at least 4 characters')
        elif len(firstname) < 2:
            print('Username must be at least 2 characters')
        elif len(lastname) < 2:
            print('Username must be at least 2 characters')
        elif password1 != password2:
            print('Passwords don\'t match')
        elif len(password1) < 4:
            pass #flash('Password must be at least 4 characters', category='error') 
        else:
            current_app.config['DBM'].SF.CLIPAccount__c.create({'Email__c': email, 'FirstName__c': firstname, 'LastName__c': lastname, 'Password__c': generate_password_hash(password1)})
            return redirect(url_for('auth.login'))

    return render_template("sign_up.html") 

@auth.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    session.pop('token', None)
    session.pop('last_page', None)
    session.pop('fileids', None)
    return redirect(url_for('views.home'))

#############################################################################################

@auth.route('/google/login')
@login_required
def drive_login():
    session.pop('token', None)
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    scopes = [
        "https://www.googleapis.com/auth/photoslibrary",
        "https://www.googleapis.com/auth/drive"
    ]
    scope_string = ' '.join(scopes)
    redirect_uri = "https://clipsite-amjzx.ondigitalocean.app/auth/google/callback"
    full_auth_url = f"{auth_url}?response_type=code&client_id={current_app.config['CLIENT_SECRETS']['web']['client_id']}&redirect_uri={current_app.config['CLIENT_SECRETS']['web']['redirect_uris'][0]}&scope={scope_string}&prompt=select_account"
    return redirect(full_auth_url)

@auth.route('/google/logout')
@login_required
def drive_logout():
    session.pop('token', None)
    return redirect(session['last_page'])
    

@auth.route('/auth/google/callback')
@login_required
def callback():
    auth_code = request.args.get('code')
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': auth_code,
        'client_id': current_app.config['CLIENT_SECRETS']['web']['client_id'],
        'client_secret': current_app.config['CLIENT_SECRETS']['web']['client_secret'],
        'redirect_uri':  current_app.config['CLIENT_SECRETS']['web']['redirect_uris'][0],
        'grant_type': 'authorization_code'
    }
    r = requests.post(token_url, data=data)
    token_response = r.json()
    session['token'] = token_response
    return redirect(session['last_page'])

@auth.route('/drive-refresh')
@login_required
def drive_refresh():
    photo_data = current_app.config['DBM'].retrievePhotos()
    feature_data = {}
    feature_data = current_app.config['MM'].loadNewFeatureData(feature_data, photo_data)
    current_app.config['DBM'].updateLibraryFeatureData(feature_data)   
    return redirect(session['last_page'])

@auth.route('/drive-data-delete')
@login_required
def drive_data_delete():
    current_app.config['DBM'].deleteLibraryFeatureData()
    session['fileids'] = False
    return redirect(session['last_page'])

@auth.route('/create-file')
@login_required
def create_file():
    current_app.config['DBM'].createFile("Hello World!")
    return redirect(url_for('views.home'))

@auth.route('/photos-test')
@login_required
def photos_test():
    print(current_app.config['DBM'].retrievePhotos())
    return redirect(url_for('views.drive'))




