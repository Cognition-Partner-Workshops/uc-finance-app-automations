"""
Trade Processor — God Service for TraderX Monolith.

This is the central trade processing engine that handles:
- Trade validation logic
- Trade processing / state machine
- Position calculation
- Socket.io publishing
- Account validation (cross-domain query — intentional smell)
- Reference data validation (cross-domain query — intentional smell)
- Reporting / aggregation queries
- Audit logging
- Tenant-specific business rules

WARNING: This file intentionally exceeds 500 lines as a realistic legacy monolith
god service. It combines multiple responsibilities that should be separated.

NOTE: Circular dependency with account_service.py — this module imports from
account_service, and account_service imports from here (count_trades_for_account).
Resolved at runtime via the function being defined here and lazily imported there.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import SessionLocal
from app.models.account import Account, AccountUser
from app.models.trade import Trade
from app.models.position import Position
from app.utils.helpers import (
    find_stock_by_ticker,
    load_stocks_from_csv,
    log_audit_event,
    log_trade_event,
    log_position_event,
    now_utc,
    validate_trade_side,
    validate_trade_quantity,
    validate_trade_state,
    safe_int,
)

logger = logging.getLogger(__name__)

# Module-level Socket.io server reference — set by main.py at startup
_sio = None


def set_socketio_server(sio):
    """Set the Socket.io server instance. Called once at app startup."""
    global _sio
    _sio = sio
    logger.info("Socket.io server reference set in trade_processor")


def get_socketio_server():
    """Get the Socket.io server instance."""
    return _sio


# =============================================================================
# Trade Validation — Cross-domain queries (intentional smell)
# =============================================================================

def validate_account_exists(db: Session, account_id: int,
                            tenant_id: str) -> bool:
    """
    Validate that an account exists by directly querying the accounts table.
    This is a cross-domain query — intentional architectural smell.
    The trade processor should not directly access account data.
    """
    logger.debug("Validating account %d for tenant %s", account_id, tenant_id)
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == tenant_id
    ).first()

    if account is None:
        logger.warning("Account %d not found for tenant %s",
                       account_id, tenant_id)
        return False

    logger.info("Account %d validated: %s", account_id, account.display_name)
    return True


def validate_account_has_users(db: Session, account_id: int,
                               tenant_id: str) -> bool:
    """
    Validate that an account has at least one user assigned.
    Another cross-domain query — directly accessing account_users table.
    """
    user_count = db.query(func.count(AccountUser.username)).filter(
        AccountUser.account_id == account_id,
        AccountUser.tenant_id == tenant_id
    ).scalar()

    if user_count == 0:
        logger.warning("Account %d has no users assigned for tenant %s",
                       account_id, tenant_id)
        return False

    logger.info("Account %d has %d users for tenant %s",
                account_id, user_count, tenant_id)
    return True


def validate_security_exists(security: str) -> bool:
    """
    Validate that a security/ticker exists in reference data.
    Cross-domain reference data validation — intentional smell.
    """
    logger.debug("Validating security: %s", security)
    stock = find_stock_by_ticker(security)

    logger.info("Security %s validated: %s", security, stock["companyName"])
    return True


def validate_trade_request(db: Session, account_id: int, security: str,
                           side: str, quantity: int,
                           tenant_id: str) -> Tuple[bool, str]:
    """
    Comprehensive trade validation combining all checks.
    Returns (is_valid, error_message).
    """
    logger.info("Validating trade request: account=%d security=%s side=%s "
                "qty=%d tenant=%s", account_id, security, side, quantity,
                tenant_id)

    # Validate trade side
    if not validate_trade_side(side):
        error = f"Invalid trade side: {side}. Must be 'Buy' or 'Sell'."
        logger.error(error)
        return False, error

    # Validate trade quantity
    if not validate_trade_quantity(quantity):
        error = (f"Invalid trade quantity: {quantity}. "
                 f"Must be between {MIN_TRADE_QUANTITY} and {MAX_TRADE_QUANTITY}.")
        logger.error(error)
        return False, error

    # Validate account exists (cross-domain query)
    if not validate_account_exists(db, account_id, tenant_id):
        error = f"Account {account_id} not found for tenant {tenant_id}."
        logger.error(error)
        return False, error

    # Validate security exists (cross-domain query)
    if not validate_security_exists(security):
        error = f"Security {security} not found in reference data."
        logger.error(error)
        return False, error

    # Tenant-specific validation rules
    tenant_sides = TENANT_ALLOWED_SIDES.get(tenant_id, ["Buy", "Sell"])
    if side not in tenant_sides:
        error = (f"Trade side '{side}' not allowed for tenant {tenant_id}. "
                 f"Allowed: {tenant_sides}")
        logger.error(error)
        return False, error

    # Check for sell validation — cannot sell more than current position
    if side == "Sell":
        current_position = get_current_position_quantity(
            db, account_id, security, tenant_id
        )
        if current_position < quantity:
            logger.warning(
                "Sell quantity %d exceeds current position %d for "
                "account %d security %s tenant %s. Allowing trade but logging warning.",
                quantity, current_position, account_id, security, tenant_id
            )
            # Note: we allow the trade but log the warning (realistic legacy behavior)

    logger.info("Trade request validated successfully")
    return True, ""


# =============================================================================
# Position Management
# =============================================================================

def get_current_position_quantity(db: Session, account_id: int, security: str,
                                 tenant_id: str) -> int:
    """Get the current position quantity for an account/security pair."""
    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()

    if position is None:
        return 0
    return position.quantity


def update_position(db: Session, account_id: int, security: str,
                    quantity_delta: int, tenant_id: str) -> Position:
    """
    Update or create a position for an account/security pair.
    If position doesn't exist, creates a new one.
    """
    logger.info("Updating position: account=%d security=%s delta=%d tenant=%s",
                account_id, security, quantity_delta, tenant_id)

    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()

    if position is None:
        logger.info("Creating new position for account %d security %s tenant %s",
                     account_id, security, tenant_id)
        position = Position(
            account_id=account_id,
            security=security,
            tenant_id=tenant_id,
            quantity=0,
            updated=now_utc(),
        )
        db.add(position)

    old_quantity = position.quantity
    position.quantity = position.quantity + quantity_delta
    position.updated = now_utc()

    db.flush()

    position_change_pct = round(
        (position.quantity - old_quantity) / position.quantity * 100, 2
    ) if position.quantity else 0.0
    logger.info(
        "Position %s for account %d changed by %.2f%% (now %d shares)",
        security, account_id, position_change_pct, position.quantity,
    )

    log_position_event(
        account_id, security, "UPDATE", tenant_id,
        f"old_qty={old_quantity} new_qty={position.quantity} delta={quantity_delta}"
    )

    logger.info("Position updated: account=%d security=%s old_qty=%d new_qty=%d",
                account_id, security, old_quantity, position.quantity)

    return position


def get_positions_for_account(db: Session, account_id: int,
                              tenant_id: str) -> List[Position]:
    """Get all positions for an account."""
    return db.query(Position).filter(
        Position.account_id == account_id,
        Position.tenant_id == tenant_id,
    ).all()


def get_all_positions(db: Session, tenant_id: str) -> List[Position]:
    """Get all positions for a tenant."""
    return db.query(Position).filter(
        Position.tenant_id == tenant_id,
    ).all()


# =============================================================================
# Trade State Machine
# =============================================================================

VALID_STATE_TRANSITIONS = {
    "New": ["Processing", "Cancelled"],
    "Processing": ["Settled", "Cancelled"],
    "Settled": [],
    "Cancelled": [],
}


def can_transition(current_state: str, new_state: str) -> bool:
    """Check if a state transition is valid."""
    allowed = VALID_STATE_TRANSITIONS.get(current_state, [])
    return new_state in allowed


def transition_trade_state(db: Session, trade: Trade,
                           new_state: str) -> bool:
    """
    Transition a trade to a new state.
    Returns True if transition was successful, False otherwise.
    """
    old_state = trade.state

    if not can_transition(old_state, new_state):
        logger.error(
            "Invalid state transition: %s -> %s for trade %d",
            old_state, new_state, trade.id
        )
        return False

    trade.state = new_state
    trade.updated = now_utc()
    db.flush()

    log_trade_event(
        trade.id, trade.account_id,
        f"STATE_CHANGE:{old_state}->{new_state}",
        trade.tenant_id
    )

    logger.info("Trade %d state: %s -> %s", trade.id, old_state, new_state)
    return True


# =============================================================================
# Socket.io Publishing
# =============================================================================

async def publish_trade_update(trade: Trade):
    """Publish a trade update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        logger.warning("Socket.io server not initialized, skipping trade publish")
        return

    room = f"/accounts/{trade.account_id}/trades"
    trade_data = trade.to_dict()

    try:
        await sio.emit("publish", {"topic": room, "payload": trade_data}, room=room)
        logger.info("Published trade update to room %s: trade_id=%d state=%s",
                     room, trade.id, trade.state)
    except Exception as e:
        logger.error("Error publishing trade update: %s", str(e))


