from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from django.contrib.auth.models import User
from .models import Appointment, AppointmentState, UserInfo


classes = [Appointment, AppointmentState]

for c in classes:
    admin.site.register(c)


# Define an inline admin descriptor for UserInfo model
# which acts a bit like a singleton
class UserInfoInLine(admin.StackedInline):
    model = UserInfo
    verbose_name_plural = 'Extra info'
    fk_name = "user"


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserInfoInLine, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
