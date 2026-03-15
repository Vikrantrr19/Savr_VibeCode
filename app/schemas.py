from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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