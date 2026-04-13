from django.contrib import admin
from django.contrib.auth.models import Group

from .models import  SubjectAllocation, Upload
from .models import Subject
class ProgramAdmin(admin.ModelAdmin):
    pass
class SubjectAdmin(admin.ModelAdmin):
    pass
class UploadAdmin(admin.ModelAdmin):
    pass
    

admin.site.register(Subject, SubjectAdmin)
admin.site.register(SubjectAllocation)
admin.site.register(Upload, UploadAdmin)
