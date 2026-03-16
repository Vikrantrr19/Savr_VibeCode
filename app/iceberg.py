from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models, schemas


def _build_leg_quantities(total_quantity: int, slices: int, lot_size: int) -> list[int]:
    """Split quantity into slices, preserving lot-size multiples and minimizing imbalance."""
    total_lots = total_quantity // lot_size
    if total_lots < slices:
        raise HTTPException(status_code=422, detail="Number of slices cannot exceed total lots")

    base_lots = total_lots // slices
    remainder_lots = total_lots % slices

    lots_per_leg = [base_lots + (1 if i < remainder_lots else 0) for i in range(slices)]
    return [lots * lot_size for lots in lots_per_leg]


def create_iceberg_order(payload: schemas.IcebergOrderCreate, db: Session) -> models.IcebergOrder:
    leg_quantities = _build_leg_quantities(
        total_quantity=payload.total_quantity,
        slices=payload.slices,
        lot_size=payload.lot_size,
    )

    revealed_quantity = min(leg_quantities)
    if revealed_quantity / payload.total_quantity < 0.05:
        raise HTTPException(
            status_code=422,
            detail="Each revealed slice must be at least 5% of total quantity",
        )

    order = models.IcebergOrder(
        user_id=payload.user_id,
        instrument=payload.instrument,
        exchange=payload.exchange,
        side=payload.side,
        product=payload.product,
        order_type=payload.order_type,
        limit_price=payload.limit_price,
        market_protection_pct=payload.market_protection_pct,
        total_quantity=payload.total_quantity,
        lot_size=payload.lot_size,
        slices=payload.slices,
        revealed_quantity_per_slice=revealed_quantity,
        status="ACTIVE",
        current_slice=1,
    )

    db.add(order)
    db.flush()

    for idx, quantity in enumerate(leg_quantities, start=1):
        leg = models.IcebergLeg(
            iceberg_order_id=order.id,
            leg_number=idx,
            quantity=quantity,
            status="OPEN" if idx == 1 else "PENDING",
            filled_quantity=0,
        )
        db.add(leg)

    db.commit()
    db.refresh(order)
    return order


def fill_current_slice(order_id: int, db: Session) -> models.IcebergOrder:
    order = db.query(models.IcebergOrder).filter(models.IcebergOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Iceberg order not found")

    if order.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Only ACTIVE iceberg orders can be filled")

    current_leg = (
        db.query(models.IcebergLeg)
        .filter(
            models.IcebergLeg.iceberg_order_id == order.id,
            models.IcebergLeg.leg_number == order.current_slice,
        )
        .first()
    )

    if not current_leg or current_leg.status == "FILLED":
        raise HTTPException(status_code=409, detail="Current slice already filled")

    current_leg.filled_quantity = current_leg.quantity
    current_leg.status = "FILLED"
    order.filled_quantity += current_leg.quantity

    next_leg = (
        db.query(models.IcebergLeg)
        .filter(
            models.IcebergLeg.iceberg_order_id == order.id,
            models.IcebergLeg.leg_number == order.current_slice + 1,
        )
        .first()
    )

    if next_leg:
        next_leg.status = "OPEN"
        order.current_slice += 1
    else:
        order.status = "COMPLETED"

    db.commit()
    db.refresh(order)
    return order
