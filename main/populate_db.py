
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate(
    '...')
firebase_admin.initialize_app(
    cred, {'databaseURL': '...'})


users_ref = db.reference('users')


with open('files/username_to_channel (6).txt', 'r') as file:
    lines = file.readlines()

for line in lines:
    username = line.split(':')[0]
    link = line.split(':')[1] + ':' + (line.split(':')[2])
    users_ref.push({'username': username, 'link': link})
