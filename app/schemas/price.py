from decimal import Decimal
from typing import Annotated

from pydantic import Field, PlainSerializer

# Match Numeric(10, 2) while preserving numeric prices in JSON responses.
Price = Annotated[
    Decimal,
    Field(ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False),
    PlainSerializer(float, return_type=float, when_used="json"),
]
