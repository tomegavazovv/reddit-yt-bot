
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate(
    'files/chatbot-eb541-firebase-adminsdk-76s8b-86eb4a55f0.json')
firebase_admin.initialize_app(
    cred, {'databaseURL': 'https://chatbot-eb541-default-rtdb.europe-west1.firebasedatabase.app'})
