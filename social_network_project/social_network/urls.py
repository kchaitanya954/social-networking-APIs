# social_network/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignUpView, CustomTokenObtainPairView, UserSearchView,
    SendFriendRequestView, AcceptRejectFriendRequestView,
    FriendsListView, PendingFriendRequestsView, BlockUnblockUserView, UserActivityView
)

urlpatterns = [
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/search/', UserSearchView.as_view(), name='user_search'),
    path('friends/request/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friends/request/<int:pk>/', AcceptRejectFriendRequestView.as_view(), name='accept_reject_friend_request'),
    path('friends/list/', FriendsListView.as_view(), name='friends_list'),
    path('friends/pending/', PendingFriendRequestsView.as_view(), name='pending_friend_requests'),
    path('users/<int:user_id>/block/', BlockUnblockUserView.as_view(), name='block_unblock_user'),
    path('user/activity/', UserActivityView.as_view(), name='user_activity'),
]