import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User,Task,TaskLog,ChatMessage
import requests
import re
app = Flask(__name__)
CORS(app)  # 允许跨域

# --- 数据库配置 ---
# 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/tasklink'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# 初始化数据库
db.init_app(app)


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名或密码不能为空"}), 400

    # --- 2. 用户名严格校验 (对标大厂) ---
    # 规则：6-20位，仅允许字母、数字、下划线，且必须以字母开头
    # 微信/QQ通常不允许纯数字或特殊字符作为账号
    username_pattern = r'^[a-zA-Z][a-zA-Z0-9_]{5,19}$'

    if not re.match(username_pattern, username):
        return jsonify({
            "code": 400,
            "msg": "用户名格式错误：需6-20位，以字母开头，仅含字母/数字/下划线"
        }), 400

    # --- 3. 密码强度强校验 ---
    # 规则：8-20位，必须包含大小写字母和数字
    if len(password) < 8 or len(password) > 20:
        return jsonify({"code": 400, "msg": "密码长度需在 8-20 位之间"}), 400

    if not re.search(r'[a-z]', password):
        return jsonify({"code": 400, "msg": "密码必须包含小写字母"}), 400

    if not re.search(r'[A-Z]', password):
        return jsonify({"code": 400, "msg": "密码必须包含大写字母"}), 400

    if not re.search(r'[0-9]', password):
        return jsonify({"code": 400, "msg": "密码必须包含数字"}), 400

    # --- 4. 检查数据库是否已存在 ---
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 400, "msg": "该用户名已被注册"}), 400

    try:
        # 5. 密码加密 & 入库
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"code": 200, "msg": "注册成功", "data": new_user.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": "服务器内部错误，注册失败"}), 500


# --- 登录接口 ---
# TaskLink_backend/app.py

# 确保文件头部导入了 check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 1. 查询用户
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # 3. 返回包含最新头像的用户信息
        return jsonify({
            "code": 200,
            "msg": "登录成功",
            "data": {
                "id": user.id,
                "username": user.username,
                # 确保返回 avatar 字段，如果没有则返回空字符串
                "avatar": user.avatar if user.avatar else "",
                "token": "fake-jwt-token"
            }
        })

    return jsonify({"code": 401, "msg": "用户名或密码错误"}), 401


# --- 获取任务列表 ---
@app.route('/api/tasks', methods=['GET'])
def get_tasks():

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少用户ID"}), 400

    # 查询该用户的所有任务，按时间排序
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.trigger_time).all()

    return jsonify({
        "code": 200,
        "data": [t.to_dict() for t in tasks]
    })


# --- 添加任务 ---
@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    user_id = data.get('user_id')
    title = data.get('title')
    time = data.get('time')
    action_type = data.get('type')  # APP / LINK / SCRIPT
    target = data.get('target')  # 包名 / URL / 脚本名

    if not all([user_id, title, time, action_type, target]):
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    new_task = Task(
        user_id=user_id,
        title=title,
        # 👇 新增：接收备注和循环开关
        description=data.get('description', ''),
        is_loop=data.get('is_loop', False),

        trigger_time=time,
        action_type=action_type,
        target_value=target
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"code": 200, "msg": "任务创建成功", "data": new_task.to_dict()})


# --- 删除任务 ---
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    # 根据主键 ID 查找任务
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"code": 404, "msg": "任务不存在"}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 更新任务 (修改内容 或 切换开关) ---
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"code": 404, "msg": "任务不存在"}), 404

    data = request.json

    # 逐个检查字段，如果有传值就更新
    if 'title' in data: task.title = data['title']
    if 'time' in data: task.trigger_time = data['time']
    if 'type' in data: task.action_type = data['type']
    if 'target' in data: task.target_value = data['target']

    # 👇 新增：更新备注和循环
    if 'description' in data: task.description = data['description']
    if 'is_loop' in data: task.is_loop = bool(data['is_loop'])

    # 特殊处理布尔值：更新任务开启/关闭状态
    if 'active' in data:
        task.is_active = bool(data['active'])

    try:
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新成功", "data": task.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500

# --- 修改密码 (个人中心用) ---
@app.route('/api/user/password', methods=['POST'])
def update_password():
    data = request.json
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not all([user_id, old_password, new_password]):
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    # 验证旧密码是否正确
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({"code": 400, "msg": "旧密码错误"}), 400

    # 更新新密码
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"code": 200, "msg": "密码修改成功"})


