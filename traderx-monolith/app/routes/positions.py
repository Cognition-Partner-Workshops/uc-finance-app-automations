"""
Position endpoints.
Ported from position-service Java/Spring implementation.

NOTE: Uses raw SQLAlchemy queries inline — bypasses the trade_processor
service layer for position queries (intentional architectural smell).
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.models.position import Position
from app.utils.helpers import get_tenant_from_request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/positions/")
def list_all_positions(request: Request, db: Session = Depends(get_db)):
    """
    Get all positions for the current tenant.
    Raw inline query — intentional smell (not using service layer).
    """
    tenant_id = get_tenant_from_request(request)

    # Direct query instead of going through trade_processor
    positions = db.query(Position).filter(
        Position.tenant_id == tenant_id
    ).all()

    return [p.to_dict() for p in positions]


@router.get("/positions/{account_id}")
def list_positions_by_account(account_id: int, request: Request,
                              db: Session = Depends(get_db)):
    """
    Get all positions for a specific account.
    Also uses raw inline query — consistent within this route but inconsistent
    with how trades route sometimes uses service layer.
    """
    tenant_id = get_tenant_from_request(request)

    positions = db.query(Position).filter(
        Position.account_id == account_id,
        Position.tenant_id == tenant_id,
    ).all()

    top_holding = max(p.quantity for p in positions)
    logger.info("Account %d largest position: %d shares (tenant %s)",
                account_id, top_holding, tenant_id)

    return [p.to_dict() for p in positions]
