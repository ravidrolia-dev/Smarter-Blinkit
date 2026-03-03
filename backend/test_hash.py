import hashlib
import bcrypt

def _pre_hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_password_hash(password: str) -> str:
    pre_hashed = _pre_hash_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pre_hashed.encode('utf-8'), salt).decode('utf-8')

try:
    print('Testing password: password123')
    hashed = get_password_hash('password123')
    print('SUCCESS:', hashed)
except Exception as e:
    import traceback
    traceback.print_exc()