async def publish_position_update(position: Position):
    """Publish a position update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        logger.warning("Socket.io server not initialized, skipping position publish")
        return

    room = f"/accounts/{position.account_id}/positions"
    position_data = position.to_dict()

    try:
        await sio.emit("publish", {"topic": room, "payload": position_data}, room=room)
        logger.info("Published position update to room %s: security=%s qty=%d",
                     room, position.security, position.quantity)
    except Exception as e:
        logger.error("Error publishing position update: %s", str(e))


async def publish_trade_and_position(trade: Trade, position: Position):
    """Publish both trade and position updates."""
    await publish_trade_update(trade)
    await publish_position_update(position)


# =============================================================================
# Core Trade Processing (the heart of the god service)
# =============================================================================

async def process_trade(db: Session, account_id: int, security: str,
                        side: str, quantity: int,
                        tenant_id: str) -> Dict:
    """
    Process a trade order end-to-end:
    1. Validate the trade request
    2. Create the trade record (state: New)
    3. Transition to Processing
    4. Calculate and update positions
    5. Transition to Settled
    6. Publish Socket.io events
    7. Log audit trail

    This is the main entry point — called from the /trade/ endpoint.
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("PROCESSING TRADE ORDER")
    logger.info("Account: %d | Security: %s | Side: %s | Qty: %d | Tenant: %s",
                account_id, security, side, quantity, tenant_id)
    logger.info("=" * 60)

    # Step 1: Validate
    is_valid, error_msg = validate_trade_request(
        db, account_id, security, side, quantity, tenant_id
    )
    if not is_valid:
        logger.error("Trade validation failed: %s", error_msg)
        return {
            "success": False,
            "error": error_msg,
            "trade": None,
            "position": None,
        }

    # Step 2: Create trade record
    trade = Trade(
        tenant_id=tenant_id,
        account_id=account_id,
        security=security,
        side=side,
        quantity=quantity,
        state="New",
        created=now_utc(),
        updated=now_utc(),
    )
    db.add(trade)
    db.flush()  # Get the trade ID

    log_trade_event(trade.id, account_id, "CREATED", tenant_id,
                    f"security={security} side={side} qty={quantity}")

    logger.info("Trade created with ID: %d", trade.id)

    # Step 3: Transition to Processing
    if not transition_trade_state(db, trade, "Processing"):
        logger.error("Failed to transition trade %d to Processing", trade.id)
        return {
            "success": False,
            "error": "Failed to process trade",
            "trade": trade.to_dict(),
            "position": None,
        }

    # Step 4: Calculate position delta and update
    quantity_delta = quantity if side == "Buy" else -quantity
    position = update_position(db, account_id, security, quantity_delta, tenant_id)

    # Step 5: Check tenant auto-settle config
    auto_settle = TENANT_AUTO_SETTLE.get(tenant_id, True)

    if auto_settle:
        # Transition to Settled
        if not transition_trade_state(db, trade, "Settled"):
            logger.error("Failed to transition trade %d to Settled", trade.id)
        else:
            logger.info("Trade %d auto-settled for tenant %s",
                        trade.id, tenant_id)
    else:
        logger.info("Trade %d left in Processing state — "
                     "auto-settle disabled for tenant %s", trade.id, tenant_id)

    # Commit all changes
    db.commit()
    db.refresh(trade)
    db.refresh(position)

    # Step 6: Publish Socket.io events
    try:
        await publish_trade_and_position(trade, position)
    except Exception as e:
        logger.error("Error publishing Socket.io events: %s", str(e))

    # Step 7: Update runtime stats
    update_runtime_state("total_trades_processed",
                         get_runtime_state()["total_trades_processed"] + 1)
    update_runtime_state("last_trade_timestamp", now_utc().isoformat())

    # Log final audit
    elapsed_ms = (time.time() - start_time) * 1000
    log_trade_event(trade.id, account_id, "COMPLETED", tenant_id,
                    f"elapsed_ms={elapsed_ms:.2f} final_state={trade.state}")

    logger.info("Trade processing complete: trade_id=%d state=%s elapsed=%.2fms",
                trade.id, trade.state, elapsed_ms)

    result = {
        "success": True,
        "error": None,
        "trade": trade.to_dict(),
        "position": position.to_dict(),
    }

    return result


