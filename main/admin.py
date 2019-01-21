from django.contrib import admin
from main.models import *

# Register your models here.
admin.site.register(User)
admin.site.register(SystemUser)
admin.site.register(UserLike)
