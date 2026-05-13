#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if not hasattr(sys, '_cuser_patched'):
    sys._cuser_patched = True
    try:
        import cuser.compat
        from django.utils.functional import lazy
        from django.contrib.auth import get_user_model
        # Replace the faulty User with a corrected lazy version
        cuser.compat.User = lazy(get_user_model, object)
        cuser.compat.get_user_model = get_user_model
    except ImportError:
        pass

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
