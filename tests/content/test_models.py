import pytest
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta

from apps.content.models import Tag, Post, Media, Reaction, Comment, SavedContent


@pytest.mark.django_db
class TestTagModel:
    """Test the Tag model."""
    
    def test_create_tag(self):
        """Test creating a tag."""
        tag = Tag.objects.create(name="Technology", slug="technology")
        assert tag.name == "Technology"
        assert tag.slug == "technology"
    
    def test_tag_str_method(self):
        """Test the string representation of a tag."""
        tag = Tag.objects.create(name="Travel", slug="travel")
        assert str(tag) == "Travel"
    
    def test_tag_name_unique_constraint(self):
        """Test the unique constraint for tag name."""
        Tag.objects.create(name="Music", slug="music")
        
        with pytest.raises(IntegrityError):
            Tag.objects.create(name="Music", slug="different-slug")
    
    def test_tag_slug_unique_constraint(self):
        """Test the unique constraint for tag slug."""
        Tag.objects.create(name="Rock", slug="rock")
        
        with pytest.raises(IntegrityError):
            Tag.objects.create(name="Different Name", slug="rock")


@pytest.mark.django_db
class TestPostModel:
    """Test the Post model."""
    
    @pytest.fixture
    def tag(self):
        """Create a tag for testing."""
        return Tag.objects.create(name="Test Tag", slug="test-tag")
    
    def test_create_post(self, create_user):
        """Test creating a post."""
        post = Post.objects.create(
            user=create_user,
            title="Test Post",
            body="This is a test post.",
            visibility="public"
        )
        assert post.user == create_user
        assert post.title == "Test Post"
        assert post.body == "This is a test post."
        assert post.visibility == "public"
        assert post.view_count == 0
        assert post.engagement_score == 0.0
        assert post.expires_at is None
    
    def test_post_str_method(self, create_user):
        """Test the string representation of a post."""
        post = Post.objects.create(
            user=create_user,
            title="Test Post",
            body="This is a test post."
        )
        assert str(post) == f"{create_user.username}'s post: Test Post"
        
        # Test with long body, no title
        post = Post.objects.create(
            user=create_user,
            body="This is a very long post body that should be truncated in the string representation."
        )
        assert str(post) == f"{create_user.username}'s post: {post.body[:30]}"
    
    def test_post_with_tags(self, create_user, tag):
        """Test adding tags to a post."""
        post = Post.objects.create(
            user=create_user,
            title="Tagged Post",
            body="This is a post with tags."
        )
        post.tags.add(tag)
        assert tag in post.tags.all()
    
    def test_post_is_expired(self, create_user):
        """Test the is_expired method."""
        # Post that doesn't expire
        post1 = Post.objects.create(
            user=create_user,
            title="No Expiry",
            body="This post doesn't expire."
        )
        assert post1.is_expired() is False
        
        # Post that expires in the future
        future = timezone.now() + timedelta(days=1)
        post2 = Post.objects.create(
            user=create_user,
            title="Future Expiry",
            body="This post expires in the future.",
            expires_at=future
        )
        assert post2.is_expired() is False
        
        # Post that has already expired
        past = timezone.now() - timedelta(days=1)
        post3 = Post.objects.create(
            user=create_user,
            title="Past Expiry",
            body="This post has already expired.",
            expires_at=past
        )
        assert post3.is_expired() is True


@pytest.mark.django_db
class TestMediaModel:
    """Test the Media model."""
    
    @pytest.fixture
    def post(self, create_user):
        """Create a post for testing."""
        return Post.objects.create(
            user=create_user,
            title="Test Post",
            body="This is a test post."
        )
    
    def test_create_media(self, post):
        """Test creating a media item."""
        media = Media.objects.create(
            post=post,
            type="image",
            file="test_image.jpg",
            alt_text="Test image",
            width=800,
            height=600,
            position=1
        )
        assert media.post == post
        assert media.type == "image"
        assert media.file == "test_image.jpg"
        assert media.alt_text == "Test image"
        assert media.width == 800
        assert media.height == 600
        assert media.position == 1
    
    def test_media_str_method(self, post):
        """Test the string representation of a media item."""
        media = Media.objects.create(
            post=post,
            type="video",
            file="test_video.mp4"
        )
        assert str(media) == f"video for {post}"
    
    def test_media_ordering(self, post):
        """Test the ordering of media items."""
        media1 = Media.objects.create(
            post=post,
            type="image",
            file="image1.jpg",
            position=2
        )
        media2 = Media.objects.create(
            post=post,
            type="image",
            file="image2.jpg",
            position=1
        )
        media3 = Media.objects.create(
            post=post,
            type="image",
            file="image3.jpg",
            position=3
        )
        
        media_list = list(Media.objects.filter(post=post))
        assert media_list == [media2, media1, media3]


