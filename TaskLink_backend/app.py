import pathlib
import uuid
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Task, TaskLog, ChatMessage, AIPlan, AIPlanTask, UserVocabStats, InvitationCode, Vocabulary, \
    UserWordProgress, TrainingSession, TrainingDetail, \
    PetSpecies, PetLevelStyle, UserPet, UserPetCustomization, UserPetPosition, \
    PetFeedingLog, PetAIProfile, UserPetAIProfile
import requests
import re
from dotenv import load_dotenv
import os
from sqlalchemy import or_
import time
import json
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import func
import jwt
from flask import g

app = Flask(__name__)
CORS(app)  # 允许跨域
warnings.filterwarnings("ignore")
# 数据库配置
# 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:ymq20050704@localhost:3306/tasklink'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# 初始化数据库
db.init_app(app)
# 配置上传文件夹 (放在 static 下方便直接访问)
AVATAR_FOLDER = 'static/uploads'  # 用来存头像
CHAT_FOLDER = 'static/chat_images'  # 用来存聊天图片/表情包

# 2. 自动创建文件夹 (如果不存在)
for folder in [AVATAR_FOLDER, CHAT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 3. 写入 Flask 配置
app.config['UPLOAD_FOLDER'] = AVATAR_FOLDER  # 保持这个不变，兼容原来的 upload_avatar 接口
app.config['CHAT_FOLDER'] = CHAT_FOLDER  # 新增这个配置给聊天用
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制最大上传 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

load_dotenv(r'C:\Users\Administrator\Desktop\TaskLink\.env')
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
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 1.3
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


# ==================== Pet helpers ====================

def pet_need_exp(level: int) -> int:
    """
    经验阈值：每级需要的经验。
    规则尽量简单可调：Lv1->20, Lv2->30, Lv3->40...
    """
    try:
        lv = int(level)
    except Exception:
        lv = 1
    if lv < 1:
        lv = 1
    return 20 + (lv - 1) * 10


def get_or_create_user_pet(user_id: int) -> UserPet:
    """
    获取用户当前宠物，如果没有则：
    - 确保至少存在一个默认品种（例如 slime）
    - 为用户创建一只默认 Lv1 宠物
    """
    pet = UserPet.query.filter_by(user_id=user_id).first()
    if pet:
        return pet

    # 找一个默认品种（优先 key='slime'，否则第一个，没有则创建一个）
    species = PetSpecies.query.filter_by(key='slime').first()
    if not species:
        species = PetSpecies.query.first()
    if not species:
        species = PetSpecies(
            key='slime',
            name='任务史莱姆',
            description='一只软乎乎的史莱姆小助手'
        )
        db.session.add(species)
        db.session.flush()

    pet = UserPet(
        user_id=user_id,
        species_id=species.id,
        nickname='小伙伴',
        level=1,
        exp=0,
        feed_points=0,
        total_feeds=0,
        pos_x=50,
        pos_y=50
    )
    db.session.add(pet)
    db.session.commit()
    return pet


def get_level_style(species_id: int, level: int):
    try:
        sid = int(species_id)
        lv = int(level)
    except Exception:
        return None
    return PetLevelStyle.query.filter_by(species_id=sid, level=lv).first()


# 可爱食物（前端可直接展示/飘字/动画，不需要额外资源）
PET_FOODS = [
    {"id": "strawberry", "name": "草莓", "icon": "🍓", "exp": 1},
    {"id": "dango", "name": "团子", "icon": "🍡", "exp": 1},
    {"id": "cookie", "name": "曲奇", "icon": "🍪", "exp": 1},
    {"id": "cake", "name": "蛋糕", "icon": "🍰", "exp": 1},
    {"id": "pudding", "name": "布丁", "icon": "🍮", "exp": 1},
    {"id": "icecream", "name": "冰淇淋", "icon": "🍦", "exp": 1},
]


@app.route('/api/plan/generate', methods=['POST'])
def generate_plan():
    data = request.json
    user_id = data.get('user_id')
    goal = data.get('goal')
    days = int(data.get('days', 7))
    expectation = data.get('expectation', '无')

    print(f"⚡ [收到请求] 用户:{user_id} 目标:{goal} 天数:{days}")

    if not user_id or not goal:
        return jsonify({"code": 400, "msg": "目标不能为空"}), 400

    if days <= 7:
        # 短周期：每天一个任务，精确执行
        task_count = days
        structure_prompt = f"必须严格输出 {task_count} 个任务节点，分别对应 Day 1 到 Day {task_count}。"
        time_unit = "Day"
    else:
        # 长周期：强制合并为 4-6 个阶段
        if days <= 15:
            task_count = 4
        elif days <= 30:
            task_count = 5
        else:
            task_count = 6

        avg_days = days // task_count
        structure_prompt = f"""
        这是一个长周期计划 ({days}天)。
        必须将计划压缩为 {task_count} 个【核心战术阶段】(Phases)。
        每个阶段跨度约 {avg_days} 天。
        JSON中的 'day' 字段请填序号 (1, 2, 3...)。
        JSON中的 'title' 必须包含时间范围 (如 "阶段一：基础架构 (Day 1-{avg_days})")。
        """
        time_unit = "Phase"

    system_prompt = """
    # Role: 你的私人AI规划顾问

    ## Profile
    - language: 中文
    - description: 一个为用户提供专属、高效、精准目标规划与执行方案的人工智能助手。
    - personality: 专业、耐心、逻辑清晰、务实进取。
    - expertise: 目标拆解、学习规划、技能提升、习惯养成、效率优化。

    ## Skills
    1. **目标规划与拆解**
       - **需求理解**: 深入理解用户的目标、背景和期望。
       - **任务拆分**: 将大目标拆解为可执行的小任务。
       - **路径设计**: 规划最高效的学习/执行路径。

    2. **内容生成与格式化**
       - **结构化输出**: 严格按照 JSON 格式生成计划。
       - **实用为主**: 内容必须100%可执行，不过度装饰。
       - **因材施教**: 根据用户设定的周期和期望，灵活调整计划颗粒度。

    ## Rules
    1. **内容核心原则**：
       - **绝对干货**: 所有内容必须可执行、无废话。
       - **领域相关**: 方案必须紧密贴合用户目标领域。
       - **循序渐进**: 任务安排需符合客观学习/执行规律。

    2. **输出行为准则**：
       - **格式严格**: 必须完全按照预设的 JSON 格式输出。
       - **标题简洁**: 标题清晰表达核心目标，不过度花哨。
       - **内容清单**: 使用清晰的步骤/清单格式。

    ## Workflows
    - 目标: 生成一份高度结构化、可执行的个性化方案。
    - 步骤 1: **理解需求** - 分析用户目标、时间周期、期望程度。
    - 步骤 2: **拆解规划** - 将目标拆解为阶段性任务。
    - 步骤 3: **内容填充** - 为每个阶段补充具体执行要点。

    ## Output JSON Format (必须严格遵循)
    ```json
    {
      "title": "计划标题，如：Python七天入门实战",
      "tasks": [
        {
          "title": "任务标题，如：Day 1 - 环境搭建与基础语法",
          "content": "详细的任务内容，包含具体步骤和要点，使用Markdown格式"
        }
      ]
    }
    ```
    - title: 计划的总标题，简洁有力
    - tasks: 任务数组
    - 每个task包含 title (任务标题) 和 content (详细执行内容)
    """

    user_prompt = f"目标：{goal}。预期：{expectation}。总时长：{days}天。请生成 {task_count} 个节点的战术路径。"

    print(f"🧠 [DeepSeek] 贾维斯正在规划 ({time_unit}模式, 节点数:{task_count})...")

    ai_result = call_deepseek_json(system_prompt, user_prompt)

    if not ai_result:
        print("❌ [Error] AI 返回为空")
        return jsonify({"code": 500, "msg": "神经网络连接中断"}), 500

    try:
        new_plan = AIPlan(
            user_id=user_id,
            title=ai_result.get('title', '未知战术'),
            goal=goal,
            total_days=days,
            is_completed=False
        )
        db.session.add(new_plan)
        db.session.flush()

        tasks_data = ai_result.get('tasks', [])
        # 双重保险：如果 AI 还是生成了太多，强制截断
        if len(tasks_data) > 10 and days > 10:
            tasks_data = tasks_data[:8]  # 强制只取前8个

        for idx, task_data in enumerate(tasks_data):
            new_task = AIPlanTask(
                plan_id=new_plan.id,
                day_order=idx + 1,
                title=task_data.get('title'),
                content=task_data.get('content')
            )
            db.session.add(new_task)

        db.session.commit()
        print(f"✅ [Success] 计划保存成功 (节点数: {len(tasks_data)})")
        return jsonify({"code": 200, "msg": "战术已装载", "data": {"plan_id": new_plan.id}})

    except Exception as e:
        db.session.rollback()
        print(f"❌ [DB Error] {e}")
        return jsonify({"code": 500, "msg": "数据库写入失败"}), 500


@app.route('/api/plan/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    plan = AIPlan.query.get(plan_id)
    if not plan:
        return jsonify({"code": 404, "msg": "计划不存在"}), 404

    try:
        # 级联删除在数据库层面配置了 (cascade="all, delete-orphan")
        # 这里直接删 plan 即可
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"code": 200, "msg": "战术协议已销毁"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@app.route('/api/plan/detail', methods=['GET'])
def get_plan_detail():
    plan_id = request.args.get('plan_id')  # 获取 ?plan_id=1

    print(f"🔍 [查询详情] Plan ID: {plan_id}")

    if not plan_id:
        return jsonify({"code": 400, "msg": "缺少参数"}), 400

    plan = AIPlan.query.get(plan_id)
    if not plan:
        print(f"❌ [404] 找不到计划 {plan_id}")
        return jsonify({"code": 404, "msg": "计划不存在"}), 404

    tasks = AIPlanTask.query.filter_by(plan_id=plan.id).order_by(AIPlanTask.day_order).all()

    return jsonify({
        "code": 200,
        "data": {
            "info": plan.to_dict(),
            "tasks": [t.to_dict() for t in tasks]
        }
    })


@app.before_request
def check_user_status():
    allowed_endpoints = ['login', 'register', 'static', 'upload_avatar', 'upload_image']
    if request.endpoint in allowed_endpoints or request.endpoint is None:
        return None

    current_user_id = None

    if request.method == 'GET':
        current_user_id = request.args.get('operator_id') or request.args.get('user_id')

    elif request.method == 'POST':
        if request.is_json:
            data = request.get_json(silent=True)
            if data:

                current_user_id = data.get('operator_id')

                if not current_user_id:
                    current_user_id = data.get('user_id')

    # 3. 检查操作者状态
    if current_user_id:
        user = User.query.get(current_user_id)
        # 如果操作者被封，才拦截
        if user and getattr(user, 'status', 1) == 0:
            return jsonify({
                "code": 403,
                "msg": "您的账号已被禁用，无法执行此操作"
            }), 403

    return None


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    invitation_code = data.get('invitation_code', '').strip()  # 允许为空

    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名或密码不能为空"}), 400

    # --- 邀请码校验（可选）---
    # 任何6位数字的邀请码都通过
    code_record = None
    if invitation_code:
        if re.match(r'^\w{6}$', invitation_code):
            # 查找是否存在该邀请码记录，如果存在则标记为已使用
            code_record = InvitationCode.query.filter_by(code=invitation_code, is_used=False).first()
            if code_record:
                code_record.is_used = True  # 标记为已使用
                db.session.add(code_record)
        else:
            return jsonify({"code": 400, "msg": "邀请码必须是6位数字"}), 400

    # --- 2. 用户名严格校验 ---
    username_pattern = r'^[a-zA-Z][a-zA-Z0-9_]{5,19}$'
    if not re.match(username_pattern, username):
        return jsonify({
            "code": 400,
            "msg": "用户名格式错误：需6-20位，以字母开头，仅含字母/数字/下划线"
        }), 400

    # --- 3. 密码强度强校验 ---
    if len(password) < 8 or len(password) > 20:
        return jsonify({"code": 400, "msg": "密码长度需在 8-20 位之间"}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({"code": 400, "msg": "密码必须包含小写字母"}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({"code": 400, "msg": "密码必须包含大写字母"}), 400
    if not re.search(r'[0-9]', password):
        return jsonify({"code": 400, "msg": "密码必须包含数字"}), 400

    # --- 4. 检查用户名是否已存在 ---
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 400, "msg": "该用户名已被注册"}), 400

    try:
        # --- 5. 密码加密 & 入库流程 ---
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)

        # 关键步骤：先 add 但不 commit
        db.session.add(new_user)

        # flush() 会执行 SQL 插入语句，生成 new_user.id，但事务还没提交
        # 这样我们才能拿到 ID 去关联邀请码
        db.session.flush()

        # 只有填写了邀请码才绑定
        if code_record:
            code_record.is_used = True
            code_record.used_at = datetime.now()
            code_record.used_by_user_id = new_user.id  # 记录是谁用了这个码

        # 最后统一提交所有更改
        db.session.commit()

        # 注册成功后自动创建宠物
        try:
            get_or_create_user_pet(new_user.id)
            print(f"🐾 [Pet] 为用户 {new_user.id} 创建了默认宠物")
        except Exception as pet_err:
            print(f"⚠️ [Pet] 创建宠物失败: {pet_err}")

        print(username, "注册成功")
        return jsonify({"code": 200, "msg": "注册成功", "data": new_user.to_dict()})

    except Exception as e:
        db.session.rollback()  # 如果出错，回滚所有操作
        print(f"注册失败: {e}")  # 打印错误日志方便调试
        return jsonify({"code": 500, "msg": "服务器内部错误，注册失败"}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        if getattr(user, 'status', 1) == 0:
            return jsonify({"code": 403, "msg": "该账号已被管理员禁用"})

        expiration = datetime.utcnow() + timedelta(days=30)
        token = jwt.encode({
            'user_id': user.id,
            'exp': expiration
        }, app.config['SECRET_KEY'], algorithm="HS256")

        user.current_token = token
        db.session.commit()

        print(f"{user.username} 登录成功，Token 已更新入库")

        return jsonify({
            "code": 200,
            "msg": "登录成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "role": getattr(user, 'role', 0),
                "avatar": user.avatar,
                "token": token  # 返回给前端
            }
        })
    else:
        return jsonify({"code": 401, "msg": "用户名或密码错误"})


@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    operator_id = request.args.get('operator_id')

    admin = User.query.get(operator_id)
    if not admin or getattr(admin, 'role', 0) != 1:
        return jsonify({"code": 403, "msg": "无权访问"})

    users = User.query.all()
    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "username": u.username,
            "role": getattr(u, 'role', 0),
            "status": getattr(u, 'status', 1),  # 默认 1
            "avatar": u.avatar,
            "created_at": u.created_at.strftime('%Y-%m-%d') if u.created_at else ''
        })

    return jsonify({"code": 200, "data": user_list})


