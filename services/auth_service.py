from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext


class AuthService(object):
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    def __init__(self, mongo_client):
        self._mongo_client = mongo_client
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    async def get_user(self, username: str):
        result = await self._mongo_client.collection.find_one({
            "username": username
        })
        return result

    async def authenticate_user(self, username: str, password: str):
        user = await self.get_user(username)
        hashed_password = self.get_password_hash(password)
        if not self.verify_password(password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entered invalid password",
            )
        return user

    def create_access_token(self, data: dict,
                            expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY,
                                 algorithm=self.ALGORITHM)
        return encoded_jwt
