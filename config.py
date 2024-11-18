from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://atuanngndai:21Pilots@todolist.f5kei.mongodb.net/?retryWrites=true&w=majority&appName=todolist"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

db = client.todo_db
user_collection = db["user_data"]
todo_collection = db["todo_data"]
messages_collection = db["msg_data"]