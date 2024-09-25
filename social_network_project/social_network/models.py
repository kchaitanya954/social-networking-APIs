from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class UserManager(BaseUserManager):
    """
    Custom user manager class for handling the creation of regular and superuser accounts.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a regular user with the given email and password.
        
        Args:
            email (str): The email address of the user.
            password (str, optional): The password for the user. Defaults to None.
            **extra_fields: Additional fields to include in the user model.

        Raises:
            ValueError: If the email is not provided.

        Returns:
            User: The created user instance.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Password is hashed here
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        
        Args:
            email (str): The email address of the superuser.
            password (str, optional): The password for the superuser. Defaults to None.
            **extra_fields: Additional fields to include in the user model.

        Returns:
            User: The created superuser instance.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier instead of username.
    Includes support for roles and full-text search.
    """
    ROLES = (
        ('READ', 'Read'),
        ('WRITE', 'Write'),
        ('ADMIN', 'Admin'),
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    role = models.CharField(max_length=5, choices=ROLES, default='READ')
    search_vector = SearchVectorField(null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        """
        String representation of the User model, which returns the email.
        
        Returns:
            str: The email of the user.
        """
        return self.email

    class Meta:
        """
        Meta options for the User model.
        """
        indexes = [GinIndex(fields=['search_vector'])]

class FriendRequestManager(models.Manager):
    """
    Custom manager for handling FriendRequest model operations.
    """
    pass

class FriendRequest(models.Model):
    """
    Model representing a friend request between two users.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FriendRequestManager()

    class Meta:
        """
        Meta options for the FriendRequest model.
        Ensures that a user cannot send multiple friend requests to the same user.
        """
        unique_together = ('sender', 'receiver')

class FriendshipManager(models.Manager):
     """
    Custom manager for handling FriendRequest model operations.
    """
    pass

class Friendship(models.Model):
    """
    Model representing a friendship between two users.
    """
    user = models.ForeignKey(User, related_name='friendships', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_of', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FriendshipManager()

    class Meta:
        """
        Meta options for the Friendship model.
        Ensures that a user cannot be friends with the same person multiple times.
        """
        unique_together = ('user', 'friend')

class BlockedUserManager(models.Manager):
    """
    Custom manager for handling BlockedUser model operations.
    """
    pass

class BlockedUser(models.Model):
    """
    Model representing a blocked user relationship between two users.
    """
    user = models.ForeignKey(User, related_name='blocked_users', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BlockedUserManager()

    class Meta:
        """
        Meta options for the BlockedUser model.
        Ensures that a user cannot block the same person multiple times.
        """
        unique_together = ('user', 'blocked_user')

class UserActivity(models.Model):
    """
    Model representing a logs of user activities.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)