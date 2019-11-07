from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class DateTimeModel(models.Model):
    """ A base model with created and edited datetime fields """

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserInfo(DateTimeModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='userinfo')
    is_vip = models.BooleanField(default=False)
    user_managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='manager', null=True, blank=True)

    def __unicode__(self):
        return self.user.username

    def __str__(self):
        return self.user.username


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
