from django.apps import AppConfig


class CoreConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):

        from core.models import School
        from core.datastore.loaders import SchoolDataLoader

        schools = School.objects.all()

        for school in schools:
            #SchoolDataLoader.load_school(school)
            pass