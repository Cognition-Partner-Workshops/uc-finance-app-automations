"""
Database seeding script for TraderX Monolith.
Populates the database with sample accounts, users, trades and positions.
Runs automatically on first startup if the database is empty.
"""

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import SessionLocal
from app.models.account import Account, AccountUser
from app.models.trade import Trade
from app.models.position import Position
from app.utils.helpers import now_utc

logger = logging.getLogger(__name__)


def is_database_empty(db: Session) -> bool:
    """Check if the database has any data."""
    account_count = db.query(Account).count()
    return account_count == 0


def seed_sample_data(db: Session):
    """
    Seed the sample dataset.
    Accounts: Test Account 20 (id: 22214), Private Clients Fund TTXX (id: 11413),
              Algo Execution Partners (id: 42422), Big Corporate Fund (id: 52355),
              Hedge Fund TXY1 (id: 62654), Internal Trading Book (id: 10031),
              Trading Account 1 (id: 44044)
    """
    logger.info("Seeding sample data")

    # Accounts
    accounts_data = [
        (22214, "Test Account 20"),
        (11413, "Private Clients Fund TTXX"),
        (42422, "Algo Execution Partners"),
        (52355, "Big Corporate Fund"),
        (62654, "Hedge Fund TXY1"),
        (10031, "Internal Trading Book"),
        (44044, "Trading Account 1"),
    ]

    for acct_id, display_name in accounts_data:
        db.add(Account(id=acct_id, display_name=display_name))
    db.flush()

    # Account Users — multiple users per account
    users_data = [
        (22214, "jsmith"),
        (22214, "jdoe"),
        (11413, "mwilliams"),
        (42422, "dchen"),
        (42422, "etaylor"),
        (52355, "mgarcia"),
        (62654, "tanderson"),
        (62654, "lmartinez"),
        (62654, "klee"),
        (10031, "pthompson"),
        (10031, "awilson"),
        (44044, "jmoore"),
        (44044, "sbrown"),
        (44044, "rjohnson"),
    ]

    for acct_id, username in users_data:
        db.add(AccountUser(account_id=acct_id, username=username))
    db.flush()

    # Trades
    now = now_utc()
    base_5d = now - timedelta(days=5)
    base_3d = now - timedelta(days=3)
    base_7d = now - timedelta(days=7)
    trades_data = [
        # Test Account 20
        (22214, "AAPL", "Buy", 100, "Settled", base_5d),
        (22214, "MSFT", "Buy", 250, "Settled", base_5d + timedelta(hours=1)),
        (22214, "GOOGL", "Buy", 50, "Settled", base_5d + timedelta(hours=2)),
        (22214, "AAPL", "Sell", 30, "Settled", base_5d + timedelta(days=1)),
        (22214, "TSLA", "Buy", 75, "Settled", base_5d + timedelta(days=2)),
        # Private Clients Fund TTXX
        (11413, "JPM", "Buy", 500, "Settled", base_5d + timedelta(days=1)),
        (11413, "BAC", "Buy", 300, "Settled",
         base_5d + timedelta(days=1, hours=2)),
        (11413, "GS", "Buy", 200, "Settled", base_5d + timedelta(days=2)),
        # Algo Execution Partners
        (42422, "BAC", "Buy", 1000, "Settled", base_3d),
        (42422, "AMZN", "Buy", 150, "Settled", base_3d + timedelta(hours=3)),
        (42422, "META", "Buy", 300, "Settled", base_3d + timedelta(days=1)),
        # Big Corporate Fund
        (52355, "NVDA", "Buy", 200, "Settled",
         base_3d + timedelta(days=1, hours=5)),
        (52355, "AMD", "Buy", 400, "Settled", base_3d + timedelta(days=2)),
        # Hedge Fund TXY1
        (62654, "AAPL", "Buy", 500, "Settled", base_7d),
        (62654, "MSFT", "Buy", 300, "Settled", base_7d + timedelta(hours=2)),
        (62654, "AAPL", "Sell", 200, "Settled", base_7d + timedelta(days=1)),
        # Internal Trading Book
        (10031, "GOOGL", "Buy", 100, "Processing", base_7d + timedelta(days=2)),
        (10031, "TSLA", "Buy", 150, "Settled", base_7d + timedelta(days=3)),
        # Trading Account 1
        (44044, "NVDA", "Buy", 250, "Settled", base_7d + timedelta(days=4)),
        (44044, "AMD", "Buy", 350, "Settled",
         base_7d + timedelta(days=4, hours=3)),
        (44044, "INTC", "Buy", 600, "Settled", base_7d + timedelta(days=5)),
    ]

    for acct_id, security, side, qty, state, created in trades_data:
        trade = Trade(
            account_id=acct_id,
            security=security,
            side=side,
            quantity=qty,
            state=state,
            created=created,
            updated=created + timedelta(seconds=5),
        )
        db.add(trade)
    db.flush()

    # Positions
    positions_data = [
        (22214, "AAPL", 70),
        (22214, "MSFT", 250),
        (22214, "GOOGL", 50),
        (22214, "TSLA", 75),
        (11413, "JPM", 500),
        (11413, "BAC", 300),
        (11413, "GS", 200),
        (42422, "BAC", 1000),
        (42422, "AMZN", 150),
        (42422, "META", 300),
        (52355, "NVDA", 200),
        (52355, "AMD", 400),
        (62654, "AAPL", 300),
        (62654, "MSFT", 300),
        (10031, "GOOGL", 100),
        (10031, "TSLA", 150),
        (44044, "NVDA", 250),
        (44044, "AMD", 350),
        (44044, "INTC", 600),
    ]

    for acct_id, security, qty in positions_data:
        pos = Position(
            account_id=acct_id,
            security=security,
            quantity=qty,
            updated=now_utc(),
        )
        db.add(pos)

    db.flush()
    logger.info("Seeded sample data: %d accounts, %d users, %d trades, %d positions",
                len(accounts_data), len(users_data), len(trades_data),
                len(positions_data))


def seed_database():
    """
    Main seed function. Populates the database with sample data.
    Only runs if the database is empty.
    """
    db = SessionLocal()
    try:
        if not is_database_empty(db):
            logger.info("Database already contains data, skipping seed")
            return False

        logger.info("=" * 60)
        logger.info("SEEDING DATABASE")
        logger.info("=" * 60)

        seed_sample_data(db)

        db.commit()

        logger.info("=" * 60)
        logger.info("DATABASE SEEDING COMPLETE")
        logger.info("  Total accounts: 7")
        logger.info("  Total trades: 21")
        logger.info("  Total positions: 19")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error("Error seeding database: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()