@app.route('/api/admin/user/status', methods=['POST'])
def update_user_status():
    data = request.json
    operator_id = data.get('operator_id')
    target_user_id = data.get('user_id')
    new_status = data.get('status')

    admin = User.query.get(operator_id)
    if not admin or getattr(admin, 'role', 0) != 1:
        return jsonify({"code": 403, "msg": "权限不足"})

    if str(operator_id) == str(target_user_id):
        return jsonify({"code": 400, "msg": "不能禁用自己的管理员账号"})

    user = User.query.get(target_user_id)
    if user:
        print(f"🔥 [Flask调试] 正在修改用户 {target_user_id} 状态为: {new_status}")

        user.status = int(new_status)
        db.session.commit()

        msg = "账号已启用"

        if int(new_status) == 0:
            msg = "账号已禁用，并强制下线"
            print(f"🚀 [Flask调试] 准备向 Node.js 发送踢人指令...")
            try:
                # 假设 Node.js 运行在本地 3000 端口
                resp = requests.post(
                    'http://127.0.0.1:3000/kick',
                    json={'user_id': target_user_id},
                    timeout=2
                )
                print(f"✅ [Flask调试] Node.js 响应: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"❌ [Flask调试] 请求 Node.js 失败! 原因: {e}")

        return jsonify({"code": 200, "msg": msg})

    return jsonify({"code": 404, "msg": "用户不存在"})


# 获取任务列表
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user_id = g.user_id

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少用户ID"}), 400

    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.trigger_time).all()

    return jsonify({
        "code": 200,
        "data": [t.to_dict() for t in tasks]
    })


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


