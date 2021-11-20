#Imports
import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth, firestore
from flask import Flask, request
import sys

#App configuration
app = Flask(__name__)

#Connect to firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
client_ref = db.collection('Clients')
user_ref = db.collection('users')

#Data source
users = [{'uid': 1, 'name': 'Noah Schairer'}]

#Api route to get users
@app.route('/api/userinfo')
def userinfo():
  return {'data': users}, 200

#Api route to sign up a new user
@app.route('/api/signup')
def signup():
  email = request.form.get('email')
  name = request.form.get('name')
  phone = request.form.get('phone')
  password = request.form.get('password')
  if email is None or password is None or phone is None or name is None:
    return {'message': 'Error missing email or password'}, 400
  try:
    user = auth.create_user(
      email=email,
      password=password
    )
    user_ref.document(user.uid).set({
      "Name": name,
      "Phone": phone,
      "Email": email
    })
    new_client_ref = client_ref.document()
    new_client_ref.set({"userId": user.uid})
    guardians = new_client_ref.collection('guardians')
    guardians.document().set({
      "Name": name,
      "Phone": phone,
      "Email": email
    })
    return {'message': f'Successfully created user {user.uid}'}, 200
  except Exception as e:
    return {'message': f'{e}'},400

#Api route to get a new token for a valid user
@app.route('/api/token')
def token():
  email = request.form.get('email')
  password = request.form.get('password')
  try:
    user = pb.auth().sign_in_with_email_and_password(email, password)
    jwt = user['idToken']
    return {'token': jwt}, 200
  except:
    return {'message': 'There was an error logging in'},400

if __name__ == '__main__':
  app.run(debug=True)