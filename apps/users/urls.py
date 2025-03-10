from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, CurrentUserView, UserViewSet,
    UserPreferenceViewSet, MoodBoardViewSet, WellbeingDataViewSet
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

# Create separate routers for nested resources
preferences_router = DefaultRouter()
preferences_router.register(r'', UserPreferenceViewSet, basename='userpreference')

mood_boards_router = DefaultRouter()
mood_boards_router.register(r'', MoodBoardViewSet, basename='moodboard')

wellbeing_router = DefaultRouter()
wellbeing_router.register(r'', WellbeingDataViewSet, basename='wellbeingdata')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('preferences/', include(preferences_router.urls)),
    path('mood-boards/', include(mood_boards_router.urls)),
    path('wellbeing/', include(wellbeing_router.urls)),
    path('', include(router.urls)),
] 