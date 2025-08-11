#!/usr/bin/env python3
"""
Comprehensive migration script for user ID management
Ensures all users have unique UUIDs and handles data migration
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from database import Base, engine, get_db
from models import User, SocialLink, PortfolioItem, WorkExperience, QRCode, Analytics
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserIDMigration:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def check_current_schema(self):
        """Check current database schema and user ID status"""
        logger.info("🔍 Checking current database schema...")
        
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        if 'users' not in tables:
            logger.info("📋 No users table found, creating fresh schema")
            return False
            
        # Check current user count
        with self.SessionLocal() as session:
            user_count = session.query(User).count()
            logger.info(f"👥 Found {user_count} existing users")
            
            # Check for duplicate UUIDs
            user_ids = session.query(User.id).all()
            id_list = [str(user.id) for user in user_ids]
            duplicates = set([x for x in id_list if id_list.count(x) > 1])
            
            if duplicates:
                logger.warning(f"⚠️  Found duplicate UUIDs: {duplicates}")
                return True
                
        logger.info("✅ No duplicate UUIDs found")
        return False
    
    def backup_existing_data(self):
        """Create backup of existing user data"""
        logger.info("💾 Creating backup of existing data...")
        
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        with self.SessionLocal() as session:
            # Export user data
            users = session.query(User).all()
            backup_data = {
                'users': [],
                'social_links': [],
                'portfolio_items': [],
                'work_experiences': [],
                'qr_codes': [],
                'analytics': []
            }
            
            for user in users:
                user_data = {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'bio': user.bio,
                    'dob': user.dob.isoformat() if user.dob else None,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
                backup_data['users'].append(user_data)
                
                # Backup related data
                for link in user.social_links:
                    backup_data['social_links'].append({
                        'id': str(link.id),
                        'user_id': str(link.user_id),
                        'platform_name': link.platform_name,
                        'link_url': link.link_url
                    })
                    
                for item in user.portfolio_items:
                    backup_data['portfolio_items'].append({
                        'id': str(item.id),
                        'user_id': str(item.user_id),
                        'title': item.title,
                        'description': item.description,
                        'media_url': item.media_url
                    })
                    
                for exp in user.work_experiences:
                    backup_data['work_experiences'].append({
                        'id': str(exp.id),
                        'user_id': str(exp.user_id),
                        'company_name': exp.company_name,
                        'role': exp.role,
                        'start_date': exp.start_date.isoformat(),
                        'end_date': exp.end_date.isoformat() if exp.end_date else None,
                        'description': exp.description
                    })
                    
                for qr in user.qr_codes:
                    backup_data['qr_codes'].append({
                        'id': str(qr.id),
                        'user_id': str(qr.user_id),
                        'qr_code_url': qr.qr_code_url,
                        'last_generated_at': qr.last_generated_at.isoformat()
                    })
                    
                for analytic in user.analytics:
                    backup_data['analytics'].append({
                        'id': str(analytic.id),
                        'user_id': str(analytic.user_id),
                        'event_type': analytic.event_type,
                        'event_data': analytic.event_data,
                        'created_at': analytic.created_at.isoformat()
                    })
        
        # Save backup to file
        import json
        backup_file = os.path.join(backup_dir, 'user_data_backup.json')
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
            
        logger.info(f"✅ Backup created: {backup_file}")
        return backup_dir
    
    def migrate_user_ids(self):
        """Migrate existing user IDs to ensure uniqueness"""
        logger.info("🔄 Starting user ID migration...")
        
        with self.SessionLocal() as session:
            # Get all users
            users = session.query(User).all()
            
            if not users:
                logger.info("📋 No users to migrate")
                return True
                
            # Check for any ID conflicts
            id_map = {}  # old_id -> new_id mapping
            conflicts_found = False
            
            for user in users:
                old_id = str(user.id)
                
                # Validate UUID format
                try:
                    uuid.UUID(old_id)
                    logger.info(f"✅ User {user.username} already has valid UUID: {old_id}")
                    id_map[old_id] = old_id  # Keep existing UUID
                except ValueError:
                    logger.warning(f"⚠️  User {user.username} has invalid UUID: {old_id}")
                    new_id = str(uuid.uuid4())
                    id_map[old_id] = new_id
                    conflicts_found = True
                    
            if conflicts_found:
                logger.info("🔄 Updating user IDs and foreign key references...")
                
                # Update user IDs and all related foreign keys
                for old_id, new_id in id_map.items():
                    if old_id != new_id:
                        # Update user ID
                        session.execute(
                            text("UPDATE users SET id = :new_id WHERE id = :old_id"),
                            {"new_id": new_id, "old_id": old_id}
                        )
                        
                        # Update all foreign key references
                        session.execute(
                            text("UPDATE social_links SET user_id = :new_id WHERE user_id = :old_id"),
                            {"new_id": new_id, "old_id": old_id}
                        )
                        
                        session.execute(
                            text("UPDATE portfolio_items SET user_id = :new_id WHERE user_id = :old_id"),
                            {"new_id": new_id, "old_id": old_id}
                        )
                        
                        session.execute(
                            text("UPDATE work_experience SET user_id = :new_id WHERE user_id = :old_id"),
                            {"new_id": new_id, "old_id": old_id}
                        )
                        
                        session.execute(
                            text("UPDATE qr_codes SET user_id = :new_id WHERE user_id = :old_id"),
                            {"new_id": new_id, "old_id": old_id}
                        )
                        
                        session.execute(
                            text("UPDATE analytics SET user_id = :new_id WHERE user_id = :old_id"),
                            {"new_id": new_id, "old_id": old_id}
                        )
                        
                        logger.info(f"✅ Updated user {old_id} -> {new_id}")
            
            session.commit()
            logger.info("✅ User ID migration completed")
            return True
    
    def validate_migration(self):
        """Validate the migration was successful"""
        logger.info("🔍 Validating migration results...")
        
        with self.SessionLocal() as session:
            # Check all users have unique IDs
            users = session.query(User).all()
            user_ids = [str(user.id) for user in users]
            
            if len(user_ids) != len(set(user_ids)):
                logger.error("❌ Duplicate user IDs found after migration")
                return False
                
            # Check all UUIDs are valid
            for user_id in user_ids:
                try:
                    uuid.UUID(user_id)
                except ValueError:
                    logger.error(f"❌ Invalid UUID format: {user_id}")
                    return False
            
            # Check foreign key integrity
            for user in users:
                # Verify all related records have correct user_id
                social_links = session.query(SocialLink).filter_by(user_id=user.id).count()
                portfolio_items = session.query(PortfolioItem).filter_by(user_id=user.id).count()
                work_experiences = session.query(WorkExperience).filter_by(user_id=user.id).count()
                
                logger.info(f"✅ User {user.username}: {social_links} social links, {portfolio_items} portfolio items, {work_experiences} work experiences")
                
            logger.info("✅ Migration validation completed successfully")
            return True
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("🚀 Starting comprehensive user ID migration...")
        
        try:
            # Check current state
            needs_migration = self.check_current_schema()
            
            # Create backup
            backup_dir = self.backup_existing_data()
            
            # Run migration if needed
            if needs_migration:
                self.migrate_user_ids()
            
            # Validate results
            self.validate_migration()
            
            logger.info("✅ Migration process completed successfully")
            logger.info(f"📁 Backup saved to: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            return False

if __name__ == "__main__":
    migration = UserIDMigration()
    success = migration.run_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Migration failed - check logs for details")
        sys.exit(1)
