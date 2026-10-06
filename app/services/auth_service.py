from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import UserModel, UserRole
from app.schemas.user import UserRegister
from app.security import get_dummy_password_hash, hash_password, verify_password
from app.services.errors import DomainConflictError


def register_user(
    *, database_session: Session, registration: UserRegister, role: UserRole = "CLIENT"
) -> UserModel:
    if (
        database_session.scalar(
            select(UserModel.id).where(UserModel.email == registration.email)
        )
        is not None
    ):
        raise DomainConflictError("Email is already registered")
    user = UserModel(
        email=registration.email,
        password_hash=hash_password(registration.password.get_secret_value()),
        first_name=registration.first_name,
        last_name=registration.last_name,
        phone=registration.phone,
        role=role,
        is_active=True,
    )
    database_session.add(user)
    try:
        database_session.commit()
    except IntegrityError as error:
        database_session.rollback()
        raise DomainConflictError("Email is already registered") from error
    database_session.refresh(user)
    return user


def authenticate_user(
    *, database_session: Session, email: str, password: str
) -> UserModel | None:
    user = database_session.scalar(
        select(UserModel).where(UserModel.email == email.strip().casefold())
    )
    password_hash = (
        user.password_hash if user is not None else get_dummy_password_hash()
    )
    if not verify_password(password, password_hash):
        return None
    if user is None or not user.is_active:
        return None
    return user
