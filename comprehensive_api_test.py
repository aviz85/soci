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
    """Get a JWT token for authentication."""
    print(f"Authenticating as {username}...")
    url = f"{BASE_URL}/token/"
    
    try:
        response = requests.post(url, json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            print("✅ Authentication successful")
            return response.json()
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def test_user_endpoints(token):
    """Test user-related endpoints."""
    print("\n===== Testing User Endpoints =====")
    
    # Test /users/me/ endpoint
    url = f"{BASE_URL}/users/me/"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ Get current user")
            user_data = response.json()
            print(f"   Username: {user_data.get('username', 'Unknown')}")
        else:
            print("❌ Get current user")
            print(f"   Error: {response.status_code}")
            print(response.text)
            return None
        
        # Test preferences
        pref_url = f"{BASE_URL}/users/preferences/"
        pref_response = requests.get(pref_url, headers=headers)
        
        if pref_response.status_code == 200:
            print("✅ Get user preferences")
            prefs = pref_response.json()
            
            # Update preferences
            patch_data = {
                'theme': 'dark' if prefs.get('theme') == 'light' else 'light',
                'notification_settings': {
                    'email_notifications': True,
                    'push_notifications': True
                }
            }
            
            patch_response = requests.patch(pref_url, json=patch_data, headers=headers)
            
            if patch_response.status_code == 200:
                print("✅ Update user preferences")
            else:
                print("❌ Update user preferences")
                print(f"   Error: {patch_response.status_code}")
                print(patch_response.text)
        else:
            print("❌ Get user preferences")
            print(f"   Error: {pref_response.status_code}")
            print(pref_response.text)
        
        # Test mood boards
        mood_board_url = f"{BASE_URL}/users/mood-boards/"
        board_data = {
            'title': f'Test Mood Board {int(time.time())}',
            'description': 'A mood board created through the comprehensive API test'
        }
        
        board_response = requests.post(mood_board_url, json=board_data, headers=headers)
        
        if board_response.status_code == 201:
            print("✅ Create mood board")
            board = board_response.json()
            board_id = board['id']
            
            # Add item to mood board
            item_url = f"{BASE_URL}/users/mood-boards/{board_id}/items/"
            item_data = {
                'content_type': 'image',
                'source_url': 'https://example.com/image.jpg',
                'notes': 'Test mood board item'
            }
            
            item_response = requests.post(item_url, json=item_data, headers=headers)
            
            if item_response.status_code == 201:
                print("✅ Add item to mood board")
            else:
                print("❌ Add item to mood board")
                print(f"   Error: {item_response.status_code}")
                print(item_response.text)
        else:
            print("❌ Create mood board")
            print(f"   Error: {board_response.status_code}")
            print(board_response.text)
    
        return user_data
    except Exception as e:
        print(f"❌ Error in user endpoints test: {str(e)}")
        return None

def test_content_endpoints(token):
    """Test content-related endpoints."""
    print("\n===== Testing Content Endpoints =====")
    
    # Get posts
    url = f"{BASE_URL}/content/posts/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get posts")
        posts_data = response.json()
        post_count = len(posts_data.get('results', []))
        print(f"   Retrieved {post_count} posts")
    else:
        print("❌ Get posts")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Create a post
    post_data = {
        'title': f'Test Post {int(time.time())}',
        'body': 'This is a test post created through the comprehensive API test.',
        'visibility': 'public'
    }
    
    response = requests.post(url, json=post_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Create post")
        new_post = response.json()
        post_id = new_post['id']
        print(f"   Created post: {new_post['title']}")
        
        # Add a comment
        comment_url = f"{BASE_URL}/content/comments/"
        comment_data = {
            'content_type': 1,  # Content type ID for Post
            'object_id': post_id,
            'body': 'This is a test comment on my own post.',
            'parent': None
        }
        
        comment_response = requests.post(comment_url, json=comment_data, headers=headers)
        
        if comment_response.status_code == 201:
            print("✅ Add comment to post")
            comment = comment_response.json()
            print(f"   Added comment: {comment['body'][:30]}...")
        else:
            print("❌ Add comment to post")
            print(f"   Error: {comment_response.status_code}")
            print(comment_response.text)
        
        # React to the post
        react_url = f"{BASE_URL}/content/posts/{post_id}/react/"
        reaction_data = {
            'reaction_type': 'like'
        }
        
        reaction_response = requests.post(react_url, json=reaction_data, headers=headers)
        
        if reaction_response.status_code in [200, 201]:
            print("✅ React to post")
        else:
            print("❌ React to post")
            print(f"   Error: {reaction_response.status_code}")
            print(reaction_response.text)
    else:
        print("❌ Create post")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Get feed
    url = f"{BASE_URL}/content/feed/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get feed")
        feed_data = response.json()
        feed_count = len(feed_data.get('results', []))
        print(f"   Retrieved {feed_count} items from feed")
    else:
        print("❌ Get feed")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Get trending
    url = f"{BASE_URL}/content/trending/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get trending content")
        trending_data = response.json()
        trending_count = len(trending_data.get('results', []))
        print(f"   Retrieved {trending_count} trending items")
    else:
        print("❌ Get trending content")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Search content
    url = f"{BASE_URL}/content/search/?q=test"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Search content")
        search_data = response.json()
        search_count = len(search_data.get('results', []))
        print(f"   Found {search_count} items matching search")
    else:
        print("❌ Search content")
        print(f"   Error: {response.status_code}")
        print(response.text)

