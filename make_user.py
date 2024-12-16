import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from passlib.context import CryptContext
from main import User, Base  # Replace 'your_module_name' with the module containing your User model

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

def promote_user_to_admin(username: str, password: str, db: Session):
    """
    Promote an existing user to admin or create a new admin user.
    """
    user = db.query(User).filter(User.username == username).first()

    if user:
        print(f"User '{username}' found. Promoting to admin...")
        user.is_admin = True
    else:
        print(f"User '{username}' not found. Creating a new admin user...")
        hashed_password = pwd_context.hash(password)
        user = User(username=username, hashed_password=hashed_password, is_admin=True)
        db.add(user)

    db.commit()
    print(f"User '{username}' is now an admin.")

if __name__ == "__main__":
    import argparse

    # Parse arguments for username and password
    parser = argparse.ArgumentParser(description="Promote or create an admin user.")
    parser.add_argument("username", type=str, help="The username of the admin user.")
    parser.add_argument("password", type=str, help="The password for the admin user.")
    args = parser.parse_args()

    # Connect to the database
    with Session(engine) as session:
        promote_user_to_admin(args.username, args.password, session)
