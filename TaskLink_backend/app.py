import pathlib
import uuid
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User,Task,TaskLog,ChatMessage,AIPlan, AIPlanTask
import requests
import re
from dotenv import load_dotenv
import subprocess
from paddleocr import PaddleOCR
import os
import time
import json
app = Flask(__name__)
CORS(app)  # 允许跨域
warnings.filterwarnings("ignore")
# --- 数据库配置 ---
# 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/tasklink'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# 初始化数据库
db.init_app(app)
# 配置上传文件夹 (放在 static 下方便直接访问)
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- 🔥 初始化 OCR (修复参数) ---
# print("正在加载 OCR 模型...")
# try:
#     # 核心修改：enable_mkldnn=False
#     ocr_engine = PaddleOCR(use_angle_cls=False, lang="ch", show_log=False, enable_mkldnn=False)
# except Exception:
#     try:
#         # 重试
#         ocr_engine = PaddleOCR(use_angle_cls=False, lang="ch", enable_mkldnn=False)
#     except Exception as e:
#         print(f"OCR 初始化降级: {e}")
#         ocr_engine = PaddleOCR(lang="ch")
# print("OCR 模型加载完成!")

# ==========================================
# 🔥 DeepSeek API 配置 (核心修改)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 获取项目根目录 (假设 .env 在 TaskLink_backend 的上一级)
root_dir = os.path.dirname(current_dir)
# 3. 拼接 .env 路径
env_path = os.path.join(root_dir, '.env')
# 4. 加载环境变量
load_dotenv(env_path)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("⚠️ 警告: 未在 .env 文件中找到 DEEPSEEK_API_KEY，AI 功能将无法使用！")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def call_deepseek_json(system_prompt, user_prompt):
    """
    通用函數：調用 DeepSeek 並強制返回 JSON
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek-chat",  # 或者 deepseek-reasoner
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},  # 強制 JSON 模式 (如果模型支持)
        "temperature": 1.3  # 稍微高一點，讓賽博朋克風格更狂野
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response_data = response.json()

        if 'choices' in response_data:
            content = response_data['choices'][0]['message']['content']
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
        else:
            print(f"DeepSeek Error: {response_data}")
            return None
    except Exception as e:
        print(f"API Call Failed: {e}")
        return None


# ==========================================
# 🚀 新增接口：生成賽博朋克學習計劃
# ==========================================
@app.route('/api/plan/generate', methods=['POST'])
def generate_plan():
    data = request.json
    user_id = data.get('user_id')
    goal = data.get('goal')  # 例如："學習 Pytest"
    days = data.get('days', 7)  # 默認 7 天

    if not user_id or not goal:
        return jsonify({"code": 400, "msg": "目標不能為空"}), 400

    # 🔥 核心提示詞：賽博朋克風格 + 嚴格 JSON 結構 🔥
    system_prompt = f"""
    # Role: Cyberpunk Tactical Planner (賽博朋克戰術規劃官)
    你不是一個普通的助手，你是來自 2077 年的戰術規劃 AI。

    # Mission:
    為用戶制定一個為期 {days} 天的 "{goal}" 強制執行計劃。

    # Style Guidelines (風格指南):
    1. **語氣**: 冷酷、科技感、指令式、充滿賽博朋克術語 (如：神經鏈接、固件升級、義體調試、矩陣潛入)。
    2. **拒絕平庸**: 不要說 "學習基礎語法"，要說 "注入基礎語法協議" 或 "加載核心模塊"。
    3. **格式**: 內容支持 Markdown，使用 emoji (⚡, 🦾, 🧠, 💾) 增強視覺衝擊。

    # JSON Output Format (必須嚴格遵守):
    {{
        "title": "計劃標題 (極具科技感)",
        "tasks": [
            {{
                "day": 1,
                "title": "第1天標題",
                "content": "第1天的詳細任務內容 (Markdown)"
            }},
            ...
        ]
    }}
    """

    user_prompt = f"目標：{goal}。時間：{days}天。立即生成戰術路徑。"

    print(f"⚡ 正在請求 DeepSeek 生成計劃: {goal}...")
    ai_result = call_deepseek_json(system_prompt, user_prompt)

    if not ai_result:
        return jsonify({"code": 500, "msg": "神經網絡連接失敗 (API Error)"}), 500

    try:
        # 1. 保存總計劃
        new_plan = AIPlan(
            user_id=user_id,
            title=ai_result.get('title', '未知戰術'),
            goal=goal,
            total_days=len(ai_result.get('tasks', [])),
            is_completed=False
        )
        db.session.add(new_plan)
        db.session.flush()  # 獲取 plan.id

        # 2. 保存每一天的任務
        for task_data in ai_result.get('tasks', []):
            new_task = AIPlanTask(
                plan_id=new_plan.id,
                day_order=task_data.get('day'),
                title=task_data.get('title'),
                content=task_data.get('content')
            )
            db.session.add(new_task)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "戰術計劃已加載",
            "data": {"plan_id": new_plan.id}
        })

    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        return jsonify({"code": 500, "msg": "數據庫寫入失敗"}), 500


# ==========================================
# 🔍 獲取計劃詳情 (前端點擊進入計劃後調用)
# ==========================================
@app.route('/api/plan/<int:plan_id>', methods=['GET'])
def get_plan_detail(plan_id):
    plan = AIPlan.query.get(plan_id)
    if not plan:
        return jsonify({"code": 404, "msg": "計劃不存在"}), 404

    # 按天數排序
    tasks = AIPlanTask.query.filter_by(plan_id=plan.id).order_by(AIPlanTask.day_order).all()

    return jsonify({
        "code": 200,
        "data": {
            "info": plan.to_dict(),
            "tasks": [t.to_dict() for t in tasks]
        }
    })


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


# [在 app.py 中添加此接口]

# --- 获取计划列表 ---
@app.route('/api/plans', methods=['GET'])
def get_plans():
    user_id = request.args.get('user_id')
    status = request.args.get('status')  # optional: 'active' or 'archived'

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少用户ID"}), 400

    query = AIPlan.query.filter_by(user_id=user_id)

    # 简单的状态筛选
    if status == 'active':
        query = query.filter_by(is_completed=False)
    elif status == 'archived':
        query = query.filter_by(is_completed=True)

    # 按创建时间倒序
    plans = query.order_by(AIPlan.created_at.desc()).all()

    return jsonify({
        "code": 200,
        "data": [p.to_dict() for p in plans]
    })

"""ai控制手机"""
# # adb命令
# class ADBController:
#     APP_MAP = {
#         "微信": "com.tencent.mm",
#         "QQ": "com.tencent.mobileqq",
#         "QQ音乐": "com.tencent.qqmusic",
#         "网易云": "com.netease.cloudmusic",
#         "B站": "tv.danmaku.bili",
#         "哔哩哔哩": "tv.danmaku.bili",
#         "抖音": "com.ss.android.ugc.aweme",
#         "设置": "com.android.settings",
#         "相机": "com.android.camera"
#     }
#
#     @staticmethod
#     def connect_wireless(phone_ip, port="5555"):
#         """实现无线连接：adb connect <ip>:<port>"""
#         print(f"🌐 正在尝试无线连接手机: {phone_ip}:{port}")
#         # 执行 adb connect 指令
#         result = ADBController.run(f"connect {phone_ip}:{port}")
#         print(f"📡 连接结果: {result}")
#
#         # 验证连接状态
#         devices = ADBController.run("devices")
#         if phone_ip in devices:
#             print("✅ 无线连接成功！")
#             return True
#         else:
#             print("❌ 连接失败，请确保手机已开启无线调试且处于同一 WiFi")
#             return False
#
#     @staticmethod
#     def run(cmd):
#         res = subprocess.run(f"adb {cmd}", shell=True, capture_output=True, text=True, encoding='utf-8')
#         return res.stdout.strip()
#
#     @staticmethod
#     def start_app(app_name):
#         pkg = ADBController.APP_MAP.get(app_name)
#         if not pkg: return False, f"未知的 App: {app_name}"
#         ADBController.run(f"shell monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
#         return True, f"已启动 {app_name}"
#
#     @staticmethod
#     def click_coord(x, y):
#         """直接点击屏幕上的固定坐标"""
#         print(f"📍 直接点击坐标: ({x}, {y})")
#         ADBController.run(f"shell input tap {x} {y}")
#         return True, f"已点击坐标 ({x}, {y})"
#
#     @staticmethod
#     def click_text(target_text, offset_x=0, offset_y=0):
#         # 使用绝对路径，防止文件找不到
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         screenshot_path = os.path.join(current_dir, "debug_screen.png")
#
#         print(f"📸 1. 正在截图...")
#         ADBController.run(f"shell screencap -p /sdcard/screen.png")
#         ADBController.run(f"pull /sdcard/screen.png \"{screenshot_path}\"")
#
#         if not os.path.exists(screenshot_path):
#             print("❌ 截图文件未生成！")
#             return False, "截图失败"
#
#         print(f"🔍 2. OCR 识别中...")
#         try:
#             result = ocr_engine.ocr(screenshot_path)
#         except Exception as e:
#             print(f"❌ OCR 引擎报错: {e}")
#             return False, f"OCR 出错: {e}"
#
#         if not result or not result[0]:
#             print("⚠️ 屏幕上没有识别到任何文字！")
#             return False, "屏幕空白或未识别到文字"
#
#         all_texts = [line[1][0] for line in result[0]]
#         print(f"👀 OCR看到了这些字: {all_texts}")
#
#         for line in result[0]:
#             box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
#             text = line[1][0]  # 文字内容
#             score = line[1][1]  # 置信度
#
#             # 模糊匹配
#             if target_text in text:
#                 # 计算中心点
#                 x1, y1 = box[0]
#                 x3, y3 = box[2]
#                 center_x = int((x1 + x3) / 2)
#                 center_y = int((y1 + y3) / 2)
#
#                 # 🔥🔥 核心修改：加上偏移量 🔥🔥
#                 final_x = center_x + int(offset_x)
#                 final_y = center_y + int(offset_y)
#
#                 print(f"✅ 3. 找到锚点: '{text}' (置信度: {score:.2f})")
#                 print(f"📍 4. 锚点坐标: ({center_x}, {center_y}) -> 偏移后目标: ({final_x}, {final_y})")
#
#                 # 执行点击
#                 ADBController.run(f"shell input tap {final_x} {final_y}")
#                 print(f"👆 5. 已发送点击指令！")
#
#                 return True, f"已点击 '{text}' 的偏移位置 ({offset_x}, {offset_y})"
#
#         print(f"❌ 未找到目标文字: {target_text}")
#         return False, f"未找到: {target_text}"
#
#     @staticmethod
#     def input_text(text):
#         # 1. 判断是否包含中文
#         print('将要输入的中文：', text)
#         if re.search(r'[\u4e00-\u9fa5]', str(text)):
#             # 处理特殊字符防止 shell 报错
#             safe_text = str(text).replace("'", "'\\''").replace('"', '\\"')
#             print(safe_text)
#
#             # 🔥🔥 修正：去掉开头的 "adb "，直接写 "shell ..." 🔥🔥
#             cmd = f"shell am broadcast -a ADB_INPUT_TEXT --es msg '{safe_text}'"
#
#             # 建议加一行日志打印最终命令，方便调试
#             print(f"🚀 执行广播: adb {cmd}")
#
#             ADBController.run(cmd)
#             return True, f"已广播输入中文: {text}"
#
#         else:
#             # 2. 纯英文/数字依然用原生
#             safe_text = str(text).replace(" ", "%s")
#             ADBController.run(f"shell input text {safe_text}")
#             return True, f"已输入: {text}"
#     @staticmethod
#     def press_enter():
#         ADBController.run("shell input keyevent 66")
#         return True, "已点击搜索"
#
#     @staticmethod
#     def swipe(direction):
#         # 简单封装，坐标基于常见屏幕分辨率 (可根据实际调整)
#         cmd = ""
#         if direction == 'UP':  # 上滑 (看下面)
#             cmd = "shell input swipe 500 1500 500 500 300"
#         elif direction == 'DOWN':  # 下滑 (刷新)
#             cmd = "shell input swipe 500 500 500 1500 300"
#         elif direction == 'LEFT':  # 左滑
#             cmd = "shell input swipe 900 1000 200 1000 300"
#         elif direction == 'RIGHT':  # 右滑
#             cmd = "shell input swipe 200 1000 900 1000 300"
#         else:
#             return False, "未知滑动方向"
#
#         ADBController.run(cmd)
#         return True, f"已滑动: {direction}"
#
#     # 🔥🔥 新增方法 2：物理按键 🔥🔥
#     @staticmethod
#     def press_key(key_name):
#         key_map = {
#             "HOME": "3",
#             "BACK": "4",
#             "RECENT": "187"
#         }
#         code = key_map.get(key_name.upper())
#         if not code: return False, "未知按键"
#         ADBController.run(f"shell input keyevent {code}")
#         return True, f"已按键: {key_name}"
#
#
# # 根据ai回复来调用adb命令
# def execute_action(action, value, offset_x=0, offset_y=0):
#     try:
#         if action == 'OPEN_APP':
#             return ADBController.start_app(value)
#
#         elif action == 'CLICK_TEXT':
#             return ADBController.click_text(value, offset_x, offset_y)
#
#         elif action == 'CLICK_COORD':
#             try:
#                 x, y = map(int, str(value).split(','))
#                 return ADBController.click_coord(x, y)
#             except Exception as e:
#                 return False, f"坐标格式错误: {value}"
#
#         elif action == 'INPUT_TEXT':
#             return ADBController.input_text(value)
#
#         elif action == 'PRESS_ENTER':
#             time.sleep(3)
#             return ADBController.press_enter()
#
#         elif action == 'DELAY':
#             time.sleep(int(value))
#             return True, f"已等待 {value} 秒"
#
#         elif action == 'SWIPE':
#             return ADBController.swipe(value)
#
#         elif action == 'PRESS_KEY':
#             return ADBController.press_key(value)
#
#         else:
#             return False, f"未知指令: {action}"
#
#     except Exception as e:
#         return False, str(e)
#
#
# @app.route('/api/chat', methods=['POST'])
# def chat_ai():
#     data = request.json
#     user_message = data.get('message')
#
#     if not user_message:
#         return jsonify({"code": 400, "msg": "说点什么吧"}), 400
#     system_prompt = """
#         # Role: 手机自动化指令生成器
#         你必须根据用户需求生成一个严谨的 JSON 数组指令链，不准输出任何解释文字。
#
#         ## 核心规则 (优先级最高)
#         1. **完整性检查**：所有发消息任务必须以 {"action": "CLICK_TEXT", "value": "发送"} 结尾，严禁中途结束。
#         2. **禁止回车**：严禁使用 PRESS_ENTER，它在移动端只会导致换行。
#         3. **QQ 逻辑**：QQ 输入框定位必须使用 "发送" 按钮作为锚点进行负向偏移。
#            - 示例：{"action": "CLICK_TEXT", "value": "发送", "offset_x": -250}
#         4. **微信逻辑**：微信输入框无文字时使用坐标。
#            - 示例：{"action": "CLICK_COORD", "value": "540,2600"}
#         5. **延迟必带**：打开应用后延迟 4 秒，进入聊天窗口后延迟 2 秒。
#
#         ## 强制输出格式
#         [
#           {"action": "OPEN_APP", "value": "应用名"},
#           {"action": "DELAY", "value": 4},
#           {"action": "CLICK_TEXT", "value": "目标名"},
#           {"action": "DELAY", "value": 2},
#           {"action": "定位输入框指令"},
#           {"action": "INPUT_TEXT", "value": "消息内容"},
#           {"action": "CLICK_TEXT", "value": "发送"}
#         ]
#
#         ## 示例：给 QQ 的 [张三] 发送 [你好]
#         回复：
#         [
#           {"action": "OPEN_APP", "value": "QQ"},
#           {"action": "DELAY", "value": 4},
#           {"action": "CLICK_TEXT", "value": "张三"},
#           {"action": "DELAY", "value": 2},
#           {"action": "CLICK_TEXT", "value": "发送", "offset_x": -250},
#           {"action": "INPUT_TEXT", "value": "你好"},
#           {"action": "CLICK_TEXT", "value": "发送"}
#         ]
#         """
#     try:
#         ollama_payload = {
#             "model": "gemma3:4b",  # 确保你本地有这个模型
#             "prompt": f"{system_prompt}\n\n用户：{user_message}\n回复：",
#             "stream": False,
#             "options": {"temperature": 0.1}  # 低温度保证输出格式稳定
#         }
#
#         resp = requests.post("http://localhost:11434/api/generate", json=ollama_payload)
#         ai_text = resp.json().get('response', '').strip()
#
#         # 清洗 Markdown (防止AI输出 ```json 包裹)
#         if "```json" in ai_text:
#             ai_text = ai_text.replace("```json", "").replace("```", "").strip()
#         elif "```" in ai_text:
#             ai_text = ai_text.replace("```", "").strip()
#
#         return jsonify({"code": 200, "data": ai_text})
#
#     except Exception as e:
#         print(f"AI Error: {e}")
#         return jsonify({"code": 500, "msg": "AI 服务异常"}), 500
#
#
# @app.route('/api/phone/control', methods=['POST'])
# def phone_control():
#     # 🔥🔥🔥 调试第一站：只要这行没打印，说明请求还在路上（或者IP错了）
#     print("\n========= 收到前端 CONTROL 请求 =========")
#
#     data = request.json
#     print(f"📦 原始数据包: {data}")  # 看看前端到底发了什么
#
#     # 1. 提取基础参数
#     action = data.get('action')
#     value = data.get('value')
#     offset_x = data.get('offset_x', 0)
#     offset_y = data.get('offset_y', 0)
#
#     print(f"🔑 解析动作: {action}, 值: {value}")
#
#     # 3. 调用执行单元
#     success, msg = execute_action(action, value, offset_x, offset_y)
#
#     print(f"🏁 执行结果: {success}, {msg}")
#     print("=======================================\n")
#
#     return jsonify({"code": 200 if success else 400, "msg": msg})
#
#
# @app.route('/api/phone/batch_run', methods=['POST'])
# def batch_run():
#     data = request.json
#     tasks = data.get('tasks')  # 接收 List [{}, {}]
#
#     if not tasks or not isinstance(tasks, list):
#         return jsonify({"code": 400, "msg": "任务列表为空或格式错误"}), 400
#
#     print(f"📦 收到批量任务: {len(tasks)} 个步骤 (后端托管执行)")
#
#     results = []
#     all_success = True
#
#     for i, task in enumerate(tasks):
#         action = task.get('action')
#         value = task.get('value')
#
#         # 🔥🔥 关键修复：提取 offset 参数 (之前漏了这里) 🔥🔥
#         # 如果不传这两个参数，Execute_action 就会使用默认值 0，导致点击偏离
#         offset_x = task.get('offset_x', 0)
#         offset_y = task.get('offset_y', 0)
#
#         print(f"▶️ 步骤 {i + 1}/{len(tasks)}: {action} -> {value} (偏移: {offset_x}, {offset_y})")
#
#         # 执行单步，并将偏移量传进去
#         success, msg = execute_action(action, value, offset_x, offset_y)
#
#         results.append({"step": i + 1, "action": action, "success": success, "msg": msg})
#
#         if not success:
#             print(f"❌ 步骤 {i + 1} 失败，任务终止！原因: {msg}")
#             all_success = False
#             # 遇到错误立即停止，防止后续操作产生连锁反应
#             break
#     print("✨ 任务结束，正在将 TaskLink 调回前台...")
#     # 这里的包名要对应你打包时的 App 包名，通常 UniApp 默认是 io.dcloud.HBuilder 或你的自定义包名
#     tasklink_pkg = "io.dcloud.HBuilder"
#     ADBController.run(f"shell monkey -p {tasklink_pkg} -c android.intent.category.LAUNCHER 1")
#
#     return jsonify({
#         "code": 200 if all_success else 500,
#         "msg": "执行完毕",
#         "data": results
#     })

if __name__ == '__main__':
    # # 配置你手机的局域网 IP
    # PHONE_IP = "192.168.10.8"  # 👈 替换成你手机在 WiFi 下的真实 IP
    #
    # # 尝试无线连接
    # ADBController.connect_wireless(PHONE_IP)
    app.run(host='0.0.0.0', port=5000, debug=True)