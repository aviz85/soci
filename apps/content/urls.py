from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('posts', views.PostViewSet, basename='posts')
router.register('tags', views.TagViewSet, basename='tags')
router.register('reactions', views.ReactionViewSet, basename='reactions')
router.register('comments', views.CommentViewSet, basename='comments')
router.register('saved', views.SavedContentViewSet, basename='saved-content')

urlpatterns = [
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('trending/', views.TrendingView.as_view(), name='trending'),
    path('search/', views.ContentSearchView.as_view(), name='content-search'),
]

urlpatterns += router.urls 