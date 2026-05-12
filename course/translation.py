from modeltranslation.translator import register, TranslationOptions
from .models import Subject, Upload, UploadVideo


@register(Subject)
class SubjectTranslationOptions(TranslationOptions):
    fields = ('title', 'summary',)
    empty_values=None

@register(Upload)
class UploadTranslationOptions(TranslationOptions):
    fields = ('title',)
    empty_values=None

@register(UploadVideo)
class UploadVideoTranslationOptions(TranslationOptions):
    fields = ('title', 'summary',)
    empty_values=None
