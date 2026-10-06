from typing import Annotated

from pydantic import BeforeValidator, Field, StringConstraints


def normalize_phone(value: object) -> object:
    if isinstance(value, str):
        return value.strip().translate(str.maketrans("", "", " ()-"))
    return value


PersonName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
]
PhoneNumber = Annotated[
    str,
    BeforeValidator(normalize_phone),
    Field(pattern=r"^\+?[0-9]{7,15}$"),
]
