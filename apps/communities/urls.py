from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.CommunityViewSet, basename='communities')
router.register('memberships', views.CommunityMembershipViewSet, basename='community-memberships')
router.register('rules', views.CommunityRuleViewSet, basename='community-rules')
router.register('posts', views.CommunityPostViewSet, basename='community-posts')
router.register('invitations', views.CommunityInvitationViewSet, basename='community-invitations')
router.register('topics', views.CommunityTopicViewSet, basename='community-topics')

urlpatterns = [
    path('discover/', views.DiscoverCommunitiesView.as_view(), name='discover-communities'),
    path('recommended/', views.RecommendedCommunitiesView.as_view(), name='recommended-communities'),
    path('<slug:slug>/join/', views.JoinCommunityView.as_view(), name='join-community'),
    path('<slug:slug>/leave/', views.LeaveCommunityView.as_view(), name='leave-community'),
]

urlpatterns += router.urls 