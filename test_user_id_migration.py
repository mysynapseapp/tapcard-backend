#!/usr/bin/env python3
"""
Comprehensive test suite for user ID migration system
Tests UUID uniqueness, data integrity, and migration process
"""

import os
import sys
import json
import uuid
import tempfile
import shutil
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Base, get_db
from models import User, SocialLink, PortfolioItem, WorkExperience, QRCode, Analytics
from migrate_user_ids import UserIDMigration

class TestUserIDMigration:
    def __init__(self):
        self.test_db_path = None
        self.test_engine = None
        self.SessionLocal = None
        
    def setup_test_database(self):
        """Create a test database with sample data"""
        # Create temporary database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        test_database_url = f"sqlite:///{self.test_db_path}"
        
        # Create test engine
        self.test_engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.test_engine)
        
        # Create session
        self.SessionLocal = sessionmaker(bind=self.test_engine)
        
        return self.SessionLocal
    
    def teardown_test_database(self):
        """Clean up test database"""
        if self.test_db_path and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def create_test_data(self):
        """Create sample test data"""
        session = self.SessionLocal()
        
        try:
            # Create test users
            users = []
            for i in range(3):
                user = User(
                    id=uuid.uuid4(),
                    username=f"testuser{i+1}",
                    email=f"test{i+1}@example.com",
                    password_hash="hashed_password",
                    bio=f"Test user {i+1}",
                    dob=datetime(1990, 1, i+1).date()
                )
                users.append(user)
                session.add(user)
            
            session.flush()  # Get IDs
            
            # Create related data for first user
            user = users[0]
            
            # Social links
            social_link = SocialLink(
                id=uuid.uuid4(),
                user_id=user.id,
                platform_name="github",
                link_url="https://github.com/testuser"
            )
            session.add(social_link)
            
            # Portfolio items
            portfolio_item = PortfolioItem(
                id=uuid.uuid4(),
                user_id=user.id,
                title="Test Project",
                description="A test project",
                media_url="https://example.com/project.jpg"
            )
            session.add(portfolio_item)
            
            # Work experience
            work_exp = WorkExperience(
                id=uuid.uuid4(),
                user_id=user.id,
                company_name="Test Company",
                role="Developer",
                start_date=datetime(2020, 1, 1).date(),
                end_date=datetime(2023, 12, 31).date(),
                description="Test work experience"
            )
            session.add(work_exp)
            
            # QR codes
            qr_code = QRCode(
                id=uuid.uuid4(),
                user_id=user.id,
                qr_code_url="https://example.com/qr.png",
                last_generated_at=datetime.utcnow()
            )
            session.add(qr_code)
            
            # Analytics
            analytics = Analytics(
                id=uuid.uuid4(),
                user_id=user.id,
                event_type="qr_scan",
                event_data='{"location": "test"}',
                created_at=datetime.utcnow()
            )
            session.add(analytics)
            
            session.commit()
            print("✅ Test data created successfully")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating test data: {e}")
            raise
        finally:
            session.close()
    
    def test_uuid_uniqueness(self):
        """Test that all user IDs are unique"""
        print("\n🧪 Testing UUID uniqueness...")
        
        session = self.SessionLocal()
        try:
            users = session.query(User).all()
            user_ids = [str(user.id) for user in users]
            
            # Check uniqueness
            unique_ids = set(user_ids)
            if len(user_ids) == len(unique_ids):
                print("✅ All user IDs are unique")
                return True
            else:
                duplicates = [id for id in user_ids if user_ids.count(id) > 1]
                print(f"❌ Duplicate IDs found: {duplicates}")
                return False
                
        finally:
            session.close()
    
    def test_uuid_format(self):
        """Test that all user IDs are valid UUIDs"""
        print("\n🧪 Testing UUID format...")
        
        session = self.SessionLocal()
        try:
            users = session.query(User).all()
            all_valid = True
            
            for user in users:
                try:
                    uuid.UUID(str(user.id))
                    print(f"✅ User {user.username}: {user.id} is valid UUID")
                except ValueError:
                    print(f"❌ User {user.username}: {user.id} is invalid UUID")
                    all_valid = False
            
            return all_valid
            
        finally:
            session.close()
    
    def test_foreign_key_integrity(self):
        """Test that all foreign key relationships are intact"""
        print("\n🧪 Testing foreign key integrity...")
        
        session = self.SessionLocal()
        try:
            users = session.query(User).all()
            all_integrity_ok = True
            
            for user in users:
                # Check social links
                social_links = session.query(SocialLink).filter_by(user_id=user.id).all()
                for link in social_links:
                    if str(link.user_id) != str(user.id):
                        print(f"❌ Social link {link.id} has wrong user_id")
                        all_integrity_ok = False
                
                # Check portfolio items
                portfolio_items = session.query(PortfolioItem).filter_by(user_id=user.id).all()
                for item in portfolio_items:
                    if str(item.user_id) != str(user.id):
                        print(f"❌ Portfolio item {item.id} has wrong user_id")
                        all_integrity_ok = False
                
                # Check work experiences
                work_exps = session.query(WorkExperience).filter_by(user_id=user.id).all()
                for exp in work_exps:
                    if str(exp.user_id) != str(user.id):
                        print(f"❌ Work experience {exp.id} has wrong user_id")
                        all_integrity_ok = False
            
            if all_integrity_ok:
                print("✅ All foreign key relationships are intact")
            
            return all_integrity_ok
            
        finally:
            session.close()
    
    def test_migration_process(self):
        """Test the complete migration process"""
        print("\n🧪 Testing migration process...")
        
        # Create migration instance with test database
        migration = UserIDMigration()
        migration.engine = self.test_engine
        migration.SessionLocal = self.SessionLocal
        
        try:
            # Run migration
            success = migration.run_migration()
            
            if success:
                print("✅ Migration process completed successfully")
                
                # Verify results
                validation_success = migration.validate_migration()
                if validation_success:
                    print("✅ Migration validation passed")
                else:
                    print("❌ Migration validation failed")
                
                return success and validation_success
            else:
                print("❌ Migration process failed")
                return False
                
        except Exception as e:
            print(f"❌ Migration test failed: {e}")
            return False
    
    def test_backup_creation(self):
        """Test backup creation functionality"""
        print("\n🧪 Testing backup creation...")
        
        migration = UserIDMigration()
        migration.engine = self.test_engine
        migration.SessionLocal = self.SessionLocal
        
        try:
            backup_dir = migration.backup_existing_data()
            
            # Check if backup file exists
            import glob
            backup_files = glob.glob(f"{backup_dir}/*.json")
            
            if backup_files:
                # Verify backup content
                with open(backup_files[0], 'r') as f:
                    backup_data = json.load(f)
                
                if 'users' in backup_data and len(backup_data['users']) > 0:
                    print("✅ Backup created successfully with user data")
                    return True
                else:
                    print("❌ Backup file is empty or invalid")
                    return False
            else:
                print("❌ No backup files created")
                return False
                
        except Exception as e:
            print(f"❌ Backup test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive user ID migration tests...\n")
        
        # Setup test environment
        self.setup_test_database()
        
        try:
            # Create test data
            self.create_test_data()
            
            # Run tests
            tests = [
                ("UUID Uniqueness", self.test_uuid_uniqueness),
                ("UUID Format", self.test_uuid_format),
                ("Foreign Key Integrity", self.test_foreign_key_integrity),
                ("Backup Creation", self.test_backup_creation),
                ("Migration Process", self.test_migration_process),
            ]
            
            results = {}
            for test_name, test_func in tests:
                print(f"\n{'='*50}")
                print(f"Running: {test_name}")
                print('='*50)
                results[test_name] = test_func()
            
            # Summary
            print("\n" + "="*60)
            print("📊 TEST SUMMARY")
            print("="*60)
            
            passed = 0
            total = len(results)
            
            for test_name, passed_test in results.items():
                status = "✅ PASS" if passed_test else "❌ FAIL"
                print(f"{test_name}: {status}")
                if passed_test:
                    passed += 1
            
            print(f"\n📈 Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed! The migration system is working correctly.")
            else:
                print("⚠️  Some tests failed. Please review the output above.")
            
            return passed == total
            
        finally:
            # Cleanup
            self.teardown_test_database()

if __name__ == "__main__":
    tester = TestUserIDMigration()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
