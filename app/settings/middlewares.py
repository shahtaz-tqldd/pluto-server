BASE_MIDDLEWARES = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CUSTOM_MIDDLEWARES = []

MIDDLEWARE = BASE_MIDDLEWARES + CUSTOM_MIDDLEWARES

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "app.authentication.SafeJWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "app.schema.ModuleAwareAutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Pluto API",
    "DESCRIPTION": "API documentation for the Pluto pet social media backend.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}
