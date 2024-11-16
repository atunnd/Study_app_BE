from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config import user_collection, todo_collection
from database.schemas import all_users, all_tasks
from database.models import Users, ToDoTask
from bson.objectid import ObjectId
from datetime import datetime
from typing import Union, Any
from security import validate_token
import jwt
from passlib.context import CryptContext 
import logging

SECURITY_ALGORITHM = 'HS256'
SECRET_KEY = '123456'


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


user_router = APIRouter()
task_router = APIRouter()

@user_router.get("/")
async def get_all_users():
    data = user_collection.find( )
    return all_users(data)

@user_router.post("/create_user")
async def create_user(new_user: Users):
    try:
        resp = user_collection.insert_one(dict(new_user))
        return {"status_code": 200, "id": str(resp.inserted_id)}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occured {e}")

@user_router.post("/log_in")
async def log_in(credentials: Users):
    logging.info(f"Received credentials: {credentials}")
    usermail = credentials.mail
    password = credentials.password

    user = user_collection.find_one({"mail": usermail})  
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

   
    if user["password"] != password:
        raise HTTPException(status_code=400, detail="Invalid password")

    return {"status_code": 200, "message": "Login successful", "user_id": str(user["_id"])}


@user_router.put("/{user_id}")
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
    
@user_router.delete("/{user_id}")
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


@task_router.get("/all_tasks")
async def get_all_tasks():
    data = todo_collection.find( )
    return all_tasks(data)

@task_router.post("/create_task")
async def create_task(new_task: ToDoTask):
    try:
        resp = todo_collection.insert_one(dict(new_task))
        return {"status_code": 200, "id": str(resp.inserted_id)}
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Some error occured {e}")

@task_router.put("/update_task/{task_id}")
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


@task_router.delete("/delete_task_{task_id}")
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