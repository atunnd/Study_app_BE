def individual_user(user):
    return {
        "id": str(user["_id"]),
        "name": str(user["name"]),
        "mail": str(user["mail"]),
        "password": str(user["password"]),
        "gemini_api": str(user['gemini_api'])
    }

def all_users(users):
    return [individual_user(user) for user in users]

def individual_task(task):
    return {
        "id": str(task["_id"]),
        "index": str(task['index']),
        "description": str(task['description']),
        "remind_noti": str(task["remind_noti"]),
        "checked": str(task['checked']),
        "user_id": str(task['user_id'])
    }

def all_tasks(tasks):
    return [individual_task(task) for task in tasks]

def individual_msg(message):
    return {
        "client_id": str(message['client_id']),
        "data": str(message['data'])
    }

def all_messages(messages):
    return [individual_msg(msg) for msg in messages]