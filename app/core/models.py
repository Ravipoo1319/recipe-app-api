from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,  # contains functionality for
    # authentication system (no fields)
    BaseUserManager,
    PermissionsMixin  # contains functionality for the permission
    # and fields
)

class UserManager(BaseUserManager):
    """manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, Save and return a new user."""
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Use in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'