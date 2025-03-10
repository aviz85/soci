#!/usr/bin/env python
"""
SociSphere API Test Client

This script demonstrates how to interact with the SociSphere API using Python requests.
It performs basic operations like authentication, user creation, and post creation.
"""

import requests
import json
from pprint import pprint
import time

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

def register_user(username, email, password):
    """Register a new user."""
    url = f"{BASE_URL}/users/register/"
    data = {
        'username': username,
        'email': email,
        'password': password,
        'password_confirm': password,
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 201:
        print("User registered successfully!")
        return response.json()
    else:
        print(f"Registration failed: {response.status_code}")
        print(response.text)
        return None

def get_current_user(token):
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

def create_post(token, title, body):
    """Create a new post."""
    url = f"{BASE_URL}/content/posts/"
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        'title': title,
        'body': body,
        'visibility': 'public'
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        print("Post created successfully!")
        return response.json()
    else:
        print(f"Post creation failed: {response.status_code}")
        print(response.text)
        return None

def get_posts(token, page=1):
    """Get posts from API."""
    url = f"{BASE_URL}/content/posts/?page={page}"
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Requesting posts from: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get posts: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text[:500]}")  # Print first 500 chars of response
        return None

def get_feed(token):
    """Get user's feed."""
    url = f"{BASE_URL}/content/feed/"
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Requesting feed from: {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get feed: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text[:500]}")  # Print first 500 chars of response
        return None

def discover_communities(token):
    """Discover communities."""
    url = f"{BASE_URL}/communities/discover/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to discover communities: {response.status_code}")
        print(response.text)
        return None

def get_communities(token):
    """Get list of communities."""
    url = f"{BASE_URL}/communities/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get communities: {response.status_code}")
        print(response.text)
        return None

def create_community(token, name, description):
    """Create a new community."""
    url = f"{BASE_URL}/communities/"
    headers = {'Authorization': f'Bearer {token}'}
    
    # Generate a unique slug using timestamp
    timestamp = int(time.time())
    slug = f"{name.lower().replace(' ', '-')}-{timestamp}"
    
    data = {
        'name': name,
        'slug': slug,
        'description': description,
        'visibility': 'public'
    }
    
    print(f"Creating community with slug: {slug}")
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        print("Community created successfully!")
        return response.json()
    else:
        print(f"Community creation failed: {response.status_code}")
        print(response.text)
        return None

def get_conversations(token):
    """Get user's conversations."""
    url = f"{BASE_URL}/interactions/conversations/"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get conversations: {response.status_code}")
        print(response.text)
        return None

def run_full_test_suite(token):
    """Run a comprehensive test of all main API endpoints."""
    results = {}
    
    # 1. Get user profile
    print("\n----- Testing User Profile -----")
    user = get_current_user(token)
    if user:
        print(f"✅ User profile retrieved for: {user.get('username')}")
        results['user_profile'] = 'PASS'
    else:
        print("❌ Failed to get user profile")
        results['user_profile'] = 'FAIL'
    
    # 2. Get posts
    print("\n----- Testing Posts Endpoint -----")
    posts = get_posts(token)
    if posts and 'results' in posts:
        print(f"✅ Retrieved {len(posts['results'])} posts")
        results['posts'] = 'PASS'
    else:
        print("❌ Failed to get posts")
        results['posts'] = 'FAIL'
    
    # 3. Create a post
    print("\n----- Testing Post Creation -----")
    post = create_post(token, 'API Test Post', 'This post was created through the API test client.')
    if post:
        print(f"✅ Created post with ID: {post.get('id')}")
        results['create_post'] = 'PASS'
    else:
        print("❌ Failed to create post")
        results['create_post'] = 'FAIL'
    
    # 4. Get feed
    print("\n----- Testing Feed Endpoint -----")
    feed = get_feed(token)
    if feed and 'results' in feed:
        print(f"✅ Retrieved feed with {len(feed['results'])} items")
        results['feed'] = 'PASS'
    else:
        print("❌ Failed to get feed")
        results['feed'] = 'FAIL'
    
    # 5. Get communities
    print("\n----- Testing Communities Endpoint -----")
    communities = get_communities(token)
    if communities and 'results' in communities:
        print(f"✅ Retrieved {len(communities['results'])} communities")
        results['communities'] = 'PASS'
    else:
        print("❌ Failed to get communities")
        results['communities'] = 'FAIL'
    
    # 6. Create a community (if there are fewer than 15)
    if communities and len(communities.get('results', [])) < 15:
        print("\n----- Testing Community Creation -----")
        community = create_community(token, f'API Test Community {user["username"]}', 'This community was created through the API test client.')
        if community:
            print(f"✅ Created community: {community.get('name')}")
            results['create_community'] = 'PASS'
        else:
            print("❌ Failed to create community")
            results['create_community'] = 'FAIL'
    
    # 7. Get conversations
    print("\n----- Testing Conversations Endpoint -----")
    conversations = get_conversations(token)
    if conversations and 'results' in conversations:
        print(f"✅ Retrieved {len(conversations['results'])} conversations")
        results['conversations'] = 'PASS'
    else:
        print("❌ Failed to get conversations")
        results['conversations'] = 'FAIL'
    
    # Print summary
    print("\n===== API TEST RESULTS =====")
    for endpoint, result in results.items():
        print(f"{endpoint.replace('_', ' ').title()}: {result}")
    
    # Calculate success percentage
    success_count = list(results.values()).count('PASS')
    total_count = len(results)
    success_percentage = (success_count / total_count) * 100
    
    print(f"\nOverall Success: {success_count}/{total_count} ({success_percentage:.1f}%)")

if __name__ == '__main__':
    # Authentication options
    print("SociSphere API Test Client")
    print("--------------------------")
    print("1. Test with existing user (user1/password123)")
    print("2. Test with admin user (admin/adminpassword)")
    print("3. Register a new user")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        token_data = get_token('user1', 'password123')
    elif choice == '2':
        token_data = get_token('admin', 'adminpassword')
    elif choice == '3':
        username = input("Enter username: ").strip()
        email = input("Enter email: ").strip()
        password = input("Enter password: ").strip()
        user_data = register_user(username, email, password)
        if user_data:
            token_data = get_token(username, password)
        else:
            token_data = None
    else:
        print("Invalid choice!")
        token_data = None
    
    if token_data:
        access_token = token_data['access']
        run_full_test_suite(access_token)
    else:
        print("Unable to obtain access token. Exiting.") 