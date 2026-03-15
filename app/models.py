from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timedelta
from .database import Base

class GTTOrder(Base):
    __tablename__ = "gtt_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    asset_ticker = Column(String, index=True)
    trigger_price = Column(Float)
    limit_price = Column(Float) # The price to actually buy at once triggered
    quantity = Column(Integer)
    condition = Column(String)  # e.g., "<=" for buy dips, ">=" for breakouts
    status = Column(String, default="ACTIVE") # ACTIVE, TRIGGERED, EXPIRED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Defaults to 1 year expiry
    expiry_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=365))