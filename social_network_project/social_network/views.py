# social_network/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.postgres.search import SearchQuery, SearchRank
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
import json
from django.core import serializers

import redis  # Redis cache integration
from django.contrib.auth import get_user_model
from .models import FriendRequest, Friendship, BlockedUser, UserActivity
from .serializers import (
    UserSerializer, SignUpSerializer, CustomTokenObtainPairSerializer,
    FriendRequestSerializer, FriendshipSerializer, BlockedUserSerializer, UserActivitySerializer
)

User = get_user_model()

# Initialize Redis for caching
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

class SignUpView(generics.CreateAPIView):
    """
    API view to handle user registration.

    Allows any user (authenticated or not) to create a new account by providing the necessary information.

    - **Method**: POST
    - **Permissions**: AllowAny (accessible to everyone)
    - **Body Parameters**:
        - name: name for the user.
        - password: Password for the user.
        - email: Email address for the user.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API view to obtain a custom token pair (access and refresh tokens).

    This endpoint is used to authenticate users and return JWT tokens for further requests.

    - **Method**: POST
    - **Body Parameters**:
        - email: The user's username.
        - password: The user's password.
    - **Response**: 
        - access: Access token.
        - refresh: Refresh token.
    """
    serializer_class = CustomTokenObtainPairSerializer

