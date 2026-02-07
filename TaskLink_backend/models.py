# backend/models.py
from database import db
from datetime import datetime
# from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Integer, default=0) # 0:普通用户, 1:管理员
    created_at = db.Column(db.DateTime, default=datetime.now)
    avatar = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        """转成字典，方便API返回"""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # 关联用户
    title = db.Column(db.String(100), nullable=False)
    trigger_time = db.Column(db.String(5), nullable=False) # 格式 "09:00"
    action_type = db.Column(db.String(20), nullable=False) # APP, LINK, CALL
    target_value = db.Column(db.String(255), nullable=False) # 包名或链接
    is_active = db.Column(db.Boolean, default=True) # 1=启用
    created_at = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.String(500), nullable=True)  # 任务备注
    is_loop = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "time": self.trigger_time,
            "type": self.action_type,
            "target": self.target_value,
            "active": bool(self.is_active)
        }

class TaskLog(db.Model):
    __tablename__ = 'task_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_title = db.Column(db.String(100), nullable=False) # 记录当时的任务名(防止任务被删后查不到)
    task_type = db.Column(db.String(20)) # APP / LINK
    status = db.Column(db.String(20), default='SUCCESS') # SUCCESS / FAIL
    executed_at = db.Column(db.DateTime, default=datetime.now) # 执行时间
    result = db.Column(db.Text, nullable=True)  # 脚本返回的详细结果(可能很长，用Text)
    def to_dict(self):
        return {
            'id': self.id,
            'task_title': self.task_title,
            'task_type': self.task_type,
            'status': self.status,
            'executed_at': self.executed_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(20), default='text')  # text / image
    created_at = db.Column(db.DateTime, default=datetime.now)


    sender = db.relationship('User', backref='messages')

    def to_dict(self):

        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.sender.username if self.sender else "Unknown",
            "avatar": self.sender.avatar if self.sender else None,
            "content": self.content,
            "type": self.msg_type,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }