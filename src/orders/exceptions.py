from fastapi import HTTPException, status

from src.orders.constants import MAX_CART_LINES


class CartFull(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            f"A basket holds {MAX_CART_LINES} different products at a time",
        )


class NothingToBuy(HTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "There is nothing in the basket to order")
