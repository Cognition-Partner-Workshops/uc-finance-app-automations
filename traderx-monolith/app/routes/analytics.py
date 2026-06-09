"""
Analytics endpoints for trade statistics and platform metrics.
Provides aggregated data and analytics for the trading platform.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.services import analytics_service
from app.utils.helpers import get_tenant_from_request

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Analytics Endpoints
# =============================================================================

@router.get("/analytics/trades")
def get_trade_analytics(request: Request, db: Session = Depends(get_db)):
    """
    Get comprehensive trade statistics for the current tenant.
    
    Returns aggregated metrics including:
    - Total trades
    - Average trade quantity
    - Buy vs sell counts and ratio
    - Trade counts by state
    - Trade counts by security
    - Recent trade activity (last 7 days, last 30 days)
    """
    tenant_id = get_tenant_from_request(request)
    statistics = analytics_service.get_trade_statistics(db, tenant_id)
    return statistics


@router.get("/analytics/trades/{account_id}")
def get_account_trade_analytics(account_id: int, request: Request, 
                                db: Session = Depends(get_db)):
    """
    Get trade statistics for a specific account within the current tenant.
    
    Returns account-specific trade metrics including:
    - Total trades for the account
    - Average trade quantity
    - Buy vs sell counts
    - Trade counts by state
    - Trade counts by security
    """
    tenant_id = get_tenant_from_request(request)
    statistics = analytics_service.get_account_trade_statistics(
        db, account_id, tenant_id
    )
    return statistics