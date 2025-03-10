import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.interactions.models import (
    Connection, Message, MessageAttachment, Conversation, ConversationMessage,
    ConversationMessageAttachment, ConversationRead, Notification,
    CollaborativeSpace, SpaceMembership
)


@pytest.mark.django_db
class TestConnectionModel:
    """Test the Connection model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    def test_create_connection(self, create_user, second_user):
        """Test creating a connection between users."""
        connection = Connection.objects.create(
            follower=create_user,
            followed=second_user,
            strength="weak"
        )
        assert connection.follower == create_user
        assert connection.followed == second_user
        assert connection.strength == "weak"
        assert connection.interaction_count == 0
        assert connection.last_interaction is None
    
    def test_connection_str_method(self, create_user, second_user):
        """Test the string representation of a connection."""
        connection = Connection.objects.create(
            follower=create_user,
            followed=second_user
        )
        assert str(connection) == f"{create_user.username} follows {second_user.username}"
    
    def test_connection_unique_constraint(self, create_user, second_user):
        """Test the unique constraint for follower and followed."""
        Connection.objects.create(
            follower=create_user,
            followed=second_user
        )
        
        with pytest.raises(IntegrityError):
            Connection.objects.create(
                follower=create_user,
                followed=second_user
            )


@pytest.mark.django_db
class TestMessageModel:
    """Test the Message model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    def test_create_message(self, create_user, second_user):
        """Test creating a message."""
        message = Message.objects.create(
            sender=create_user,
            recipient=second_user,
            body="Hello, how are you?"
        )
        assert message.sender == create_user
        assert message.recipient == second_user
        assert message.body == "Hello, how are you?"
        assert message.has_attachment is False
        assert message.is_read is False
        assert message.read_at is None
        assert message.is_voice is False
        assert message.voice_duration is None
    
    def test_message_str_method(self, create_user, second_user):
        """Test the string representation of a message."""
        message = Message.objects.create(
            sender=create_user,
            recipient=second_user,
            body="Test message"
        )
        assert str(message) == f"Message from {create_user.username} to {second_user.username}"
    
    def test_message_ordering(self, create_user, second_user):
        """Test the ordering of messages."""
        message1 = Message.objects.create(
            sender=create_user,
            recipient=second_user,
            body="First message",
            created_at=timezone.now()
        )
        message2 = Message.objects.create(
            sender=create_user,
            recipient=second_user,
            body="Second message",
            created_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        messages = list(Message.objects.all())
        assert messages == [message1, message2]


@pytest.mark.django_db
class TestMessageAttachmentModel:
    """Test the MessageAttachment model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def message(self, create_user, second_user):
        """Create a message for testing."""
        return Message.objects.create(
            sender=create_user,
            recipient=second_user,
            body="Message with attachment",
            has_attachment=True
        )
    
    def test_create_attachment(self, message):
        """Test creating a message attachment."""
        attachment = MessageAttachment.objects.create(
            message=message,
            file="test_file.jpg",
            type="image",
            file_name="test_file.jpg",
            file_size=1024
        )
        assert attachment.message == message
        assert attachment.file == "test_file.jpg"
        assert attachment.type == "image"
        assert attachment.file_name == "test_file.jpg"
        assert attachment.file_size == 1024
    
    def test_attachment_str_method(self, message):
        """Test the string representation of an attachment."""
        attachment = MessageAttachment.objects.create(
            message=message,
            file="test_doc.pdf",
            type="document",
            file_name="test_doc.pdf",
            file_size=2048
        )
        assert str(attachment) == f"document attachment for {message}"


@pytest.mark.django_db
class TestConversationModel:
    """Test the Conversation model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def third_user(self):
        """Create a third user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="thirduser",
            email="third@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def fourth_user(self):
        """Create a fourth user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="fourthuser",
            email="fourth@example.com",
            password="password123"
        )
    
    def test_create_conversation(self, create_user, second_user):
        """Test creating a conversation."""
        conversation = Conversation.objects.create()
        conversation.participants.add(create_user, second_user)
        
        assert create_user in conversation.participants.all()
        assert second_user in conversation.participants.all()
        assert conversation.is_group is False
        assert conversation.name == ""
    
    def test_conversation_str_method_two_participants(self, create_user, second_user):
        """Test the string representation of a conversation with two participants."""
        conversation = Conversation.objects.create()
        conversation.participants.add(create_user, second_user)
        
        assert str(conversation) == f"Conversation with {create_user.username}, {second_user.username}"
    
    def test_conversation_str_method_group(self, create_user, second_user, third_user):
        """Test the string representation of a group conversation."""
        conversation = Conversation.objects.create(
            is_group=True,
            name="Test Group"
        )
        conversation.participants.add(create_user, second_user, third_user)
        
        assert str(conversation) == "Group: Test Group"
    
    def test_conversation_str_method_many_participants(self, create_user, second_user, third_user, fourth_user):
        """Test the string representation of a conversation with many participants."""
        conversation = Conversation.objects.create()
        conversation.participants.add(create_user, second_user, third_user, fourth_user)
        
        # The exact order of the participants may vary, so we'll just check that it contains 'and others'
        assert "and others" in str(conversation)
    
    def test_conversation_ordering(self, create_user, second_user):
        """Test the ordering of conversations."""
        conversation1 = Conversation.objects.create(
            updated_at=timezone.now()
        )
        conversation1.participants.add(create_user, second_user)
        
        conversation2 = Conversation.objects.create(
            updated_at=timezone.now() + timezone.timedelta(hours=1)
        )
        conversation2.participants.add(create_user, second_user)
        
        conversations = list(Conversation.objects.all())
        assert conversations == [conversation2, conversation1]


