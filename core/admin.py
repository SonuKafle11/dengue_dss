from django.contrib import admin
from .models import User, AdminUser, PatientRecord

admin.site.register(User)
admin.site.register(AdminUser)
admin.site.register(PatientRecord)