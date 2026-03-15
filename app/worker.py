'''import time
import requests
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GTTOrder

# Mock URL for SAVR's main trading backend
SAVR_EXECUTION_WEBHOOK = "https://internal.savr.com/api/orders/execute"

def get_current_price(ticker: str) -> float:
    # In reality, this would query Redis or a live Market Data API
    # Mocking a price drop for demonstration
    mock_prices = {"VOLV-B.ST": 450.00, "INVE-B.ST": 210.00}
    return mock_prices.get(ticker, 500.00)
'''

import time
import requests 
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import GTTOrder

# Point this to the fake endpoint we just made in main.py
SAVR_EXECUTION_WEBHOOK = "http://127.0.0.1:8000/mock-savr-execute"

# A simple variable to simulate the stock price falling over time
current_mock_price = 455.0 

def get_current_price(ticker: str) -> float:
    global current_mock_price
    if ticker == "VOLV-B.ST":
        # Drop the price by 2 SEK every time this is called
        current_mock_price -= 2.0 
        return current_mock_price
    return 500.0

# ... keep the rest of your evaluate_and_execute_gtts() function ...
def evaluate_and_execute_gtts():
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch all ACTIVE orders
        active_orders = db.query(GTTOrder).filter(GTTOrder.status == "ACTIVE").all()
        
        for order in active_orders:
            current_price = get_current_price(order.asset_ticker)
            triggered = False
            
            # 2. Check Conditions
            if order.condition == "<=" and current_price <= order.trigger_price:
                triggered = True
            elif order.condition == ">=" and current_price >= order.trigger_price:
                triggered = True
                
            # 3. Execute Order
            if triggered:
                print(f"TRIGGER HIT! {order.asset_ticker} at {current_price}. Placing order for User {order.user_id}")
                
                # Send the actual order request to SAVR's main backend
                payload = {
                    "user_id": order.user_id,
                    "asset_ticker": order.asset_ticker,
                    "order_type": "LIMIT",
                    "price": order.limit_price,
                    "quantity": order.quantity
                }
                
                response = requests.post(SAVR_EXECUTION_WEBHOOK, json=payload)
                if response.status_code == 200:
                    print(f"Order executed for order {order.id}; marking as TRIGGERED")
                    # Mark as triggered so it doesn't fire again
                    order.status = "TRIGGERED"
                    db.commit()
                else:
                    print(f"Failed to execute order {order.id} via SAVR webhook: {response.status_code} {response.text}")

    finally:
        db.close()

if __name__ == "__main__":
    print("Starting GTT Evaluation Worker...")
    while True:
        evaluate_and_execute_gtts()
        # Sleep to prevent overloading (adjust based on your market data rate limits)
        time.sleep(5)