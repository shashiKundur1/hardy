from pydantic import BaseModel, Field

from src.constants import MAX_SQLITE_INTEGER
from src.orders.constants import MAX_LINE_QUANTITY


class CartLine(BaseModel):
    product_id: int = Field(ge=1, le=MAX_SQLITE_INTEGER)
    quantity: int = Field(default=1, ge=1, le=MAX_LINE_QUANTITY)
