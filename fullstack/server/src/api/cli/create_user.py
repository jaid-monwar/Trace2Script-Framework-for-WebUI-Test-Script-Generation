import argparse
import getpass
import logging
import sys
from typing import Optional

from sqlmodel import Session, select

sys.path.append(".")

from src.api.db.session import create_db_and_tables, engine
from src.api.models.user import User
from src.api.services.security import hash_password

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_user(username: str, password: Optional[str] = None) -> None:
    create_db_and_tables()
    
    if password is None:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            logger.error("Passwords do not match")
            sys.exit(1)
    
    hashed_password = hash_password(password)
    
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            logger.error(f"User '{username}' already exists")
            sys.exit(1)
        
        user = User(username=username, hashed_password=hashed_password)
        session.add(user)
        try:
            session.commit()
            session.refresh(user)
            logger.info(f"User '{username}' created successfully with ID: {user.id}")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            session.rollback()
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new user in the database")
    parser.add_argument("--username", "-u", help="Username for the new user")
    parser.add_argument("--password", "-p", help="Password for the new user (not recommended, use prompt instead)")
    
    args = parser.parse_args()
    
    username = args.username
    if not username:
        username = input("Enter username: ")
    
    create_user(username, args.password)


if __name__ == "__main__":
    main()