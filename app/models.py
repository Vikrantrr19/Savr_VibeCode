from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class GTTOrder(Base):
    __tablename__ = "gtt_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    asset_ticker = Column(String, index=True)
    trigger_price = Column(Float)
    limit_price = Column(Float)  # Price used when trigger condition is met
    quantity = Column(Integer)
    condition = Column(String)  # "<=" for buy dips, ">=" for breakouts
    status = Column(String, default="ACTIVE")  # ACTIVE, TRIGGERED, EXPIRED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)

    # Defaults to 1 year expiry
    expiry_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=365))


class IcebergOrder(Base):
    __tablename__ = "iceberg_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    instrument = Column(String, index=True, nullable=False)
    exchange = Column(String, default="NFO", nullable=False)
    side = Column(String, nullable=False)  # BUY / SELL
    product = Column(String, default="NRML", nullable=False)
    order_type = Column(String, default="LIMIT", nullable=False)  # LIMIT / MARKET_PROTECTED
    limit_price = Column(Float, nullable=True)
    market_protection_pct = Column(Float, nullable=True)
    total_quantity = Column(Integer, nullable=False)
    lot_size = Column(Integer, nullable=False)
    slices = Column(Integer, nullable=False)
    revealed_quantity_per_slice = Column(Integer, nullable=False)
    filled_quantity = Column(Integer, default=0, nullable=False)
    current_slice = Column(Integer, default=1, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)  # ACTIVE, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    legs = relationship("IcebergLeg", back_populates="iceberg_order", cascade="all, delete-orphan")


class IcebergLeg(Base):
    __tablename__ = "iceberg_legs"

    id = Column(Integer, primary_key=True, index=True)
    iceberg_order_id = Column(Integer, ForeignKey("iceberg_orders.id"), nullable=False, index=True)
    leg_number = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="PENDING", nullable=False)  # PENDING, OPEN, FILLED
    filled_quantity = Column(Integer, default=0, nullable=False)

    iceberg_order = relationship("IcebergOrder", back_populates="legs")
