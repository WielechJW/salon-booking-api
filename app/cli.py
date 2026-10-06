import argparse
import getpass
import sys

from pydantic import ValidationError

from app.database import SessionLocal
from app.schemas.user import UserRegister
from app.services.auth_service import register_user
from app.services.errors import DomainConflictError


def main() -> int:
    parser = argparse.ArgumentParser(description="Salon account administration")
    commands = parser.add_subparsers(dest="command", required=True)
    create_admin = commands.add_parser("create-admin")
    create_admin.add_argument("--email", required=True)
    create_admin.add_argument("--first-name", required=True)
    create_admin.add_argument("--last-name", required=True)
    create_admin.add_argument("--phone", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Confirm password: "):
        print("Passwords do not match", file=sys.stderr)
        return 1
    try:
        registration = UserRegister(
            email=args.email,
            password=password,
            first_name=args.first_name,
            last_name=args.last_name,
            phone=args.phone,
        )
    except ValidationError:
        print(
            "Invalid administrator details (password must have 8–128 characters)",
            file=sys.stderr,
        )
        return 1
    try:
        with SessionLocal() as session:
            user = register_user(
                database_session=session, registration=registration, role="ADMIN"
            )
            print(f"Administrator created: {user.email}")
    except DomainConflictError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
