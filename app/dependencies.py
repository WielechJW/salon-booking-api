from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import EmployeeModel
from app.models.user import UserModel
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    database_session: Session = Depends(get_db),
) -> UserModel:
    try:
        user_id = decode_access_token(token)
    except InvalidTokenError as error:
        raise authentication_error() from error
    user = database_session.get(UserModel, user_id)
    if user is None or not user.is_active:
        raise authentication_error()
    return user


def require_admin(user: UserModel = Depends(get_current_user)) -> UserModel:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def require_employee_access(
    employee_id: int,
    user: UserModel = Depends(get_current_user),
    database_session: Session = Depends(get_db),
) -> UserModel:
    if user.role == "ADMIN":
        return user
    employee = database_session.get(EmployeeModel, employee_id)
    if user.role != "EMPLOYEE" or employee is None or employee.user_id != user.id:
        raise HTTPException(status_code=403, detail="Employee calendar access denied")
    return user
