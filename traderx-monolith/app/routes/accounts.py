"""
Account and AccountUser endpoints.
Ported from account-service Java/Spring implementation.

NOTE: Some endpoints use the service layer, others bypass it with inline
SQLAlchemy queries — intentionally inconsistent (architectural smell).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.models.account import Account, AccountUser
from app.models.position import Position
from app.services import account_service
from app.services.people_service import validate_person
from app.utils.helpers import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class AccountCreate(BaseModel):
    id: Optional[int] = None
    displayName: str


class AccountUserCreate(BaseModel):
    accountId: int
    username: str


# =============================================================================
# Account Endpoints
# =============================================================================

@router.get("/account/")
def list_accounts(db: Session = Depends(get_db)):
    """List all accounts."""
    accounts = account_service.get_all_accounts(db)
    return [a.to_dict() for a in accounts]


@router.post("/account/")
def create_account(body: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account."""
    account = account_service.upsert_account(db, body.id, body.displayName)
    return account.to_dict()


@router.put("/account/")
def update_account(body: AccountCreate, db: Session = Depends(get_db)):
    """Update an existing account."""
    account = account_service.upsert_account(db, body.id, body.displayName)
    return account.to_dict()


@router.get("/account/{account_id}")
def get_account(account_id: int, db: Session = Depends(get_db)):
    """
    Get account by ID with portfolio summary.
    NOTE: This endpoint directly queries the positions table — cross-domain
    query intentional smell (bypasses service layer).
    """
    account = account_service.get_account_by_id(db, account_id)
    if account is None:
        raise HTTPException(status_code=404,
                            detail=f"Account {account_id} not found")

    # Cross-domain query: directly query positions table for portfolio summary
    positions = db.query(Position).filter(
        Position.account_id == account_id,
    ).all()

    result = account.to_dict()
    result["positions"] = [p.to_dict() for p in positions]
    return result


# =============================================================================
# AccountUser Endpoints
# =============================================================================

@router.get("/accountuser/")
def list_account_users(db: Session = Depends(get_db)):
    """List all account users."""
    users = account_service.get_all_account_users(db)
    return [u.to_dict() for u in users]


@router.post("/accountuser/")
def create_account_user(body: AccountUserCreate,
                        db: Session = Depends(get_db)):
    """
    Create a new account user.
    Validates the person against the people service first.
    """
    # Validate person exists in people service
    if not validate_person(logon_id=body.username):
        raise HTTPException(
            status_code=404,
            detail=f"{body.username} not found in People service."
        )

    user = account_service.upsert_account_user(
        db, body.accountId, body.username
    )
    return user.to_dict()


@router.put("/accountuser/")
def update_account_user(body: AccountUserCreate,
                        db: Session = Depends(get_db)):
    """Update an account user."""
    user = account_service.upsert_account_user(
        db, body.accountId, body.username
    )
    return user.to_dict()
