#Imports
import firebase_admin
import pyrebase
import json
from firebase_admin import credentials, auth, firestore
from flask import Flask, request
from functools import wraps

#App configuration
app = Flask(__name__)

#Connect to firebase
cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('fbConfig.json')))
db = firestore.client()
client_ref = db.collection('Clients')
user_ref = db.collection('users')

def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('authorization'):
            return {'message': 'No token provided'}, 400
        try:
            user = auth.verify_id_token(request.headers['authorization'])
            request.user = user
        except:
            return {'message':'Invalid token provided.'},400
        return f(*args, **kwargs)
    return wrap
    
@app.route('/api/poc', methods=['POST'])
@check_token
def add_poc():
  try:
    req_json = request.json
    user = request.user
    userId = user['user_id']
    client_list = list(client_ref.where("userId", "==", userId).stream())
    doc_ids = []
    for doc in client_list:
      doc_ids.append(doc.id)
    client_id = doc_ids[0]
    print(client_id)
    guardian_collec = client_ref.document(client_id).collection('guardians')
    guardians = req_json["guardians"]
    for guardian in guardians:
      guardian_collec.document().set({
        "Name": guardian['name'],
        "Email": guardian['email'],
        "Phone": guardian['phone'],
      })
    return {'message': f'{user}'}, 200
  except Exception as e:
    return {'message': f'There was an POSTING {e}'}, 400

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
    return {'message': 'There was an error logging'}, 400

if __name__ == '__main__':
  app.run(debug=True)