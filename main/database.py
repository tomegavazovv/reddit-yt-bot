
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate(
    '...')
firebase_admin.initialize_app(
    cred, {'databaseURL': '...'})