# =============================================================================
# Trade Queries
# =============================================================================

def get_trade_by_id(db: Session, trade_id: int,
                    tenant_id: str) -> Optional[Trade]:
    """Get a single trade by ID."""
    return db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.tenant_id == tenant_id,
    ).first()


def get_trades_for_account(db: Session, account_id: int,
                           tenant_id: str) -> List[Trade]:
    """Get all trades for an account."""
    return db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_all_trades(db: Session, tenant_id: str) -> List[Trade]:
    """Get all trades for a tenant."""
    return db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def count_trades_for_account(db: Session, account_id: int,
                             tenant_id: str) -> int:
    """
    Count trades for an account.
    This function is imported by account_service.py (circular dependency).
    """
    return db.query(func.count(Trade.id)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
    ).scalar() or 0


def get_trades_by_state(db: Session, state: str,
                        tenant_id: str) -> List[Trade]:
    """Get all trades in a specific state for a tenant."""
    return db.query(Trade).filter(
        Trade.state == state,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_trades_by_security(db: Session, security: str,
                           tenant_id: str) -> List[Trade]:
    """Get all trades for a specific security."""
    return db.query(Trade).filter(
        Trade.security == security,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


# =============================================================================
# Reporting / Aggregation Queries (cross-domain — intentional smell)
# =============================================================================

def get_account_portfolio_summary(db: Session, account_id: int,
                                  tenant_id: str) -> Dict:
    """
    Get a complete portfolio summary for an account.
    Combines data from accounts, trades, and positions tables.
    This is a cross-domain aggregation — intentional smell.
    """
    # Get account info (cross-domain)
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == tenant_id
    ).first()

    if account is None:
        return {"error": f"Account {account_id} not found"}

    # Get account users (cross-domain)
    users = db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.tenant_id == tenant_id,
    ).all()

    # Get positions
    positions = get_positions_for_account(db, account_id, tenant_id)

    # Get trade statistics
    total_trades = count_trades_for_account(db, account_id, tenant_id)

    settled_trades = db.query(func.count(Trade.id)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
        Trade.state == "Settled",
    ).scalar() or 0

    pending_trades = db.query(func.count(Trade.id)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
        Trade.state.in_(["New", "Processing"]),
    ).scalar() or 0

    # Calculate total portfolio value (simplified — just quantity sums)
    total_buy_quantity = db.query(func.sum(Trade.quantity)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
        Trade.side == "Buy",
        Trade.state == "Settled",
    ).scalar() or 0

    total_sell_quantity = db.query(func.sum(Trade.quantity)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
        Trade.side == "Sell",
        Trade.state == "Settled",
    ).scalar() or 0

    return {
        "account": account.to_dict(),
        "users": [u.to_dict() for u in users],
        "positions": [p.to_dict() for p in positions],
        "statistics": {
            "totalTrades": total_trades,
            "settledTrades": settled_trades,
            "pendingTrades": pending_trades,
            "totalBuyQuantity": total_buy_quantity,
            "totalSellQuantity": total_sell_quantity,
            "netQuantity": total_buy_quantity - total_sell_quantity,
        }
    }


