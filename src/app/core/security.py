import base64
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import rsa
from clerk_backend_api import Clerk
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastcrud.exceptions.http_exceptions import CustomException
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.crud_users import crud_users
from .config import settings
from .db.crud_token_blacklist import crud_token_blacklist
from .schemas import TokenBlacklistCreate, TokenData

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

class DecodeTokenException(CustomException):
    code = 400
    error_code = "TOKEN__DECODE_ERROR"
    message = "token decode error"


class ExpiredTokenException(CustomException):
    code = 400
    error_code = "TOKEN__EXPIRE_TOKEN"
    message = "expired token"

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    correct_password: bool = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    return correct_password


def get_password_hash(password: str) -> str:
    hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashed_password


async def authenticate_user(username_or_email: str, password: str, db: AsyncSession) -> dict[str, Any] | Literal[False]:
    if "@" in username_or_email:
        db_user: dict | None = await crud_users.get(db=db, email=username_or_email, is_deleted=False)
    else:
        db_user = await crud_users.get(db=db, username=username_or_email, is_deleted=False)

    if not db_user:
        return False

    elif not await verify_password(password, db_user["hashed_password"]):
        return False

    return db_user


async def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, db: AsyncSession) -> TokenData | None:
    """Verify a JWT token and return TokenData if valid.

    Parameters
    ----------
    token: str
        The JWT token to be verified.
    db: AsyncSession
        Database session for performing database operations.

    Returns
    -------
    TokenData | None
        TokenData instance if the token is valid, None otherwise.
    """
    is_blacklisted = await crud_token_blacklist.exists(db, token=token)
    if is_blacklisted:
        return None

    try:
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = jwt_claim(token)
        username_or_email: str = payload.get("email") or payload.get("username")
        if username_or_email is None:
            return None
        return TokenData(username_or_email=username_or_email)

    except JWTError:
        return None


async def blacklist_token(token: str, db: AsyncSession) -> None:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expires_at = datetime.fromtimestamp(payload.get("exp"))
    await crud_token_blacklist.create(db, object=TokenBlacklistCreate(**{"token": token, "expires_at": expires_at}))



def jwt_claim(token: str):
        try:
            with Clerk(bearer_auth=settings.CLERK_SECRET_KEY) as sdk:
                # get key set
                jdk = sdk.jwks.get()
                first_key = jdk.keys[0]  # Extract the first key
                decoded = TokenHelper.decode_jwt(token, first_key)  # Pass the first key to decode_jwt
                if decoded is not None:
                    # handle response
                    return decoded
        except Exception as e:
            print('error:', e)
            HTTPException(status_code=401, detail="Invalid Token")


class TokenHelper:

    @staticmethod
    def jwk_to_pem(jwk):
        n = base64.urlsafe_b64decode(jwk.n + '==')
        e = base64.urlsafe_b64decode(jwk.e + '==')

        public_numbers = rsa.RSAPublicNumbers(
            e=int.from_bytes(e, 'big'),
            n=int.from_bytes(n, 'big')
        )
        public_key = public_numbers.public_key()

        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def decode_jwt(token, jwk):
        pem = TokenHelper.jwk_to_pem(jwk)
        public_key = serialization.load_pem_public_key(pem)
        return jwt.decode(token, public_key, algorithms=['RS256'])