from models import User
from auth import get_password_hash

def create_test_user(db, username="testuser", password="testpassword"):
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
