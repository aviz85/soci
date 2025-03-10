from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count

from .models import (
    Community, CommunityMembership, CommunityRule,
    CommunityPost, CommunityInvitation, CommunityTopic
)
from .serializers import (
    CommunitySerializer, CommunityMembershipSerializer, CommunityRuleSerializer,
    CommunityPostSerializer, CommunityInvitationSerializer, CommunityTopicSerializer
)
from apps.interactions.models import Notification


class CommunityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing communities."""
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'slug']
    lookup_field = 'slug'

    def get_queryset(self):
        """Return communities the user can access."""
        user = self.request.user
        
        # Return communities that are:
        # 1. Public
        # 2. Restricted, but the user is a member
        # 3. Private, but the user is a member
        return Community.objects.filter(
            Q(visibility='public') |
            (Q(visibility__in=['restricted', 'private']) & 
             Q(memberships__user=user, memberships__status='member'))
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the creator and add them as a moderator."""
        community = serializer.save(creator=self.request.user)
        community.moderators.add(self.request.user)
        
        # Also add the creator as a member
        CommunityMembership.objects.create(
            user=self.request.user,
            community=community,
            status='member'
        )

    @action(detail=True, methods=['post'])
    def add_moderator(self, request, slug=None):
        """Add a moderator to the community."""
        community = self.get_object()
        
        # Ensure the user is the creator or already a moderator
        if request.user != community.creator and request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can add moderators."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the user to add as moderator
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "No user specified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # Ensure the user is a member
            if not CommunityMembership.objects.filter(
                user=user, community=community, status='member'
            ).exists():
                return Response(
                    {"detail": "User must be a member to become a moderator."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add as moderator
            community.moderators.add(user)
            
            # Notify the user
            Notification.objects.create(
                recipient=user,
                notification_type='system',
                title=f'New Role in {community.name}',
                message=f'You are now a moderator of {community.name}.'
            )
            
            return Response({"status": "moderator added"})
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_moderator(self, request, slug=None):
        """Remove a moderator from the community."""
        community = self.get_object()
        
        # Ensure the user is the creator
        if request.user != community.creator:
            return Response(
                {"detail": "Only the creator can remove moderators."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the user to remove
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "No user specified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # Remove as moderator
            community.moderators.remove(user)
            
            # Notify the user
            Notification.objects.create(
                recipient=user,
                notification_type='system',
                title=f'Role Change in {community.name}',
                message=f'You are no longer a moderator of {community.name}.'
            )
            
            return Response({"status": "moderator removed"})
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """Get members of the community."""
        community = self.get_object()
        
        # Get the memberships
        memberships = CommunityMembership.objects.filter(
            community=community, status='member'
        ).order_by('-joined_at')
        
        serializer = CommunityMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def moderators(self, request, slug=None):
        """Get moderators of the community."""
        community = self.get_object()
        moderators = community.moderators.all()
        
        from apps.users.serializers import UserSerializer
        serializer = UserSerializer(moderators, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def rules(self, request, slug=None):
        """Get rules of the community."""
        community = self.get_object()
        rules = CommunityRule.objects.filter(community=community)
        
        serializer = CommunityRuleSerializer(rules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def topics(self, request, slug=None):
        """Get topics of the community."""
        community = self.get_object()
        topics = CommunityTopic.objects.filter(community=community)
        
        serializer = CommunityTopicSerializer(topics, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def posts(self, request, slug=None):
        """Get posts in the community."""
        community = self.get_object()
        user = request.user
        
        # Check if user is a member for restricted/private communities
        is_member = CommunityMembership.objects.filter(
            user=user, community=community, status='member'
        ).exists()
        
        if community.visibility != 'public' and not is_member:
            return Response(
                {"detail": "You must be a member to view posts in this community."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get approved posts
        posts = CommunityPost.objects.filter(
            community=community, status='approved'
        ).order_by('-is_pinned', '-created_at')
        
        # If user is a moderator, include pending posts
        if user == community.creator or user in community.moderators.all():
            pending_posts = CommunityPost.objects.filter(
                community=community, status='pending'
            ).order_by('-created_at')
            posts = list(posts) + list(pending_posts)
        
        serializer = CommunityPostSerializer(posts, many=True)
        return Response(serializer.data)


class CommunityMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community memberships."""
    serializer_class = CommunityMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the current user's community memberships."""
        return CommunityMembership.objects.filter(
            user=self.request.user
        ).order_by('-joined_at')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of a membership."""
        membership = self.get_object()
        community = membership.community
        
        # Ensure the user is a moderator
        if request.user != community.creator and request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can update membership status."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        if not new_status or new_status not in dict(CommunityMembership.STATUS_CHOICES):
            return Response(
                {"detail": "Invalid or missing status."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the status
        membership.status = new_status
        membership.save()
        
        # If banned, notify the user
        if new_status == 'banned':
            Notification.objects.create(
                recipient=membership.user,
                notification_type='system',
                title=f'Banned from {community.name}',
                message=f'You have been banned from the community {community.name}.'
            )
        
        serializer = self.get_serializer(membership)
        return Response(serializer.data)


class CommunityRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community rules."""
    serializer_class = CommunityRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return rules the user can access."""
        user = self.request.user
        
        # Return rules for communities where the user is a moderator or creator
        return CommunityRule.objects.filter(
            Q(community__creator=user) | Q(community__moderators=user)
        ).distinct().order_by('community', 'position')

    def perform_create(self, serializer):
        """Create a new rule."""
        community = serializer.validated_data['community']
        
        # Ensure the user is a moderator
        if self.request.user != community.creator and self.request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can create rules."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save()


class CommunityPostViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community posts."""
    serializer_class = CommunityPostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'body', 'tags__name']

    def get_queryset(self):
        """Return posts the user can access."""
        user = self.request.user
        
        # Return posts from:
        # 1. Public communities
        # 2. Restricted/private communities where the user is a member
        return CommunityPost.objects.filter(
            Q(community__visibility='public') |
            (Q(community__visibility__in=['restricted', 'private']) & 
             Q(community__memberships__user=user, community__memberships__status='member'))
        ).filter(
            status='approved'
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        """Create a new post."""
        community = serializer.validated_data['community']
        
        # Ensure the user is a member
        if not CommunityMembership.objects.filter(
            user=self.request.user, community=community, status='member'
        ).exists():
            return Response(
                {"detail": "You must be a member to post in this community."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Set the initial status based on community settings
        initial_status = 'pending' if community.requires_post_approval else 'approved'
        
        # Create the post
        post = serializer.save(
            user=self.request.user,
            status=initial_status
        )
        
        # Increment the posts_count if approved
        if initial_status == 'approved':
            community.posts_count += 1
            community.save()
        
        # If needs approval, notify moderators
        if initial_status == 'pending':
            # Notify moderators
            for moderator in community.moderators.all():
                Notification.objects.create(
                    recipient=moderator,
                    notification_type='system',
                    title=f'New Post in {community.name}',
                    message=f'A new post requires approval in {community.name}.'
                )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending post."""
        post = self.get_object()
        community = post.community
        
        # Ensure the user is a moderator
        if request.user != community.creator and request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can approve posts."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already approved
        if post.status != 'pending':
            return Response(
                {"detail": "Post is not pending approval."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve the post
        post.status = 'approved'
        post.save()
        
        # Increment the posts_count
        community.posts_count += 1
        community.save()
        
        # Notify the author
        Notification.objects.create(
            recipient=post.user,
            notification_type='system',
            title=f'Post Approved in {community.name}',
            message=f'Your post "{post.title}" has been approved in {community.name}.'
        )
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a pending post."""
        post = self.get_object()
        community = post.community
        
        # Ensure the user is a moderator
        if request.user != community.creator and request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can reject posts."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already approved or rejected
        if post.status != 'pending':
            return Response(
                {"detail": "Post is not pending approval."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the reason for rejection
        reason = request.data.get('reason', 'No reason provided.')
        
        # Reject the post
        post.status = 'rejected'
        post.save()
        
        # Notify the author
        Notification.objects.create(
            recipient=post.user,
            notification_type='system',
            title=f'Post Rejected in {community.name}',
            message=f'Your post "{post.title}" was rejected in {community.name}. Reason: {reason}'
        )
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin a post to the top of the community."""
        post = self.get_object()
        community = post.community
        
        # Ensure the user is a moderator
        if request.user != community.creator and request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can pin posts."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if approved
        if post.status != 'approved':
            return Response(
                {"detail": "Only approved posts can be pinned."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Pin the post
        post.is_pinned = True
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Unpin a post from the top of the community."""
        post = self.get_object()
        community = post.community
        
        # Ensure the user is a moderator
        if request.user != community.creator and request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can unpin posts."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Unpin the post
        post.is_pinned = False
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)


class CommunityInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community invitations."""
    serializer_class = CommunityInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return invitations relevant to the user."""
        user = self.request.user
        
        # Return invitations that:
        # 1. The user sent
        # 2. The user received
        return CommunityInvitation.objects.filter(
            Q(inviter=user) | Q(invitee=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Create a new invitation."""
        community = serializer.validated_data['community']
        invitee = serializer.validated_data['invitee']
        
        # Ensure the user is a member
        if not CommunityMembership.objects.filter(
            user=self.request.user, community=community, status='member'
        ).exists():
            return Response(
                {"detail": "You must be a member to invite others to this community."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the invitee is already a member
        if CommunityMembership.objects.filter(
            user=invitee, community=community
        ).exists():
            return Response(
                {"detail": "User is already a member or has a pending request."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if there's already an invitation
        if CommunityInvitation.objects.filter(
            community=community, invitee=invitee, status='pending'
        ).exists():
            return Response(
                {"detail": "An invitation already exists for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the invitation
        invitation = serializer.save(inviter=self.request.user, status='pending')
        
        # Notify the invitee
        Notification.objects.create(
            recipient=invitee,
            notification_type='invitation',
            title=f'Invitation to Join {community.name}',
            message=f'{self.request.user.username} has invited you to join {community.name}.'
        )
        
        return invitation

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept an invitation."""
        invitation = self.get_object()
        
        # Ensure the user is the invitee
        if request.user != invitation.invitee:
            return Response(
                {"detail": "You can only accept invitations sent to you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if pending
        if invitation.status != 'pending':
            return Response(
                {"detail": "Invitation has already been accepted or declined."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the invitation
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Create the membership
        CommunityMembership.objects.create(
            user=request.user,
            community=invitation.community,
            status='member'
        )
        
        # Increment members count
        community = invitation.community
        community.members_count += 1
        community.save()
        
        # Notify the inviter
        Notification.objects.create(
            recipient=invitation.inviter,
            notification_type='system',
            title=f'Invitation Accepted',
            message=f'{request.user.username} has accepted your invitation to join {community.name}.'
        )
        
        serializer = self.get_serializer(invitation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline an invitation."""
        invitation = self.get_object()
        
        # Ensure the user is the invitee
        if request.user != invitation.invitee:
            return Response(
                {"detail": "You can only decline invitations sent to you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if pending
        if invitation.status != 'pending':
            return Response(
                {"detail": "Invitation has already been accepted or declined."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the invitation
        invitation.status = 'declined'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        serializer = self.get_serializer(invitation)
        return Response(serializer.data)


class CommunityTopicViewSet(viewsets.ModelViewSet):
    """ViewSet for managing community topics."""
    serializer_class = CommunityTopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return topics the user can access."""
        user = self.request.user
        
        # Return topics from communities where:
        # 1. The community is public
        # 2. The community is restricted/private and the user is a member
        return CommunityTopic.objects.filter(
            Q(community__visibility='public') |
            (Q(community__visibility__in=['restricted', 'private']) & 
             Q(community__memberships__user=user, community__memberships__status='member'))
        ).distinct().order_by('community', 'position')

    def perform_create(self, serializer):
        """Create a new topic."""
        community = serializer.validated_data['community']
        
        # Ensure the user is a moderator
        if self.request.user != community.creator and self.request.user not in community.moderators.all():
            return Response(
                {"detail": "Only the creator or moderators can create topics."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(created_by=self.request.user)


class DiscoverCommunitiesView(generics.ListAPIView):
    """View for discovering public communities."""
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        """Return public communities ordered by popularity."""
        return Community.objects.filter(
            visibility='public'
        ).order_by('-members_count', '-posts_count', '-created_at')


class RecommendedCommunitiesView(generics.ListAPIView):
    """View for recommended communities for the user."""
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return recommended communities based on user connections."""
        user = self.request.user
        
        # Get communities the user's connections are in
        from apps.interactions.models import Connection
        connections = Connection.objects.filter(follower=user).values_list('followed', flat=True)
        
        connection_communities = CommunityMembership.objects.filter(
            user__in=connections, status='member'
        ).values_list('community', flat=True)
        
        # Exclude communities the user is already in
        user_communities = CommunityMembership.objects.filter(
            user=user
        ).values_list('community', flat=True)
        
        recommended = Community.objects.filter(
            id__in=connection_communities
        ).exclude(
            id__in=user_communities
        ).filter(
            visibility__in=['public', 'restricted']
        ).annotate(
            connection_count=Count('memberships__user', filter=Q(memberships__user__in=connections))
        ).order_by('-connection_count', '-members_count')
        
        return recommended


class JoinCommunityView(APIView):
    """View for joining a community."""
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        """Join a community."""
        community = get_object_or_404(Community, slug=slug)
        user = request.user
        
        # Check if already a member
        existing_membership = CommunityMembership.objects.filter(
            user=user, community=community
        ).first()
        
        if existing_membership:
            if existing_membership.status == 'member':
                return Response(
                    {"detail": "You are already a member of this community."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif existing_membership.status == 'banned':
                return Response(
                    {"detail": "You have been banned from this community."},
                    status=status.HTTP_403_FORBIDDEN
                )
            else:  # 'pending'
                return Response(
                    {"detail": "Your membership request is pending approval."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle based on community visibility
        if community.visibility == 'public':
            # Create membership directly
            membership = CommunityMembership.objects.create(
                user=user,
                community=community,
                status='member'
            )
            
            # Increment members count
            community.members_count += 1
            community.save()
            
            serializer = CommunityMembershipSerializer(membership)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif community.visibility == 'restricted':
            # Create pending membership
            membership = CommunityMembership.objects.create(
                user=user,
                community=community,
                status='pending'
            )
            
            # Notify moderators
            for moderator in community.moderators.all():
                Notification.objects.create(
                    recipient=moderator,
                    notification_type='system',
                    title=f'New Membership Request for {community.name}',
                    message=f'{user.username} has requested to join {community.name}.'
                )
            
            serializer = CommunityMembershipSerializer(membership)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:  # 'private'
            return Response(
                {"detail": "This community is private. You must be invited to join."},
                status=status.HTTP_403_FORBIDDEN
            )


class LeaveCommunityView(APIView):
    """View for leaving a community."""
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        """Leave a community."""
        community = get_object_or_404(Community, slug=slug)
        user = request.user
        
        # Check if a member
        membership = CommunityMembership.objects.filter(
            user=user, community=community, status='member'
        ).first()
        
        if not membership:
            return Response(
                {"detail": "You are not a member of this community."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot leave if you're the creator
        if user == community.creator:
            return Response(
                {"detail": "As the creator, you cannot leave this community. Transfer ownership or delete it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove as moderator if applicable
        if user in community.moderators.all():
            community.moderators.remove(user)
        
        # Delete membership
        membership.delete()
        
        # Decrement members count
        community.members_count -= 1
        community.save()
        
        return Response({"status": "left community"}, status=status.HTTP_200_OK) 