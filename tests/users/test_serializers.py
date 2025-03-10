import pytest
from datetime import date, time
from django.contrib.auth import get_user_model
from apps.users.models import UserPreference, MoodBoard, MoodBoardItem, WellbeingData
from apps.users.serializers import (
    UserSerializer, UserRegistrationSerializer, UserPreferenceSerializer,
    MoodBoardSerializer, MoodBoardItemSerializer, WellbeingDataSerializer
)

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializer:
    """Test the UserSerializer."""
    
    def test_serialize_user(self, create_user):
        """Test serializing a user."""
        serializer = UserSerializer(create_user)
        data = serializer.data
        
        assert data['id'] == create_user.id
        assert data['username'] == create_user.username
        assert 'email' not in data  # email should be write_only
        assert data['first_name'] == create_user.first_name
        assert data['last_name'] == create_user.last_name
        assert data['bio'] == create_user.bio
        assert data['private_profile'] is False
        assert data['show_online_status'] is True
        assert data['is_verified'] is False


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Test the UserRegistrationSerializer."""
    
    def test_validate_matching_passwords(self):
        """Test validation with matching passwords."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
    
    def test_validate_mismatched_passwords(self):
        """Test validation with mismatched passwords."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'wrong_password',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
    
    def test_create_user(self):
        """Test creating a user with the serializer."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.check_password('password123')
        assert user.first_name == 'New'
        assert user.last_name == 'User'


@pytest.mark.django_db
class TestUserPreferenceSerializer:
    """Test the UserPreferenceSerializer."""
    
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
            daily_usage_limit=60,
            scheduled_downtime_start=time(22, 0),
            scheduled_downtime_end=time(6, 0)
        )
    
    def test_serialize_user_preference(self, user_preference):
        """Test serializing a user preference."""
        serializer = UserPreferenceSerializer(user_preference)
        data = serializer.data
        
        assert data['id'] == user_preference.id
        assert data['user'] == user_preference.user.id
        assert data['email_notifications'] is True
        assert data['push_notifications'] is False
        assert data['content_language'] == 'en'
        assert data['content_sensitivity'] == 'low'
        assert data['who_can_message'] == 'followers'
        assert data['daily_usage_limit'] == 60
        assert data['scheduled_downtime_start'] == '22:00:00'
        assert data['scheduled_downtime_end'] == '06:00:00'
    
    def test_update_user_preference(self, user_preference):
        """Test updating a user preference with the serializer."""
        data = {
            'email_notifications': False,
            'push_notifications': True,
            'content_language': 'fr',
            'content_sensitivity': 'high',
            'who_can_message': 'everyone',
            'daily_usage_limit': 120
        }
        serializer = UserPreferenceSerializer(user_preference, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_preference = serializer.save()
        assert updated_preference.email_notifications is False
        assert updated_preference.push_notifications is True
        assert updated_preference.content_language == 'fr'
        assert updated_preference.content_sensitivity == 'high'
        assert updated_preference.who_can_message == 'everyone'
        assert updated_preference.daily_usage_limit == 120


@pytest.mark.django_db
class TestMoodBoardSerializer:
    """Test the MoodBoardSerializer."""
    
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
    
    def test_serialize_mood_board(self, mood_board, mood_board_item):
        """Test serializing a mood board."""
        serializer = MoodBoardSerializer(mood_board)
        data = serializer.data
        
        assert data['id'] == mood_board.id
        assert data['user'] == mood_board.user.id
        assert data['title'] == 'Test Mood'
        assert data['description'] == 'A test mood board'
        assert data['is_current'] is True
        assert len(data['items']) == 1
        assert data['items'][0]['id'] == mood_board_item.id
        assert data['items'][0]['text'] == 'Happy'


@pytest.mark.django_db
class TestMoodBoardItemSerializer:
    """Test the MoodBoardItemSerializer."""
    
    @pytest.fixture
    def mood_board(self, create_user):
        """Create a mood board for testing."""
        return MoodBoard.objects.create(
            user=create_user,
            title="Test Mood"
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
    
    def test_serialize_mood_board_item(self, mood_board_item):
        """Test serializing a mood board item."""
        serializer = MoodBoardItemSerializer(mood_board_item)
        data = serializer.data
        
        assert data['id'] == mood_board_item.id
        assert data['mood_board'] == mood_board_item.mood_board.id
        assert data['text'] == 'Happy'
        assert data['link'] == 'https://example.com'
        assert data['position_x'] == 10
        assert data['position_y'] == 20


@pytest.mark.django_db
class TestWellbeingDataSerializer:
    """Test the WellbeingDataSerializer."""
    
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
    
    def test_serialize_wellbeing_data(self, wellbeing_data):
        """Test serializing wellbeing data."""
        serializer = WellbeingDataSerializer(wellbeing_data)
        data = serializer.data
        
        assert data['id'] == wellbeing_data.id
        assert data['user'] == wellbeing_data.user.id
        assert data['date'] == wellbeing_data.date.isoformat()
        assert data['time_spent'] == 3600
        assert data['sessions_count'] == 5
        assert data['interactions_count'] == 20
        assert data['mood_assessment'] == 'positive' 