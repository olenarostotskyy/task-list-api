from flask import Blueprint, make_response,request,jsonify,abort
from app import db
from app.models.goal import Goal
from app.models.task import Task
from datetime import datetime
import requests
from flask import current_app as app


# ****************************registering my blueprints********************************
tasks_bp = Blueprint ("tasks", __name__, url_prefix= "/tasks", )
goals_bp = Blueprint ("goals", __name__, url_prefix= "/goals", )


#**********************************helper_functions************************************

# helper function to send a slack message
def send_slack_message(message):
    url = "https://slack.com/api/chat.postMessage?channel=task-notifications&text=" + message
   
    headers = {'Authorization': f'Bearer {app.config["SLACK_TOKEN"]}'} # using hidden token from .env
    
    r = requests.patch(url, headers=headers)
    


# helper function to check if id is correct
def validate_task(task_id):
    # handling invalid planet_id input
    try:
        task_id=int(task_id)
    except:
        abort(make_response({"msg":f"Task # {task_id} is invalid id "},400)) 
    
    #read task id 
    task=Task.query.get(task_id)
    if task is None:
        abort(make_response({"msg":f"Task # {task_id} not found "},404)) 
    
    return task


# helper function to check goal id
def validate_goal(goal_id):
    # handling invalid id input
    try:
        goal_id=int(goal_id)
    except:
        abort(make_response({"msg":f"Goal # {goal_id} is invalid id "},400)) 
    
    #read id 
    goal=Goal.query.get(goal_id)
    if goal is None:
        abort(make_response({"msg":f"Goal # {goal_id} not found "},404)) 
    
    return goal   



# helper function to check request body for tasks
def check_request_body():
    request_body = request.get_json()

    if "title" not in request_body or "description" not in request_body:
        abort(make_response({"details":f"Invalid data"}, 400))
   
    return request_body


# helper function to check request body for goals
def check_request_body_for_goals():
    request_body = request.get_json()

    if "title" not in request_body:
        abort(make_response({"details":f"Invalid data"}, 400))
   
    return request_body



#**************************************************************************************
# ************************************TASK_ROUTES**************************************

# create new task
@tasks_bp.route("", methods=["POST"])
def create_task():
    request_body = check_request_body()
    
    new_task=Task(
        title=request_body["title"],
        description=request_body["description"],
        completed_at=request_body.get("completed_at", None)
    )
    db.session.add(new_task)
    db.session.commit()

    rsp={
        "task": {
            "id": new_task.task_id,
             "title": new_task.title,
             "description": new_task.description,
             "is_complete": new_task.completed_at !=None }}

    return jsonify(rsp),201         


# get tasks
@tasks_bp.route("", methods=["GET"])
def get_tasks():  

    tasks = Task.query.all()
    
    # building planet response
    tasks_response = [] 
    
    for task in tasks:
        tasks_response.append({
            "id": task.task_id,
            "title": task.title,
            "description": task.description,
            "is_complete":False
        })

    # query parameters
    params=request.args #this returns the value of the query param if it was set, or None if the query param is not found.

    if "sort" in params and params["sort"]=="asc":
        tasks_response.sort(key=lambda x:x["title"])
    elif "sort" in params and params["sort"]=="desc":
        tasks_response.sort(key=lambda x:x["title"], reverse=True)  

    return jsonify(tasks_response)   



# get one task
@tasks_bp.route("/<task_id>", methods=["GET"]) 
def get_one_task(task_id):
    
    task=validate_task(task_id)
    
    resp = {
        "task": {
        "id" : task.task_id,
        "title": task.title,
        "description": task.description,
        "is_complete":False}
        }
    
    if task.goal != None:
        resp["task"]["goal_id"] = task.goal_id
        print("hii")

    return resp, 200  



# update task
@tasks_bp.route("/<task_id>", methods=["PUT"])
def update_task(task_id):

    task=validate_task(task_id)

    request_body=check_request_body()
    task.title=request_body["title"]
    task.description=request_body["description"]
    task.completed_at=request_body.get("completed_at", None)

    db.session.commit()

    rsp={
        "task": {
            "id": task.task_id,
             "title": task.title,
             "description": task.description,
             "is_complete": task.completed_at !=None }}
    
    return jsonify(rsp),200



