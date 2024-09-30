from pymongo import MongoClient
from werkzeug.security import generate_password_hash

from user import User

client = MongoClient('mongodb+srv://devilworld:jatin1112003@cluster0.ratif.mongodb.net/')

chat_db = client.get_database('ChatDB')
users_collection = chat_db.get_collection('users')

def save_user(name, email, password):
    hashed_password = generate_password_hash(password)
    users_collection.insert_one({'_id': name, 'email': email, 'password': hashed_password})

def get_user(username):
    user_data=users_collection.find_one({'_id':username})
    return User(user_data['_id'] ,user_data['email'] ,user_data['password'] ) if user_data else None