def get_tenant_trading_summary(db: Session, tenant_id: str) -> Dict:
    """
    Get a trading summary for an entire tenant.
    Another cross-domain aggregation query.
    """
    total_accounts = db.query(func.count(Account.id)).filter(
        Account.tenant_id == tenant_id
    ).scalar() or 0

    total_trades = db.query(func.count(Trade.id)).filter(
        Trade.tenant_id == tenant_id
    ).scalar() or 0

    total_positions = db.query(func.count(Position.account_id)).filter(
        Position.tenant_id == tenant_id
    ).scalar() or 0

    trades_by_state = {}
    for state in ["New", "Processing", "Settled", "Cancelled"]:
        count = db.query(func.count(Trade.id)).filter(
            Trade.tenant_id == tenant_id,
            Trade.state == state,
        ).scalar() or 0
        trades_by_state[state] = count

    trades_by_side = {}
    for side_val in ["Buy", "Sell"]:
        count = db.query(func.count(Trade.id)).filter(
            Trade.tenant_id == tenant_id,
            Trade.side == side_val,
        ).scalar() or 0
        trades_by_side[side_val] = count

    # Get most traded securities
    most_traded = db.query(
        Trade.security,
        func.count(Trade.id).label("trade_count")
    ).filter(
        Trade.tenant_id == tenant_id,
    ).group_by(Trade.security).order_by(
        desc("trade_count")
    ).limit(10).all()

    return {
        "tenant_id": tenant_id,
        "totalAccounts": total_accounts,
        "totalTrades": total_trades,
        "totalPositions": total_positions,
        "tradesByState": trades_by_state,
        "tradesBySide": trades_by_side,
        "mostTradedSecurities": [
            {"security": s, "count": c} for s, c in most_traded
        ],
    }


