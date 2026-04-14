import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

firebase_json = os.getenv("FIREBASE_CREDENTIALS")

if not firebase_json:
    raise ValueError("FIREBASE_CREDENTIALS no está definida")

cred_dict = json.loads(firebase_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_dict))

db = firestore.client()
