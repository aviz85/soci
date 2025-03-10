#!/usr/bin/env python
#!/usr/bin/env python
"""
SociSphere Comprehensive API Test

This script performs a comprehensive test of the SociSphere API,
testing various endpoints and functionality.
"""

import requests
import json
import time
from pprint import pprint
from datetime import datetime

# API base URL
BASE_URL = 'http://localhost:8080/api'

def get_token(username, password):
    """Get JWT token for authentication."""
    url = f"{BASE_URL}/token/"
    response = requests.post(url, json={
        'username': username,
        'password': password
    })
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

def test_user_endpoints(token):
    """Test user-related endpoints."""
    print("\n===== Testing User Endpoints =====")
    
    # Get current user
    url = f"{BASE_URL}/users/me/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    user_data = None
    
    if response.status_code == 200:
        print("✅ Current user endpoint")
        user_data = response.json()
        print(f"   Username: {user_data['username']}")
    else:
        print("❌ Current user endpoint")
        print(f"   Error: {response.status_code}")
        print(response.text)
        return None
    
    # Get user preferences
    url = f"{BASE_URL}/users/preferences/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ User preferences endpoint")
        prefs_data = response.json()
        if prefs_data.get('results') and len(prefs_data['results']) > 0:
            pref_id = prefs_data['results'][0]['id']
            
            # Update user preferences
            update_url = f"{BASE_URL}/users/preferences/{pref_id}/"
            update_data = {
                'daily_usage_limit': 120,
                'content_sensitivity': 'low'
            }
            
            update_response = requests.patch(update_url, json=update_data, headers=headers)
            
            if update_response.status_code == 200:
                print("✅ Update user preferences")
                updated_prefs = update_response.json()
                print(f"   Updated daily usage limit: {updated_prefs['daily_usage_limit']}")
            else:
                print("❌ Update user preferences")
                print(f"   Error: {update_response.status_code}")
                print(update_response.text)
    else:
        print("❌ User preferences endpoint")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Test mood boards
    url = f"{BASE_URL}/users/mood-boards/"
    mood_board_data = {
        'title': f'Test Mood Board {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'description': 'A mood board created through API testing',
        'is_current': True
    }
    
    response = requests.post(url, json=mood_board_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Create mood board")
        board_data = response.json()
        board_id = board_data['id']
        print(f"   Created mood board: {board_data['title']}")
        
        # Add item to mood board
        items_url = f"{BASE_URL}/users/mood-boards/{board_id}/items/"
        item_data = {
            'text': 'Feeling creative today!',
            'position_x': 10,
            'position_y': 20
        }
        
        item_response = requests.post(items_url, json=item_data, headers=headers)
        
        if item_response.status_code == 201:
            print("✅ Add mood board item")
            item = item_response.json()
            print(f"   Added item: {item['text']}")
        else:
            print("❌ Add mood board item")
            print(f"   Error: {item_response.status_code}")
            print(item_response.text)
    else:
        print("❌ Create mood board")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    return user_data 