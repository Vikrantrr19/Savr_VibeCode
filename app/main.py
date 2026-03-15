from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, database

# Create tables (In production, use Alembic for migrations)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SAVR GTT Microservice")

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



    # --- MOCK SAVR BACKEND FOR TESTING ---
from pydantic import BaseModel

class MockExecutionPayload(BaseModel):
    user_id: str
    asset_ticker: str
    order_type: str
    price: float
    quantity: int

@app.post("/mock-savr-execute")
def mock_execute_trade(payload: MockExecutionPayload):
    # This simulates SAVR receiving your GTT trigger
    print(f"\n[FAKE SAVR BACKEND] Received Trade Request!")
    print(f"--> Buying {payload.quantity} shares of {payload.asset_ticker} at {payload.price} SEK for {payload.user_id}\n")
    return {"status": "success", "message": "Trade executed on mock exchange"}