
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate(
    'files/chatbot-eb541-firebase-adminsdk-76s8b-86eb4a55f0.json')
firebase_admin.initialize_app(
    cred, {'databaseURL': 'https://chatbot-eb541-default-rtdb.europe-west1.firebasedatabase.app'})


users_ref = db.reference('users')


with open('files/username_to_channel.txt', 'r') as file:
    lines = file.readlines()

for line in lines:
    username = line.split(':')[0]
    link = line.split(':')[1] + ':' + (line.split(':')[2])
    users_ref.push({'username': username, 'link': link})
