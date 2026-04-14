import os
import json
import firebase_admin
from firebase_admin import credentials

firebase_json = os.getenv("FIREBASE_CREDENTIALS")

cred = credentials.Certificate(json.loads(firebase_json))

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
