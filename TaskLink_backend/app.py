import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User,Task,TaskLog,ChatMessage
import requests
import re
import subprocess
from paddleocr import PaddleOCR

app = Flask(__name__)
CORS(app)  # 允许跨域

# --- 数据库配置 ---
# 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/tasklink'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# 初始化数据库
db.init_app(app)

ocr_engine = PaddleOCR(use_textline_orientation=True, lang="ch")
print("OCR 模型加载完成!")


# --- 🛠️ ADB 控制器 (核心黑科技) ---
class ADBController:
    # 常用 App 包名映射字典
    APP_MAP = {
        "微信": "com.tencent.mm",
        "QQ": "com.tencent.mobileqq",
        "QQ音乐": "com.tencent.qqmusic",
        "网易云": "com.netease.cloudmusic",
        "B站": "tv.danmaku.bili",
        "哔哩哔哩": "tv.danmaku.bili",
        "抖音": "com.ss.android.ugc.aweme",
        "设置": "com.android.settings",
        "相机": "com.android.camera"
    }

    @staticmethod
    def run(cmd):
        """执行 ADB 命令"""
        # 注意：这里假设只有一台手机连接。如果有多台，需加 -s device_id
        res = subprocess.run(f"adb {cmd}", shell=True, capture_output=True, text=True, encoding='utf-8')
        return res.stdout.strip()

    @staticmethod
    def start_app(app_name):
        """启动 App"""
        pkg = ADBController.APP_MAP.get(app_name)
        if not pkg:
            return False, f"未知的 App: {app_name}，请先在后端字典配置包名"

        # 使用 monkey 命令启动 App (比 am start 兼容性更好)
        ADBController.run(f"shell monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
        return True, f"已启动 {app_name}"

    @staticmethod
    def click_text(target_text):
        """核心：OCR 识图点击"""
        screenshot_path = "screen.png"

        # 1. 截图并拉取到电脑
        ADBController.run("shell screencap -p /sdcard/screen.png")
        ADBController.run(f"pull /sdcard/screen.png {screenshot_path}")

        if not os.path.exists(screenshot_path):
            return False, "截图失败，请检查 ADB 连接"

        # 2. OCR 识别
        result = ocr_engine.ocr(screenshot_path, cls=True)

        # 3. 查找坐标
        # result 结构: [[[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)], ...]
        if not result or not result[0]:
            return False, "屏幕上没有识别到文字"

        for line in result[0]:
            box = line[0]
            text = line[1][0]

            # 模糊匹配：只要包含了目标文字 (比如 "发现" 在 "发现(1)")
            if target_text in text:
                # 计算中心点坐标
                center_x = int((box[0][0] + box[2][0]) / 2)
                center_y = int((box[0][1] + box[2][1]) / 2)

                print(f"找到 '{text}' -> 点击坐标 ({center_x}, {center_y})")

                # 4. 执行点击
                ADBController.run(f"shell input tap {center_x} {center_y}")
                return True, f"已点击: {text}"

        return False, f"屏幕上未找到文字: {target_text}"


# --- 🧠 AI 聊天接口 (更新 Prompt) ---
# TaskLink_backend/app.py

@app.route('/api/chat', methods=['POST'])
def chat_ai():
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"code": 400, "msg": "说点什么吧"}), 400

    # 🔥🔥 核心修改：提示词升级，要求返回数组 [{}, {}] 🔥🔥
    system_prompt = """
    你是一个手机自动化助手。请分析用户指令，返回标准 JSON 数组格式。
    支持的操作(action)：
    1. OPEN_APP: 打开应用。value 填应用名称。
    2. CLICK_TEXT: 点击屏幕文字。value 填要点击的文字。
    3. DELAY: 等待。value 填秒数(整数)。

    规则：
    - 如果涉及多步操作，请返回包含多个对象的数组。
    - 在打开应用后，通常需要等待 3-5 秒加载，请务必插入 DELAY 指令。

    示例：
    - 用户："打开微信并点一下发现"
    - 回复：[
        {"action": "OPEN_APP", "value": "微信"}, 
        {"action": "DELAY", "value": 5}, 
        {"action": "CLICK_TEXT", "value": "发现"}
      ]

    如果只是闲聊，请直接返回文本，不要带JSON。
    """

    try:
        ollama_payload = {
            "model": "gemma3:4b",
            "prompt": f"{system_prompt}\n\n用户：{user_message}\n回复：",
            "stream": False,
            "options": {"temperature": 0.1}
        }

        resp = requests.post("http://localhost:11434/api/generate", json=ollama_payload)
        ai_text = resp.json().get('response', '').strip()

        # 清洗 Markdown
        if "```json" in ai_text:
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()

        return jsonify({"code": 200, "data": ai_text})

    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"code": 500, "msg": "AI 服务异常"}), 500


@app.route('/api/phone/control', methods=['POST'])
def phone_control():
    data = request.json
    action = data.get('action')
    value = data.get('value')

    print(f"收到控制指令: {action} -> {value}")

    try:
        if action == 'OPEN_APP':
            success, msg = ADBController.start_app(value)
            return jsonify({"code": 200 if success else 400, "msg": msg})

        elif action == 'CLICK_TEXT':
            success, msg = ADBController.click_text(value)
            return jsonify({"code": 200 if success else 400, "msg": msg})

        return jsonify({"code": 400, "msg": "未知指令"})

    except Exception as e:
        print(f"ADB Error: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500
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




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)