def test_community_endpoints(token, username):
    """Test community-related endpoints."""
    print("\n===== Testing Community Endpoints =====")
    
    # Get communities
    url = f"{BASE_URL}/communities/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get communities")
        communities_data = response.json()
        community_count = len(communities_data.get('results', []))
        print(f"   Retrieved {community_count} communities")
    else:
        print("❌ Get communities")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Create a community
    timestamp = int(time.time())
    community_data = {
        'name': f'Test Community {timestamp}',
        'slug': f'test-community-{timestamp}-{username}',  # Make slug unique per user
        'description': 'A community created through the comprehensive API test.',
        'visibility': 'public'
    }
    
    response = requests.post(url, json=community_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Create community")
        new_community = response.json()
        print(f"   Created community: {new_community['name']}")
    else:
        print("❌ Create community")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Discover communities
    url = f"{BASE_URL}/communities/discover/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Discover communities")
        discover_data = response.json()
        discover_count = len(discover_data.get('results', []))
        print(f"   Discovered {discover_count} communities")
        
        if discover_count > 0:
            # Join a community
            community_slug = discover_data['results'][0]['slug']
            join_url = f"{BASE_URL}/communities/{community_slug}/join/"
            
            join_response = requests.post(join_url, headers=headers)
            
            if join_response.status_code in [200, 201]:
                print("✅ Join community")
                
                # Leave the community
                leave_url = f"{BASE_URL}/communities/{community_slug}/leave/"
                leave_response = requests.post(leave_url, headers=headers)
                
                if leave_response.status_code in [200, 204]:
                    print("✅ Leave community")
                else:
                    print("❌ Leave community")
                    print(f"   Error: {leave_response.status_code}")
                    print(leave_response.text)
            else:
                print("❌ Join community")
                print(f"   Error: {join_response.status_code}")
                print(join_response.text)
    else:
        print("❌ Discover communities")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Get recommended communities
    url = f"{BASE_URL}/communities/recommended/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get recommended communities")
        recommended_data = response.json()
        recommended_count = len(recommended_data.get('results', []))
        print(f"   Retrieved {recommended_count} recommended communities")
    else:
        print("❌ Get recommended communities")
        print(f"   Error: {response.status_code}")
        print(response.text)

