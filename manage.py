#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvj.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise

    if (
        os.environ.get("RUN_MAIN") or os.environ.get("WERKZEUG_RUN_MAIN")
    ) and os.environ.get("VSCODE_DEBUGGER", False):
        import debugpy

        debugpy.listen(("0.0.0.0", 5678))

    execute_from_command_line(sys.argv)
