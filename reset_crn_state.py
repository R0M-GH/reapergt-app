#!/usr/bin/env python3
"""
Script to manually reset a CRN's state to 'closed' in DynamoDB
This allows testing the notification system by forcing a state transition
"""

import boto3
import json
from datetime import datetime

def reset_crn_state(crn_to_reset):
    """Reset a CRN's state to closed in all user records"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('reapergt-dynamo-users')
    
    print(f"🔄 Resetting CRN {crn_to_reset} state to 'closed'...")
    
    try:
        # Scan all users
        response = table.scan()
        users_updated = 0
        
        for user_item in response.get('Items', []):
            user_id = user_item.get('user_id')
            crns_list = user_item.get('crns', [])
            
            # Check if this user has the CRN
            updated_crns = []
            needs_update = False
            
            for crn_data in crns_list:
                if crn_data.get('crn') == crn_to_reset:
                    # Reset this CRN's state to closed
                    crn_data.update({
                        'isOpen': False,
                        'seats_remaining': 0,
                        'last_checked': datetime.utcnow().isoformat(),
                        'state_reset': True,  # Mark that we manually reset this
                        'reset_timestamp': datetime.utcnow().isoformat()
                    })
                    needs_update = True
                    print(f"  📝 Found CRN {crn_to_reset} in user {user_id}")
                
                updated_crns.append(crn_data)
            
            # Update user if needed
            if needs_update:
                # Preserve all existing user data
                updated_item = {
                    'user_id': user_id,
                    'crns': updated_crns
                }
                
                # Preserve other fields
                for key, value in user_item.items():
                    if key not in ['user_id', 'crns']:
                        updated_item[key] = value
                
                table.put_item(Item=updated_item)
                users_updated += 1
                print(f"  ✅ Updated user {user_id}")
        
        print(f"\n🎉 Successfully reset CRN {crn_to_reset} state in {users_updated} user records")
        print(f"⏳ The scraper will detect this as 'opening' on the next check cycle")
        print(f"📱 This should trigger SMS notifications!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting CRN state: {e}")
        return False

def main():
    """Main function"""
    CRN_TO_RESET = "91575"  # The CRN we want to test
    
    print("🚀 Reaper Notification System - CRN State Reset Tool")
    print("=" * 60)
    print(f"Target CRN: {CRN_TO_RESET}")
    print(f"Action: Reset to 'closed' state")
    print(f"Purpose: Trigger notification on next scraper check")
    print("=" * 60)
    
    # Confirm action
    confirm = input(f"\n⚠️  Are you sure you want to reset CRN {CRN_TO_RESET} to closed? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Operation cancelled")
        return
    
    # Reset the CRN state
    success = reset_crn_state(CRN_TO_RESET)
    
    if success:
        print("\n📋 Next Steps:")
        print("1. Wait 15-30 seconds for the scraper to run")
        print("2. Check scraper logs for '🎉 Course X is now OPEN!' message")
        print("3. Check notifier logs for SMS sending activity")
        print("4. Check your phone for SMS notification")
        print("\n🔍 Monitor logs with:")
        print("aws logs tail /aws/lambda/reaper-ScraperFunction --follow")
        print("aws logs tail /aws/lambda/reaper-NotifierFunction --follow")
    else:
        print("\n❌ Failed to reset CRN state. Check AWS permissions and table name.")

if __name__ == "__main__":
    main() 