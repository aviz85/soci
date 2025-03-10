#!/usr/bin/env python
"""
SociSphere API Test

This script tests the key functionality of the SociSphere API.
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = 'http://localhost:8080/api'

def test_api():
    """Test the SociSphere API."""
    print("SociSphere API Test")
    print("-----------------")
    
    # Get token for user1
    token = get_token('user1', 'password123')
    if not token:
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Get user info
    user_data = get_user_info(token)
    if not user_data:
        print("❌ Failed to get user info")
        return
    
    print(f"✅ Got user info for: {user_data['username']}")
    
    # Test content endpoints
    test_content(token)
    
    # Test community endpoints
    test_communities(token)
    
    # Test interaction endpoints
    test_interactions(token, user_data['id'])
    
    print("\nAPI Test Complete!")

def get_token(username, password):
    """Get JWT token for authentication."""
    url = f"{BASE_URL}/token/"
    response = requests.post(url, json={
        'username': username,
        'password': password
    })
    
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

def get_user_info(token):
    """Get current user info."""
    url = f"{BASE_URL}/users/me/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get user info: {response.status_code}")
        print(response.text)
        return None

def test_content(token):
    """Test content-related endpoints."""
    print("\n--- Testing Content ---")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get posts
    response = requests.get(f"{BASE_URL}/content/posts/", headers=headers)
    if response.status_code == 200:
        print(f"✅ Got posts: {len(response.json()['results'])}")
    else:
        print(f"❌ Failed to get posts: {response.status_code}")
    
    # Create post
    post_data = {
        'title': f'Test Post {int(time.time())}',
        'body': 'This is a test post.',
        'visibility': 'public'
    }
    
    response = requests.post(f"{BASE_URL}/content/posts/", json=post_data, headers=headers)
    if response.status_code == 201:
        post_id = response.json()['id']
        print(f"✅ Created post: {post_id}")
        
        # Add comment
        comment_data = {
            'content_type': 1,  # Content type ID for Post
            'object_id': post_id,
            'body': 'This is a test comment.',
            'parent': None
        }
        
        response = requests.post(f"{BASE_URL}/content/comments/", json=comment_data, headers=headers)
        if response.status_code == 201:
            print("✅ Added comment")
        else:
            print(f"❌ Failed to add comment: {response.status_code}")
        
        # React to post
        reaction_data = {'reaction_type': 'like'}
        response = requests.post(f"{BASE_URL}/content/posts/{post_id}/react/", json=reaction_data, headers=headers)
        if response.status_code in [200, 201]:
            print("✅ Added reaction")
        else:
            print(f"❌ Failed to add reaction: {response.status_code}")
    else:
        print(f"❌ Failed to create post: {response.status_code}")
    
    # Get feed
    response = requests.get(f"{BASE_URL}/content/feed/", headers=headers)
    if response.status_code == 200:
        print(f"✅ Got feed: {len(response.json()['results'])}")
    else:
        print(f"❌ Failed to get feed: {response.status_code}")
    
    # Search content
    response = requests.get(f"{BASE_URL}/content/search/?q=test", headers=headers)
    if response.status_code == 200:
        print(f"✅ Searched content: {len(response.json()['results'])}")
    else:
        print(f"❌ Failed to search content: {response.status_code}")

def test_communities(token):
    """Test community-related endpoints."""
    print("\n--- Testing Communities ---")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get communities
    response = requests.get(f"{BASE_URL}/communities/", headers=headers)
    if response.status_code == 200:
        print(f"✅ Got communities: {len(response.json()['results'])}")
    else:
        print(f"❌ Failed to get communities: {response.status_code}")
    
    # Create community
    timestamp = int(time.time())
    community_data = {
        'name': f'Test Community {timestamp}',
        'slug': f'test-community-{timestamp}',
        'description': 'This is a test community.',
        'visibility': 'public'
    }
    
    response = requests.post(f"{BASE_URL}/communities/", json=community_data, headers=headers)
    if response.status_code == 201:
        print(f"✅ Created community: {response.json()['name']}")
    else:
        print(f"❌ Failed to create community: {response.status_code}")
    
    # Discover communities
    response = requests.get(f"{BASE_URL}/communities/discover/", headers=headers)
    if response.status_code == 200:
        communities = response.json()['results']
        print(f"✅ Discovered communities: {len(communities)}")
        
        if communities:
            # Join community
            community_slug = communities[0]['slug']
            response = requests.post(f"{BASE_URL}/communities/{community_slug}/join/", headers=headers)
            if response.status_code in [200, 201]:
                print(f"✅ Joined community: {community_slug}")
                
                # Leave community
                response = requests.post(f"{BASE_URL}/communities/{community_slug}/leave/", headers=headers)
                if response.status_code in [200, 204]:
                    print(f"✅ Left community: {community_slug}")
                else:
                    print(f"❌ Failed to leave community: {response.status_code}")
            else:
                print(f"❌ Failed to join community: {response.status_code}")
    else:
        print(f"❌ Failed to discover communities: {response.status_code}")

def test_interactions(token, user_id):
    """Test interaction-related endpoints."""
    print("\n--- Testing Interactions ---")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get conversations
    response = requests.get(f"{BASE_URL}/interactions/conversations/", headers=headers)
    if response.status_code == 200:
        print(f"✅ Got conversations: {len(response.json()['results'])}")
    else:
        print(f"❌ Failed to get conversations: {response.status_code}")
    
    # Create conversation
    conversation_data = {
        'participants': [user_id, user_id + 1],  # Assuming user_id + 1 exists
        'is_group': False
    }
    
    response = requests.post(f"{BASE_URL}/interactions/conversations/", json=conversation_data, headers=headers)
    if response.status_code == 201:
        conversation_id = response.json()['id']
        print(f"✅ Created conversation: {conversation_id}")
        
        # Send message
        message_data = {'body': 'This is a test message.'}
        response = requests.post(f"{BASE_URL}/interactions/conversations/{conversation_id}/messages/", json=message_data, headers=headers)
        if response.status_code == 201:
            print("✅ Sent message")
            
            # Mark conversation as read
            response = requests.post(f"{BASE_URL}/interactions/conversations/{conversation_id}/read/", headers=headers)
            if response.status_code == 200:
                print("✅ Marked conversation as read")
            else:
                print(f"❌ Failed to mark conversation as read: {response.status_code}")
        else:
            print(f"❌ Failed to send message: {response.status_code}")
    else:
        print(f"❌ Failed to create conversation: {response.status_code}")
    
    # Get notifications
    response = requests.get(f"{BASE_URL}/interactions/notifications/", headers=headers)
    if response.status_code == 200:
        print(f"✅ Got notifications: {len(response.json()['results'])}")
        
        # Mark all notifications as read
        response = requests.post(f"{BASE_URL}/interactions/notifications/read-all/", headers=headers)
        if response.status_code == 200:
            print("✅ Marked all notifications as read")
        else:
            print(f"❌ Failed to mark all notifications as read: {response.status_code}")
    else:
        print(f"❌ Failed to get notifications: {response.status_code}")
    
    # Follow user
    target_user_id = user_id + 2  # Assuming user_id + 2 exists
    response = requests.post(f"{BASE_URL}/interactions/follow/{target_user_id}/", headers=headers)
    if response.status_code in [200, 201]:
        print(f"✅ Followed user: {target_user_id}")
        
        # Unfollow user
        response = requests.post(f"{BASE_URL}/interactions/unfollow/{target_user_id}/", headers=headers)
        if response.status_code in [200, 204]:
            print(f"✅ Unfollowed user: {target_user_id}")
        else:
            print(f"❌ Failed to unfollow user: {response.status_code}")
    else:
        print(f"❌ Failed to follow user: {response.status_code}")

if __name__ == '__main__':
    test_api() 