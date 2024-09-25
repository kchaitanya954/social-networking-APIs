from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import FriendRequest, Friendship, BlockedUser, UserActivity

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'role')
        read_only_fields = ('id', 'role')

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True,
                                    #  validators=[validate_password]
                                     )

    class Meta:
        model = User
        fields = ('email', 'password', 'name')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', '')
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ('id', 'sender', 'receiver', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'sender', 'created_at', 'updated_at')

class FriendshipSerializer(serializers.ModelSerializer):
    friend = UserSerializer()

    class Meta:
        model = Friendship
        fields = ('id', 'friend', 'created_at')

class BlockedUserSerializer(serializers.ModelSerializer):
    blocked_user = UserSerializer()

    class Meta:
        model = BlockedUser
        fields = ('id', 'blocked_user', 'created_at')
        read_only_fields = ('id', 'created_at')

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['user', 'activity', 'timestamp']