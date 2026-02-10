import random
import string
from app import app, db
from models import InvitationCode


def generate_code():
    """生成6位随机大写字母+数字"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))


def create_codes(num=50):
    """批量生成"""
    with app.app_context():
        count = 0
        for _ in range(num):
            code_str = generate_code()
            # 查重
            if not InvitationCode.query.filter_by(code=code_str).first():
                new_code = InvitationCode(code=code_str)
                db.session.add(new_code)
                count += 1

        db.session.commit()
        print(f"✅ 成功生成 {count} 个邀请码！")


if __name__ == '__main__':
    create_codes(20)  # 生成 20 个