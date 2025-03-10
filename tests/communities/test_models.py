import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.communities.models import (
    Community, CommunityMembership, CommunityRule, 
    CommunityPost, CommunityInvitation, CommunityTopic
)


@pytest.mark.django_db
class TestCommunityModel:
    """Test the Community model."""
    
    def test_create_community(self, create_user):
        """Test creating a community."""
        community = Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user,
            visibility="public"
        )
        assert community.name == "Test Community"
        assert community.slug == "test-community"
        assert community.description == "This is a test community."
        assert community.creator == create_user
        assert community.visibility == "public"
        assert community.allow_post_images is True
        assert community.allow_post_videos is True
        assert community.requires_post_approval is False
        assert community.members_count == 0
        assert community.posts_count == 0
    
    def test_community_str_method(self, create_user):
        """Test the string representation of a community."""
        community = Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
        assert str(community) == "Test Community"
    
    def test_community_moderators(self, create_user):
        """Test adding moderators to a community."""
        community = Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
        
        # Add the creator as a moderator
        community.moderators.add(create_user)
        assert create_user in community.moderators.all()
        
        # Check the reverse relation
        assert community in create_user.moderated_communities.all()


@pytest.mark.django_db
class TestCommunityMembershipModel:
    """Test the CommunityMembership model."""
    
    @pytest.fixture
    def community(self, create_user):
        """Create a community for testing."""
        return Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
    
    def test_create_membership(self, create_user, community):
        """Test creating a community membership."""
        membership = CommunityMembership.objects.create(
            user=create_user,
            community=community,
            status="member"
        )
        assert membership.user == create_user
        assert membership.community == community
        assert membership.status == "member"
        assert membership.muted is False
    
    def test_membership_str_method(self, create_user, community):
        """Test the string representation of a membership."""
        membership = CommunityMembership.objects.create(
            user=create_user,
            community=community
        )
        assert str(membership) == f"{create_user.username} in {community.name}"
    
    def test_membership_unique_constraint(self, create_user, community):
        """Test the unique constraint for user and community."""
        CommunityMembership.objects.create(
            user=create_user,
            community=community
        )
        
        with pytest.raises(IntegrityError):
            CommunityMembership.objects.create(
                user=create_user,
                community=community
            )


@pytest.mark.django_db
class TestCommunityRuleModel:
    """Test the CommunityRule model."""
    
    @pytest.fixture
    def community(self, create_user):
        """Create a community for testing."""
        return Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
    
    def test_create_rule(self, community):
        """Test creating a community rule."""
        rule = CommunityRule.objects.create(
            community=community,
            title="Be respectful",
            description="Treat others with respect and kindness.",
            position=1
        )
        assert rule.community == community
        assert rule.title == "Be respectful"
        assert rule.description == "Treat others with respect and kindness."
        assert rule.position == 1
    
    def test_rule_str_method(self, community):
        """Test the string representation of a rule."""
        rule = CommunityRule.objects.create(
            community=community,
            title="No spam"
        )
        assert str(rule) == f"{community.name} rule: No spam"
    
    def test_rule_ordering(self, community):
        """Test the ordering of rules."""
        rule1 = CommunityRule.objects.create(
            community=community,
            title="Rule 1",
            position=2
        )
        rule2 = CommunityRule.objects.create(
            community=community,
            title="Rule 2",
            position=1
        )
        rule3 = CommunityRule.objects.create(
            community=community,
            title="Rule 3",
            position=3
        )
        
        rules = list(CommunityRule.objects.filter(community=community))
        assert rules == [rule2, rule1, rule3]


