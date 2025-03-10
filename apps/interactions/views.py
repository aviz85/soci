from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count

from .models import (
    Connection, Message, MessageAttachment, Conversation, ConversationMessage,
    ConversationMessageAttachment, ConversationRead, Notification,
    CollaborativeSpace, SpaceMembership
)
from .serializers import (
    ConnectionSerializer, MessageSerializer, MessageAttachmentSerializer,
    ConversationSerializer, ConversationMessageSerializer, ConversationMessageAttachmentSerializer,
    ConversationReadSerializer, NotificationSerializer,
    CollaborativeSpaceSerializer, SpaceMembershipSerializer
)
from apps.users.models import User


class ConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user connections."""
    serializer_class = ConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the current user's following connections."""
        return Connection.objects.filter(follower=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the follower."""
        serializer.save(follower=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing direct messages."""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return messages the current user has sent or received."""
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the current user as the sender."""
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read."""
        message = self.get_object()
        
        # Ensure the user is the recipient
        if message.recipient != request.user:
            return Response(
                {"detail": "You can only mark messages addressed to you as read."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
        
        return Response({"status": "message marked as read"})

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """Add an attachment to a message."""
        message = self.get_object()
        
        # Ensure the user is the sender
        if message.sender != request.user:
            return Response(
                {"detail": "You can only add attachments to your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageAttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(message=message)
            
            # Update the message to indicate it has an attachment
            if not message.has_attachment:
                message.has_attachment = True
                message.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversations."""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return conversations the current user is participating in."""
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()
        
        return Conversation.objects.filter(
            participants=self.request.user
        ).order_by('-updated_at')

    def perform_create(self, serializer):
        """Create a new conversation."""
        conversation = serializer.save()
        
        # Add the current user as a participant
        conversation.participants.add(self.request.user)
        
        # Add other participants from the request
        participant_ids = self.request.data.get('participant_ids', [])
        for participant_id in participant_ids:
            try:
                user = User.objects.get(id=participant_id)
                conversation.participants.add(user)
            except User.DoesNotExist:
                pass
        
        return conversation

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to a conversation."""
        conversation = self.get_object()
        
        # Ensure the user is already a participant
        if request.user not in conversation.participants.all():
            return Response(
                {"detail": "You must be a participant to add others to this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "No user specified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            conversation.participants.add(user)
            return Response({"status": "participant added"})
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a conversation."""
        conversation = self.get_object()
        
        if request.user in conversation.participants.all():
            conversation.participants.remove(request.user)
            return Response({"status": "left conversation"})
        
        return Response(
            {"detail": "You are not a participant in this conversation."},
            status=status.HTTP_400_BAD_REQUEST
        )


class ConversationMessagesView(generics.ListCreateAPIView):
    """View for listing and creating messages in a conversation."""
    serializer_class = ConversationMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return messages for a specific conversation."""
        conversation_id = self.kwargs.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Ensure the user is a participant
        if self.request.user not in conversation.participants.all():
            return ConversationMessage.objects.none()
        
        return ConversationMessage.objects.filter(
            conversation=conversation
        ).order_by('created_at')

    def perform_create(self, serializer):
        """Create a message in the conversation."""
        conversation_id = self.kwargs.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Ensure the user is a participant
        if self.request.user not in conversation.participants.all():
            return Response(
                {"detail": "You are not a participant in this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message
        serializer.save(
            conversation=conversation,
            sender=self.request.user
        )
        
        # Update the conversation's updated_at time
        conversation.updated_at = timezone.now()
        conversation.save()


class MarkConversationReadView(APIView):
    """View for marking a conversation as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        """Mark a conversation as read."""
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Ensure the user is a participant
        if request.user not in conversation.participants.all():
            return Response(
                {"detail": "You are not a participant in this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update or create the read mark
        read_mark, created = ConversationRead.objects.update_or_create(
            conversation=conversation,
            user=request.user,
            defaults={"last_read_at": timezone.now()}
        )
        
        serializer = ConversationReadSerializer(read_mark)
        return Response(serializer.data)


class FollowUserView(APIView):
    """View for following a user."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Follow a user."""
        user_to_follow = get_object_or_404(User, id=user_id)
        
        # Can't follow yourself
        if user_to_follow == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already following
        if Connection.objects.filter(follower=request.user, followed=user_to_follow).exists():
            return Response(
                {"detail": "You are already following this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the connection
        connection = Connection.objects.create(
            follower=request.user,
            followed=user_to_follow
        )
        
        serializer = ConnectionSerializer(connection)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnfollowUserView(APIView):
    """View for unfollowing a user."""
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Unfollow a user."""
        user_to_unfollow = get_object_or_404(User, id=user_id)
        
        # Find and delete the connection
        connection = Connection.objects.filter(
            follower=request.user,
            followed=user_to_unfollow
        ).first()
        
        if not connection:
            return Response(
                {"detail": "You are not following this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        connection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notifications."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the current user's notifications, filtered if requested."""
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
            
        queryset = Notification.objects.filter(
            recipient=self.request.user
        )
        
        # Apply filtering if requested
        filter_param = self.request.query_params.get('filter', None)
        if filter_param:
            if filter_param == 'read':
                queryset = queryset.filter(is_read=True)
            elif filter_param == 'unread':
                queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        
        return Response({"status": "notification marked as read"})


class MarkAllNotificationsReadView(APIView):
    """View for marking all notifications as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Mark all notifications as read."""
        now = timezone.now()
        
        # Update all unread notifications
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=now)
        
        return Response({"count": count, "status": "all notifications marked as read"})


class CollaborativeSpaceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing collaborative spaces."""
    serializer_class = CollaborativeSpaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        """Return spaces the current user is a member of."""
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return CollaborativeSpace.objects.none()
            
        return CollaborativeSpace.objects.filter(
            Q(members=self.request.user) | Q(is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        """Create a new space and add the current user as creator and member."""
        space = serializer.save(creator=self.request.user)
        
        # Add the creator as an admin member
        SpaceMembership.objects.create(
            user=self.request.user,
            space=space,
            role='admin'
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to a space."""
        space = self.get_object()
        
        # Check if the current user is an admin
        try:
            membership = SpaceMembership.objects.get(
                user=request.user,
                space=space
            )
            if membership.role != 'admin':
                return Response(
                    {"detail": "Only admins can add members."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except SpaceMembership.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this space."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add the new member
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "No user specified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        role = request.data.get('role', 'contributor')
        
        try:
            user = User.objects.get(id=user_id)
            # Check if already a member
            if SpaceMembership.objects.filter(user=user, space=space).exists():
                return Response(
                    {"detail": "User is already a member of this space."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the membership
            member = SpaceMembership.objects.create(
                user=user,
                space=space,
                role=role
            )
            
            # Create a notification for the added user
            Notification.objects.create(
                recipient=user,
                notification_type='invitation',
                title='Space Invitation',
                message=f"You've been added to the space '{space.name}'."
            )
            
            serializer = SpaceMembershipSerializer(member)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from a space."""
        space = self.get_object()
        
        # Check if the current user is an admin
        try:
            membership = SpaceMembership.objects.get(
                user=request.user,
                space=space
            )
            if membership.role != 'admin':
                return Response(
                    {"detail": "Only admins can remove members."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except SpaceMembership.DoesNotExist:
            return Response(
                {"detail": "You are not a member of this space."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove the member
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"detail": "No user specified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            
            # Cannot remove the creator
            if user == space.creator:
                return Response(
                    {"detail": "Cannot remove the creator of the space."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete the membership
            membership = SpaceMembership.objects.filter(
                user=user,
                space=space
            ).first()
            
            if not membership:
                return Response(
                    {"detail": "User is not a member of this space."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a collaborative space."""
        space = self.get_object()
        
        # Find the user's membership
        membership = SpaceMembership.objects.filter(
            user=request.user,
            space=space
        ).first()
        
        if not membership:
            return Response(
                {"detail": "You are not a member of this space."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot leave if you're the creator
        if request.user == space.creator:
            return Response(
                {"detail": "As the creator, you cannot leave this space. Transfer ownership or delete it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get members of a space."""
        space = self.get_object()
        
        # Ensure the user has access to see members
        if not space.is_public and request.user not in space.members.all():
            return Response(
                {"detail": "You do not have permission to view this space's members."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        memberships = SpaceMembership.objects.filter(
            space=space
        ).order_by('role', 'joined_at')
        
        serializer = SpaceMembershipSerializer(memberships, many=True)
        return Response(serializer.data) 