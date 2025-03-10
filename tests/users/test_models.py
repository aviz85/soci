import pytest
from django.db import IntegrityError
from datetime import date, time

from apps.users.models import User, UserPreference, MoodBoard, MoodBoardItem, WellbeingData


@pytest.mark.django_db
class TestUserModel:
    """Test the User model."""
    
    def test_create_user(self, user_data):
        """Test creating a user."""
        user = User.objects.create_user(**user_data)
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        assert user.check_password(user_data["password"])
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active
    
    def test_create_superuser(self, user_data):
        """Test creating a superuser."""
        user_data.pop("first_name")
        user_data.pop("last_name")
        user = User.objects.create_superuser(**user_data)
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        assert user.check_password(user_data["password"])
        assert user.is_staff
        assert user.is_superuser
        assert user.is_active
    
    def test_user_str_method(self, create_user):
        """Test the string representation of a user."""
        assert str(create_user) == create_user.username
    
    def test_email_unique(self, user_data):
        """Test that email is unique."""
        User.objects.create_user(**user_data)
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="anotheruser",
                email=user_data["email"],
                password="password123"
            )
    
    def test_user_profile_fields(self, create_user):
        """Test additional profile fields."""
        create_user.bio = "This is my bio"
        create_user.location = "New York"
        create_user.website = "https://example.com"
        create_user.birth_date = date(1990, 1, 1)
        create_user.save()
        
        user = User.objects.get(id=create_user.id)
        assert user.bio == "This is my bio"
        assert user.location == "New York"
        assert user.website == "https://example.com"
        assert user.birth_date == date(1990, 1, 1)
    
    def test_user_privacy_fields(self, create_user):
        """Test privacy fields."""
        assert create_user.private_profile is False
        assert create_user.show_online_status is True
        
        create_user.private_profile = True
        create_user.show_online_status = False
        create_user.save()
        
        user = User.objects.get(id=create_user.id)
        assert user.private_profile is True
        assert user.show_online_status is False


@pytest.mark.django_db
class TestUserPreferenceModel:
    """Test the UserPreference model."""
    
    def test_create_user_preference(self, create_user):
        """Test creating a user preference."""
        # Delete any existing preferences for this user
        UserPreference.objects.filter(user=create_user).delete()
        
        pref = UserPreference.objects.create(user=create_user)
        assert pref.user == create_user
        assert pref.email_notifications is True
        assert pref.push_notifications is True
        assert pref.content_language == "en"
        assert pref.content_sensitivity == "medium"
        assert pref.who_can_message == "everyone"
        assert pref.daily_usage_limit == 0
    
    def test_user_preference_str_method(self, create_user):
        """Test the string representation of a user preference."""
        # Delete any existing preferences for this user
        UserPreference.objects.filter(user=create_user).delete()
        
        pref = UserPreference.objects.create(user=create_user)
        assert str(pref) == f"{create_user.username}'s preferences"
    
    def test_user_preference_update(self, create_user):
        """Test updating user preferences."""
        # Delete any existing preferences for this user
        UserPreference.objects.filter(user=create_user).delete()
        
        pref = UserPreference.objects.create(user=create_user)
        
        pref.email_notifications = False
        pref.push_notifications = False
        pref.content_language = "fr"
        pref.content_sensitivity = "low"
        pref.who_can_message = "followers"
        pref.daily_usage_limit = 120
        pref.scheduled_downtime_start = time(22, 0)
        pref.scheduled_downtime_end = time(6, 0)
        pref.save()
        
        updated_pref = UserPreference.objects.get(id=pref.id)
        assert updated_pref.email_notifications is False
        assert updated_pref.push_notifications is False
        assert updated_pref.content_language == "fr"
        assert updated_pref.content_sensitivity == "low"
        assert updated_pref.who_can_message == "followers"
        assert updated_pref.daily_usage_limit == 120
        assert updated_pref.scheduled_downtime_start == time(22, 0)
        assert updated_pref.scheduled_downtime_end == time(6, 0)


@pytest.mark.django_db
class TestMoodBoardModel:
    """Test the MoodBoard model."""
    
    def test_create_mood_board(self, create_user):
        """Test creating a mood board."""
        board = MoodBoard.objects.create(
            user=create_user,
            title="My Mood",
            description="This is my current mood",
            is_current=True
        )
        assert board.user == create_user
        assert board.title == "My Mood"
        assert board.description == "This is my current mood"
        assert board.is_current is True
    
    def test_mood_board_str_method(self, create_user):
        """Test the string representation of a mood board."""
        board = MoodBoard.objects.create(
            user=create_user,
            title="My Mood"
        )
        assert str(board) == f"{create_user.username}'s mood board: My Mood"


@pytest.mark.django_db
class TestMoodBoardItemModel:
    """Test the MoodBoardItem model."""
    
    @pytest.fixture
    def mood_board(self, create_user):
        """Create a mood board for testing."""
        return MoodBoard.objects.create(
            user=create_user,
            title="Test Board"
        )
    
    def test_create_mood_board_item(self, mood_board):
        """Test creating a mood board item."""
        item = MoodBoardItem.objects.create(
            mood_board=mood_board,
            text="Happy thoughts",
            link="https://example.com",
            position_x=10,
            position_y=20
        )
        assert item.mood_board == mood_board
        assert item.text == "Happy thoughts"
        assert item.link == "https://example.com"
        assert item.position_x == 10
        assert item.position_y == 20
    
    def test_mood_board_item_str_method(self, mood_board):
        """Test the string representation of a mood board item."""
        item = MoodBoardItem.objects.create(
            mood_board=mood_board,
            text="Test Item"
        )
        assert str(item) == f"Item in {mood_board.title}"


@pytest.mark.django_db
class TestWellbeingDataModel:
    """Test the WellbeingData model."""
    
    def test_create_wellbeing_data(self, create_user):
        """Test creating wellbeing data."""
        data = WellbeingData.objects.create(
            user=create_user,
            time_spent=3600,
            sessions_count=5,
            interactions_count=20,
            mood_assessment="positive"
        )
        assert data.user == create_user
        assert data.time_spent == 3600
        assert data.sessions_count == 5
        assert data.interactions_count == 20
        assert data.mood_assessment == "positive"
    
    def test_wellbeing_data_str_method(self, create_user):
        """Test the string representation of wellbeing data."""
        data = WellbeingData.objects.create(
            user=create_user
        )
        assert str(data) == f"{create_user.username}'s wellbeing data on {data.date}"
    
    def test_wellbeing_data_unique_constraint(self, create_user):
        """Test the unique constraint for user and date."""
        WellbeingData.objects.create(
            user=create_user,
            date=date(2023, 1, 1)
        )
        with pytest.raises(IntegrityError):
            WellbeingData.objects.create(
                user=create_user,
                date=date(2023, 1, 1)
            ) 