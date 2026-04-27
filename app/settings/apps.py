DJANGO_BASE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "channels",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_celery_results",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    # "django_filters",
]


MODULER_APPS = [
    "auth.apps.AuthConfig",
    "adopters.apps.AdoptersConfig",
    "messages.apps.MessagesConfig",
    "pets.apps.PetsConfig",
    "rescuers.apps.RescuersConfig",
]

INSTALLED_APPS = DJANGO_BASE_APPS + THIRD_PARTY_APPS + MODULER_APPS
