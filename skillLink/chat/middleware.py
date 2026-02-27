from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(user_id):
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


class JwtAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        token_list = params.get("token")

        if not token_list:
            raise DenyConnection("Missing token")

        token = token_list[0]
        try:
            access_token = AccessToken(token)
            user_id = access_token.get("user_id")
            if not user_id:
                raise DenyConnection("Invalid token")

            user = await _get_user(user_id)
            if not user:
                raise DenyConnection("User not found")

            scope["user"] = user
        except Exception as exc:
            raise DenyConnection("Invalid token") from exc

        return await self.inner(scope, receive, send)
