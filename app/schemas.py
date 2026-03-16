from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class GTTOrderCreate(BaseModel):
    user_id: str
    asset_ticker: str
    trigger_price: float
    limit_price: float
    quantity: int
    condition: str = "<="


class GTTOrderResponse(GTTOrderCreate):
    id: int
    status: str
    created_at: datetime
    expiry_date: datetime

    class Config:
        from_attributes = True


class IcebergOrderCreate(BaseModel):
    user_id: str
    instrument: str = Field(description="Trading symbol, e.g., NIFTY 03JUL25700CE")
    exchange: str = "NFO"
    side: Literal["BUY", "SELL"]
    product: str = "NRML"
    order_type: Literal["LIMIT", "MARKET_PROTECTED"] = "LIMIT"
    limit_price: float | None = Field(default=None, gt=0)
    market_protection_pct: float | None = Field(default=None, ge=0.1, le=5.0)
    total_quantity: int = Field(gt=0)
    lot_size: int = Field(default=75, gt=0)
    slices: int = Field(default=10, ge=2, le=10)

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.total_quantity % self.lot_size != 0:
            raise ValueError("total_quantity must be a multiple of lot_size")

        if self.order_type == "LIMIT" and self.limit_price is None:
            raise ValueError("limit_price is required for LIMIT iceberg orders")

        if self.order_type == "MARKET_PROTECTED" and self.market_protection_pct is None:
            raise ValueError("market_protection_pct is required for MARKET_PROTECTED orders")

        return self


class IcebergLegResponse(BaseModel):
    leg_number: int
    quantity: int
    status: str
    filled_quantity: int

    class Config:
        from_attributes = True


class IcebergOrderResponse(BaseModel):
    id: int
    user_id: str
    instrument: str
    exchange: str
    side: str
    product: str
    order_type: str
    limit_price: float | None
    market_protection_pct: float | None
    total_quantity: int
    lot_size: int
    slices: int
    revealed_quantity_per_slice: int
    filled_quantity: int
    current_slice: int
    status: str
    created_at: datetime
    updated_at: datetime
    legs: list[IcebergLegResponse]

    class Config:
        from_attributes = True


class IcebergFillResponse(BaseModel):
    message: str
    order: IcebergOrderResponse
