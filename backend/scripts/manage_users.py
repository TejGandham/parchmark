import argparse
import os
import sys

from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.auth import get_password_hash
from app.database.database import SessionLocal
from app.models.models import User


def create_user(db: Session, username: str, password: str):
    """Creates a new user in the database."""
    user = db.query(User).filter(User.username == username).first()
    if user:
        print(f"Error: User '{username}' already exists.")
        return

    hashed_password = get_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    print(f"User '{username}' created successfully.")


def update_password(db: Session, username: str, password: str):
    """Updates the password for an existing user."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"Error: User '{username}' not found.")
        return

    hashed_password = get_password_hash(password)
    user.password_hash = hashed_password
    db.commit()
    print(f"Password for user '{username}' updated successfully.")


def delete_user(db: Session, username: str):
    """Deletes a user from the database."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"Error: User '{username}' not found.")
        return

    db.delete(user)
    db.commit()
    print(f"User '{username}' deleted successfully.")


def main():
    parser = argparse.ArgumentParser(description="Manage ParchMark users.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create user command
    parser_create = subparsers.add_parser("create", help="Create a new user.")
    parser_create.add_argument("username", help="The username for the new user.")
    parser_create.add_argument("password", help="The password for the new user.")

    # Update password command
    parser_update = subparsers.add_parser("update-password", help="Update a user's password.")
    parser_update.add_argument("username", help="The username of the user to update.")
    parser_update.add_argument("password", help="The new password.")

    # Delete user command
    parser_delete = subparsers.add_parser("delete", help="Delete a user.")
    parser_delete.add_argument("username", help="The username of the user to delete.")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.command == "create":
            create_user(db, args.username, args.password)
        elif args.command == "update-password":
            update_password(db, args.username, args.password)
        elif args.command == "delete":
            delete_user(db, args.username)
    finally:
        db.close()


if __name__ == "__main__":
    main()