@pytest.mark.django_db
class TestConversationMessageModel:
    """Test the ConversationMessage model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def conversation(self, create_user, second_user):
        """Create a conversation for testing."""
        conversation = Conversation.objects.create()
        conversation.participants.add(create_user, second_user)
        return conversation
    
    def test_create_conversation_message(self, create_user, conversation):
        """Test creating a conversation message."""
        message = ConversationMessage.objects.create(
            conversation=conversation,
            sender=create_user,
            body="Hello everyone!"
        )
        assert message.conversation == conversation
        assert message.sender == create_user
        assert message.body == "Hello everyone!"
        assert message.has_attachment is False
        assert message.is_voice is False
        assert message.voice_duration is None
    
    def test_conversation_message_str_method(self, create_user, conversation):
        """Test the string representation of a conversation message."""
        message = ConversationMessage.objects.create(
            conversation=conversation,
            sender=create_user,
            body="Test message"
        )
        assert str(message) == f"Message from {create_user.username} in {conversation}"
    
    def test_conversation_message_ordering(self, create_user, conversation):
        """Test the ordering of conversation messages."""
        message1 = ConversationMessage.objects.create(
            conversation=conversation,
            sender=create_user,
            body="First message",
            created_at=timezone.now()
        )
        message2 = ConversationMessage.objects.create(
            conversation=conversation,
            sender=create_user,
            body="Second message",
            created_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        
        messages = list(ConversationMessage.objects.filter(conversation=conversation))
        assert messages == [message1, message2]


@pytest.mark.django_db
class TestConversationMessageAttachmentModel:
    """Test the ConversationMessageAttachment model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def conversation(self, create_user, second_user):
        """Create a conversation for testing."""
        conversation = Conversation.objects.create()
        conversation.participants.add(create_user, second_user)
        return conversation
    
    @pytest.fixture
    def conversation_message(self, create_user, conversation):
        """Create a conversation message for testing."""
        return ConversationMessage.objects.create(
            conversation=conversation,
            sender=create_user,
            body="Message with attachment",
            has_attachment=True
        )
    
    def test_create_conversation_attachment(self, conversation_message):
        """Test creating a conversation message attachment."""
        attachment = ConversationMessageAttachment.objects.create(
            message=conversation_message,
            file="test_file.jpg",
            type="image",
            file_name="test_file.jpg",
            file_size=1024
        )
        assert attachment.message == conversation_message
        assert attachment.file == "test_file.jpg"
        assert attachment.type == "image"
        assert attachment.file_name == "test_file.jpg"
        assert attachment.file_size == 1024
    
    def test_conversation_attachment_str_method(self, conversation_message):
        """Test the string representation of a conversation message attachment."""
        attachment = ConversationMessageAttachment.objects.create(
            message=conversation_message,
            file="test_doc.pdf",
            type="document",
            file_name="test_doc.pdf",
            file_size=2048
        )
        assert str(attachment) == f"document attachment for message in {conversation_message.conversation}"


