#!/usr/bin/env python3
"""
Simple runner script for user ID migration
"""

import os
import sys
from migrate_user_ids import UserIDMigration

if __name__ == "__main__":
    print("🚀 Starting User ID Migration...")
    
    # Check if we're in the right directory
    if not os.path.exists('migrate_user_ids.py'):
        print("❌ Please run this script from the tapcard-backend directory")
        sys.exit(1)
    
    migration = UserIDMigration()
    success = migration.run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review the backup files created")
        print("2. Test your application to ensure everything works")
        print("3. Update your deployment scripts if needed")
    else:
        print("❌ Migration failed - check the logs above")
        sys.exit(1)
