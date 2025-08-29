from typing import Dict, TypeAlias
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.authentication import (
    AbstractAuthenticationMiddleware,
    AuthenticationResult,
)
from dotenv import load_dotenv
import os

load_dotenv()

Key: TypeAlias = str
Token: TypeAlias = str

users: Dict[Token, str] = {
    os.getenv("USER_TOKEN"): "user",
}


class InvalidKeyError(Exception):
    pass


def exchange_key(key: Key) -> Token:
    user = users.get(key)
    if not user:
        raise InvalidKeyError()
    return key


class AuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(
        self, connection: ASGIConnection
    ) -> AuthenticationResult:
        auth_token = connection.headers.get("Authorization")
        if not auth_token:
            raise NotAuthorizedException("No authentication token found")

        auth_token = auth_token.replace("Bearer ", "")
        user = users.get(auth_token)
        if not user:
            raise NotAuthorizedException("Invalid authentication token")

        return AuthenticationResult(user=user, auth=auth_token)