class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class to handle pagination in API responses.

    - Default page size: 10
    - Query Parameter `page_size`: Allows the user to control the number of results per page.
    - Maximum page size: 100
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserSearchView(generics.ListAPIView):
    """
    API view to search for users based on a query string.

    Allows authenticated users to search for other users by name or email. It supports both exact matches and partial matches.

    - **Method**: GET
    - **Permissions**: IsAuthenticated
    - **Query Parameters**:
        - q: The search query (can be a name or email).
    - **Pagination**: Custom pagination is applied to limit results.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        
        if not query:
            return User.objects.none()

        # Check if the query is an exact email match
        try:
            validate_email(query)
            exact_email_match = User.objects.filter(email__iexact=query).exclude(id=self.request.user.id)
            if exact_email_match.exists():

                return exact_email_match
        except ValidationError:
            pass

        # Perform full-text search on name and partial email match
        search_query = SearchQuery(query)
        name_results = User.objects.annotate(
            rank=SearchRank('search_vector', search_query)
        ).filter(
            Q(search_vector=search_query) | Q(email__icontains=query)
        ).exclude(id=self.request.user.id).order_by('-rank')

        return name_results


class SendFriendRequestView(generics.CreateAPIView):
    """
    API view to send a friend request to another user.

    Allows authenticated users to send a friend request to another user. It also enforces various validations like preventing duplicate requests, checking if users are blocked, and ensuring a cooldown period.

    - **Method**: POST
    - **Permissions**: IsAuthenticated
    - **Body Parameters**:
        - receiver: The user who will receive the friend request.
    - **Validations**:
        - Prevents sending requests if blocked.
        - Prevents duplicate or excessive friend requests within a cooldown period.
    """
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        sender = self.request.user
        receiver = serializer.validated_data['receiver']

        # Check if a friend request already exists between sender and receiver
        existing_request = FriendRequest.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).first()

        if existing_request:
            if existing_request.status == 'PENDING':
                return Response({"detail": "A pending friend request already exists between you and this user."}, status=status.HTTP_400_BAD_REQUEST)
            elif existing_request.status == 'ACCEPTED':
                return Response({"detail": "You are already friends with this user."}, status=status.HTTP_400_BAD_REQUEST)
            elif existing_request.status == 'REJECTED':
                return Response({"detail": "You cannot send another friend request yet."}, status=status.HTTP_400_BAD_REQUEST)


        cooldown_key = f"cooldown_friend_request_{sender.id}_{receiver.id}"
        if cache.get(cooldown_key):
            raise ValidationError("You cannot send a friend request yet, cooldown in effect.")


        if BlockedUser.objects.filter(user=receiver, blocked_user=sender).exists():
            raise ValidationError("You cannot send a friend request to this user.")

        cache_key = f"friend_request_count_{sender.id}"
        request_count = cache.get(cache_key, 0)
        if request_count >= 3:
            raise ValidationError("You can only send 3 friend requests per minute.")

        last_rejected_request = FriendRequest.objects.filter(
            sender=sender,
            receiver=receiver,
            status='REJECTED',
            updated_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).first()
        if last_rejected_request:
            raise ValidationError("You cannot send a friend request to this user yet.")

        with transaction.atomic():
            serializer.save(sender=sender)
            cache.set(cache_key, request_count + 1, 60)  # 60 seconds expiration
            UserActivity.objects.create(user=sender, activity="Sent friend request")


class AcceptRejectFriendRequestView(generics.UpdateAPIView):
    """
    API view to accept or reject a friend request.

    Allows the receiver of a friend request to accept or reject it. Also creates a friendship if the request is accepted.

    - **Method**: PUT
    - **Permissions**: IsAuthenticated
    - **Body Parameters**:
        - status: The new status of the friend request ('ACCEPTED' or 'REJECTED').
    - **Validations**:
        - Only the receiver of the request can modify its status.
    """
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure that only requests where the logged-in user is the receiver are returned
        return FriendRequest.objects.filter(receiver=self.request.user)

    def update(self, request, *args, **kwargs):
        # Fetch the specific friend request
        instance = self.get_object()

        sender = self.request.user
        receiver = instance.receiver
        # Check if a friend request already exists between sender and receiver
        existing_request = FriendRequest.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        ).first()

        if existing_request:
            if existing_request.status == 'PENDING':
                return Response({"detail": "A pending friend request already exists between you and this user."}, status=status.HTTP_400_BAD_REQUEST)
            elif existing_request.status == 'ACCEPTED':
                return Response({"detail": "You are already friends with this user."}, status=status.HTTP_400_BAD_REQUEST)
            elif existing_request.status == 'REJECTED':
                return Response({"detail": "You cannot send another friend request yet."}, status=status.HTTP_400_BAD_REQUEST)


        # Ensure only the receiver can accept/reject the friend request
        if instance.receiver != request.user:
            return Response({"detail": "You can't accept/reject this friend request."},
                            status=status.HTTP_403_FORBIDDEN)

        # Deserialize and validate request data
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Check if the 'status' field is present
        friendship_status = serializer.validated_data.get('status', '')
        if not friendship_status:
            return Response({"detail": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set cooldown if rejected
        if friendship_status == 'REJECTED':
            cache.set(f"cooldown_friend_request_{instance.sender.id}_{instance.receiver.id}", True, timeout=86400)  # 24 hours

        # Update the friend request
        self.perform_update(serializer)

        # If the status is 'ACCEPTED', create a Friendship relationship
        if friendship_status == 'ACCEPTED':
            Friendship.objects.create(user=instance.sender, friend=instance.receiver)
            Friendship.objects.create(user=instance.receiver, friend=instance.sender)
            UserActivity.objects.create(user=request.user, activity="Accepted friend request")

        return Response(serializer.data)


class FriendsListView(generics.ListAPIView):
    """
    API view to list all friends of the logged-in user.

    Retrieves a cached list of friends if available, otherwise queries the database and caches the result.

    - **Method**: GET
    - **Permissions**: IsAuthenticated
    """
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.user.id
        cache_key = f"friends_list_{user_id}"
        cached_friends = redis_client.get(cache_key)

        if cached_friends:
            friends_list = json.loads(cached_friends)
            return friends_list
        else:
            friends = Friendship.objects.filter(user=self.request.user).select_related('friend')  # Optimized query
            # Serialize the QuerySet to JSON
            friends_json = serializers.serialize('json', friends)
            redis_client.set(cache_key, friends_json, ex=300)  # Cache friends list for 5 minutes
            return friends
        # return Friendship.objects.filter(user=self.request.user)

class PendingFriendRequestsView(generics.ListAPIView):
    """
    API view to list all pending friend requests for the logged-in user.

    - **Method**: GET
    - **Permissions**: IsAuthenticated
    """
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(receiver=self.request.user, status='PENDING')

class BlockUnblockUserView(APIView):
    """
    API view to block or unblock a user.

    Allows authenticated users to block or unblock another user. Blocked users cannot send friend requests or become friends with the blocking user.

    - **Method**: POST (for blocking), DELETE (for unblocking)
    - **Permissions**: IsAuthenticated
    - **Path Parameters**:
        - user_id: The ID of the user to block or unblock.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        if user_id == request.user.id:
            return Response({"detail": "You cannot block yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_to_block = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        blocked, created = BlockedUser.objects.get_or_create(user=request.user, blocked_user=user_to_block)
        
        if created:
            # Remove any existing friend requests or friendships
            FriendRequest.objects.filter(
                Q(sender=request.user, receiver=user_to_block) |
                Q(sender=user_to_block, receiver=request.user)
            ).delete()
            Friendship.objects.filter(
                Q(user=request.user, friend=user_to_block) |
                Q(user=user_to_block, friend=request.user)
            ).delete()
            return Response({"detail": "User blocked successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "User is already blocked."}, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        if user_id == request.user.id:
            return Response({"detail": "You cannot unblock yourself."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_to_unblock = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            blocked_user = BlockedUser.objects.get(user=request.user, blocked_user=user_to_unblock)
            blocked_user.delete()
            return Response({"detail": "User unblocked successfully."}, status=status.HTTP_200_OK)
        except BlockedUser.DoesNotExist:
            return Response({"detail": "User is not blocked."}, status=status.HTTP_400_BAD_REQUEST)
        
class UserActivityView(generics.ListAPIView):
    """
    API view to list the recent activities of the logged-in user.

    - **Method**: GET
    - **Permissions**: IsAuthenticated
    """
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)