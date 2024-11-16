from pydantic import BaseModel
from datetime import datetime

class Users(BaseModel):
    name: str
    mail: str
    password: str
    updated_at: int = int ( datetime.timestamp(datetime.now()))
    creation: int = int ( datetime.timestamp(datetime.now()))

class ToDoTask(BaseModel):
    index: str
    description: str
    remind_noti: bool = False
    user_id: str
    updated_at: int = int ( datetime.timestamp(datetime.now()))
    creation: int = int ( datetime.timestamp(datetime.now()))