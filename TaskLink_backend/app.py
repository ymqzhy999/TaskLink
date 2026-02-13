import pathlib
import uuid
import warnings
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Task, TaskLog, ChatMessage, AIPlan, AIPlanTask, InvitationCode, Vocabulary, UserWordProgress, \
    TrainingSession, TrainingDetail
import requests
import re
from dotenv import load_dotenv
import subprocess
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/tasklink'
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
        "model": "deepseek-reasoner",  # 或者 deepseek-reasoner
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

    # ==========================================
    # 🧠 智能分段逻辑 (强制接管 AI 的规划)
    # ==========================================
    if days <= 7:
        # 短周期：每天一个任务，精确执行
        task_count = days
        structure_prompt = f"必须严格输出 {task_count} 个任务节点，分别对应 Day 1 到 Day {task_count}。"
        time_unit = "Day"
    else:
        # 长周期：强制合并为 4-6 个阶段，杜绝流水账
        if days <= 15:
            task_count = 4
        elif days <= 30:
            task_count = 5
        else:
            task_count = 6

        avg_days = days // task_count
        structure_prompt = f"""
        这是一个长周期计划 ({days}天)。
        ⚠️ 严禁按天罗列！必须将计划压缩为 {task_count} 个【核心战术阶段】(Phases)。
        每个阶段跨度约 {avg_days} 天。
        JSON中的 'day' 字段请填序号 (1, 2, 3...)。
        JSON中的 'title' 必须包含时间范围 (如 "阶段一：基础架构 (Day 1-{avg_days})")。
        """
        time_unit = "Phase"

    # 🔥 核心提示词：重拳整治废话 🔥
    system_prompt = f"""
    # Role: 阿琪的贾维斯 (Cyberpunk Tactical AI)

## Profile
- language: 中文
- description: 一个为阿琪提供专属、高效、精准战术规划与执行方案的人工智能顾问。其核心是剥离所有冗余的赛博朋克美学修饰，直接输出最纯粹、最实用的行动指南。
- background: 诞生于一个高度实用主义的数字空间，其设计初衷是摒弃一切形式主义，将复杂目标分解为可执行的原子任务。
- personality: 冷静、精准、高效、务实。厌恶任何形式的废话和无效信息堆砌，追求极致的逻辑清晰与目标导向。
- expertise: 目标拆解、战术规划、流程优化、风险评估、进度管理。
- target_audience: 阿琪，以及任何需要清晰、直接、无废话行动方案的用户。

## Skills

1. **战术规划与拆解**
   - **目标解构**: 将宏观、模糊的“目标”拆解为具体、可衡量、可执行、相关性强、有时限的子任务。
   - **路径优化**: 分析多种执行路径，选择最高效、风险最低的方案，并预设备用计划。
   - **资源映射**: 识别执行目标所需的知识、工具、时间及外部资源，并进行合理分配。
   - **风险管理**: 预判执行过程中可能遇到的障碍与风险，并提前制定应对策略。

2. **内容生成与格式化**
   - **结构化输出**: 严格按照指定格式（如JSON）生成内容，确保数据结构清晰、易于解析。
   - **干货提炼**: 过滤所有装饰性、重复性语言，确保内容每一条信息都具有实际指导意义。
   - **领域适配**: 根据目标领域（如编程、健身、学习）自动嵌入该领域的核心概念、术语和具体行动项。
   - **Markdown精通**: 熟练运用Markdown语法进行内容排版，使方案条理清晰，重点突出。

## Rules

1. **内容核心原则**：
   - **绝对干货**: 输出内容必须100%为可执行的实用信息。严禁出现“系统自检中...”、“神经连接稳定”等无实际意义的赛博朋克风格填充词。
   - **强领域关联**: 方案内容必须紧密贴合目标领域。例如，编程目标必须包含具体的代码概念、库、框架或算法；健身目标必须包含具体的动作名称、组数、次数、器械。
   - **逻辑递进**: 任务安排需符合学习或执行的客观规律，由易到难，由基础到综合，确保每一步都建立在前一步的成功之上。

2. **输出行为准则**：
   - **格式严格遵守**: 必须完全按照预设的JSON格式输出，包含`title`和`tasks`数组，每个任务对象包含`day`, `title`, `content`。
   - **标题风格化**: `title`和每个任务的`title`需保持简洁、有力的赛博朋克词汇风格（如“协议注入”、“核心重构”、“数据链路铺设”），但**仅限于标题**。
   - **内容清单化**: `content`部分必须使用Markdown无序列表，清晰罗列【核心目标】、【执行步骤】、【验收标准】等模块的具体要点。

3. **交互限制条件**：
   - **不解释规则**: 不向用户复述或解释自身的工作规则，直接输出方案。
   - **不进行开放式提问**: 当输入信息（如`{goal}`, `{structure_prompt}`, `{task_count}`）不全时，输出一个标准错误提示，要求补全必要参数，而非猜测。
   - **不生成额外内容**: 严格限定输出内容为请求的战术方案JSON对象，不添加任何总结、祝福或额外说明。

## Workflows
- 目标: 接收包含`{goal}`（目标）、`{structure_prompt}`（结构提示）、`{task_count}`（任务数量）的指令，生成一份高度结构化、可执行的战术方案。
- 步骤 1: **解析与确认**。解析输入指令，确认`{goal}`, `{structure_prompt}`, `{task_count}`三个关键参数均已提供且含义明确。
- 步骤 2: **目标解构与规划**。基于`{goal}`和`{structure_prompt}`，运用战术规划技能，将总目标科学拆解为`{task_count}`个递进式的子任务。为每个子任务确定一个阶段性的核心目标。
- 步骤 3: **内容填充与格式化**。为每个子任务填充纯粹的“干货”内容，严格遵循内容规则（强领域关联、清单化）。为总计划和每个子任务生成符合赛博朋克风格的标题。最后，将全部内容组装成严格的JSON格式对象。
- 预期结果: 输出一个完整的、可直接使用的JSON对象，包含一个总标题和一个由指定数量任务组成的数组，每个任务都提供了清晰、具体、无废话的每日/阶段行动指南。

## Initialization
作为阿琪的贾维斯 (Cyberpunk Tactical AI)，你必须遵守上述Rules，按照Workflows执行任务。
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
    # 1. 放行白名单
    allowed_endpoints = ['login', 'register', 'static', 'upload_avatar', 'upload_image']
    if request.endpoint in allowed_endpoints or request.endpoint is None:
        return None

    # 2. 识别“谁在发起请求”
    current_user_id = None

    if request.method == 'GET':
        # GET 请求通常只有 operator_id 或者 user_id (视作查看自己)
        current_user_id = request.args.get('operator_id') or request.args.get('user_id')

    elif request.method == 'POST':
        if request.is_json:
            data = request.get_json(silent=True)
            if data:
                # 🔥🔥🔥 核心修复 🔥🔥🔥
                # 优先认定 operator_id 为操作者
                # 如果没有 operator_id，才把 user_id 当作操作者
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
    invitation_code = data.get('invitation_code')  # 1. 获取邀请码

    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名或密码不能为空"}), 400

    if not invitation_code:
        return jsonify({"code": 400, "msg": "请输入邀请码"}), 400

    # 查询该邀请码是否存在，且 is_used 为 False (未使用)
    code_record = InvitationCode.query.filter_by(code=invitation_code, is_used=False).first()

    if not code_record:
        return jsonify({"code": 400, "msg": "邀请码无效或已被使用"}), 400

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

        code_record.is_used = True
        code_record.used_at = datetime.now()
        code_record.used_by_user_id = new_user.id  # 记录是谁用了这个码

        # 最后统一提交所有更改
        db.session.commit()
        print(username, "注册成功")
        return jsonify({"code": 200, "msg": "注册成功", "data": new_user.to_dict()})

    except Exception as e:
        db.session.rollback()  # 如果出错，回滚所有操作（用户也不会创建，邀请码也不会被废弃）
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

        # 生成 Token
        import datetime
        import jwt

        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        token = jwt.encode({
            'user_id': user.id,
            'exp': expiration
        }, app.config['SECRET_KEY'], algorithm="HS256")

        # 🔥🔥🔥 关键步骤：把 Token 存入数据库 🔥🔥🔥
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


# --- 2. 新增：管理员获取用户列表 ---
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    # 鉴权：从 URL 参数获取操作者 ID (实际项目建议用 Token 解析)
    operator_id = request.args.get('operator_id')

    admin = User.query.get(operator_id)
    # 只有 role == 1 才能看
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

        # 🔥 如果是禁用操作，通知 Node.js 踢人
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
    current_user_id = g.user_id

    if not user_id:
        return jsonify({"code": 400, "msg": "缺少用户ID"}), 400

    # 查询该用户的所有任务，按时间排序
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.trigger_time).all()

    return jsonify({
        "code": 200,
        "data": [t.to_dict() for t in tasks]
    })


# 添加任务
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


# 删除任务
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
        # 👇 新增：接收脚本运行结果
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


# TaskLink_backend/app.py

@app.route('/api/square/history', methods=['GET'])
def get_square_history():
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(50).all()

    return jsonify({
        "code": 200,
        "data": [m.to_dict() for m in messages][::-1]  # 翻转列表，旧的在上面
    })


# 获取计划列表
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


@app.route('/api/plan/task/<int:task_id>/toggle', methods=['POST'])
def toggle_task_status(task_id):
    task = AIPlanTask.query.get(task_id)
    if not task:
        return jsonify({"code": 404, "msg": "任务节点不存在"}), 404

    try:
        # 1. 切换当前任务状态
        task.is_completed = not task.is_completed

        # 2. 🔥 核心修复：检查所属计划的所有任务是否都已完成
        plan = AIPlan.query.get(task.plan_id)
        if plan:
            # 获取该计划下的所有任务
            all_tasks = AIPlanTask.query.filter_by(plan_id=plan.id).all()
            # 判断是否全部完成
            all_done = all(t.is_completed for t in all_tasks)

            # 更新计划状态
            plan.is_completed = all_done

            status_hint = " (计划已归档)" if all_done else ""
        else:
            status_hint = ""

        db.session.commit()

        # 返回信息带上计划状态，方便前端调试
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
    # 1. 检查是否有文件
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "未接收到文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"code": 400, "msg": "文件名为空"}), 400

    # 2. 检查文件类型
    if file and allowed_file(file.filename):
        try:
            # 获取后缀 (如 .jpg)
            ext = os.path.splitext(file.filename)[1]

            # 生成唯一文件名 (防止文件名冲突覆盖)
            # 格式: chat_时间戳_随机串.jpg
            filename = f"chat_{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"

            # 3. 保存到 CHAT_FOLDER (static/chat_images)
            save_path = os.path.join(app.config['CHAT_FOLDER'], filename)
            file.save(save_path)

            # 4. 生成访问 URL
            # 这里的 URL 不需要加 http 域名，前端会自动拼接或者由 Nginx 处理
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
    """获取单词 (支持强制拉取新词 + 困难模式) - 每组 15 个"""
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
    """提交单词学习结果，使用优化版 SM-2 算法"""
    user_id = getattr(g, 'user_id', None)

    # 如果 g 中没有，尝试从 JSON body 中获取 (兼容你前端的传参方式)
    if not user_id and request.json:
        user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({"code": 400, "msg": "未授权"}), 400

    data = request.json
    word_id = data.get('word_id')
    quality = data.get('quality')  # 0=忘记, 3=模糊, 4=认识, 5=精通

    if not word_id or quality is None:
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    # 获取或创建用户单词进度记录
    progress = UserWordProgress.query.filter_by(user_id=user_id, word_id=word_id).first()

    # 初始化新词
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

    # --- SM-2 算法核心 ---

    # 1. 更新易读度 (EF)
    old_ef = progress.easiness_factor
    new_ef = old_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # 设定下限

    # 2. 计算复习间隔 (Interval) & 连续次数 (Repetitions)
    new_repetitions = progress.repetitions
    new_interval = progress.interval

    if quality < 3:
        new_repetitions = 0  # 归零
        new_interval = 1  # 必须第二天复习

    elif quality == 3:
        new_repetitions = 0
        new_interval = max(1, round(progress.interval * 1.2))  # 稍微延长一点

    else:
        new_repetitions += 1

        # 阶段 1: 第一次复习
        if new_repetitions == 1:
            new_interval = 2 if quality == 5 else 1

        # 阶段 2: 第二次复习
        elif new_repetitions == 2:
            new_interval = 4 if quality == 5 else 3

        # 阶段 3+: 后续复习
        else:
            bonus = 1.15 if quality == 5 else 1.0
            new_interval = round(progress.interval * new_ef * bonus)

    # 应用计算结果
    progress.easiness_factor = new_ef
    progress.repetitions = new_repetitions
    progress.interval = new_interval
    progress.last_reviewed_at = datetime.now()
    progress.next_review_at = datetime.now() + timedelta(days=new_interval)

    try:
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
        return jsonify({"code": 500, "msg": str(e)}), 500


@app.route('/api/vocab/sentence', methods=['POST'])
def generate_sentence():
    """调用 DeepSeek 为单词生成例句和近义词"""
    data = request.json
    word = data.get('word')

    if not word:
        return jsonify({"code": 400, "msg": "缺少单词参数"}), 400

    try:
        # 🔥 修改 Prompt: 明确要求返回 en, cn 和 synonyms
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
            "model": "deepseek-chat",  # 或 deepseek-v3
            "messages": [
                {"role": "system",
                 "content": "你是一个专业的英语教学助手。请只返回 JSON 数据，不要包含任何 Markdown 格式或额外文字。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"}  # 🔥 强制让 DeepSeek 返回 JSON 对象
        }

        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=15)  # 稍微增加超时时间

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(content)
            # --- JSON 清洗与解析 ---
            import json
            # 去除可能的 markdown 标记
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

    # 1. 获取参数
    search_term = request.args.get('word', '').strip()
    first_letter = request.args.get('letter', '').strip()
    only_difficult = request.args.get('difficult', 'false') == 'true'
    # 🔥 新增：获取目标等级 (默认空字符串表示全部)
    target_level = request.args.get('level', '').strip()

    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    stmt = db.session.query(Vocabulary)

    # 2. 难词筛选
    if only_difficult:
        stmt = stmt.join(UserWordProgress, Vocabulary.id == UserWordProgress.word_id) \
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.easiness_factor < 2.5)

    # 3. 首字母筛选
    if first_letter:
        stmt = stmt.filter(Vocabulary.word.like(f"{first_letter}%"))

    # 4. 🔥 新增：等级筛选 (如果传了具体等级，且不是 'ALL')
    if target_level and target_level != 'ALL':
        stmt = stmt.filter(Vocabulary.level == target_level)

    # 5. 关键词搜索 (中英混合)
    if search_term:
        from sqlalchemy import or_
        stmt = stmt.filter(
            or_(
                Vocabulary.word.like(f"%{search_term}%"),
                Vocabulary.translate.like(f"%{search_term}%")
            )
        )

    # 6. 分页与返回
    total = stmt.count()
    results = stmt.limit(page_size).offset((page - 1) * page_size).all()

    return jsonify({
        "code": 200,
        "data": [w.to_dict() for w in results],
        "total": total,
        "page": page,
        "has_more": (page * page_size) < total
    })


# 1. 保存/提交打卡记录
@app.route('/api/training/save', methods=['POST'])
def save_training_session():
    """
    保存当前的训练进度（无论是中途保存还是全部完成）
    前端需要传: user_id, level, status, details(数组)
    """
    data = request.json
    user_id = data.get('user_id')
    level = data.get('level')
    status = data.get('status', 0)  # 0=未完成, 1=已完成
    details_data = data.get('details', [])  # 包含单词列表 [{word_id, word, trans, quality}, ...]

    if not user_id or not details_data:
        return jsonify({"code": 400, "msg": "数据不能为空"}), 400

    try:
        # A. 创建主记录
        new_session = TrainingSession(
            user_id=user_id,
            level=level,
            status=status,
            total_words=len(details_data)
        )
        db.session.add(new_session)
        db.session.flush()  # 立即执行以获取 new_session.id，但暂不提交事务

        # B. 批量插入详情
        for item in details_data:
            detail = TrainingDetail(
                session_id=new_session.id,
                word_id=item.get('word_id'),
                word_text=item.get('word'),
                word_trans=item.get('trans'),  # 翻译
                quality=item.get('quality', 0)
            )
            db.session.add(detail)

        # C. 提交事务
        db.session.commit()
        print(f"✅ [History] 用户 {user_id} 保存打卡记录: ID={new_session.id}, 单词数={len(details_data)}")

        return jsonify({"code": 200, "msg": "保存成功", "session_id": new_session.id})

    except Exception as e:
        db.session.rollback()  # 🔥 关键：出错了就全部撤销，防止产生脏数据
        print(f"❌ [History Error] 保存失败: {str(e)}")
        return jsonify({"code": 500, "msg": "保存失败，请重试"}), 500


# 2. 获取历史记录列表 (分页)
@app.route('/api/training/history', methods=['GET'])
def get_training_history():
    """
    获取历史球的列表，每页 6 条
    """
    user_id = request.args.get('user_id')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 6))  # 默认每页 6 条

    if not user_id:
        return jsonify({"code": 400, "msg": "未授权"}), 400

    # 按时间倒序排列
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


# 3. 获取某次打卡的详细单词列表
@app.route('/api/training/detail', methods=['GET'])
def get_training_detail():
    """
    点击某个历史球，进入详情页查看那次背了哪些词
    """
    session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({"code": 400, "msg": "缺少参数"}), 400

    # 查询该次记录的所有单词
    details = TrainingDetail.query.filter_by(session_id=session_id).all()

    # 🔥 补充：如果我们之前加了 audio_url 字段，可以在这里联表查询 Vocabulary 获取
    # 这里先演示基础版，直接返回当时存的 word_text

    return jsonify({
        "code": 200,
        "data": [d.to_dict() for d in details]
    })


# 4. 删除打卡记录 (长按删除)
@app.route('/api/training/delete', methods=['POST'])
def delete_training_session():
    """
    删除某条打卡记录
    """
    data = request.json
    session_id = data.get('session_id')
    user_id = data.get('user_id')  # 用于安全校验，防止删别人的

    session = TrainingSession.query.filter_by(id=session_id, user_id=user_id).first()

    if not session:
        return jsonify({"code": 404, "msg": "记录不存在或无权删除"}), 404

    try:
        # 由于设置了 cascade="all, delete-orphan" 或者数据库外键级联，
        # 删除 session 会自动删除对应的 details
        db.session.delete(session)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


if __name__ == '__main__':
    # # 配置你手机的局域网 IP
    # PHONE_IP = "192.168.10.8"  # 👈 替换成你手机在 WiFi 下的真实 IP
    # # 尝试无线连接
    # ADBController.connect_wireless(PHONE_IP)
    app.run(host='0.0.0.0', port=5000, debug=True)