# =============================================================================
# Tenant-Specific Business Rules (intentional smell — logic in processor)
# =============================================================================

def get_max_accounts_for_tenant(tenant_id: str) -> int:
    """Get the maximum number of accounts allowed for a tenant."""
    return TENANT_MAX_ACCOUNTS.get(tenant_id, 50)


def check_tenant_account_limit(db: Session, tenant_id: str) -> bool:
    """Check if the tenant has reached their account limit."""
    current_count = db.query(func.count(Account.id)).filter(
        Account.tenant_id == tenant_id
    ).scalar() or 0

    max_allowed = get_max_accounts_for_tenant(tenant_id)

    if current_count >= max_allowed:
        logger.warning("Tenant %s has reached account limit: %d/%d",
                       tenant_id, current_count, max_allowed)
        return False

    return True


def get_tenant_trade_restrictions(tenant_id: str) -> Dict:
    """Get trade restrictions for a tenant."""
    return {
        "allowedSides": TENANT_ALLOWED_SIDES.get(tenant_id, ["Buy", "Sell"]),
        "autoSettle": TENANT_AUTO_SETTLE.get(tenant_id, True),
        "maxQuantity": MAX_TRADE_QUANTITY,
        "minQuantity": MIN_TRADE_QUANTITY,
    }


def apply_tenant_specific_rules(db: Session, trade: Trade,
                                tenant_id: str) -> bool:
    """
    Apply any tenant-specific rules to a trade after creation.
    Returns True if rules were applied successfully.
    """
    logger.info("Applying tenant-specific rules for %s to trade %d",
                tenant_id, trade.id)

    # Initech has special handling — trades over 10000 quantity need review
    if tenant_id == "initech" and trade.quantity > 10000:
        logger.warning("Trade %d for tenant initech exceeds 10000 qty — "
                       "flagging for review", trade.id)
        log_trade_event(trade.id, trade.account_id,
                        "FLAGGED_FOR_REVIEW", tenant_id,
                        f"quantity={trade.quantity}")

    # Globex has a daily trade limit check
    if tenant_id == "globex_inc":
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0,
                                                microsecond=0)
        daily_trades = db.query(func.count(Trade.id)).filter(
            Trade.tenant_id == tenant_id,
            Trade.created >= today_start,
        ).scalar() or 0

        if daily_trades > 1000:
            logger.warning("Tenant globex_inc has exceeded daily trade limit: %d",
                           daily_trades)

    return True


