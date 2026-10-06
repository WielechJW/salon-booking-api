from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import authentication_error
from app.schemas.user import TokenResponse, UserRegister, UserResponse
from app.security import create_access_token
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserResponse)
def register(registration: UserRegister, database_session: Session = Depends(get_db)):
    return register_user(database_session=database_session, registration=registration)


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    database_session: Session = Depends(get_db),
):
    if len(form.password) > 128 or len(form.username) > 254:
        raise authentication_error()
    user = authenticate_user(
        database_session=database_session, email=form.username, password=form.password
    )
    if user is None:
        raise authentication_error()
    return TokenResponse(access_token=create_access_token(user.id))
