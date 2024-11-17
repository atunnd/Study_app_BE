from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config import user_collection, todo_collection, messages_collection
from database.schemas import all_users, all_tasks
from database.models import Users, ToDoTask
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Union, Any
from security import validate_token
import jwt
from passlib.context import CryptContext 
import logging
import json

SECURITY_ALGORITHM = 'HS256'
SECRET_KEY = '123456'


app = FastAPI(
    title='FastAPI JWT', openapi_url='/openapi.json', docs_url='/docs',
    description='fastapi jwt')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_text(message)

    async def broadcast(self, message: dict, exclude_client: str = None):
        message_str = json.dumps(message)
        for client_id, connection in self.active_connections.items():
            if client_id != exclude_client:
                try:
                    await connection.send_text(message_str)
                except WebSocketDisconnect:
                    self.disconnect(client_id)

manager = ConnectionManager()

# Helper function to log messages in the database
def save_message_to_db(client_id: str, message: str):
    message_entry = {
        "client_id": client_id,
        "message": message,
        "timestamp": datetime.utcnow()
    }
    try:
        messages_collection.insert_one(message_entry)
        logging.info(f"Message saved to database: {message_entry}")
    except Exception as e:
        logging.error(f"Error saving message to database: {e}")

# WebSocket Endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(client_id: str, websocket: WebSocket):
    await manager.connect(client_id, websocket)
    try:
        #await manager.send_personal_message(f"Hello Client {client_id}!", client_id)
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"{data}", client_id)
            await manager.broadcast({"id": client_id, "data": data}, exclude_client=client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logging.info(f"Client {client_id} disconnected")
        #await manager.broadcast(f"Client {client_id} has left the chat.")

user_router = APIRouter()
task_router = APIRouter()

@user_router.get("/all_users")
async def get_all_users():
    data = user_collection.find( )
    return all_users(data)

@user_router.get("/get_user_name_{user_id}")
async def get_user_name(user_id: str):
    try:
        #{"_id":user_id}
        data = user_collection.find({"_id":ObjectId(user_id)})
        if data is None:
            raise HTTPException(status_code=404, detail="User not found")
        return all_users(data)[0]['name']
    except Exception as e:
        return HTTPException(status_code=500, detail="Internal Server Error")

@user_router.post("/create_user")
async def create_user(new_user: Users):
    try:
        # Check if the username already exists
        existing_user = user_collection.find_one({"name": new_user.name})
        if existing_user:
            return HTTPException(status_code=400, detail="Username already exists")

        resp = user_collection.insert_one(dict(new_user))
        return {"status_code": 200, "id": str(resp.inserted_id)}

    except HTTPException as e:
        return e
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occurred: {e}")
    
def generate_token(username: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(
        seconds=60 * 60 * 24 * 3  # Expired after 3 days
    )
    to_encode = {
        "exp": expire, "username": username
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=SECURITY_ALGORITHM)
    return encoded_jwt

@user_router.post("/log_in")
async def log_in(credentials: Users):
    logging.info(f"Received credentials: {credentials}")
    usermail = credentials.mail
    password = credentials.password

    user = user_collection.find_one({"mail": usermail})  
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    token = generate_token(str(user['_id']))
   
    if user["password"] != password:
        return HTTPException(status_code=400, detail="Invalid password")

    #return {"status_code": 200, "message": "Login successful", "user_id": str(user["_id"])}
    return {
        'token': token,
        'user_id': str(user['_id']),
        'user_name': str(user['name']),
        'mail': str(user['mail']),
    }

@user_router.put("/update_user_{user_id}")
async def update_user(user_id: str, updated_user: Users):
    try:
        id = ObjectId(user_id)
        existing_doc = user_collection.find_one({"_id": id})
        if not existing_doc:
            return HTTPException(status_code=404, detail=f"User does not exists")
        updated_user.updated_at = datetime.timestamp(datetime.now())
        resp = user_collection.update_one({"_id": id}, {"$set": dict(updated_user)})
        return {"status_code": 200, "message": "User Updated Successfully"}

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occured {e}")
    
@user_router.delete("/delete_user{user_id}")
async def delete_user(user_id:str):
    try:
        id = ObjectId(user_id)
        existing_user = user_collection.find_one({"_id": id})
        if not existing_user:
            return HTTPException(status_code=404, detail=f"User does not exists")
        resp = user_collection.delete_one({"_id": id})
        return {"status_code": 200, "message": "User Deleted Successfully"}

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occured {e}")


@task_router.get("/all_tasks", dependencies=[Depends(validate_token)])
async def get_all_tasks():
    data = todo_collection.find( )
    return all_tasks(data)

@task_router.get("/tasks/{user_id}", dependencies=[Depends(validate_token)])
async def get_tasks_by_user(user_id: str):
    try:
        # Convert user_id to ObjectId if necessary, depending on how it's stored
        tasks = todo_collection.find({"user_id": user_id})  # Find tasks that match the user_id
        tasks = list(tasks)  # Convert the cursor to a list
        task_list = [
            ToDoTask(
                id=str(task["_id"]),
                index = str(task.get("index")),
                description=task.get("description"),
                remind_noti=task.get("remind_noti"),
                checked=task.get("checked"),
                user_id=task.get("user_id")
            ) for task in tasks
        ]
        return task_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@task_router.post("/create_task", dependencies=[Depends(validate_token)])
async def create_task(new_task: ToDoTask):
    try:
        resp = todo_collection.insert_one(dict(new_task))
        return str(resp.inserted_id)
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occured {e}")

@task_router.put("/update_task/{task_id}", dependencies=[Depends(validate_token)])
async def update_task(task_id: str, updated_task: ToDoTask):
    try:
        logging.info(f"Updating task {task_id} with data: {updated_task}")
        id = ObjectId(task_id)
        existing_task = todo_collection.find_one({"_id": id})
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task does not exist")
        
        updated_data = dict(updated_task)
        updated_data["updated_at"] = datetime.timestamp(datetime.now())

        resp = todo_collection.update_one({"_id": id}, {"$set": updated_data})
        if resp.matched_count == 0:
            raise HTTPException(status_code=404, detail="Task update failed")
        
        return {"status_code": 200, "message": "Task Updated Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@task_router.delete("/delete_task_{task_id}", dependencies=[Depends(validate_token)])
async def delete_task(task_id:str):
    try:
        id = ObjectId(task_id)
        existing_task = todo_collection.find_one({"_id": id})
        if not existing_task:
            return HTTPException(status_code=404, detail=f"Task does not exists")
        resp = todo_collection.delete_one({"_id": id})
        return {"status_code": 200, "message": "Task Deleted Successfully"}

    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occured {e}")



app.include_router(task_router)
app.include_router(user_router)