import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage

firebase_json = os.getenv("FIREBASE_CREDENTIALS")

if not firebase_json:
    raise ValueError("FIREBASE_CREDENTIALS no está definida")

cred_dict = json.loads(firebase_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_dict))

cred = credentials.Certificate("firebase_json.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'bioaccess-1074c.appspot.com'
})


db = firestore.client()
bucket = storage.bucket()
