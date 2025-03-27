import fastapi
import sqlalchemy.orm
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from task_manager import models
from task_manager.database import get_db


secret_key = "your_secret_key"
alg = "HS256"
token = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    return hash_password(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    return create_token(data, expires_delta)


def verify_password(plain_pwd, hashed_pwd):
    return pwd_context.verify(plain_pwd, hashed_pwd)


def hash_password(pwd):
    return pwd_context.hash(pwd)


def authenticate_user(db: sqlalchemy.orm.Session, username: str, pwd: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(pwd, user.hashed_password):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=token))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=alg)


async def get_current_user(db: sqlalchemy.orm.Session = fastapi.Depends(get_db),
                           token: str = fastapi.Depends(oauth2_scheme)):
    credentials_exception = fastapi.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, secret_key, algorithms=[alg])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