def test_interaction_endpoints(token, user_id):
    """Test interaction-related endpoints."""
    print("\n===== Testing Interaction Endpoints =====")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get conversations
    url = f"{BASE_URL}/interactions/conversations/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get conversations")
        conversations_data = response.json()
        conversation_count = len(conversations_data.get('results', []))
        print(f"   Retrieved {conversation_count} conversations")
        
        # Create a new conversation
        data = {
            'participants': [user_id, user_id + 1],  # Assuming user_id + 1 exists
            'is_group': False
        }
        
        create_response = requests.post(url, json=data, headers=headers)
        
        if create_response.status_code == 201:
            print("✅ Create conversation")
            new_conversation = create_response.json()
            conversation_id = new_conversation['id']
            print(f"   Created conversation with ID: {conversation_id}")
            
            # Send a message
            message_url = f"{BASE_URL}/interactions/conversations/{conversation_id}/messages/"
            message_data = {
                'body': 'Hello, this is a test message from the comprehensive API test.'
            }
            
            message_response = requests.post(message_url, json=message_data, headers=headers)
            
            if message_response.status_code == 201:
                print("✅ Send message")
                
                # Get messages
                messages_response = requests.get(message_url, headers=headers)
                
                if messages_response.status_code == 200:
                    print("✅ Get messages")
                    messages_data = messages_response.json()
                    message_count = len(messages_data.get('results', []))
                    print(f"   Retrieved {message_count} messages")
                else:
                    print("❌ Get messages")
                    print(f"   Error: {messages_response.status_code}")
                    print(messages_response.text)
                
                # Mark conversation as read
                read_url = f"{BASE_URL}/interactions/conversations/{conversation_id}/read/"
                read_response = requests.post(read_url, headers=headers)
                
                if read_response.status_code == 200:
                    print("✅ Mark conversation as read")
                else:
                    print("❌ Mark conversation as read")
                    print(f"   Error: {read_response.status_code}")
                    print(read_response.text)
            else:
                print("❌ Send message")
                print(f"   Error: {message_response.status_code}")
                print(message_response.text)
        else:
            print("❌ Create conversation")
            print(f"   Error: {create_response.status_code}")
            print(create_response.text)
    else:
        print("❌ Get conversations")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Get notifications
    url = f"{BASE_URL}/interactions/notifications/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Get notifications")
        notifications_data = response.json()
        notification_count = len(notifications_data.get('results', []))
        print(f"   Retrieved {notification_count} notifications")
        
        # Mark all notifications as read
        read_all_url = f"{BASE_URL}/interactions/notifications/read-all/"
        read_all_response = requests.post(read_all_url, headers=headers)
        
        if read_all_response.status_code == 200:
            print("✅ Mark all notifications as read")
        else:
            print("❌ Mark all notifications as read")
            print(f"   Error: {read_all_response.status_code}")
            print(read_all_response.text)
    else:
        print("❌ Get notifications")
        print(f"   Error: {response.status_code}")
        print(response.text)
    
    # Test following/unfollowing
    # Follow a user
    follow_url = f"{BASE_URL}/interactions/follow/{user_id + 2}/"  # Assuming user_id + 2 exists
    follow_response = requests.post(follow_url, headers=headers)
    
    if follow_response.status_code in [200, 201]:
        print("✅ Follow user")
        
        # Unfollow the user
        unfollow_url = f"{BASE_URL}/interactions/unfollow/{user_id + 2}/"
        unfollow_response = requests.post(unfollow_url, headers=headers)
        
        if unfollow_response.status_code in [200, 204]:
            print("✅ Unfollow user")
        else:
            print("❌ Unfollow user")
            print(f"   Error: {unfollow_response.status_code}")
            print(unfollow_response.text)
    else:
        print("❌ Follow user")
        print(f"   Error: {follow_response.status_code}")
        print(follow_response.text)

def run_comprehensive_test():
    """Run all tests in sequence."""
    print("\n================================================")
    print("   SociSphere Comprehensive API Test")
    print("================================================")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing against: {BASE_URL}")
    print("------------------------------------------------")
    
    # Use both regular user and admin user
    users = [
        ('user1', 'password123'),
        ('admin', 'adminpassword')
    ]
    
    success_count = 0
    total_tests = len(users)
    
    for username, password in users:
        print(f"\n\n========== Testing as user: {username} ==========")
        
        # Get token
        token_data = get_token(username, password)
        
        if token_data:
            token = token_data['access']
            
            # Run user tests
            user_data = test_user_endpoints(token)
            
            # Run content tests
            test_content_endpoints(token)
            
            # Run community tests
            test_community_endpoints(token, username)
            
            # Run interaction tests
            if user_data and 'id' in user_data:
                user_id = user_data['id']
                print(f"\nUser ID: {user_id}")
                test_interaction_endpoints(token, user_id)
                success_count += 1
            else:
                print("\n❌ Skipping interaction tests due to missing user data")
        else:
            print(f"❌ Authentication failed for user: {username}")
            continue
    
    print("\n\n================================================")
    print("   Comprehensive API Test Results")
    print("================================================")
    print(f"Tests completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Success rate: {success_count}/{total_tests} users ({success_count/total_tests*100:.1f}%)")
    print("================================================")

# Add to end of file
if __name__ == '__main__':
    run_comprehensive_test() 