# delete a task
@tasks_bp.route("/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task=validate_task(task_id)

    db.session.delete(task)
    db.session.commit()

    return (make_response({"details":f'Task {task_id} "{task.title}" successfully deleted'}), 200)



# update completed task 
@tasks_bp.route("/<task_id>/mark_complete", methods=["PATCH"])
def update_complete_task(task_id):
    
    task=validate_task(task_id)
    
    task.completed_at= datetime.utcnow()

    db.session.commit()

    send_slack_message(f'Someone just completed the task "{task.title}"')
    
    rsp={
        "task": {
            "id": task.task_id,
             "title": task.title,
             "description": task.description,
             "is_complete": task.completed_at != None }}

    return (rsp),200


# update incomplete task
@tasks_bp.route("/<task_id>/mark_incomplete", methods=["PATCH"])
def update_incomplete_task(task_id):
   
    task=validate_task(task_id)
    
    task.completed_at= None

    db.session.commit()
    
    rsp={
        "task": {
            "id": task.task_id,
             "title": task.title,
             "description": task.description,
             "is_complete": task.completed_at != None }}
    
    return ((rsp),200)    



#*************************************************************************************
#***********************************GOAL_ROUTES***************************************

# create new goal
@goals_bp.route("", methods=["POST"])
def create_goal():
    
    request_body = check_request_body_for_goals()
    
    new_goal=Goal(
        title=request_body["title"])
        
    db.session.add(new_goal)
    db.session.commit()

    rsp={
        "goal": {
             "id": new_goal.goal_id,
             "title": new_goal.title }}
    
    return jsonify(rsp),201  



# get all goals
@goals_bp.route("", methods=["GET"])
def get_all_goals():  

    goals = Goal.query.all()
    
    goals_response = [] 
    
    for goal in goals:
        goals_response.append({
            "id": goal.goal_id,
            "title": goal.title })

    return jsonify(goals_response)    



# get one saved goal
@goals_bp.route("/<goal_id>", methods=["GET"]) 
def get_one_goal(goal_id):
    
    goal=validate_goal(goal_id)
    
    return {
        "goal": {
        "id" : goal.goal_id,
        "title": goal.title }}, 200  



# update goal
@goals_bp.route("/<goal_id>", methods=["PUT"])   
def update_goal(goal_id):
    
    goal=validate_goal(goal_id)
    
    request_body=check_request_body_for_goals()

    goal.title=request_body["title"]
   
    db.session.commit()

    rsp={
        "goal": {
            "id": goal.goal_id,
            "title": goal.title }}
    
    return jsonify(rsp),200



# delete goal
@goals_bp.route("/<goal_id>", methods=["DELETE"])   
def delete_goal(goal_id):
    
    goal=validate_goal(goal_id)

    db.session.delete(goal)
    db.session.commit()

    return (make_response({"details":f'Goal {goal_id} "{goal.title}" successfully deleted'}), 200)    



# get all tasks for one goal
@goals_bp.route("/<goal_id>/tasks", methods=["POST"])  
def get_tasks(goal_id):

    goal=validate_goal(goal_id)

    request_body = request.get_json()

    task_ids=request_body.get('task_ids')
    
    for taskid in task_ids:
        task = validate_task(taskid)
        task.goal_id = goal_id

    db.session.commit()  

    goal = validate_goal(goal_id)

    task_ids_response = []
    
    for task in goal.tasks:
        task_ids_response.append(task.task_id)

    resp = {
        "id": goal.goal_id,
        "task_ids": task_ids_response }

    return jsonify(resp), 200


# get tasks for one goal
@goals_bp.route("/<goal_id>/tasks", methods=["GET"])  
def get_tasks_for_goal(goal_id): 
    
    goal=validate_goal(goal_id)

    tasks_response=[]
    for task in goal.tasks:
        tasks_response.append(
            {
      "id": task.task_id,
      "goal_id": goal.goal_id,
      "title": task.title,
      "description": task.description,
      "is_complete": task.completed_at != None })

    goal_response = {
        "id": goal.goal_id,
        "title": goal.title,
        "tasks": tasks_response }

    return jsonify(goal_response), 200



