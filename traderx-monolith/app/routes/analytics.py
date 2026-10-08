"""
Analytics endpoints for trade statistics and platform metrics.
Provides aggregated data and analytics for the trading platform.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Analytics Endpoints
# =============================================================================

@router.get("/analytics/trades")
def get_trade_analytics(db: Session = Depends(get_db)):
    """
    Get comprehensive trade statistics.
    
    Returns aggregated metrics including:
    - Total trades
    - Average trade quantity
    - Buy vs sell counts and ratio
    - Trade counts by state
    - Trade counts by security
    - Recent trade activity (last 7 days, last 30 days)
    """
    statistics = analytics_service.get_trade_statistics(db)
    return statistics


@router.get("/analytics/trades/{account_id}")
def get_account_trade_analytics(account_id: int,
                                db: Session = Depends(get_db)):
    """
    Get trade statistics for a specific account.
    
    Returns account-specific trade metrics including:
    - Total trades for the account
    - Average trade quantity
    - Buy vs sell counts
    - Trade counts by state
    - Trade counts by security
    """
    statistics = analytics_service.get_account_trade_statistics(db, account_id)
    return statistics