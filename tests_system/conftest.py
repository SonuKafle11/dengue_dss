import os
import django

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dengue_project.settings")

# Initialize Django
django.setup()