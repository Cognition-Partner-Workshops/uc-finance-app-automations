"""
Analytics service for trade statistics and metrics.
Provides aggregated data and analytics for the trading platform.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.trade import Trade
from app.config import *  # noqa: F401,F403 — intentional global config import

logger = logging.getLogger(__name__)


def get_trade_statistics(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Get comprehensive trade statistics for a tenant.
    
    Returns aggregated metrics including:
    - Total trades
    - Average trade quantity
    - Buy vs sell counts and ratio
    - Trade counts by state
    - Trade counts by security
    - Recent trade activity (last 7 days)
    """
    # Base query for tenant-specific trades
    base_query = db.query(Trade).filter(Trade.tenant_id == tenant_id)
    
    # Total trades
    total_trades = base_query.count()
    
    if total_trades == 0:
        return {
            "totalTrades": 0,
            "averageQuantity": 0,
            "buyCount": 0,
            "sellCount": 0,
            "buySellRatio": 0,
            "tradesByState": {},
            "tradesBySecurity": {},
            "recentActivity": {
                "last7Days": 0,
                "last30Days": 0
            }
        }
    
    # Average quantity
    avg_quantity = db.query(func.avg(Trade.quantity)).filter(
        Trade.tenant_id == tenant_id
    ).scalar() or 0
    
    # Buy vs Sell counts
    buy_count = base_query.filter(Trade.side == "Buy").count()
    sell_count = base_query.filter(Trade.side == "Sell").count()
    buy_sell_ratio = buy_count / sell_count if sell_count > 0 else buy_count
    
    # Trade counts by state
    trades_by_state = dict(
        db.query(Trade.state, func.count(Trade.id))
        .filter(Trade.tenant_id == tenant_id)
        .group_by(Trade.state)
        .all()
    )
    
    # Trade counts by security (top 10)
    trades_by_security = dict(
        db.query(Trade.security, func.count(Trade.id))
        .filter(Trade.tenant_id == tenant_id)
        .group_by(Trade.security)
        .order_by(func.count(Trade.id).desc())
        .limit(10)
        .all()
    )
    
    # Recent activity
    now = datetime.utcnow()
    last_7_days = base_query.filter(Trade.created >= now - timedelta(days=7)).count()
    last_30_days = base_query.filter(Trade.created >= now - timedelta(days=30)).count()
    
    statistics = {
        "totalTrades": total_trades,
        "averageQuantity": round(float(avg_quantity), 2),
        "buyCount": buy_count,
        "sellCount": sell_count,
        "buySellRatio": round(float(buy_sell_ratio), 2),
        "tradesByState": trades_by_state,
        "tradesBySecurity": trades_by_security,
        "recentActivity": {
            "last7Days": last_7_days,
            "last30Days": last_30_days
        }
    }
    
    logger.info("Generated trade statistics for tenant %s: %d total trades", 
                tenant_id, total_trades)
    return statistics


def get_account_trade_statistics(db: Session, account_id: int, tenant_id: str) -> Dict[str, Any]:
    """
    Get trade statistics for a specific account within a tenant.
    
    Returns account-specific trade metrics.
    """
    # Base query for account-specific trades
    base_query = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
        Trade.account_id == account_id
    )
    
    # Total trades for account
    total_trades = base_query.count()
    
    if total_trades == 0:
        return {
            "accountId": account_id,
            "totalTrades": 0,
            "averageQuantity": 0,
            "buyCount": 0,
            "sellCount": 0,
            "tradesByState": {},
            "tradesBySecurity": {}
        }
    
    # Average quantity
    avg_quantity = db.query(func.avg(Trade.quantity)).filter(
        Trade.tenant_id == tenant_id,
        Trade.account_id == account_id
    ).scalar() or 0
    
    # Buy vs Sell counts
    buy_count = base_query.filter(Trade.side == "Buy").count()
    sell_count = base_query.filter(Trade.side == "Sell").count()
    
    # Trade counts by state
    trades_by_state = dict(
        db.query(Trade.state, func.count(Trade.id))
        .filter(
            Trade.tenant_id == tenant_id,
            Trade.account_id == account_id
        )
        .group_by(Trade.state)
        .all()
    )
    
    # Trade counts by security
    trades_by_security = dict(
        db.query(Trade.security, func.count(Trade.id))
        .filter(
            Trade.tenant_id == tenant_id,
            Trade.account_id == account_id
        )
        .group_by(Trade.security)
        .all()
    )
    
    statistics = {
        "accountId": account_id,
        "totalTrades": total_trades,
        "averageQuantity": round(float(avg_quantity), 2),
        "buyCount": buy_count,
        "sellCount": sell_count,
        "tradesByState": trades_by_state,
        "tradesBySecurity": trades_by_security
    }
    
    logger.info("Generated trade statistics for account %d tenant %s: %d total trades", 
                account_id, tenant_id, total_trades)
    return statistics