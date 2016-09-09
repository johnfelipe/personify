from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_famous', 'created')
    list_filter = ('is_famous', )


admin.site.register(Profile, ProfileAdmin)
