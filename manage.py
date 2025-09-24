#!/usr/bin/env python
import os
import sys
import warnings

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "climforge.settings.dev")

    from django.core.management import execute_from_command_line

    warnings.filterwarnings(
        "ignore",
        message="Accessing the database during app initialization is discouraged",
        category=RuntimeWarning,
        module="django.db.backends.utils"
    )

    execute_from_command_line(sys.argv)