@pytest.mark.django_db
class TestCommunityPostModel:
    """Test the CommunityPost model."""
    
    @pytest.fixture
    def community(self, create_user):
        """Create a community for testing."""
        return Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
    
    def test_create_post(self, create_user, community):
        """Test creating a community post."""
        post = CommunityPost.objects.create(
            user=create_user,
            community=community,
            title="Test Post",
            body="This is a test post.",
            status="approved",
            visibility="public"
        )
        assert post.user == create_user
        assert post.community == community
        assert post.title == "Test Post"
        assert post.body == "This is a test post."
        assert post.status == "approved"
        assert post.visibility == "public"
        assert post.is_pinned is False
        assert post.view_count == 0
        assert post.engagement_score == 0.0
    
    def test_post_str_method(self, create_user, community):
        """Test the string representation of a post."""
        post = CommunityPost.objects.create(
            user=create_user,
            community=community,
            title="Test Post",
            body="This is a test post."
        )
        assert str(post) == f"Test Post in {community.name}"
    
    def test_post_ordering(self, create_user, community):
        """Test the ordering of posts."""
        # Create a regular post
        post1 = CommunityPost.objects.create(
            user=create_user,
            community=community,
            title="Regular Post",
            body="This is a regular post.",
            created_at=timezone.now()
        )
        
        # Create an older pinned post
        post2 = CommunityPost.objects.create(
            user=create_user,
            community=community,
            title="Older Pinned Post",
            body="This is an older pinned post.",
            is_pinned=True,
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        
        # Create a newer post
        post3 = CommunityPost.objects.create(
            user=create_user,
            community=community,
            title="Newer Post",
            body="This is a newer post.",
            created_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        posts = list(CommunityPost.objects.filter(community=community))
        # Pinned posts should come first, then sorted by creation date (newest first)
        assert posts == [post2, post3, post1]


@pytest.mark.django_db
class TestCommunityInvitationModel:
    """Test the CommunityInvitation model."""
    
    @pytest.fixture
    def community(self, create_user):
        """Create a community for testing."""
        return Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
    
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
    
    def test_create_invitation(self, create_user, second_user, community):
        """Test creating a community invitation."""
        invitation = CommunityInvitation.objects.create(
            community=community,
            inviter=create_user,
            invitee=second_user,
            message="Please join our community!"
        )
        assert invitation.community == community
        assert invitation.inviter == create_user
        assert invitation.invitee == second_user
        assert invitation.message == "Please join our community!"
        assert invitation.status == "pending"
        assert invitation.responded_at is None
    
    def test_invitation_str_method(self, create_user, second_user, community):
        """Test the string representation of an invitation."""
        invitation = CommunityInvitation.objects.create(
            community=community,
            inviter=create_user,
            invitee=second_user
        )
        assert str(invitation) == f"{create_user.username} invited {second_user.username} to {community.name}"
    
    def test_invitation_unique_constraint(self, create_user, second_user, community):
        """Test the unique constraint for community, inviter, and invitee."""
        CommunityInvitation.objects.create(
            community=community,
            inviter=create_user,
            invitee=second_user
        )
        
        with pytest.raises(IntegrityError):
            CommunityInvitation.objects.create(
                community=community,
                inviter=create_user,
                invitee=second_user
            )


@pytest.mark.django_db
class TestCommunityTopicModel:
    """Test the CommunityTopic model."""
    
    @pytest.fixture
    def community(self, create_user):
        """Create a community for testing."""
        return Community.objects.create(
            name="Test Community",
            slug="test-community",
            description="This is a test community.",
            creator=create_user
        )
    
    def test_create_topic(self, create_user, community):
        """Test creating a community topic."""
        topic = CommunityTopic.objects.create(
            community=community,
            name="General Discussion",
            description="For general discussions about anything.",
            icon="chat",
            position=1,
            created_by=create_user
        )
        assert topic.community == community
        assert topic.name == "General Discussion"
        assert topic.description == "For general discussions about anything."
        assert topic.icon == "chat"
        assert topic.position == 1
        assert topic.created_by == create_user
    
    def test_topic_str_method(self, create_user, community):
        """Test the string representation of a topic."""
        topic = CommunityTopic.objects.create(
            community=community,
            name="Announcements",
            created_by=create_user
        )
        assert str(topic) == f"Announcements in {community.name}"
    
    def test_topic_ordering(self, create_user, community):
        """Test the ordering of topics."""
        topic1 = CommunityTopic.objects.create(
            community=community,
            name="Topic 1",
            position=2,
            created_by=create_user
        )
        topic2 = CommunityTopic.objects.create(
            community=community,
            name="Topic 2",
            position=1,
            created_by=create_user
        )
        topic3 = CommunityTopic.objects.create(
            community=community,
            name="Topic 3",
            position=3,
            created_by=create_user
        )
        
        topics = list(CommunityTopic.objects.filter(community=community))
        assert topics == [topic2, topic1, topic3]
    
    def test_topic_unique_constraint(self, create_user, community):
        """Test the unique constraint for community and name."""
        CommunityTopic.objects.create(
            community=community,
            name="Unique Topic",
            created_by=create_user
        )
        
        with pytest.raises(IntegrityError):
            CommunityTopic.objects.create(
                community=community,
                name="Unique Topic",
                created_by=create_user
            ) 