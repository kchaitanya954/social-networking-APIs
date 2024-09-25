from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import FriendRequest, Friendship, BlockedUser, UserActivity

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model. 
    Used to represent user details such as id, email, name, and role.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'role')
        read_only_fields = ('id', 'role')

class SignUpSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user sign-up.
    Handles user creation with email, password, and name.
    """
    password = serializers.CharField(write_only=True, required=True,
                                    #  validators=[validate_password]
                                     )

    class Meta:
        model = User
        fields = ('email', 'password', 'name')

    def create(self, validated_data):
        """
        Create a new user with validated data during sign-up.
        
        Args:
            validated_data (dict): The validated data containing email, password, and name.
        
        Returns:
            User: The created user instance.
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', '')
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT tokens.
    Adds user email and role to the token payload.
    """
    @classmethod
    def get_token(cls, user):
        """
        Get and customize the JWT token to include additional user information.
        
        Args:
            user (User): The user object for whom the token is being created.
        
        Returns:
            token (Token): The customized JWT token.
        """
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

class FriendRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for the FriendRequest model.
    Used to handle friend request data such as sender, receiver, status, and timestamps.
    """
    class Meta:
        model = FriendRequest
        fields = ('id', 'sender', 'receiver', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'sender', 'created_at', 'updated_at')

class FriendshipSerializer(serializers.ModelSerializer):
    """
    Serializer for the Friendship model.
    Used to represent friendships, with details of the friend and when the friendship was created.
    """
    friend = UserSerializer()

    class Meta:
        model = Friendship
        fields = ('id', 'friend', 'created_at')

class BlockedUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the BlockedUser model.
    Represents the blocked user and when the block action took place.
    """
    blocked_user = UserSerializer()

    class Meta:
        model = BlockedUser
        fields = ('id', 'blocked_user', 'created_at')
        read_only_fields = ('id', 'created_at')

class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for the UserActivity model.
    Used to handle user activities and timestamps of when the activities occurred.
    """
    class Meta:
        model = UserActivity
        fields = ['user', 'activity', 'timestamp']