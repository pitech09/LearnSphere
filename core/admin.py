from django.contrib import admin
from django.contrib import admin
from .models import Session, Semester, NewsAndEvents


class NewsAndEventsAdmin(admin.ModelAdmin):
    pass


admin.site.register(Semester)
admin.site.register(Session)
admin.site.register(NewsAndEvents, NewsAndEventsAdmin)