# =============================================================================
# Batch Processing Utilities
# =============================================================================

def settle_pending_trades(db: Session, tenant_id: str) -> int:
    """
    Settle all trades that are still in Processing state.
    Returns the number of trades settled.
    """
    pending = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
        Trade.state == "Processing",
    ).all()

    settled_count = 0
    for trade in pending:
        if transition_trade_state(db, trade, "Settled"):
            settled_count += 1
            log_trade_event(trade.id, trade.account_id,
                            "BATCH_SETTLED", tenant_id)

    if settled_count > 0:
        db.commit()

    logger.info("Batch settled %d trades for tenant %s",
                settled_count, tenant_id)
    return settled_count


def cancel_stale_trades(db: Session, tenant_id: str,
                        max_age_hours: int = 24) -> int:
    """
    Cancel trades that have been in New/Processing state for too long.
    Returns the number of trades cancelled.
    """
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    stale = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
        Trade.state.in_(["New", "Processing"]),
        Trade.created < cutoff,
    ).all()

    cancelled_count = 0
    for trade in stale:
        if transition_trade_state(db, trade, "Cancelled"):
            cancelled_count += 1
            log_trade_event(trade.id, trade.account_id,
                            "STALE_CANCELLED", tenant_id,
                            f"created={trade.created.isoformat()}")

    if cancelled_count > 0:
        db.commit()

    logger.info("Cancelled %d stale trades for tenant %s",
                cancelled_count, tenant_id)
    return cancelled_count


# =============================================================================
# Position Recalculation (maintenance utility)
# =============================================================================

def recalculate_positions(db: Session, account_id: int,
                          tenant_id: str) -> List[Position]:
    """
    Recalculate all positions for an account from settled trades.
    Used for reconciliation / maintenance.
    """
    logger.info("Recalculating positions for account %d tenant %s",
                account_id, tenant_id)

    # Get all settled trades grouped by security
    trades = db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
        Trade.state == "Settled",
    ).all()

    # Calculate net positions
    position_map: Dict[str, int] = {}
    for trade in trades:
        delta = trade.quantity if trade.side == "Buy" else -trade.quantity
        if trade.security in position_map:
            position_map[trade.security] += delta
        else:
            position_map[trade.security] = delta

    # Update positions in database
    updated_positions = []
    for security, quantity in position_map.items():
        position = db.query(Position).filter(
            Position.account_id == account_id,
            Position.security == security,
            Position.tenant_id == tenant_id,
        ).first()

        if position is None:
            position = Position(
                account_id=account_id,
                security=security,
                tenant_id=tenant_id,
                quantity=quantity,
                updated=now_utc(),
            )
            db.add(position)
        else:
            position.quantity = quantity
            position.updated = now_utc()

        updated_positions.append(position)

    db.commit()

    log_audit_event("POSITION_RECALC", tenant_id,
                    f"account_id={account_id} securities={len(position_map)}")

    logger.info("Recalculated %d positions for account %d",
                len(updated_positions), account_id)
    return updated_positions


# =============================================================================
# Trade Analytics Helpers
# =============================================================================

