from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from . import database, iceberg, models, schemas

# Create tables (In production, use Alembic for migrations)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SAVR Trading Microservice")


@app.post("/gtt/", response_model=schemas.GTTOrderResponse)
def create_gtt_order(order: schemas.GTTOrderCreate, db: Session = Depends(database.get_db)):
    db_order = models.GTTOrder(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@app.get("/gtt/{user_id}", response_model=list[schemas.GTTOrderResponse])
def get_user_gtts(user_id: str, db: Session = Depends(database.get_db)):
    orders = db.query(models.GTTOrder).filter(models.GTTOrder.user_id == user_id).all()
    return orders


@app.delete("/gtt/{order_id}")
def cancel_gtt_order(order_id: int, db: Session = Depends(database.get_db)):
    order = db.query(models.GTTOrder).filter(models.GTTOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "CANCELLED"
    db.commit()
    return {"message": "GTT Order Cancelled successfully"}


@app.post("/iceberg/orders", response_model=schemas.IcebergOrderResponse)
def create_iceberg_order(payload: schemas.IcebergOrderCreate, db: Session = Depends(database.get_db)):
    """
    Zerodha-like iceberg behavior:
    - Max 10 slices
    - Reveal one slice at a time
    - Server-managed child leg lifecycle
    - LIMIT or MARKET_PROTECTED order flow
    """
    return iceberg.create_iceberg_order(payload, db)


@app.get("/iceberg/orders/{order_id}", response_model=schemas.IcebergOrderResponse)
def get_iceberg_order(order_id: int, db: Session = Depends(database.get_db)):
    order = (
        db.query(models.IcebergOrder)
        .options(joinedload(models.IcebergOrder.legs))
        .filter(models.IcebergOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Iceberg order not found")
    return order


@app.post("/iceberg/orders/{order_id}/fill", response_model=schemas.IcebergFillResponse)
def fill_iceberg_current_slice(order_id: int, db: Session = Depends(database.get_db)):
    order = iceberg.fill_current_slice(order_id, db)
    return {
        "message": "Current iceberg slice executed and next leg advanced",
        "order": order,
    }


# --- MOCK SAVR BACKEND FOR TESTING ---
class MockExecutionPayload(BaseModel):
    user_id: str
    asset_ticker: str
    order_type: str
    price: float
    quantity: int


@app.post("/mock-savr-execute")
def mock_execute_trade(payload: MockExecutionPayload):
    # This simulates SAVR receiving your GTT trigger
    print("\n[FAKE SAVR BACKEND] Received Trade Request!")
    print(
        f"--> Buying {payload.quantity} shares of {payload.asset_ticker} "
        f"at {payload.price} SEK for {payload.user_id}\n"
    )
    return {"status": "success", "message": "Trade executed on mock exchange"}
