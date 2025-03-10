import random
from datetime import datetime, timedelta, date, time
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from apps.users.models import (
    UserPreference, MoodBoard, MoodBoardItem, WellbeingData
)
from apps.content.models import (
    Tag, Post, Media, Reaction, Comment, SavedContent
)
from apps.communities.models import (
    Community, CommunityMembership, CommunityRule, 
    CommunityPost, CommunityInvitation, CommunityTopic
)
from apps.interactions.models import (
    Connection, Message, Conversation, ConversationMessage,
    ConversationRead, Notification, CollaborativeSpace, SpaceMembership
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--section',
            type=str,
            help='Specific section to populate (users, preferences, wellbeing, mood_boards, connections, tags, posts, communities, conversations, spaces, notifications, all)',
            default='all'
        )

    def handle(self, *args, **kwargs):
        section = kwargs['section']
        self.stdout.write(f'Populating {section} section...')
        
        # Always initialize users list
        if section != 'users':
            self.load_users()
        
        with transaction.atomic():
            # Always create users first if not specifically choosing another section
            if section in ['users', 'all']:
                self.create_users()
            
            # These sections depend on users
            if section in ['preferences', 'all']:
                self.create_user_preferences()
                
            if section in ['wellbeing', 'all']:
                self.create_wellbeing_data()
                
            if section in ['mood_boards', 'all']:
                self.create_mood_boards()
                
            if section in ['connections', 'all']:
                self.create_connections()
                
            if section in ['tags', 'all']:
                self.create_tags()
                
            # These depend on tags and users
            if section in ['posts', 'all']:
                # Load tags if we're only creating posts
                if section == 'posts':
                    self.load_tags()
                self.create_posts()
                self.create_post_interactions()
                
            if section in ['communities', 'all']:
                # Load tags if we're only creating communities
                if section == 'communities' and not hasattr(self, 'tags'):
                    self.load_tags()
                self.create_communities()
                self.create_community_content()
                
            if section in ['conversations', 'all']:
                self.create_conversations()
                
            if section in ['spaces', 'all']:
                self.create_collaborative_spaces()
                
            if section in ['notifications', 'all']:
                self.create_notifications()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {section} data'))
        
    def load_users(self):
        """Load existing users from the database."""
        self.stdout.write('Loading existing users...')
        self.users = list(User.objects.exclude(username='admin').order_by('id'))
        self.stdout.write(f'Loaded {len(self.users)} users')
        
    def load_tags(self):
        """Load existing tags from the database."""
        self.stdout.write('Loading existing tags...')
        self.tags = list(Tag.objects.all())
        if not self.tags:
            self.create_tags()
        else:
            self.stdout.write(f'Loaded {len(self.tags)} tags')

    def create_users(self):
        self.stdout.write('Creating users...')
        # Create admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
        
        # Create regular users
        self.users = []
        for i in range(1, 11):
            username = f'user{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'user{i}@example.com',
                    password='password123',
                    first_name=f'Test{i}',
                    last_name=f'User{i}'
                )
                self.users.append(user)
            else:
                self.users.append(User.objects.get(username=username))
        
        self.stdout.write(f'Created {len(self.users)} users')

    def create_user_preferences(self):
        self.stdout.write('Creating user preferences...')
        for user in self.users:
            UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    'email_notifications': bool(random.randint(0, 1)),
                    'push_notifications': bool(random.randint(0, 1)),
                    'content_language': random.choice(['en', 'es', 'fr']),
                    'content_sensitivity': random.choice(['low', 'medium', 'high']),
                    'who_can_message': random.choice(['everyone', 'followers', 'none']),
                    'daily_usage_limit': random.choice([30, 60, 90, 120]),
                    'scheduled_downtime_start': time(22, 0) if random.randint(0, 1) else None,
                    'scheduled_downtime_end': time(7, 0) if random.randint(0, 1) else None,
                }
            )

    def create_wellbeing_data(self):
        self.stdout.write('Creating wellbeing data...')
        today = date.today()
        for user in self.users:
            # Create wellbeing data for the past week
            for i in range(7):
                entry_date = today - timedelta(days=i)
                # Check for existing entries and only create if not exists
                if not WellbeingData.objects.filter(user=user, date=entry_date).exists():
                    WellbeingData.objects.create(
                        user=user,
                        date=entry_date,
                        time_spent=random.randint(900, 7200),  # 15 min to 2 hours
                        sessions_count=random.randint(1, 10),
                        interactions_count=random.randint(5, 50),
                        mood_assessment=random.choice(['positive', 'neutral', 'negative']),
                    )

    def create_mood_boards(self):
        self.stdout.write('Creating mood boards...')
        for user in self.users:
            # Create 1-3 mood boards per user
            for i in range(random.randint(1, 3)):
                mood_board, created = MoodBoard.objects.get_or_create(
                    user=user,
                    title=f'{user.username}\'s Mood Board {i+1}',
                    defaults={
                        'description': f'A collection of moods and inspirations for {user.username}',
                        'is_current': i == 0,  # First one is current
                    }
                )
                
                # Add 3-5 items to each mood board
                if created:
                    for j in range(random.randint(3, 5)):
                        MoodBoardItem.objects.create(
                            mood_board=mood_board,
                            content_type=random.choice(['image', 'text', 'color']),
                            content=f'Sample content {j+1} for mood board',
                            position=j,
                        )

    def create_connections(self):
        self.stdout.write('Creating connections between users...')
        for follower in self.users:
            # Each user follows 3-7 random other users
            for _ in range(random.randint(3, 7)):
                followed = random.choice(self.users)
                if followed != follower:
                    Connection.objects.get_or_create(
                        follower=follower,
                        followed=followed,
                        defaults={
                            'strength': random.choice(['weak', 'moderate', 'strong']),
                            'interaction_count': random.randint(0, 100),
                            'last_interaction': timezone.now() - timedelta(days=random.randint(0, 30)),
                        }
                    )

    def create_tags(self):
        self.stdout.write('Creating tags...')
        self.tags = []
        tag_names = ['technology', 'science', 'art', 'music', 'food', 'travel', 
                    'fitness', 'fashion', 'education', 'wellbeing', 'nature', 'sports']
        
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={'slug': name}
            )
            self.tags.append(tag)

    def create_posts(self):
        self.stdout.write('Creating posts...')
        self.posts = []
        
        for user in self.users:
            # Create 5-10 posts per user
            post_count = random.randint(5, 10)
            existing_posts = Post.objects.filter(user=user).count()
            
            # Only create new posts if needed
            for i in range(existing_posts, existing_posts + post_count):
                post = Post.objects.create(
                    user=user,
                    title=f'Post {i+1} by {user.username}',
                    body=f'This is test post number {i+1} by {user.username} with some random content to make it interesting.',
                    visibility=random.choice(['public', 'followers', 'private']),
                    expires_at=timezone.now() + timedelta(days=random.randint(30, 90)) if random.random() > 0.7 else None,
                    view_count=random.randint(0, 1000),
                    engagement_score=random.uniform(0, 10),
                )
                
                # Add 1-3 random tags to the post
                post_tags = random.sample(self.tags, random.randint(1, 3))
                post.tags.set(post_tags)
                
                # Add post to the list
                self.posts.append(post)
        
        self.stdout.write(f'Created {len(self.posts)} posts')

    def create_post_interactions(self):
        self.stdout.write('Creating post interactions...')
        post_content_type = ContentType.objects.get_for_model(Post)
        
        for post in self.posts:
            # Create 3-7 comments per post
            for _ in range(random.randint(3, 7)):
                commenter = random.choice(self.users)
                comment = Comment.objects.create(
                    user=commenter,
                    content_type=post_content_type,
                    object_id=post.id,
                    body=f'This is a test comment by {commenter.username} on post "{post.title}"',
                    is_deleted=random.random() > 0.9,  # 10% chance of being deleted
                )
                
                # 30% chance of having replies
                if random.random() > 0.7:
                    # Add 1-3 replies
                    for _ in range(random.randint(1, 3)):
                        replier = random.choice(self.users)
                        Comment.objects.create(
                            user=replier,
                            content_type=post_content_type,
                            object_id=post.id,
                            parent=comment,
                            body=f'Reply by {replier.username} to comment by {commenter.username}',
                        )
            
            # Create 5-15 reactions per post
            for _ in range(random.randint(5, 15)):
                reactor = random.choice(self.users)
                Reaction.objects.get_or_create(
                    user=reactor,
                    content_type=post_content_type,
                    object_id=post.id,
                    defaults={
                        'reaction_type': random.choice(['like', 'love', 'laugh', 'sad', 'angry', 'wow', 'support']),
                    }
                )
            
            # 20% chance of post being saved by users
            for user in self.users:
                if random.random() > 0.8:
                    SavedContent.objects.get_or_create(
                        user=user,
                        content_type=post_content_type,
                        object_id=post.id,
                    )

    def create_communities(self):
        self.stdout.write('Creating communities...')
        self.communities = []
        community_names = [
            'Tech Enthusiasts', 'Science Explorers', 'Art Lovers', 'Music Fans', 
            'Foodies Unite', 'Travel Adventures', 'Fitness Fanatics', 'Fashion Forward',
            'Educational Hub', 'Wellbeing Circle', 'Nature Photography', 'Sports Talk'
        ]
        
        for i, name in enumerate(community_names):
            try:
                creator = self.users[i % len(self.users)]
                slug = name.lower().replace(' ', '-')
                
                community, created = Community.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'description': f'A community for people interested in {name.lower()}',
                        'creator': creator,
                        'visibility': random.choice(['public', 'restricted', 'private']),
                        'allow_post_images': random.random() > 0.1,  # 90% chance of allowing images
                        'allow_post_videos': random.random() > 0.2,  # 80% chance of allowing videos
                        'requires_post_approval': random.random() > 0.7,  # 30% chance of requiring approval
                        'members_count': 0,  # Will be updated as members are added
                        'posts_count': 0,  # Will be updated as posts are added
                    }
                )
                
                if created:
                    # Add creator as moderator
                    community.moderators.add(creator)
                
                self.communities.append(community)
                
                # Add members to the community (including creator)
                members = random.sample(self.users, random.randint(3, len(self.users)))
                if creator not in members:
                    members.append(creator)
                
                for user in members:
                    membership, _ = CommunityMembership.objects.get_or_create(
                        user=user,
                        community=community,
                        defaults={'status': 'member'}
                    )
                
                # Update members count
                community.members_count = CommunityMembership.objects.filter(
                    community=community, status='member'
                ).count()
                community.save()
                
                # Create 2-5 community rules
                if created:
                    for j in range(random.randint(2, 5)):
                        CommunityRule.objects.create(
                            community=community,
                            title=f'Rule {j+1}',
                            description=f'Description of rule {j+1} for {community.name}',
                            position=j,
                        )
                    
                    # Create 3-5 community topics
                    for j in range(random.randint(3, 5)):
                        CommunityTopic.objects.create(
                            community=community,
                            name=f'Topic {j+1}',
                            description=f'Description of topic {j+1} for {community.name}',
                            icon='📌',
                            position=j,
                            created_by=creator,
                        )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error creating community {name}: {e}"))

    def create_community_content(self):
        self.stdout.write('Creating community content...')
        for community in self.communities:
            # Get community members
            memberships = CommunityMembership.objects.filter(
                community=community, status='member'
            )
            members = [m.user for m in memberships]
            
            # Create 5-10 posts per community
            for i in range(random.randint(5, 10)):
                author = random.choice(members)
                status_value = 'approved'
                if community.requires_post_approval and random.random() > 0.7:
                    status_value = 'pending'  # 30% chance of pending if approval required
                
                post = CommunityPost.objects.create(
                    community=community,
                    user=author,
                    title=f'Community Post {i+1} in {community.name}',
                    body=f'This is a community post by {author.username} in {community.name}.',
                    status=status_value,
                    visibility='public',  # Community posts are always public within the community
                    is_pinned=i == 0 and random.random() > 0.7,  # First post has 30% chance of being pinned
                    view_count=random.randint(0, 500),
                    engagement_score=random.uniform(0, 10),
                )
                
                # Add 1-3 random tags to the post
                post_tags = random.sample(self.tags, random.randint(1, 3))
                post.tags.set(post_tags)
            
            # Update posts count for approved posts
            community.posts_count = CommunityPost.objects.filter(
                community=community, status='approved'
            ).count()
            community.save()
            
            # Create pending invitations (30% chance for non-members)
            non_members = [u for u in self.users if u not in members]
            for user in non_members:
                if random.random() > 0.7:
                    inviter = random.choice(members)
                    CommunityInvitation.objects.get_or_create(
                        community=community,
                        inviter=inviter,
                        invitee=user,
                        defaults={
                            'status': 'pending',
                            'message': f'Hey {user.username}, join our {community.name} community!',
                        }
                    )

    def create_conversations(self):
        self.stdout.write('Creating conversations and messages...')
        
        # Check existing conversation count to avoid duplicating too many
        existing_count = Conversation.objects.count()
        if existing_count > 15:
            self.stdout.write(f"Skipping conversation creation, already have {existing_count} conversations")
            return
            
        # Create one-on-one conversations
        for i in range(15):  # Create 15 different conversations
            try:
                participants = random.sample(self.users, 2)  # Two random users
                
                conversation = Conversation.objects.create(
                    is_group=False,
                )
                conversation.participants.set(participants)
                
                # Add 5-15 messages per conversation
                for j in range(random.randint(5, 15)):
                    sender = participants[j % 2]  # Alternate sender
                    message = ConversationMessage.objects.create(
                        conversation=conversation,
                        sender=sender,
                        body=f'Message {j+1} from {sender.username} in a one-on-one conversation',
                    )
                
                # Set last read for participants (if they've read messages)
                for participant in participants:
                    if random.random() > 0.3:  # 70% chance of having read
                        last_message = ConversationMessage.objects.filter(
                            conversation=conversation
                        ).order_by('-created_at').first()
                        
                        if last_message:
                            ConversationRead.objects.create(
                                conversation=conversation,
                                user=participant,
                                last_read_at=last_message.created_at - timedelta(minutes=random.randint(0, 60))
                            )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error creating conversation {i}: {e}"))
        
        # Create group conversations
        existing_group_count = Conversation.objects.filter(is_group=True).count()
        if existing_group_count > 5:
            self.stdout.write(f"Skipping group conversation creation, already have {existing_group_count} group conversations")
            return
            
        for i in range(5):  # Create 5 different group conversations
            try:
                participant_count = random.randint(3, 7)  # 3-7 participants
                participants = random.sample(self.users, participant_count)
                
                conversation = Conversation.objects.create(
                    is_group=True,
                    name=f'Group Conversation {i+1}',
                )
                conversation.participants.set(participants)
                
                # Add 10-30 messages per group conversation
                for j in range(random.randint(10, 30)):
                    sender = random.choice(participants)
                    message = ConversationMessage.objects.create(
                        conversation=conversation,
                        sender=sender,
                        body=f'Message {j+1} from {sender.username} in the group conversation',
                    )
                
                # Set last read for participants (if they've read messages)
                for participant in participants:
                    if random.random() > 0.3:  # 70% chance of having read
                        last_message = ConversationMessage.objects.filter(
                            conversation=conversation
                        ).order_by('-created_at').first()
                        
                        if last_message:
                            ConversationRead.objects.create(
                                conversation=conversation,
                                user=participant,
                                last_read_at=last_message.created_at - timedelta(minutes=random.randint(0, 60))
                            )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error creating group conversation {i}: {e}"))

    def create_collaborative_spaces(self):
        self.stdout.write('Creating collaborative spaces...')
        for i in range(5):  # Create 5 collaborative spaces
            creator = random.choice(self.users)
            
            space = CollaborativeSpace.objects.create(
                name=f'Collaborative Space {i+1}',
                description=f'A space for collaboration on project {i+1}',
                creator=creator,
                is_public=random.random() > 0.4,  # 60% chance of being public
                allows_comments=random.random() > 0.2,  # 80% chance of allowing comments
            )
            
            # Add members with different roles
            member_count = random.randint(3, 7)
            members = random.sample(self.users, member_count)
            if creator not in members:
                members.append(creator)
            
            for user in members:
                role = 'admin' if user == creator else random.choice(['viewer', 'contributor', 'editor'])
                SpaceMembership.objects.create(
                    space=space,
                    user=user,
                    role=role,
                )

    def create_notifications(self):
        self.stdout.write('Creating notifications...')
        notification_types = [
            'follow', 'like', 'comment', 'mention', 'message', 'invitation', 'system'
        ]
        
        for user in self.users:
            # Create 5-15 random notifications per user
            for i in range(random.randint(5, 15)):
                notification_type = random.choice(notification_types)
                is_read = random.random() > 0.5  # 50% chance of being read
                
                notification = Notification.objects.create(
                    recipient=user,
                    notification_type=notification_type,
                    title=f'New {notification_type} notification',
                    message=f'This is a test {notification_type} notification number {i+1}',
                    link='#',  # Placeholder link
                    is_read=is_read,
                    read_at=timezone.now() if is_read else None,
                ) 