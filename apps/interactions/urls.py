from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('connections', views.ConnectionViewSet, basename='connections')
router.register('messages', views.MessageViewSet, basename='messages')
router.register('conversations', views.ConversationViewSet, basename='conversations')
router.register('notifications', views.NotificationViewSet, basename='notifications')
router.register('spaces', views.CollaborativeSpaceViewSet, basename='collaborative-spaces')

urlpatterns = [
    path('follow/<int:user_id>/', views.FollowUserView.as_view(), name='follow-user'),
    path('unfollow/<int:user_id>/', views.UnfollowUserView.as_view(), name='unfollow-user'),
    path('conversations/<int:conversation_id>/messages/', views.ConversationMessagesView.as_view(), name='conversation-messages'),
    path('conversations/<int:conversation_id>/read/', views.MarkConversationReadView.as_view(), name='mark-conversation-read'),
    path('notifications/read-all/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('notifications/read_all/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read-underscore'),
]

urlpatterns += router.urls 