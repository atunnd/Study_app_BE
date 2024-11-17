def individual_user(user):
    return {
        "id": str(user["_id"]),
        "name": str(user["name"]),
        "mail": str(user["mail"]),
        "password": str(user["password"])
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