"""Declare models for users app."""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()


class DateTimeModel(models.Model):
    """ A base model with created and edited datetime fields """

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserInfo(DateTimeModel):
    # settings.AUTH_USER_MODEL takes User model from settings.py AUTH_USER_MODEL = 'dates.User'
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='userinfo')
    user_managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='manager', null=True, blank=True)
    is_vip = models.BooleanField(default=False)
    last_token = models.CharField(default=None, max_length=255, null=True, blank=True)
    is_used_last_token = models.BooleanField(default=False)

    def __unicode__(self):
        return self.user.email

    def __str__(self):
        return self.user.email


class AppointmentState(DateTimeModel):
    name = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Appointment(DateTimeModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    appointment_state = models.ForeignKey(AppointmentState, on_delete=models.CASCADE, related_name='appointments')

    def __unicode__(self):
        return '{} - {}'.format(self.user, self.appointment_date)

    def __str__(self):
        return '{} - {}'.format(self.user, self.appointment_date)