@pytest.mark.django_db
class TestConversationReadModel:
    """Test the ConversationRead model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def conversation(self, create_user, second_user):
        """Create a conversation for testing."""
        conversation = Conversation.objects.create()
        conversation.participants.add(create_user, second_user)
        return conversation
    
    def test_create_conversation_read(self, create_user, conversation):
        """Test creating a conversation read mark."""
        now = timezone.now()
        read_mark = ConversationRead.objects.create(
            conversation=conversation,
            user=create_user,
            last_read_at=now
        )
        assert read_mark.conversation == conversation
        assert read_mark.user == create_user
        assert read_mark.last_read_at == now
    
    def test_conversation_read_str_method(self, create_user, conversation):
        """Test the string representation of a conversation read mark."""
        now = timezone.now()
        read_mark = ConversationRead.objects.create(
            conversation=conversation,
            user=create_user,
            last_read_at=now
        )
        assert str(read_mark) == f"{create_user.username} last read {conversation} at {now}"
    
    def test_conversation_read_unique_constraint(self, create_user, conversation):
        """Test the unique constraint for conversation and user."""
        now = timezone.now()
        ConversationRead.objects.create(
            conversation=conversation,
            user=create_user,
            last_read_at=now
        )
        
        with pytest.raises(IntegrityError):
            ConversationRead.objects.create(
                conversation=conversation,
                user=create_user,
                last_read_at=now
            )


@pytest.mark.django_db
class TestNotificationModel:
    """Test the Notification model."""
    
    def test_create_notification(self, create_user):
        """Test creating a notification."""
        notification = Notification.objects.create(
            recipient=create_user,
            notification_type="follow",
            title="New follower",
            message="Someone started following you!",
            link="https://example.com/profile"
        )
        assert notification.recipient == create_user
        assert notification.notification_type == "follow"
        assert notification.title == "New follower"
        assert notification.message == "Someone started following you!"
        assert notification.link == "https://example.com/profile"
        assert notification.is_read is False
        assert notification.read_at is None
    
    def test_notification_str_method(self, create_user):
        """Test the string representation of a notification."""
        notification = Notification.objects.create(
            recipient=create_user,
            notification_type="like",
            title="New like",
            message="Someone liked your post!"
        )
        assert str(notification) == f"like notification for {create_user.username}"
    
    def test_notification_ordering(self, create_user):
        """Test the ordering of notifications."""
        notification1 = Notification.objects.create(
            recipient=create_user,
            notification_type="follow",
            title="Old notification",
            message="Old message",
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        notification2 = Notification.objects.create(
            recipient=create_user,
            notification_type="message",
            title="New notification",
            message="New message",
            created_at=timezone.now()
        )
        
        notifications = list(Notification.objects.all())
        assert notifications == [notification2, notification1]


@pytest.mark.django_db
class TestCollaborativeSpaceModel:
    """Test the CollaborativeSpace model."""
    
    def test_create_collaborative_space(self, create_user):
        """Test creating a collaborative space."""
        space = CollaborativeSpace.objects.create(
            name="Project Space",
            description="A space for our collaborative project.",
            creator=create_user,
            is_public=False,
            allows_comments=True
        )
        assert space.name == "Project Space"
        assert space.description == "A space for our collaborative project."
        assert space.creator == create_user
        assert space.is_public is False
        assert space.allows_comments is True
    
    def test_collaborative_space_str_method(self, create_user):
        """Test the string representation of a collaborative space."""
        space = CollaborativeSpace.objects.create(
            name="Design Team",
            description="For design collaboration.",
            creator=create_user
        )
        assert str(space) == "Design Team"


@pytest.mark.django_db
class TestSpaceMembershipModel:
    """Test the SpaceMembership model."""
    
    @pytest.fixture
    def second_user(self):
        """Create a second user for testing."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create_user(
            username="seconduser",
            email="second@example.com",
            password="password123"
        )
    
    @pytest.fixture
    def collaborative_space(self, create_user):
        """Create a collaborative space for testing."""
        return CollaborativeSpace.objects.create(
            name="Test Space",
            description="A test collaborative space.",
            creator=create_user
        )
    
    def test_create_space_membership(self, create_user, collaborative_space):
        """Test creating a space membership."""
        membership = SpaceMembership.objects.create(
            user=create_user,
            space=collaborative_space,
            role="admin"
        )
        assert membership.user == create_user
        assert membership.space == collaborative_space
        assert membership.role == "admin"
    
    def test_space_membership_str_method(self, create_user, collaborative_space):
        """Test the string representation of a space membership."""
        membership = SpaceMembership.objects.create(
            user=create_user,
            space=collaborative_space,
            role="contributor"
        )
        assert str(membership) == f"{create_user.username} as contributor in {collaborative_space.name}"
    
    def test_space_membership_unique_constraint(self, create_user, collaborative_space):
        """Test the unique constraint for user and space."""
        SpaceMembership.objects.create(
            user=create_user,
            space=collaborative_space,
            role="editor"
        )
        
        with pytest.raises(IntegrityError):
            SpaceMembership.objects.create(
                user=create_user,
                space=collaborative_space,
                role="viewer"
            ) 