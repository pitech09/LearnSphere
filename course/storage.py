from django.conf import settings
from django.core.files.storage import FileSystemStorage


def course_file_storage():
    if getattr(settings, "CLOUDINARY_MEDIA_ENABLED", False):
        from cloudinary_storage.storage import RawMediaCloudinaryStorage

        return RawMediaCloudinaryStorage()
    return FileSystemStorage()


def course_video_storage():
    if getattr(settings, "CLOUDINARY_MEDIA_ENABLED", False):
        from cloudinary_storage.storage import VideoMediaCloudinaryStorage

        return VideoMediaCloudinaryStorage()
    return FileSystemStorage()
