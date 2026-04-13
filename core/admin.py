from django.contrib import admin
from django.contrib import admin
from .models import Session, NewsAndEvents, SchoolClass


class NewsAndEventsAdmin(admin.ModelAdmin):
    pass



admin.site.register(SchoolClass)

admin.site.register(Session)
admin.site.register(NewsAndEvents, NewsAndEventsAdmin)
