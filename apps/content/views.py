from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.utils import timezone
from apps.users.models import User

from .models import Tag, Post, Media, Reaction, Comment, SavedContent
from .serializers import (
    TagSerializer, PostSerializer, MediaSerializer,
    ReactionSerializer, CommentSerializer, SavedContentSerializer
)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags."""
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing posts."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'body', 'tags__name']

    def get_queryset(self):
        """Return posts based on user permissions and visibility settings."""
        user = self.request.user
        # Users can view their own posts (including private ones)
        own_posts = Q(user=user)
        # Users can view public posts
        public_posts = Q(visibility='public')
        # Users can view posts shared with followers if they are following the creator
        # Get the users that the current user is following
        following_users = user.following.values_list('followed', flat=True)
        followers_posts = Q(visibility='followers', user__in=following_users)
        
        return Post.objects.filter(
            own_posts | public_posts | followers_posts
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the post author."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_media(self, request, pk=None):
        """Add media to a post."""
        post = self.get_object()
        if post.user != request.user:
            return Response(
                {"detail": "You cannot add media to someone else's post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MediaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """React to a post."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        
        reaction_type = request.data.get('reaction_type')
        if not reaction_type:
            return Response(
                {"detail": "Reaction type is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already reacted to this post
        existing_reaction = Reaction.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=post.id
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Remove the reaction if it's the same type
                existing_reaction.delete()
                return Response(
                    {"detail": f"Removed {reaction_type} reaction."},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                # Update the reaction if it's a different type
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                serializer = ReactionSerializer(existing_reaction)
                return Response(serializer.data)
        
        # Create a new reaction
        reaction = Reaction.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=post.id,
            reaction_type=reaction_type
        )
        serializer = ReactionSerializer(reaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for a post."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        
        # Get only top-level comments (no parent)
        comments = Comment.objects.filter(
            content_type=content_type,
            object_id=post.id,
            parent=None
        ).order_by('-created_at')
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to a post."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                content_type=content_type,
                object_id=post.id
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save a post for later viewing."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        
        # Check if already saved
        saved = SavedContent.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=post.id
        ).first()
        
        if saved:
            return Response(
                {"detail": "Post already saved."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save the post
        saved_content = SavedContent.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=post.id
        )
        serializer = SavedContentSerializer(saved_content)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        """Remove a post from saved content."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        
        # Find and delete the saved content
        saved = SavedContent.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=post.id
        ).first()
        
        if not saved:
            return Response(
                {"detail": "Post not saved."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        saved.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing comments."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comments the user can access."""
        return Comment.objects.filter(
            Q(user=self.request.user) |  # User's own comments
            Q(content_object__visibility='public') |  # Comments on public content
            Q(content_object__visibility='followers', content_object__user__followers=self.request.user)  # Comments on follower-only content
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the comment author."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get replies to a comment."""
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment).order_by('-created_at')
        serializer = CommentSerializer(replies, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_reply(self, request, pk=None):
        """Add a reply to a comment."""
        parent_comment = self.get_object()
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                content_type=parent_comment.content_type,
                object_id=parent_comment.object_id,
                parent=parent_comment
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reactions."""
    serializer_class = ReactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return reactions the user can access."""
        return Reaction.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the reaction author."""
        serializer.save(user=self.request.user)


class SavedContentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing saved content."""
    serializer_class = SavedContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return saved content for the current user."""
        return SavedContent.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the owner of the saved content."""
        serializer.save(user=self.request.user)


class FeedView(generics.ListAPIView):
    """View for the user's personalized feed."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return posts for the user's feed."""
        user = self.request.user
        
        # Get the users that the current user is following
        following_users = user.following.values_list('followed', flat=True)
        
        # Get posts from users the current user is following
        following_posts = Post.objects.filter(
            user__in=following_users,
            visibility__in=['public', 'followers']
        )
        
        # Get public posts that are trending (or recent if no trending)
        trending_posts = Post.objects.filter(
            visibility='public'
        ).order_by('-created_at')[:20]
        
        # Combine and remove duplicates
        return (following_posts | trending_posts).distinct().order_by('-created_at')


class TrendingView(generics.ListAPIView):
    """View for trending content."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return trending posts."""
        # Get public posts with high engagement in the last 24 hours
        yesterday = timezone.now() - timezone.timedelta(days=1)
        
        return Post.objects.filter(
            visibility='public',
            created_at__gte=yesterday
        ).order_by('-engagement_score', '-view_count')[:50]


class ContentSearchView(generics.ListAPIView):
    """View for searching content."""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'body', 'tags__name']

    def get_queryset(self):
        """Return posts that match the search criteria."""
        user = self.request.user
        query = self.request.query_params.get('q', '')
        
        if not query:
            return Post.objects.none()
        
        # Users can view their own posts (including private ones)
        own_posts = Q(user=user)
        
        # Users can view public posts
        public_posts = Q(visibility='public')
        
        # Users can view posts shared with followers if they are following the creator
        # Get the users that the current user follows
        followed_users = User.objects.filter(followers__follower=user)
        followers_posts = Q(visibility='followers', user__in=followed_users)
        
        # First filter by visibility permissions
        base_queryset = Post.objects.filter(
            own_posts | public_posts | followers_posts
        ).distinct()
        
        # Then apply search filter manually
        search_query = Q()
        for field in self.search_fields:
            search_query |= Q(**{f"{field}__icontains": query})
        
        return base_queryset.filter(search_query).order_by('-created_at') 