# --- 上报执行日志 (App端执行时调用) ---
@app.route('/api/logs', methods=['POST'])
def add_log():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "参数错误"}), 400

    new_log = TaskLog(
        user_id=user_id,
        task_title=data.get('title'),
        task_type=data.get('type'),
        status=data.get('status', 'SUCCESS'),
        # 👇 新增：接收脚本运行结果
        result=data.get('result', '')
    )

    db.session.add(new_log)
    db.session.commit()

    return jsonify({"code": 200, "msg": "日志记录成功"})


# --- 获取执行日志 (历史页调用) ---
@app.route('/api/logs', methods=['GET'])
def get_logs():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少用户ID"}), 400

    # 按时间倒序排列 (最新的在最前面)
    logs = TaskLog.query.filter_by(user_id=user_id).order_by(TaskLog.executed_at.desc()).all()

    return jsonify({
        "code": 200,
        "data": [log.to_dict() for log in logs]
    })


@app.route('/api/chat', methods=['POST'])
def chat_ai():
    data = request.json
    user_message = data.get('message')
    history = data.get('history', [])  # 暂时没用上，后续可做上下文

    if not user_message:
        return jsonify({"code": 400, "msg": "说点什么吧"}), 400

    try:
        # 注意：如果你用的是 gemma:2b 或其他模型，请在这里修改 'model'
        ollama_payload = {
            "model": "gemma3:4b",
            "prompt": user_message,
            "stream": False
        }

        # 这里的 localhost 指向你电脑的 Ollama 服务
        response = requests.post("http://localhost:11434/api/generate", json=ollama_payload)

        if response.status_code == 200:
            ai_text = response.json().get('response', '')
            return jsonify({"code": 200, "data": ai_text})
        else:
            return jsonify({"code": 500, "msg": "AI 脑子短路了"}), 500

    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"code": 500, "msg": "无法连接本地模型，请检查 Ollama 是否运行"}), 500



import os
import time
from werkzeug.utils import secure_filename

# 配置上传文件夹 (放在 static 下方便直接访问)
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/upload_avatar', methods=['POST'])
def upload_avatar():
    user_id = request.form.get('user_id')
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"code": 400, "msg": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # 获取文件后缀 (比如 .jpg)
        ext = os.path.splitext(file.filename)[1]

        # 🔥 生成新文件名：使用 UUID (看起来像 550e8400-e29b....jpg)
        new_filename = f"{uuid.uuid4().hex}{ext}"

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(save_path)

        file_url = f"/static/uploads/{new_filename}"

        # 更新数据库
        try:
            user = User.query.get(user_id)
            if user:
                user.avatar = file_url
                db.session.commit()

                # 返回完整的用户信息以便前端更新缓存
                return jsonify({
                    "code": 200,
                    "msg": "上传成功",
                    "data": {
                        "avatar": file_url
                    }
                })
            else:
                return jsonify({"code": 404, "msg": "User not found"}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({"code": 500, "msg": str(e)}), 500

    return jsonify({"code": 400, "msg": "Type not allowed"}), 400



@app.route('/api/square/history', methods=['GET'])
def get_square_history():
    # 获取最近 50 条消息，按时间倒序查，然后翻转为正序
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(50).all()
    return jsonify({
        "code": 200,
        "data": [m.to_dict() for m in messages][::-1]  # 翻转列表，旧的在上面
    })


@app.route('/api/chat/messages', methods=['DELETE'])
def delete_chat_messages():
    data = request.json
    user_id = data.get('user_id')
    message_ids = data.get('message_ids')  # 前端传这就必须是数组: [12, 13, 15]

    if not user_id or not message_ids:
        return jsonify({"code": 400, "msg": "参数错误"}), 400

    try:
        # 批量删除：只能删除属于该用户(user_id)的消息
        # synchronize_session=False 用于提高批量删除性能
        deleted_count = ChatMessage.query.filter(
            ChatMessage.id.in_(message_ids),
            ChatMessage.user_id == user_id
        ).delete(synchronize_session=False)

        db.session.commit()

        if deleted_count == 0:
            return jsonify({"code": 400, "msg": "没有权限或消息不存在"}), 400

        return jsonify({"code": 200, "msg": f"成功删除 {deleted_count} 条消息"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)