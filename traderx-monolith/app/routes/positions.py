"""
Position endpoints.
Ported from position-service Java/Spring implementation.

NOTE: Uses raw SQLAlchemy queries inline — bypasses the trade_processor
service layer for position queries (intentional architectural smell).
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.models.position import Position

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/positions/")
def list_all_positions(db: Session = Depends(get_db)):
    """
    Get all positions.
    Raw inline query — intentional smell (not using service layer).
    """
    # Direct query instead of going through trade_processor
    positions = db.query(Position).all()

    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}")
def list_positions_by_account(account_id: int, db: Session = Depends(get_db)):
    """
    Get all positions for a specific account.
    Also uses raw inline query — consistent within this route but inconsistent
    with how trades route sometimes uses service layer.
    """
    positions = db.query(Position).filter(
        Position.account_id == account_id,
    ).all()

    return [p.to_dict() for p in positions]
