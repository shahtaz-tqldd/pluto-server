from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "messages"
    label = "pluto_messages"
    verbose_name = "Pluto Messages"

