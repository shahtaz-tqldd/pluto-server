from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def _get_user_for_token(raw_token):
    authenticator = JWTAuthentication()
    validated_token = authenticator.get_validated_token(raw_token)
    return authenticator.get_user(validated_token)


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = scope.get("user") or AnonymousUser()
        token = None

        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        if query_params.get("token"):
            token = query_params["token"][0]

        if token is None:
            for header_name, header_value in scope.get("headers", []):
                if header_name == b"authorization":
                    header_text = header_value.decode()
                    if header_text.lower().startswith("bearer "):
                        token = header_text.split(" ", 1)[1].strip()
                    break

        if token:
            try:
                scope["user"] = await _get_user_for_token(token)
            except Exception:
                scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
