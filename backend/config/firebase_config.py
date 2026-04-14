import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json
from firebase_admin import credentials, initialize_app

firebase_json = os.environ.get("FIREBASE_CREDENTIALS")

cred_dict = json.loads(firebase_json)
cred = credentials.Certificate(cred_dict)

initialize_app(cred)

firebase_admin.initialize_app(cred)

db = firestore.client()
