"""
Trade SQLAlchemy model.
Ported from trade-processor Java/Spring implementation.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
from app.config import *  # noqa: F401,F403 — intentional global config import


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    security = Column(String(50), nullable=False)
    side = Column(String(4), nullable=False)  # Buy or Sell
    quantity = Column(Integer, nullable=False)
    state = Column(String(20), nullable=False, default="New")
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "accountId": self.account_id,
            "security": self.security,
            "side": self.side,
            "quantity": self.quantity,
            "state": self.state,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }
