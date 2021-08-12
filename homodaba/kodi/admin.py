from django.contrib import admin

from .models import KodiHost

# Register your models here.
class KodiHostAdmin(admin.ModelAdmin):
    list_display = ('host_name', 'host_url', 'owner')
    list_filter = ('owner', )
admin.site.register(KodiHost, KodiHostAdmin)