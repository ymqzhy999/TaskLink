from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Integer, default=0)  # 0:普通用户, 1:管理员
    current_token = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Integer, default=1)  # 1:正常, 0:禁用 (补上这个字段以免报错)
    created_at = db.Column(db.DateTime, default=datetime.now)
    avatar = db.Column(db.String(255), nullable=True)

    plans = db.relationship('AIPlan', backref='owner', lazy=True)

    def set_password(self, password):
        """生成加密密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码是否正确"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "status": self.status,
            "avatar": self.avatar,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    trigger_time = db.Column(db.String(5), nullable=False)  # 格式 "09:00"
    action_type = db.Column(db.String(20), nullable=False)  # APP, LINK, CALL
    target_value = db.Column(db.String(255), nullable=False)  # 包名或链接
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.String(500), nullable=True)
    is_loop = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "time": self.trigger_time,
            "type": self.action_type,
            "target": self.target_value,
            "description": self.description,
            "is_loop": self.is_loop,
            "active": bool(self.is_active)
        }


# --- 🔥 新增：AI 智能计划总表 ---
class AIPlan(db.Model):
    __tablename__ = 'ai_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)  # 计划名：如 "Pytest 一周速成"
    goal = db.Column(db.Text, nullable=True)  # 用户的原始需求
    total_days = db.Column(db.Integer, default=7)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联每天的子任务
    tasks = db.relationship('AIPlanTask', backref='plan', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        # 简单计算进度
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.is_completed)
        progress = int((done / total * 100)) if total > 0 else 0

        return {
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "total_days": self.total_days,
            "progress": progress,  # 返回进度百分比，方便前端展示进度条
            "is_completed": self.is_completed,
            "created_at": self.created_at.strftime('%Y-%m-%d')
        }


# --- 🔥 新增：计划每日详情表 ---
class AIPlanTask(db.Model):
    __tablename__ = 'ai_plan_tasks'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('ai_plans.id'), nullable=False)
    day_order = db.Column(db.Integer, nullable=False)  # 第几天
    title = db.Column(db.String(100), nullable=True)  # 当天的主题，如 "环境搭建与Hello World"
    content = db.Column(db.Text, nullable=True)  # AI生成的详细指导 (Markdown)
    is_completed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "day": self.day_order,
            "title": self.title,
            "content": self.content,
            "is_completed": self.is_completed
        }


# --- 日志与聊天 (保持不变) ---
class TaskLog(db.Model):
    __tablename__ = 'task_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_title = db.Column(db.String(100), nullable=False)
    task_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='SUCCESS')
    executed_at = db.Column(db.DateTime, default=datetime.now)
    result = db.Column(db.Text, nullable=True)

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
    msg_type = db.Column(db.String(20), default='text')
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


class InvitationCode(db.Model):
    __tablename__ = 'invitation_code'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False)  # 6位邀请码
    is_used = db.Column(db.Boolean, default=False)  # 是否已使用
    created_at = db.Column(db.DateTime, default=datetime.now)  # 创建时间
    used_at = db.Column(db.DateTime, nullable=True)  # 使用时间

    used_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'is_used': self.is_used,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Vocabulary(db.Model):
    __tablename__ = 'vocabulary'  # 👈 确认表名是 vocabulary
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    phonetic = db.Column(db.String(100), nullable=True)
    translate = db.Column(db.Text, nullable=True)
    level = db.Column(db.String(20), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "word": self.word,
            "phonetic": self.phonetic,
            "translation": self.translate,
            "level": self.level
        }


class UserWordProgress(db.Model):
    __tablename__ = 'user_word_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    word_id = db.Column(db.Integer, db.ForeignKey('vocabulary.id'), nullable=False)

    next_review_at = db.Column(db.DateTime, default=None)
    interval = db.Column(db.Float, default=0)
    repetitions = db.Column(db.Integer, default=0)
    easiness_factor = db.Column(db.Float, default=2.5)
    last_reviewed_at = db.Column(db.DateTime, default=None)


class TrainingSession(db.Model):
    __tablename__ = 'training_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    level = db.Column(db.String(20))
    status = db.Column(db.Integer, default=0)  # 0=未完成, 1=已完成
    total_words = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 建立关系，方便级联查询
    details = db.relationship('TrainingDetail', backref='session', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'level': self.level,
            'status': self.status,
            'total_words': self.total_words,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'timestamp': int(self.created_at.timestamp())
        }


# 2. 日志详情模型
class TrainingDetail(db.Model):
    __tablename__ = 'training_details'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('training_sessions.id'), nullable=False)
    word_id = db.Column(db.Integer, nullable=False)
    word_text = db.Column(db.String(100))
    word_trans = db.Column(db.String(255))
    quality = db.Column(db.Integer, default=0)  # 0=忘记, 3=模糊...

    def to_dict(self):
        return {
            'id': self.id,
            'word_id': self.word_id,
            'word': self.word_text,
            'trans': self.word_trans,
            'quality': self.quality
        }


class UserVocabStats(db.Model):
    __tablename__ = 'user_vocab_stats'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    total_learned = db.Column(db.Integer, default=0)  # 总背诵单词数
    count_0 = db.Column(db.Integer, default=0)  # 评分0：忘记
    count_3 = db.Column(db.Integer, default=0)  # 评分3：模糊
    count_4 = db.Column(db.Integer, default=0)  # 评分4：认识
    count_5 = db.Column(db.Integer, default=0)  # 评分5：精通
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联用户，方便查询
    user = db.relationship('User', backref=db.backref('stats', uselist=False))

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "total_learned": self.total_learned,
            "count_0": self.count_0,
            "count_3": self.count_3,
            "count_4": self.count_4,
            "count_5": self.count_5,
            "last_updated": self.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        }



# -------------------
# 宠物系统 2.0：品种 / 等级样式 / 用户实例 / 自定义 / AI
# -------------------

class PetSpecies(db.Model):
    """宠物品种：猫 / 狗 / 史莱姆 / 机器人等"""
    __tablename__ = 'pet_species'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)  # cat / dog / slime / bot ...
    name = db.Column(db.String(100), nullable=False)             # 展示名称
    description = db.Column(db.String(255), nullable=True)

    base_style_json = db.Column(db.Text, nullable=True)          # 品种级别的基础样式 JSON
    default_ai_profile_id = db.Column(db.Integer, nullable=True) # 预留：默认 AI 模板

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "base_style_json": self.base_style_json,
            "default_ai_profile_id": self.default_ai_profile_id,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PetLevelStyle(db.Model):
    """品种 + 等级 的样式配置"""
    __tablename__ = 'pet_level_styles'

    id = db.Column(db.Integer, primary_key=True)

    species_id = db.Column(db.Integer, db.ForeignKey('pet_species.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1~20

    name = db.Column(db.String(100), nullable=False, default='默认形态')

    # 一些基础外观参数（前端 Canvas 根据这些字段来画）
    body_color = db.Column(db.String(20), default='#FFCC99')   # 主体颜色
    eye_color = db.Column(db.String(20), default='#000000')
    accent_color = db.Column(db.String(20), default='#FF9900')  # 点缀色

    size_scale = db.Column(db.Float, default=1.0)  # 尺寸倍率，比如 1.0 / 1.2 / 1.5

    has_ears = db.Column(db.Boolean, default=False)
    has_tail = db.Column(db.Boolean, default=False)
    has_wings = db.Column(db.Boolean, default=False)

    extra_effect = db.Column(db.String(50), default='none')  # none / glow / aura 等

    # 预留：更复杂的结构直接塞到 JSON 里，方便你以后扩展
    config_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    species = db.relationship('PetSpecies', backref=db.backref('level_styles', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('species_id', 'level', name='uq_species_level'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "species_id": self.species_id,
            "level": self.level,
            "name": self.name,
            "body_color": self.body_color,
            "eye_color": self.eye_color,
            "accent_color": self.accent_color,
            "size_scale": self.size_scale,
            "has_ears": self.has_ears,
            "has_tail": self.has_tail,
            "has_wings": self.has_wings,
            "extra_effect": self.extra_effect,
            "config_json": self.config_json,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class UserPet(db.Model):
    """用户拥有的一只宠物（实例）"""
    __tablename__ = 'user_pets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    species_id = db.Column(db.Integer, db.ForeignKey('pet_species.id'), nullable=False)

    nickname = db.Column(db.String(50), default='小伙伴')

    level = db.Column(db.Integer, default=1, nullable=False)
    exp = db.Column(db.Integer, default=0, nullable=False)
    feed_points = db.Column(db.Integer, default=0, nullable=False)  # 可用喂食点
    total_feeds = db.Column(db.Integer, default=0, nullable=False)  # 总喂次数

    mood = db.Column(db.String(20), default='normal')               # normal/happy/...
    status = db.Column(db.String(20), default='active')             # active/hidden/...

    pos_x = db.Column(db.Integer, default=50)  # 记录默认拖拽位置
    pos_y = db.Column(db.Integer, default=50)
    
    custom_image = db.Column(db.Text, nullable=True)  # 自定义宠物图片（base64）

    ai_profile_id = db.Column(db.Integer, nullable=True)           # FK -> user_pet_ai_profiles.id（稍后定义）

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('pets', lazy='dynamic'))
    species = db.relationship('PetSpecies', backref=db.backref('user_pets', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "species_id": self.species_id,
            "nickname": self.nickname,
            "level": self.level,
            "exp": self.exp,
            "feed_points": self.feed_points,
            "total_feeds": self.total_feeds,
            "mood": self.mood,
            "status": self.status,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "custom_image": self.custom_image,
            "ai_profile_id": self.ai_profile_id,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class UserPetCustomization(db.Model):
    """用户对某只宠物的外观自定义（颜色/配件/SVG/动画等）"""
    __tablename__ = 'user_pet_customizations'

    id = db.Column(db.Integer, primary_key=True)
    user_pet_id = db.Column(db.Integer, db.ForeignKey('user_pets.id'), nullable=False, unique=True)

    color_overrides_json = db.Column(db.Text, nullable=True)      # 颜色覆盖
    accessories_json = db.Column(db.Text, nullable=True)          # 配件，例如帽子/眼镜
    animation_overrides_json = db.Column(db.Text, nullable=True)  # 动画偏好
    
    # 新增：SVG 自定义和动画配置
    svg_content = db.Column(db.Text, nullable=True)              # 用户自定义的 SVG 内容
    animation_config = db.Column(db.Text, nullable=True)         # 动画配置 JSON

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    pet = db.relationship('UserPet', backref=db.backref('customization', uselist=False))

    def to_dict(self):
        return {
            "id": self.id,
            "user_pet_id": self.user_pet_id,
            "color_overrides_json": self.color_overrides_json,
            "accessories_json": self.accessories_json,
            "animation_overrides_json": self.animation_overrides_json,
            "svg_content": self.svg_content,
            "animation_config": self.animation_config,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class UserPetPosition(db.Model):
    """（可选）按页面存宠物位置"""
    __tablename__ = 'user_pet_positions'

    id = db.Column(db.Integer, primary_key=True)
    user_pet_id = db.Column(db.Integer, db.ForeignKey('user_pets.id'), nullable=False)
    page_key = db.Column(db.String(100), nullable=False)  # /pages/index/index 等

    pos_x = db.Column(db.Integer, default=50)
    pos_y = db.Column(db.Integer, default=50)

    created_at = db.Column(db.DateTime, default=datetime.now)

    pet = db.relationship('UserPet', backref=db.backref('positions', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_pet_id', 'page_key', name='uq_pet_page'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_pet_id": self.user_pet_id,
            "page_key": self.page_key,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class PetFeedingLog(db.Model):
    """喂食日志，用于成就/统计"""
    __tablename__ = 'pet_feeding_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_pet_id = db.Column(db.Integer, db.ForeignKey('user_pets.id'), nullable=False)

    source_type = db.Column(db.String(50), default='manual')  # manual / training_session / ...
    source_id = db.Column(db.Integer, nullable=True)

    food_type = db.Column(db.String(50), nullable=True)       # strawberry / cookie / ...
    amount = db.Column(db.Integer, default=1)
    gained_exp = db.Column(db.Integer, default=0)

    level_before = db.Column(db.Integer, nullable=True)
    level_after = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    pet = db.relationship('UserPet', backref=db.backref('feeding_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_pet_id": self.user_pet_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "food_type": self.food_type,
            "amount": self.amount,
            "gained_exp": self.gained_exp,
            "level_before": self.level_before,
            "level_after": self.level_after,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class PetAIProfile(db.Model):
    """全局 AI 提示词模板"""
    __tablename__ = 'pet_ai_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    system_prompt = db.Column(db.Text, nullable=False)
    style_tags = db.Column(db.Text, nullable=True)  # JSON 数组字符串

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "style_tags": self.style_tags,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class UserPetAIProfile(db.Model):
    """每只宠物的专属 AI 提示词"""
    __tablename__ = 'user_pet_ai_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_pet_id = db.Column(db.Integer, db.ForeignKey('user_pets.id'), nullable=False, unique=True)

    base_profile_id = db.Column(db.Integer, db.ForeignKey('pet_ai_profiles.id'), nullable=True)

    system_prompt = db.Column(db.Text, nullable=False)
    memory_json = db.Column(db.Text, nullable=True)  # 预留：宠物记忆

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    pet = db.relationship('UserPet', backref=db.backref('ai_profile', uselist=False))
    base_profile = db.relationship('PetAIProfile', backref=db.backref('user_profiles', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_pet_id": self.user_pet_id,
            "base_profile_id": self.base_profile_id,
            "system_prompt": self.system_prompt,
            "memory_json": self.memory_json,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }