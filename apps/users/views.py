from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import UserPreference, MoodBoard, MoodBoardItem, WellbeingData
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserPreferenceSerializer,
    MoodBoardSerializer, MoodBoardItemSerializer, WellbeingDataSerializer
)
from datetime import time

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Delete any existing preferences first
        UserPreference.objects.filter(user=user).delete()
        # Create default user preferences
        UserPreference.objects.create(
            user=user,
            email_notifications=True,
            push_notifications=True,
            content_language='en',
            content_sensitivity='medium',
            who_can_message='everyone',
            daily_usage_limit=120,
            scheduled_downtime_start=time(22, 0),
            scheduled_downtime_end=time(6, 0)
        )


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the current user."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users."""
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            users = self.get_queryset().filter(username__icontains=query)
            serializer = self.get_serializer(users, many=True)
            return Response(serializer.data)
        return Response([])


class UserPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user preferences."""
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user).order_by('id')


class MoodBoardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mood boards."""
    serializer_class = MoodBoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MoodBoard.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'])
    def items(self, request, pk=None):
        mood_board = self.get_object()
        if request.method == 'GET':
            items = MoodBoardItem.objects.filter(mood_board=mood_board).order_by('id')
            serializer = MoodBoardItemSerializer(items, many=True)
            return Response(serializer.data)
        else:
            serializer = MoodBoardItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(mood_board=mood_board)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WellbeingDataViewSet(viewsets.ModelViewSet):
    """ViewSet for managing wellbeing data."""
    serializer_class = WellbeingDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WellbeingData.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        wellbeing_data = self.get_queryset()
        serializer = self.get_serializer(wellbeing_data, many=True)
        return Response(serializer.data) 