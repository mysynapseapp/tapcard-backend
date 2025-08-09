#!/usr/bin/env python3
"""
Test script to verify UUID fix works correctly
"""

import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import SessionLocal
from models import SocialLink

def test_social_links_uuid():
    """Test social links functionality after UUID fix"""
    
    print("🧪 Testing social links UUID functionality...")
    
    with SessionLocal() as db:
        try:
            # Test 1: Check current schema
            print("📊 Checking current schema...")
            result = db.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'social_links'
                ORDER BY ordinal_position;
            """))
            
            schema_info = []
            for row in result:
                schema_info.append(f"{row.column_name}: {row.data_type}")
                print(f"  {row.column_name}: {row.data_type} ({row.is_nullable})")
            
            # Test 2: Create a test social link
            print("🔨 Creating test social link...")
            test_user_id = uuid.UUID('35b2aea2-4251-4d29-b7e5-d3b1a70573b6')
            
            test_link = SocialLink(
                user_id=test_user_id,
                platform_name="YouTube",
                link_url="https://youtube.com/@testchannel"
            )
            
            db.add(test_link)
            db.commit()
            db.refresh(test_link)
            
            print(f"✅ Created test link with ID: {test_link.id}")
            print(f"   Type of ID: {type(test_link.id)}")
            
            # Test 3: Query the link by UUID
            print("🔍 Testing query by UUID...")
            retrieved_link = db.query(SocialLink).filter(
                SocialLink.id == test_link.id
            ).first()
            
            if retrieved_link:
                print(f"✅ Successfully retrieved link: {retrieved_link.id}")
                print(f"   Platform: {retrieved_link.platform_name}")
                print(f"   URL: {retrieved_link.link_url}")
            else:
                print("❌ Failed to retrieve link")
                
            # Test 4: Update the link
            print("✏️ Testing update functionality...")
            retrieved_link.link_url = "https://youtube.com/@updatedchannel"
            db.commit()
            
            updated_link = db.query(SocialLink).filter(
                SocialLink.id == test_link.id
            ).first()
            
            if updated_link and updated_link.link_url == "https://youtube.com/@updatedchannel":
                print("✅ Successfully updated link")
            else:
                print("❌ Failed to update link")
                
            # Test 5: Query by string UUID
            print("🔗 Testing query by string UUID...")
            string_id = str(test_link.id)
            string_query = db.query(SocialLink).filter(
                SocialLink.id == uuid.UUID(string_id)
            ).first()
            
            if string_query:
                print("✅ String UUID query works correctly")
            else:
                print("❌ String UUID query failed")
                
            # Clean up
            db.delete(test_link)
            db.commit()
            print("🧹 Cleaned up test data")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Test failed: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Starting UUID functionality tests...")
    
    success = test_social_links_uuid()
    
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed")
        sys.exit(1)