@pytest.mark.django_db
class TestReactionModel:
    """Test the Reaction model."""
    
    @pytest.fixture
    def post(self, create_user):
        """Create a post for testing."""
        return Post.objects.create(
            user=create_user,
            title="Test Post",
            body="This is a test post."
        )
    
    def test_create_reaction(self, create_user, post):
        """Test creating a reaction."""
        content_type = ContentType.objects.get_for_model(Post)
        reaction = Reaction.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            reaction_type="like"
        )
        
        assert reaction.user == create_user
        assert reaction.content_type == content_type
        assert reaction.object_id == post.id
        assert reaction.reaction_type == "like"
        assert reaction.content_object == post
    
    def test_reaction_str_method(self, create_user, post):
        """Test the string representation of a reaction."""
        content_type = ContentType.objects.get_for_model(Post)
        reaction = Reaction.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            reaction_type="love"
        )
        assert str(reaction) == f"{create_user.username} loved {post}"
    
    def test_reaction_unique_constraint(self, create_user, post):
        """Test the unique constraint for user, content_type, and object_id."""
        content_type = ContentType.objects.get_for_model(Post)
        Reaction.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            reaction_type="like"
        )
        
        with pytest.raises(IntegrityError):
            Reaction.objects.create(
                user=create_user,
                content_type=content_type,
                object_id=post.id,
                reaction_type="love"
            )


@pytest.mark.django_db
class TestCommentModel:
    """Test the Comment model."""
    
    @pytest.fixture
    def post(self, create_user):
        """Create a post for testing."""
        return Post.objects.create(
            user=create_user,
            title="Test Post",
            body="This is a test post."
        )
    
    def test_create_comment(self, create_user, post):
        """Test creating a comment."""
        content_type = ContentType.objects.get_for_model(Post)
        comment = Comment.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            body="This is a test comment."
        )
        
        assert comment.user == create_user
        assert comment.content_type == content_type
        assert comment.object_id == post.id
        assert comment.body == "This is a test comment."
        assert comment.parent is None
        assert comment.is_deleted is False
        assert comment.content_object == post
    
    def test_comment_str_method(self, create_user, post):
        """Test the string representation of a comment."""
        content_type = ContentType.objects.get_for_model(Post)
        comment = Comment.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            body="This is a test comment."
        )
        assert str(comment) == f"{create_user.username}'s comment on {post}"
    
    def test_nested_comments(self, create_user, post):
        """Test creating nested comments (replies)."""
        content_type = ContentType.objects.get_for_model(Post)
        parent_comment = Comment.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            body="Parent comment."
        )
        
        reply = Comment.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id,
            parent=parent_comment,
            body="Reply to parent comment."
        )
        
        assert reply.parent == parent_comment
        assert reply in parent_comment.replies.all()


@pytest.mark.django_db
class TestSavedContentModel:
    """Test the SavedContent model."""
    
    @pytest.fixture
    def post(self, create_user):
        """Create a post for testing."""
        return Post.objects.create(
            user=create_user,
            title="Test Post",
            body="This is a test post."
        )
    
    def test_create_saved_content(self, create_user, post):
        """Test creating saved content."""
        content_type = ContentType.objects.get_for_model(Post)
        saved = SavedContent.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id
        )
        
        assert saved.user == create_user
        assert saved.content_type == content_type
        assert saved.object_id == post.id
        assert saved.content_object == post
    
    def test_saved_content_str_method(self, create_user, post):
        """Test the string representation of saved content."""
        content_type = ContentType.objects.get_for_model(Post)
        saved = SavedContent.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id
        )
        assert str(saved) == f"{create_user.username} saved {post}"
    
    def test_saved_content_unique_constraint(self, create_user, post):
        """Test the unique constraint for user, content_type, and object_id."""
        content_type = ContentType.objects.get_for_model(Post)
        SavedContent.objects.create(
            user=create_user,
            content_type=content_type,
            object_id=post.id
        )
        
        with pytest.raises(IntegrityError):
            SavedContent.objects.create(
                user=create_user,
                content_type=content_type,
                object_id=post.id
            ) 