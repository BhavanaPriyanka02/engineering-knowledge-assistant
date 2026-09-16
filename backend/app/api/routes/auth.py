from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.user import User
from app.schemas import token as token_schema
from app.schemas import user as user_schema
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", response_model=user_schema.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_create: user_schema.UserCreate, db: Session = Depends(get_db)):
    existing_user = auth_service.get_user_by_email(db, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    new_user = auth_service.create_user(db, user_create)
    return new_user


@router.post("/login", response_model=token_schema.Token)
def login_user(user_login: user_schema.UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, user_login.email, user_login.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        user = auth_service.get_current_user(db, token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/me", response_model=user_schema.UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
