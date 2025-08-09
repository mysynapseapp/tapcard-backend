#!/usr/bin/env python3
"""
Database testing script for tapcard backend
Tests database connection, schema, and data integrity
"""

from sqlalchemy import text
from database import engine
from models import Base, User, SocialLink, WorkExperience, PortfolioItem
from sqlalchemy.orm import Session
import uuid

class DatabaseTester:
    def __init__(self):
        self.engine = engine
        
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Print test results with consistent formatting"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text('SELECT 1'))
                return result.fetchone()[0] == 1
        except Exception as e:
            self.print_result("Database Connection", False, str(e))
            return False
            
    def test_tables_exist(self) -> bool:
        """Test if all required tables exist"""
        try:
            with self.engine.connect() as conn:
                # Check for all required tables
                required_tables = ['users', 'social_links', 'work_experience', 'portfolio_items']
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                existing_tables = [row[0] for row in result.fetchall()]
                
                missing_tables = [table for table in required_tables if table not in existing_tables]
                if missing_tables:
                    self.print_result("Tables Exist", False, f"Missing tables: {missing_tables}")
                    return False
                    
                self.print_result("Tables Exist", True, f"All required tables found: {required_tables}")
                return True
        except Exception as e:
            self.print_result("Tables Exist", False, str(e))
            return False
            
    def test_uuid_columns(self) -> bool:
        """Test if UUID columns are properly configured"""
        try:
            with self.engine.connect() as conn:
                # Check UUID columns in users table
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'id'
                """))
                column_info = result.fetchone()
                
                if column_info and 'uuid' in str(column_info[1]).lower():
                    self.print_result("UUID Columns", True, "UUID columns properly configured")
                    return True
                else:
                    self.print_result("UUID Columns", False, f"UUID column type: {column_info[1] if column_info else 'Not found'}")
                    return False
        except Exception as e:
            self.print_result("UUID Columns", False, str(e))
            return False
            
    def test_test_user_exists(self) -> bool:
        """Test if test user exists"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, email, username, full_name 
                    FROM users 
                    WHERE email = 'curltest@example.com'
                """))
                user = result.fetchone()
                
                if user:
                    self.print_result("Test User", True, f"Found: ID={user[0]}, Username={user[2]}, Name={user[3]}")
                    return True
                else:
                    self.print_result("Test User", False, "Test user not found in database")
                    return False
        except Exception as e:
            self.print_result("Test User", False, str(e))
            return False
            
    def test_foreign_keys(self) -> bool:
        """Test foreign key relationships"""
        try:
            with self.engine.connect() as conn:
                # Check if social_links has proper foreign key to users
                result = conn.execute(text("""
                    SELECT 
                        tc.constraint_name, 
                        tc.table_name, 
                        kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name 
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'social_links'
                """))
                fk_info = result.fetchall()
                
                if fk_info:
                    self.print_result("Foreign Keys", True, f"Found {len(fk_info)} foreign key constraints")
                    return True
                else:
                    self.print_result("Foreign Keys", False, "No foreign key constraints found")
                    return False
        except Exception as e:
            self.print_result("Foreign Keys", False, str(e))
            return False
            
    def test_data_integrity(self) -> bool:
        """Test data integrity and relationships"""
        try:
            with self.engine.connect() as conn:
                # Check for orphaned social links
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM social_links sl 
                    LEFT JOIN users u ON sl.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_links = result.fetchone()[0]
                
                if orphaned_links > 0:
                    self.print_result("Data Integrity", False, f"Found {orphaned_links} orphaned social links")
                    return False
                    
                # Check for orphaned work experiences
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM work_experience we 
                    LEFT JOIN users u ON we.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_experiences = result.fetchone()[0]
                
                if orphaned_experiences > 0:
                    self.print_result("Data Integrity", False, f"Found {orphaned_experiences} orphaned work experiences")
                    return False
                    
                self.print_result("Data Integrity", True, "No orphaned records found")
                return True
        except Exception as e:
            self.print_result("Data Integrity", False, str(e))
            return False
            
    def test_column_types(self) -> bool:
        """Test column data types"""
        try:
            with self.engine.connect() as conn:
                # Check users table columns
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                expected_columns = {
                    'id': 'uuid',
                    'email': 'character varying',
                    'username': 'character varying',
                    'password_hash': 'character varying',
                    'full_name': 'character varying',
                    'bio': 'character varying',
                    'dob': 'date',
                    'created_at': 'timestamp without time zone',
                    'updated_at': 'timestamp without time zone'
                }
                
                found_columns = {col[0]: col[1] for col in columns}
                
                mismatches = []
                for col, expected_type in expected_columns.items():
                    if col in found_columns and expected_type not in found_columns[col].lower():
                        mismatches.append(f"{col}: expected {expected_type}, got {found_columns[col]}")
                
                if mismatches:
                    self.print_result("Column Types", False, f"Type mismatches: {mismatches}")
                    return False
                else:
                    self.print_result("Column Types", True, "All column types are correct")
                    return True
        except Exception as e:
            self.print_result("Column Types", False, str(e))
            return False
            
    def run_all_tests(self):
        """Run all database tests"""
        print("🗄️  Starting Database Tests")
        print("=" * 50)
        
        tests = [
            self.test_connection,
            self.test_tables_exist,
            self.test_uuid_columns,
            self.test_test_user_exists,
            self.test_foreign_keys,
            self.test_data_integrity,
            self.test_column_types
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
                
        print("=" * 50)
        print(f"📊 Database Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All database tests passed! The database is properly configured.")
        else:
            print("⚠️  Some database tests failed. Check the details above.")

if __name__ == "__main__":
    tester = DatabaseTester()
    tester.run_all_tests()