# 更新任务
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"code": 404, "msg": "任务不存在"}), 404

    data = request.json

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


# 修改密码 (个人中心用)
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


# 上报执行日志
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
        result=data.get('result', '')
    )

    db.session.add(new_log)
    db.session.commit()

    return jsonify({"code": 200, "msg": "日志记录成功"})


# 获取执行日志
@app.route('/api/logs', methods=['GET'])
def get_logs():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少用户ID"}), 400

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
        ext = os.path.splitext(file.filename)[1]

        new_filename = f"{uuid.uuid4().hex}{ext}"

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(save_path)

        file_url = f"/static/uploads/{new_filename}"

        try:
            user = User.query.get(user_id)
            if user:
                user.avatar = file_url
                db.session.commit()
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

    user_id = request.args.get('user_id')
    print(user_id)
    if str(user_id) in ['11', '12']:
        return jsonify({
            "code": 403,
            "msg": "app需要更新",
            "data": []
        })

    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(50).all()

    return jsonify({
        "code": 200,
        "data": [m.to_dict() for m in messages][::-1]  # 翻转列表，让旧消息在上方
    })


@app.route('/api/plans', methods=['GET'])
def get_plans():
    user_id = request.args.get('user_id')
    status = request.args.get('status')

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


@app.route('/api/plan/task/<int:task_id>/toggle', methods=['POST'])
def toggle_task_status(task_id):
    task = AIPlanTask.query.get(task_id)
    if not task:
        return jsonify({"code": 404, "msg": "任务节点不存在"}), 404

    try:
        task.is_completed = not task.is_completed

        plan = AIPlan.query.get(task.plan_id)
        if plan:
            all_tasks = AIPlanTask.query.filter_by(plan_id=plan.id).all()
            all_done = all(t.is_completed for t in all_tasks)
            plan.is_completed = all_done

            status_hint = " (计划已归档)" if all_done else ""
        else:
            status_hint = ""

        db.session.commit()
        status_msg = "已完成" if task.is_completed else "已重置"
        return jsonify({
            "code": 200,
            "msg": f"节点{status_msg}{status_hint}",
            "data": {
                "is_completed": task.is_completed,
                "plan_completed": plan.is_completed
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@app.route('/api/chat/upload', methods=['POST'])
def upload_chat_image():
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "未接收到文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"code": 400, "msg": "文件名为空"}), 400

    if file and allowed_file(file.filename):
        try:
            ext = os.path.splitext(file.filename)[1]

            filename = f"chat_{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"

            save_path = os.path.join(app.config['CHAT_FOLDER'], filename)
            file.save(save_path)

            image_url = f"/static/chat_images/{filename}"

            return jsonify({
                "code": 200,
                "msg": "上传成功",
                "data": {
                    "url": image_url,
                    "name": filename
                }
            })
        except Exception as e:
            return jsonify({"code": 500, "msg": f"保存失败: {str(e)}"}), 500
    else:
        return jsonify({"code": 400, "msg": "不支持的文件格式"}), 400


@app.route('/api/vocab/due', methods=['GET'])
def get_due_vocab():
    user_id = getattr(g, 'user_id', None) or request.args.get('user_id')
    target_level = request.args.get('level', 'CET4')
    force_new = request.args.get('force_new', 'false') == 'true'

    only_difficult = request.args.get('difficult', 'false') == 'true'

    if not user_id:
        return jsonify({"code": 400, "msg": "未授权"}), 400

    due_words = []

    if only_difficult:
        print(f"🔥 用户 {user_id} 开启困难模式 (Level: {target_level})")
        difficult_results = db.session.query(UserWordProgress, Vocabulary).join(
            Vocabulary, UserWordProgress.word_id == Vocabulary.id
        ).filter(
            UserWordProgress.user_id == user_id,
            UserWordProgress.easiness_factor < 2.5,
            Vocabulary.level == target_level
        ).order_by(UserWordProgress.easiness_factor.asc()).limit(15).all()

        for progress, word in difficult_results:
            word_dict = word.to_dict()
            word_dict['is_new'] = False
            word_dict['ef'] = progress.easiness_factor
            due_words.append(word_dict)

        return jsonify({
            "code": 200,
            "data": due_words,
            "msg": f"已加载 {len(due_words)} 个困难单词"
        })

    if not force_new:
        from datetime import datetime
        now = datetime.now()

        due_results = db.session.query(UserWordProgress, Vocabulary).join(
            Vocabulary, UserWordProgress.word_id == Vocabulary.id
        ).filter(
            UserWordProgress.user_id == user_id,
            UserWordProgress.next_review_at <= now,
            Vocabulary.level == target_level
        ).limit(15).all()

        for progress, word in due_results:
            word_dict = word.to_dict()
            word_dict['is_new'] = False
            due_words.append(word_dict)

    needed = 15 - len(due_words)

    if needed > 0:
        learned_ids = db.session.query(UserWordProgress.word_id).filter_by(user_id=user_id).subquery()
        unlearned_words = Vocabulary.query.filter(
            Vocabulary.id.notin_(learned_ids),
            Vocabulary.level == target_level
        ).order_by(func.rand()).limit(needed).all()

        for word in unlearned_words:
            word_dict = word.to_dict()
            word_dict['is_new'] = True
            due_words.append(word_dict)

    return jsonify({
        "code": 200,
        "data": due_words,
        "level": target_level
    })


@app.route('/api/vocab/review', methods=['POST'])
def submit_vocab_review():
    user_id = getattr(g, 'user_id', None)

    if not user_id and request.json:
        user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "未授权"}), 400

    data = request.json
    word_id = data.get('word_id')
    quality = data.get('quality')  # 0=忘记, 3=模糊, 4=认识, 5=精通

    if not word_id or quality is None:
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    progress = UserWordProgress.query.filter_by(user_id=user_id, word_id=word_id).first()

    if not progress:
        progress = UserWordProgress(
            user_id=user_id,
            word_id=word_id,
            next_review_at=datetime.now(),
            interval=0,
            repetitions=0,
            easiness_factor=2.5
        )
        db.session.add(progress)


    old_ef = progress.easiness_factor or 2.5
    new_ef = old_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # 设定下限

    # 防止 None 值
    current_interval = progress.interval or 0
    current_repetitions = progress.repetitions or 0

    new_repetitions = current_repetitions

    if quality < 3:
        new_repetitions = 0  # 归零
        new_interval = 1  # 必须第二天复习

    elif quality == 3:
        new_repetitions = 0
        new_interval = max(1, round(current_interval * 1.2))  # 稍微延长一点

    else:
        new_repetitions = current_repetitions + 1

        if new_repetitions == 1:
            new_interval = 2 if quality == 5 else 1

        elif new_repetitions == 2:
            new_interval = 4 if quality == 5 else 3

        else:
            bonus = 1.15 if quality == 5 else 1.0
            new_interval = round(current_interval * new_ef * bonus)

    progress.easiness_factor = new_ef
    progress.repetitions = new_repetitions
    progress.interval = new_interval
    progress.last_reviewed_at = datetime.now()
    progress.next_review_at = datetime.now() + timedelta(days=new_interval)


    try:
        stats = UserVocabStats.query.get(user_id)
        if not stats:
            stats = UserVocabStats(user_id=user_id)
            db.session.add(stats)

        # 防止 None 值导致 += 报错，先初始化为 0
        if stats.total_learned is None:
            stats.total_learned = 0
        if stats.count_0 is None:
            stats.count_0 = 0
        if stats.count_3 is None:
            stats.count_3 = 0
        if stats.count_4 is None:
            stats.count_4 = 0
        if stats.count_5 is None:
            stats.count_5 = 0

        # 增加总学习次数
        stats.total_learned += 1
        stats.last_updated = datetime.now()

        # 根据评分增加对应计数
        if quality == 0:
            stats.count_0 += 1
        elif quality == 3:
            stats.count_3 += 1
        elif quality == 4:
            stats.count_4 += 1
        elif quality == 5:
            stats.count_5 += 1

        # 提交所有更改 (Progress + Stats)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "进度已更新",
            "data": {
                "next_review": progress.next_review_at.strftime('%Y-%m-%d'),
                "interval": new_interval,
                "quality": quality
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting review: {e}")  # 打印错误日志方便调试
        return jsonify({"code": 500, "msg": str(e)}), 500


@app.route('/api/vocab/sentence', methods=['POST'])
def generate_sentence():
    data = request.json
    word = data.get('word')

    if not word:
        return jsonify({"code": 400, "msg": "缺少单词参数"}), 400

    try:
        prompt = f"""
        请为英语单词 "{word}" 生成以下数据 (必须是严格的 JSON 格式):
        1. "en": 一个简短、地道的英语例句，包含该单词。
        2. "cn": 例句的中文翻译。
        3. "synonyms": 一个包含 3 个同义词或近义词的数组 (例如 ["word1", "word2", "word3"])。
        """

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-reasoner",
            "messages": [
                {"role": "system",
                 "content": "你是一个专业的英语教学助手。请只返回 JSON 数据，不要包含任何 Markdown 格式或额外文字。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.3,
            "response_format": {"type": "json_object"}
        }

        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(content)
            import json
            clean_content = content.replace("```json", "").replace("```", "").strip()

            try:
                sentence_data = json.loads(clean_content)

                if 'synonyms' not in sentence_data:
                    sentence_data['synonyms'] = []
                if 'en' not in sentence_data:
                    sentence_data['en'] = f"No sentence available for {word}."
                if 'cn' not in sentence_data:
                    sentence_data['cn'] = "暂无例句。"

                return jsonify({"code": 200, "data": sentence_data})

            except json.JSONDecodeError:
                print(f"JSON解析失败: {content}")
                # 降级处理：如果 JSON 挂了，至少返回一个空结构防止前端报错
                return jsonify({
                    "code": 200,
                    "data": {
                        "en": f"AI response error for {word}.",
                        "cn": "生成失败，请重试。",
                        "synonyms": []
                    }
                })
        else:
            print(f"DeepSeek API Error: {response.status_code} - {response.text}")
            return jsonify({"code": 500, "msg": "AI 服务响应异常"}), 500

    except Exception as e:
        print(f"DeepSeek Error: {e}")
        return jsonify({"code": 500, "msg": "生成失败"}), 500


@app.route('/api/vocab/search', methods=['GET'])
def search_vocab():
    user_id = getattr(g, 'user_id', None) or request.args.get('user_id')

    search_term = request.args.get('word', '').strip()
    first_letter = request.args.get('letter', '').strip()
    only_difficult = request.args.get('difficult', 'false') == 'true'
    target_level = request.args.get('level', '').strip()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    stmt = db.session.query(Vocabulary)

    if only_difficult:
        stmt = stmt.join(UserWordProgress, Vocabulary.id == UserWordProgress.word_id) \
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.easiness_factor < 2.5)

    if first_letter:
        stmt = stmt.filter(Vocabulary.word.like(f"{first_letter}%"))

    if target_level and target_level != 'ALL':
        stmt = stmt.filter(Vocabulary.level == target_level)

    if search_term:
        from sqlalchemy import or_
        stmt = stmt.filter(
            or_(
                Vocabulary.word.like(f"%{search_term}%"),
                Vocabulary.translate.like(f"%{search_term}%")
            )
        )

    total = stmt.count()
    results = stmt.limit(page_size).offset((page - 1) * page_size).all()

    return jsonify({
        "code": 200,
        "data": [w.to_dict() for w in results],
        "total": total,
        "page": page,
        "has_more": (page * page_size) < total
    })


@app.route('/api/training/save', methods=['POST'])
def save_training_session():

    data = request.json
    user_id = data.get('user_id')
    level = data.get('level')
    status = data.get('status', 0)
    details_data = data.get('details', [])

    if not user_id or not details_data:
        return jsonify({"code": 400, "msg": "数据不能为空"}), 400

    try:
        new_session = TrainingSession(
            user_id=user_id,
            level=level,
            status=status,
            total_words=len(details_data)
        )
        db.session.add(new_session)
        db.session.flush()

        for item in details_data:
            detail = TrainingDetail(
                session_id=new_session.id,
                word_id=item.get('word_id'),
                word_text=item.get('word'),
                word_trans=item.get('trans'),
                quality=item.get('quality', 0)
            )
            db.session.add(detail)

        db.session.commit()
        print(f"✅ [History] 用户 {user_id} 保存打卡记录: ID={new_session.id}, 单词数={len(details_data)}")

        # ✅ 背单词 -> 食物点数：每个单词=1个 feed_points
        # 如果后续你想“新词更多点、复习更少点”，可以在这里改换算规则
        try:
            pet = get_or_create_user_pet(int(user_id))
            pet.feed_points = int(pet.feed_points or 0) + int(len(details_data))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ [Pet] 增加 feed_points 失败: {e}")

        return jsonify({"code": 200, "msg": "保存成功", "session_id": new_session.id})

    except Exception as e:
        db.session.rollback()
        print(f"❌ [History Error] 保存失败: {str(e)}")
        return jsonify({"code": 500, "msg": "保存失败，请重试"}), 500


# ==================== 宠物养成 API ====================

@app.route('/api/pet/foods', methods=['GET'])
def get_pet_foods():
    """给前端：可展示的食物图标列表（emoji），用于喂食动画/选择。"""
    return jsonify({"code": 200, "data": PET_FOODS})


@app.route('/api/pet/species', methods=['GET'])
def list_pet_species():
    """列出所有可选宠物品种，用于 Profile 宠物设计页。"""
    try:
        species = PetSpecies.query.order_by(PetSpecies.id.asc()).all()
        return jsonify({
            "code": 200,
            "data": [s.to_dict() for s in species]
        })
    except Exception as e:
        print(f"❌ [Pet] 获取品种列表失败: {e}")
        return jsonify({"code": 500, "msg": "获取品种失败"}), 500


@app.route('/api/pet/profile-data', methods=['GET'])
def get_pet_profile_data():
    """
    Profile 页面宠物设计初始化数据：
    - 当前宠物状态
    - 当前等级样式
    - 当前品种信息
    - 用户自定义外观
    - 可选品种列表
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        style = get_level_style(pet.species_id, int(pet.level))
        customization = pet.customization.to_dict() if hasattr(pet, 'customization') and pet.customization else None
        species = pet.species.to_dict() if pet.species else None
        all_species = [s.to_dict() for s in PetSpecies.query.order_by(PetSpecies.id.asc()).all()]

        return jsonify({
            "code": 200,
            "data": {
                "pet": pet.to_dict(),
                "style": style.to_dict() if style else None,
                "species": species,
                "customization": customization,
                "species_options": all_species,
                "need_exp": pet_need_exp(pet.level)
            }
        })
    except Exception as e:
        print(f"❌ [Pet] 获取 profile 数据失败: {e}")
        return jsonify({"code": 500, "msg": "获取宠物配置失败"}), 500


@app.route('/api/pet/state', methods=['GET'])
def get_pet_state():
    """获取宠物当前状态 + 当前等级样式（无则返回默认样式 None）。"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        style = get_level_style(pet.species_id, int(pet.level))
        customization = pet.customization.to_dict() if hasattr(pet, 'customization') and pet.customization else None
        species = pet.species.to_dict() if pet.species else None
        return jsonify({
            "code": 200,
            "data": {
                "pet": pet.to_dict(),
                "style": style.to_dict() if style else None,
                "species": species,
                "customization": customization,
                "need_exp": pet_need_exp(pet.level)
            }
        })
    except Exception as e:
        print(f"❌ [Pet] 获取状态失败: {e}")
        return jsonify({"code": 500, "msg": "获取宠物状态失败"}), 500


@app.route('/api/pet/position', methods=['POST'])
def save_pet_position():
    """保存宠物拖拽位置（可选）。"""
    data = request.json or {}
    user_id = data.get('user_id')
    pos_x = data.get('pos_x')
    pos_y = data.get('pos_y')
    page_key = data.get('page_key')  # 可选：指定页面

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))

        if page_key:
            # 针对特定页面保存位置
            record = UserPetPosition.query.filter_by(user_pet_id=pet.id, page_key=page_key).first()
            if not record:
                record = UserPetPosition(user_pet_id=pet.id, page_key=page_key)
                db.session.add(record)
            if pos_x is not None:
                record.pos_x = int(pos_x)
            if pos_y is not None:
                record.pos_y = int(pos_y)
        else:
            # 全局默认位置
            if pos_x is not None:
                pet.pos_x = int(pos_x)
            if pos_y is not None:
                pet.pos_y = int(pos_y)

        db.session.commit()

        return jsonify({"code": 200, "msg": "ok", "data": pet.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 保存位置失败: {e}")
        return jsonify({"code": 500, "msg": "保存位置失败"}), 500


@app.route('/api/pet/visibility', methods=['POST'])
def toggle_pet_visibility():
    """切换宠物显示/隐藏状态"""
    data = request.json or {}
    user_id = data.get('user_id')
    status = data.get('status')  # 'active' 或 'hidden'

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    if status not in ['active', 'hidden']:
        return jsonify({"code": 400, "msg": "status 必须是 'active' 或 'hidden'"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        pet.status = status
        db.session.commit()

        print(f"✅ [Pet] 用户 {user_id} 宠物状态已设为: {status}")

        return jsonify({"code": 200, "msg": "状态已更新", "data": pet.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 更新状态失败: {e}")
        return jsonify({"code": 500, "msg": "更新状态失败"}), 500


@app.route('/api/pet/custom', methods=['POST'])
def save_pet_custom():
    """保存用户自定义宠物图片（手绘或导入的图片）"""
    data = request.json or {}
    user_id = data.get('user_id')
    image_data = data.get('image_data')  # base64 编码的图片

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400
    
    if not image_data:
        return jsonify({"code": 400, "msg": "缺少图片数据"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        pet.custom_image = image_data
        db.session.commit()
        
        print(f"✅ [Pet] 用户 {user_id} 自定义图片已保存，长度: {len(image_data)}")
        
        return jsonify({"code": 200, "msg": "保存成功", "data": pet.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 保存自定义图片失败: {e}")
        return jsonify({"code": 500, "msg": "保存失败"}), 500


@app.route('/api/pet/customization', methods=['GET'])
def get_pet_customization():
    """获取用户宠物自定义配置（SVG内容/动画配置）"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        customization = pet.customization if hasattr(pet, 'customization') and pet.customization else None
        
        if not customization:
            return jsonify({"code": 200, "data": None})
        
        return jsonify({
            "code": 200,
            "data": {
                "svg_content": customization.svg_content,
                "animation_config": customization.animation_config,
                "color_overrides": customization.color_overrides_json,
                "accessories": customization.accessories_json
            }
        })
    except Exception as e:
        print(f"❌ [Pet] 获取自定义配置失败: {e}")
        return jsonify({"code": 500, "msg": "获取失败"}), 500


@app.route('/api/pet/customization', methods=['POST'])
def save_pet_customization():
    """保存用户宠物自定义配置（SVG内容/动画配置）"""
    data = request.json or {}
    user_id = data.get('user_id')
    svg_content = data.get('svg_content')
    animation_config = data.get('animation_config')
    color_overrides = data.get('color_overrides')
    accessories = data.get('accessories')

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        
        # 获取或创建 customization 记录
        customization = pet.customization if hasattr(pet, 'customization') and pet.customization else None
        if not customization:
            customization = UserPetCustomization(user_pet_id=pet.id)
            db.session.add(customization)

        if svg_content is not None:
            customization.svg_content = svg_content
        if animation_config is not None:
            if isinstance(animation_config, dict):
                customization.animation_config = json.dumps(animation_config, ensure_ascii=False)
            else:
                customization.animation_config = animation_config
        if color_overrides is not None:
            if isinstance(color_overrides, dict):
                customization.color_overrides_json = json.dumps(color_overrides, ensure_ascii=False)
            else:
                customization.color_overrides_json = color_overrides
        if accessories is not None:
            if isinstance(accessories, dict):
                customization.accessories_json = json.dumps(accessories, ensure_ascii=False)
            else:
                customization.accessories_json = accessories

        db.session.commit()
        
        print(f"✅ [Pet] 用户 {user_id} 自定义配置已保存")
        
        return jsonify({"code": 200, "msg": "保存成功", "data": customization.to_dict()})
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 保存自定义配置失败: {e}")
        return jsonify({"code": 500, "msg": "保存失败"}), 500


@app.route('/api/pet/customization', methods=['DELETE'])
def delete_pet_customization():
    """删除用户宠物自定义配置"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))
        customization = pet.customization if hasattr(pet, 'customization') and pet.customization else None
        
        if customization:
            customization.svg_content = None
            customization.animation_config = None
            db.session.commit()
        
        return jsonify({"code": 200, "msg": "删除成功"})
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 删除自定义配置失败: {e}")
        return jsonify({"code": 500, "msg": "删除失败"}), 500


@app.route('/api/pet/generate-svg', methods=['POST'])
def generate_pet_svg():
    """AI 生成宠物 SVG（可选功能）"""
    data = request.json or {}
    user_id = data.get('user_id')
    prompt = data.get('prompt', '')

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    if not prompt:
        return jsonify({"code": 400, "msg": "请提供描述"}), 400

    # 这里可以调用 AI 生成 SVG，暂时返回占位符
    # TODO: 接入 AI 生成逻辑
    return jsonify({
        "code": 200,
        "msg": "SVG 生成功能开发中",
        "data": {
            "svg_content": None
        }
    })


@app.route('/api/pet/styles', methods=['GET'])
def get_pet_styles():
    """获取等级样式：支持 ?species_id=1&level=1 或只传 species_id / 不传返回全部。"""
    level = request.args.get('level')
    species_id = request.args.get('species_id')
    try:
        query = PetLevelStyle.query
        if species_id:
            query = query.filter_by(species_id=int(species_id))
        if level:
            query = query.filter_by(level=int(level))

        if level and species_id:
            style = query.first()
            return jsonify({"code": 200, "data": style.to_dict() if style else None})

        styles = query.order_by(PetLevelStyle.species_id.asc(), PetLevelStyle.level.asc()).all()
        return jsonify({"code": 200, "data": [s.to_dict() for s in styles]})
    except Exception as e:
        print(f"❌ [Pet] 获取样式失败: {e}")
        return jsonify({"code": 500, "msg": "获取样式失败"}), 500


@app.route('/api/pet/profile/save', methods=['POST'])
def save_pet_profile():
    """
    Profile 页面保存宠物设计：
    - 选择/切换品种 species_id
    - 修改昵称 nickname
    - 保存自定义外观（颜色/配件/动画）
    """
    data = request.json or {}
    user_id = data.get('user_id')
    species_id = data.get('species_id')
    nickname = data.get('nickname')

    color_overrides = data.get('color_overrides')      # dict
    accessories = data.get('accessories')              # dict
    animation_overrides = data.get('animation_overrides')  # dict

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))

        # 切换品种（如果前端传 species_id）
        if species_id:
            try:
                new_species_id = int(species_id)
                if pet.species_id != new_species_id:
                    # 简单策略：换品种时重置等级和经验（经验保留的话这里可以调规则）
                    pet.species_id = new_species_id
                    pet.level = 1
                    pet.exp = 0
            except Exception:
                pass

        if nickname:
            pet.nickname = nickname

        # 处理自定义外观：user_pet_customizations（1:1）
        customization = pet.customization if hasattr(pet, 'customization') else None
        if customization is None:
            customization = UserPetCustomization(user_pet_id=pet.id)
            db.session.add(customization)

        if color_overrides is not None:
            customization.color_overrides_json = json.dumps(color_overrides, ensure_ascii=False)
        if accessories is not None:
            customization.accessories_json = json.dumps(accessories, ensure_ascii=False)
        if animation_overrides is not None:
            customization.animation_overrides_json = json.dumps(animation_overrides, ensure_ascii=False)

        db.session.commit()

        style = get_level_style(pet.species_id, int(pet.level))

        return jsonify({
            "code": 200,
            "msg": "保存成功",
            "data": {
                "pet": pet.to_dict(),
                "style": style.to_dict() if style else None,
                "species": pet.species.to_dict() if pet.species else None,
                "customization": customization.to_dict(),
                "need_exp": pet_need_exp(pet.level)
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 保存宠物配置失败: {e}")
        return jsonify({"code": 500, "msg": "保存宠物配置失败"}), 500


@app.route('/api/pet/feed', methods=['POST'])
def feed_pet():
    """
    喂食接口：
    - 消耗 feed_points
    - 增加 exp
    - 自动升级
    - 返回一个可爱的 food icon（emoji）给前端做动画
    """
    data = request.json or {}
    user_id = data.get('user_id')
    count = int(data.get('count', 1) or 1)

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少 user_id"}), 400
    if count <= 0:
        return jsonify({"code": 400, "msg": "count 必须大于 0"}), 400

    try:
        pet = get_or_create_user_pet(int(user_id))

        if int(pet.feed_points or 0) < count:
            return jsonify({"code": 400, "msg": "食物不足", "data": pet.to_dict()}), 400

        # 随机挑食物（emoji）
        food = PET_FOODS[int(time.time()) % len(PET_FOODS)]

        pet.feed_points -= count
        pet.total_feeds = int(pet.total_feeds or 0) + count

        gained_exp = count * int(food.get("exp", 1))
        pet.exp = int(pet.exp or 0) + gained_exp

        leveled_up = False
        old_level = int(pet.level or 1)
        # 多级连升
        while True:
            need = pet_need_exp(int(pet.level or 1))
            if pet.exp >= need:
                pet.exp -= need
                pet.level = int(pet.level or 1) + 1
                leveled_up = True
            else:
                break

        # 记录喂食日志（失败不影响主流程）
        try:
            log = PetFeedingLog(
                user_pet_id=pet.id,
                source_type='manual',
                source_id=None,
                food_type=food.get("id"),
                amount=count,
                gained_exp=gained_exp,
                level_before=old_level,
                level_after=int(pet.level)
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ [Pet] 记录喂食日志失败: {e}")

        style = get_level_style(pet.species_id, int(pet.level))
        return jsonify({
            "code": 200,
            "msg": "喂食成功",
            "data": {
                "pet": pet.to_dict(),
                "style": style.to_dict() if style else None,
                "need_exp": pet_need_exp(pet.level),
                "event": {
                    "food": food,
                    "gained_exp": gained_exp,
                    "leveled_up": leveled_up,
                    "old_level": old_level,
                    "new_level": int(pet.level)
                }
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ [Pet] 喂食失败: {e}")
        return jsonify({"code": 500, "msg": "喂食失败"}), 500


@app.route('/api/training/history', methods=['GET'])
def get_training_history():
    user_id = request.args.get('user_id')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 6))

    if not user_id:
        return jsonify({"code": 400, "msg": "未授权"}), 400

    pagination = TrainingSession.query.filter_by(user_id=user_id) \
        .order_by(TrainingSession.created_at.desc()) \
        .paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        "code": 200,
        "data": [s.to_dict() for s in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
        "has_more": pagination.has_next
    })


@app.route('/api/training/detail', methods=['GET'])
def get_training_detail():

    session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({"code": 400, "msg": "缺少参数"}), 400

    details = TrainingDetail.query.filter_by(session_id=session_id).all()

    return jsonify({
        "code": 200,
        "data": [d.to_dict() for d in details]
    })


@app.route('/api/training/delete', methods=['POST'])
def delete_training_session():
    """
    删除某条打卡记录
    """
    data = request.json
    session_id = data.get('session_id')
    user_id = data.get('user_id')

    session = TrainingSession.query.filter_by(id=session_id, user_id=user_id).first()

    if not session:
        return jsonify({"code": 404, "msg": "记录不存在或无权删除"}), 404

    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@app.route('/api/stats/user', methods=['GET'])
def get_user_stats():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "Missing user_id"})

    stats = UserVocabStats.query.get(user_id)

    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "msg": "User not found"})

    if not stats:
        return jsonify({
            "code": 200,
            "data": {
                "user_id": user.id,
                "username": user.username,
                "avatar": user.avatar,
                "total_learned": 0,
                "count_0": 0,
                "count_3": 0,
                "count_4": 0,
                "count_5": 0
            }
        })

    # 组合数据：统计数据 + 用户基础信息
    result = stats.to_dict()
    result['username'] = user.username
    result['avatar'] = user.avatar

    return jsonify({"code": 200, "data": result})


@app.route('/api/stats/leaderboard', methods=['GET'])
def get_leaderboard():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = db.session.query(UserVocabStats, User) \
        .join(User, UserVocabStats.user_id == User.id) \
        .order_by(UserVocabStats.total_learned.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    ranks = []
    for stat, user in pagination.items:
        ranks.append({
            "user_id": user.id,
            "username": user.username,
            "avatar": user.avatar,
            "total_learned": stat.total_learned
        })

    return jsonify({
        "code": 200,
        "data": ranks,
        "has_more": pagination.has_next,
        "total": pagination.total
    })


@app.route('/api/stats/trend', methods=['GET'])
def get_learning_trend():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"code": 400, "msg": "Missing user_id"})

    now = datetime.now()
    seven_days_ago = now - timedelta(days=6)
    seven_days_ago = seven_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)

    sessions = db.session.query(TrainingSession).filter(
        TrainingSession.user_id == user_id,
        TrainingSession.created_at >= seven_days_ago
    ).all()

    data_map = {}
    for s in sessions:
        day_str = s.created_at.strftime('%Y-%m-%d')
        if day_str in data_map:
            data_map[day_str] += s.total_words
        else:
            data_map[day_str] = s.total_words

    trend_data = []
    date_labels = []

    for i in range(6, -1, -1):
        target_date = now - timedelta(days=i)
        day_key = target_date.strftime('%Y-%m-%d')
        label_key = target_date.strftime('%m-%d')

        date_labels.append(label_key)
        trend_data.append(data_map.get(day_key, 0))

    return jsonify({
        "code": 200,
        "data": {
            "dates": date_labels,
            "values": trend_data
        }
    })





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
