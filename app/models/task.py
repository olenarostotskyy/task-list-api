from app import db
from sqlalchemy import null

class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    completed_at=db.Column(db.DateTime, nullable=True)
    goal_id=db.Column(db.Integer, db.ForeignKey('goal.goal_id'))
    goal=db.relationship("Goal", back_populates="tasks")