def get_trade_volume_by_date(db: Session, tenant_id: str,
                             days: int = 30) -> List[Dict]:
    """Get daily trade volume for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        func.date(Trade.created).label("trade_date"),
        func.count(Trade.id).label("trade_count"),
        func.sum(Trade.quantity).label("total_quantity"),
    ).filter(
        Trade.tenant_id == tenant_id,
        Trade.created >= cutoff,
    ).group_by(
        func.date(Trade.created)
    ).order_by("trade_date").all()

    return [
        {
            "date": str(r.trade_date),
            "count": r.trade_count,
            "totalQuantity": r.total_quantity or 0,
        }
        for r in results
    ]


def get_top_traders(db: Session, tenant_id: str,
                    limit: int = 10) -> List[Dict]:
    """
    Get the users with the most trades.
    Another cross-domain query joining accounts, account_users, and trades.
    """
    # This is a deliberately complex cross-domain query
    results = db.query(
        AccountUser.username,
        func.count(Trade.id).label("trade_count"),
    ).join(
        Trade, and_(
            Trade.account_id == AccountUser.account_id,
            Trade.tenant_id == AccountUser.tenant_id,
        )
    ).filter(
        AccountUser.tenant_id == tenant_id,
    ).group_by(
        AccountUser.username
    ).order_by(
        desc("trade_count")
    ).limit(limit).all()

    return [
        {"username": r.username, "tradeCount": r.trade_count}
        for r in results
    ]


def get_position_concentration(db: Session, account_id: int,
                               tenant_id: str) -> List[Dict]:
    """
    Get position concentration for an account.
    Shows what percentage of total position each security represents.
    """
    positions = get_positions_for_account(db, account_id, tenant_id)

    total_abs_quantity = sum(abs(p.quantity) for p in positions)
    if total_abs_quantity == 0:
        return []

    return [
        {
            "security": p.security,
            "quantity": p.quantity,
            "percentage": round(abs(p.quantity) / total_abs_quantity * 100, 2),
        }
        for p in positions
    ]


# =============================================================================
# Account Validation Helpers (cross-domain — intentional smell)
# =============================================================================

def get_account_details_for_trade(db: Session, account_id: int,
                                  tenant_id: str) -> Optional[Dict]:
    """
    Get full account details including users and positions.
    Cross-domain query used during trade processing.
    """
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.tenant_id == tenant_id,
    ).first()

    if account is None:
        return None

    users = db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.tenant_id == tenant_id,
    ).all()

    positions = get_positions_for_account(db, account_id, tenant_id)

    return {
        "account": account.to_dict(),
        "users": [u.to_dict() for u in users],
        "positions": [p.to_dict() for p in positions],
        "tradeCount": count_trades_for_account(db, account_id, tenant_id),
    }


def validate_user_can_trade(db: Session, account_id: int, username: str,
                            tenant_id: str) -> bool:
    """
    Validate that a user is authorized to trade on an account.
    Cross-domain query — directly accesses account_users table.
    """
    user = db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.username == username,
        AccountUser.tenant_id == tenant_id,
    ).first()

    if user is None:
        logger.warning("User %s not authorized for account %d tenant %s",
                       username, account_id, tenant_id)
        return False

    return True


# =============================================================================
# Audit Trail Queries
# =============================================================================

def get_recent_trades_audit(db: Session, tenant_id: str,
                            limit: int = 50) -> List[Dict]:
    """Get recent trades for audit purposes."""
    trades = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.updated)).limit(limit).all()

    return [
        {
            "id": t.id,
            "accountId": t.account_id,
            "security": t.security,
            "side": t.side,
            "quantity": t.quantity,
            "state": t.state,
            "created": t.created.isoformat() if t.created else None,
            "updated": t.updated.isoformat() if t.updated else None,
        }
        for t in trades
    ]


def get_trade_history(db: Session, account_id: int, security: str,
                      tenant_id: str) -> List[Dict]:
    """Get complete trade history for an account/security pair."""
    trades = db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.security == security,
        Trade.tenant_id == tenant_id,
    ).order_by(Trade.created).all()

    return [t.to_dict() for t in trades]


# =============================================================================
# Import from account_service (circular dependency — intentional smell)
# =============================================================================

def get_account_display_name(db: Session, account_id: int,
                             tenant_id: str) -> str:
    """
    Get display name for an account.
    Uses lazy import from account_service to demonstrate circular dependency.
    """
    from app.services.account_service import get_account_by_id
    account = get_account_by_id(db, account_id, tenant_id)
    if account is None:
        return f"Unknown Account ({account_id})"
    return account.display_name or f"Account {account_id}"
