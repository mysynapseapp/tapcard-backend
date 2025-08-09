#!/usr/bin/env python3
"""
Quick script to run the UUID type fix
"""

import subprocess
import sys
import os

def run_fix():
    """Run the UUID type fix"""
    print("Running UUID type fix for social_links table...")
    
    # Change to tapcard-backend directory
    os.chdir('tapcard-backend')
    
    try:
        # Run the migration script
        result = subprocess.run([
            sys.executable, 'migrate_social_links_uuid.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ UUID fix completed successfully!")
            print(result.stdout)
        else:
            print("❌ UUID fix failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"Error running fix: {str(e)}")

if __name__ == "__main__":
    run_fix()
