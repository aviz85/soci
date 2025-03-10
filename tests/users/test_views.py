import pytest
import json
from datetime import date, time
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.users.models import UserPreference, MoodBoard, MoodBoardItem, WellbeingData

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationView:
    """Test the UserRegistrationView."""
    
    def test_register_user_success(self, api_client):
        """Test successfully registering a user."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        url = '/api/users/register/'
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()
        assert User.objects.filter(email='newuser@example.com').exists()
        
        # Check that a UserPreference was created
        user = User.objects.get(username='newuser')
        assert UserPreference.objects.filter(user=user).exists()
    
    def test_register_user_missing_data(self, api_client):
        """Test registering a user with missing data."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }
        url = '/api/users/register/'
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data
    
    def test_register_user_mismatched_passwords(self, api_client):
        """Test registering a user with mismatched passwords."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'wrong_password',
            'first_name': 'New',
            'last_name': 'User'
        }
        url = '/api/users/register/'
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data


@pytest.mark.django_db
class TestCurrentUserView:
    """Test the CurrentUserView."""
    
    def test_get_current_user(self, authenticated_client, create_user):
        """Test getting the current authenticated user."""
        url = '/api/users/me/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == create_user.id
        assert response.data['username'] == create_user.username
        assert 'email' not in response.data  # email should be write_only
    
    def test_get_current_user_unauthenticated(self, api_client):
        """Test getting the current user without authentication."""
        url = '/api/users/me/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserViewSet:
    """Test the UserViewSet."""
    
    def test_list_users(self, authenticated_client, create_user):
        """Test listing users."""
        url = '/api/users/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        assert len(results) >= 1  # At least the created user should be listed
        assert any(user['id'] == create_user.id for user in results)
    
    def test_retrieve_user(self, authenticated_client, create_user):
        """Test retrieving a specific user."""
        url = f'/api/users/{create_user.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == create_user.id
        assert response.data['username'] == create_user.username
    
    def test_update_user(self, authenticated_client, create_user):
        """Test updating a user."""
        url = f'/api/users/{create_user.id}/'
        data = {
            'bio': 'Updated bio',
            'location': 'New York',
            'website': 'https://example.com'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bio'] == 'Updated bio'
        assert response.data['location'] == 'New York'
        assert response.data['website'] == 'https://example.com'
        
        # Verify the database was updated
        create_user.refresh_from_db()
        assert create_user.bio == 'Updated bio'
        assert create_user.location == 'New York'
        assert create_user.website == 'https://example.com'
    
    def test_search_users(self, authenticated_client, create_user):
        """Test searching for users."""
        url = '/api/users/search/'
        response = authenticated_client.get(url, {'q': create_user.username[:3]})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(user['id'] == create_user.id for user in response.data)


@pytest.mark.django_db
class TestUserPreferenceViewSet:
    """Test the UserPreferenceViewSet."""
    
    @pytest.fixture
    def user_preference(self, create_user):
        """Create a user preference for testing."""
        # Delete any existing preference first
        UserPreference.objects.filter(user=create_user).delete()
        return UserPreference.objects.create(
            user=create_user,
            email_notifications=True,
            push_notifications=False,
            content_language="en",
            content_sensitivity="low",
            who_can_message="followers",
            daily_usage_limit=60
        )
    
    def test_list_user_preferences(self, authenticated_client, user_preference):
        """Test listing user preferences."""
        url = '/api/users/preferences/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == user_preference.id
    
    def test_retrieve_user_preference(self, authenticated_client, user_preference):
        """Test retrieving a specific user preference."""
        url = f'/api/users/preferences/{user_preference.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user_preference.id
        assert response.data['email_notifications'] is True
        assert response.data['push_notifications'] is False
    
    def test_update_user_preference(self, authenticated_client, user_preference):
        """Test updating a user preference."""
        url = f'/api/users/preferences/{user_preference.id}/'
        data = {
            'email_notifications': False,
            'content_language': 'fr',
            'who_can_message': 'everyone'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_notifications'] is False
        assert response.data['content_language'] == 'fr'
        assert response.data['who_can_message'] == 'everyone'
        
        # Verify the database was updated
        user_preference.refresh_from_db()
        assert user_preference.email_notifications is False
        assert user_preference.content_language == 'fr'
        assert user_preference.who_can_message == 'everyone'


@pytest.mark.django_db
class TestMoodBoardViewSet:
    """Test the MoodBoardViewSet."""
    
    @pytest.fixture
    def mood_board(self, create_user):
        """Create a mood board for testing."""
        return MoodBoard.objects.create(
            user=create_user,
            title="Test Mood",
            description="A test mood board",
            is_current=True
        )
    
    @pytest.fixture
    def mood_board_item(self, mood_board):
        """Create a mood board item for testing."""
        return MoodBoardItem.objects.create(
            mood_board=mood_board,
            text="Happy",
            link="https://example.com",
            position_x=10,
            position_y=20
        )
    
    def test_list_mood_boards(self, authenticated_client, mood_board):
        """Test listing mood boards."""
        url = '/api/users/mood-boards/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert any(board['id'] == mood_board.id for board in response.data['results'])
    
    def test_retrieve_mood_board(self, authenticated_client, mood_board):
        """Test retrieving a specific mood board."""
        url = f'/api/users/mood-boards/{mood_board.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == mood_board.id
        assert response.data['title'] == 'Test Mood'
        assert response.data['description'] == 'A test mood board'
    
    def test_create_mood_board(self, authenticated_client, create_user):
        """Test creating a mood board."""
        url = '/api/users/mood-boards/'
        data = {
            'title': 'New Mood',
            'description': 'A new mood board',
            'is_current': False
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Mood'
        assert response.data['description'] == 'A new mood board'
        assert response.data['is_current'] is False
        assert response.data['user'] == create_user.id
    
    def test_update_mood_board(self, authenticated_client, mood_board):
        """Test updating a mood board."""
        url = f'/api/users/mood-boards/{mood_board.id}/'
        data = {
            'title': 'Updated Mood',
            'is_current': False
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Mood'
        assert response.data['is_current'] is False
        
        # Verify the database was updated
        mood_board.refresh_from_db()
        assert mood_board.title == 'Updated Mood'
        assert mood_board.is_current is False
    
    def test_delete_mood_board(self, authenticated_client, mood_board):
        """Test deleting a mood board."""
        url = f'/api/users/mood-boards/{mood_board.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not MoodBoard.objects.filter(id=mood_board.id).exists()
    
    def test_get_mood_board_items(self, authenticated_client, mood_board, mood_board_item):
        """Test getting items for a mood board."""
        url = f'/api/users/mood-boards/{mood_board.id}/items/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == mood_board_item.id
        assert response.data[0]['text'] == 'Happy'
    
    def test_add_mood_board_item(self, authenticated_client, mood_board):
        """Test adding an item to a mood board."""
        url = f'/api/users/mood-boards/{mood_board.id}/items/'
        data = {
            'text': 'Excited',
            'link': 'https://example.org',
            'position_x': 30,
            'position_y': 40
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['text'] == 'Excited'
        assert response.data['link'] == 'https://example.org'
        assert response.data['position_x'] == 30
        assert response.data['position_y'] == 40
        assert response.data['mood_board'] == mood_board.id


@pytest.mark.django_db
class TestWellbeingDataViewSet:
    """Test the WellbeingDataViewSet."""
    
    @pytest.fixture
    def wellbeing_data(self, create_user):
        """Create wellbeing data for testing."""
        return WellbeingData.objects.create(
            user=create_user,
            date=date(2023, 1, 1),
            time_spent=3600,
            sessions_count=5,
            interactions_count=20,
            mood_assessment="positive"
        )
    
    def test_list_wellbeing_data(self, authenticated_client, wellbeing_data):
        """Test listing wellbeing data."""
        url = '/api/users/wellbeing/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        assert any(data['id'] == wellbeing_data.id for data in response.data['results'])
    
    def test_retrieve_wellbeing_data(self, authenticated_client, wellbeing_data):
        """Test retrieving specific wellbeing data."""
        url = f'/api/users/wellbeing/{wellbeing_data.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == wellbeing_data.id
        assert response.data['time_spent'] == 3600
        assert response.data['mood_assessment'] == 'positive'
    
    def test_create_wellbeing_data(self, authenticated_client, create_user):
        """Test creating wellbeing data."""
        today = date.today().isoformat()
        url = '/api/users/wellbeing/'
        data = {
            'date': today,
            'time_spent': 1800,
            'sessions_count': 3,
            'interactions_count': 10,
            'mood_assessment': 'neutral'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['date'] == data['date']
        assert response.data['time_spent'] == data['time_spent']
        assert response.data['sessions_count'] == data['sessions_count']
        assert response.data['interactions_count'] == data['interactions_count']
        assert response.data['mood_assessment'] == data['mood_assessment']
        assert response.data['user'] == create_user.id
    
    def test_update_wellbeing_data(self, authenticated_client, wellbeing_data):
        """Test updating wellbeing data."""
        url = f'/api/users/wellbeing/{wellbeing_data.id}/'
        data = {
            'time_spent': 7200,
            'mood_assessment': 'negative'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['time_spent'] == 7200
        assert response.data['mood_assessment'] == 'negative'
        
        # Verify the database was updated
        wellbeing_data.refresh_from_db()
        assert wellbeing_data.time_spent == 7200
        assert wellbeing_data.mood_assessment == 'negative'
    
    def test_get_wellbeing_summary(self, authenticated_client, wellbeing_data):
        """Test getting a summary of wellbeing data."""
        url = '/api/users/wellbeing/summary/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1
        # The summary should include our test data
        assert any(data['id'] == wellbeing_data.id for data in response.data) 