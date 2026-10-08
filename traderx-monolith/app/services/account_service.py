"""
Account CRUD service.
Ported from account-service Java/Spring implementation.

NOTE: This module has a circular dependency with trade_processor.py.
trade_processor imports from here, and this module imports from trade_processor
(to get trade count for account validation). Resolved via lazy imports.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.models.account import Account, AccountUser
from app.utils.helpers import log_audit_event

logger = logging.getLogger(__name__)


# =============================================================================
# Account CRUD
# =============================================================================

def get_account_by_id(db: Session, account_id: int) -> Optional[Account]:
    """Get a single account by ID."""
    return db.query(Account).filter(Account.id == account_id).first()


def get_all_accounts(db: Session) -> List[Account]:
    """Get all accounts."""
    return db.query(Account).all()


def create_account(db: Session, display_name: str,
                   account_id: Optional[int] = None) -> Account:
    """Create a new account."""
    account = Account(display_name=display_name)
    if account_id is not None:
        account.id = account_id

    db.add(account)
    db.commit()
    db.refresh(account)
    log_audit_event("ACCOUNT_CREATED",
                    f"account_id={account.id} display_name={display_name}")
    logger.info("Created account %d", account.id)
    return account


def update_account(db: Session, account_id: int,
                   display_name: str) -> Optional[Account]:
    """Update an existing account."""
    account = get_account_by_id(db, account_id)
    if account is None:
        return None

    account.display_name = display_name
    db.commit()
    db.refresh(account)
    log_audit_event("ACCOUNT_UPDATED",
                    f"account_id={account.id} display_name={display_name}")
    logger.info("Updated account %d", account.id)
    return account


def upsert_account(db: Session, account_id: Optional[int],
                   display_name: str) -> Account:
    """Create or update an account (mirrors Java upsertAccount)."""
    if account_id is not None:
        existing = get_account_by_id(db, account_id)
        if existing is not None:
            existing.display_name = display_name
            db.commit()
            db.refresh(existing)
            return existing

    return create_account(db, display_name, account_id)


# =============================================================================
# AccountUser CRUD
# =============================================================================

def get_account_user_by_id(db: Session, account_id: int,
                           username: str) -> Optional[AccountUser]:
    """Get a single account user by composite key."""
    return db.query(AccountUser).filter(
        AccountUser.account_id == account_id,
        AccountUser.username == username,
    ).first()


def get_all_account_users(db: Session) -> List[AccountUser]:
    """Get all account users."""
    return db.query(AccountUser).all()


def create_account_user(db: Session, account_id: int,
                        username: str) -> AccountUser:
    """Create a new account user."""
    account_user = AccountUser(
        account_id=account_id,
        username=username,
    )
    db.add(account_user)
    db.commit()
    db.refresh(account_user)
    log_audit_event("ACCOUNT_USER_CREATED",
                    f"account_id={account_id} username={username}")
    logger.info("Created account user %s for account %d",
                username, account_id)
    return account_user


def upsert_account_user(db: Session, account_id: int,
                        username: str) -> AccountUser:
    """Create or update an account user."""
    existing = get_account_user_by_id(db, account_id, username)
    if existing is not None:
        return existing
    return create_account_user(db, account_id, username)


# =============================================================================
# Cross-domain helper (circular dependency — intentional smell)
# =============================================================================

def get_trade_count_for_account(db: Session, account_id: int) -> int:
    """
    Get the number of trades for an account.
    Uses lazy import from trade_processor to avoid circular import at module load.
    This is an intentional architectural smell — circular dependency.
    """
    from app.services.trade_processor import count_trades_for_account
    return count_trades_for_account(db, account_id)


def can_delete_account(db: Session, account_id: int) -> bool:
    """Check if an account can be deleted (no trades associated)."""
    trade_count = get_trade_count_for_account(db, account_id)
    return trade_count == 0
