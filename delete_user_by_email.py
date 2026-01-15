#!/usr/bin/env python3
"""
Script to delete a user by email from the database.
Run from the tapcard-backend directory.
Usage: python delete_user_by_email.py
"""

from database import SessionLocal, engine
import models

def delete_user_by_email(email: str):
    """
    Delete a user and all their related data by email address.
    """
    db = SessionLocal()
    try:
        # Find the user
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found.")
            return False
        
        print(f"Found user: {user.fullname} (@{user.username})")
        print(f"User ID: {user.id}")
        print(f"Firebase UID: {user.firebase_uid}")
        
        # Delete related data first (due to foreign key constraints)
        # Note: With cascade="all, delete-orphan" in models, these should auto-delete
        
        # Delete the user
        db.delete(user)
        db.commit()
        
        print(f"✅ Successfully deleted user with email '{email}'")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting user: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    target_email = "anithamatharishw110@gmail.com"
    print(f"Deleting user with email: {target_email}")
    print("-" * 50)
    delete_user_by_email(target_email)

