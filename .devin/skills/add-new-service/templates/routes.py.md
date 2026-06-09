# FastAPI Route Module Template

Use this template when creating a new route module. Replace `<Domain>` and `<domain>` with the actual domain name.

## Template

```python
"""
<Domain> endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.services import <domain>_service
from app.utils.helpers import get_tenant_from_request, log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class <Domain>Create(BaseModel):
    # Use camelCase field names to match frontend JSON:
    # name: str
    # status: Optional[str] = None
    pass


class <Domain>Update(BaseModel):
    id: int
    # name: str
    # status: Optional[str] = None
    pass


# =============================================================================
# <Domain> Endpoints
# =============================================================================

@router.get("/<domain>/")
def list_<domain>s(request: Request, db: Session = Depends(get_db)):
    """List all <domain>s for the current tenant."""
    tenant_id = get_tenant_from_request(request)
    items = <domain>_service.get_all_<domain>s(db, tenant_id)
    return [item.to_dict() for item in items]


@router.post("/<domain>/")
def create_<domain>(body: <Domain>Create, request: Request,
                    db: Session = Depends(get_db)):
    """Create a new <domain>."""
    tenant_id = get_tenant_from_request(request)
    item = <domain>_service.create_<domain>(
        db, tenant_id,
        # Pass fields from body:
        # name=body.name,
    )
    return item.to_dict()


@router.put("/<domain>/")
def update_<domain>(body: <Domain>Update, request: Request,
                    db: Session = Depends(get_db)):
    """Update an existing <domain>."""
    tenant_id = get_tenant_from_request(request)
    item = <domain>_service.update_<domain>(
        db, body.id, tenant_id,
        # Pass fields from body:
        # name=body.name,
    )
    if item is None:
        raise HTTPException(status_code=404,
                            detail=f"<Domain> {body.id} not found")
    return item.to_dict()


@router.get("/<domain>/{<domain>_id}")
def get_<domain>(<domain>_id: int, request: Request,
                 db: Session = Depends(get_db)):
    """Get a single <domain> by ID."""
    tenant_id = get_tenant_from_request(request)
    item = <domain>_service.get_<domain>_by_id(db, <domain>_id, tenant_id)
    if item is None:
        raise HTTPException(status_code=404,
                            detail=f"<Domain> {<domain>_id} not found")
    return item.to_dict()
```

## Notes

- **Always use the service layer** — do NOT write inline SQLAlchemy queries in route handlers. The existing codebase has inconsistencies here (noted in LEGACY_ARCHITECTURE.md); new code should be clean.
- **Pydantic models** use camelCase field names to match the frontend's JSON expectations
- **`get_tenant_from_request()`** extracts the tenant from the middleware-injected `request.state.tenant_id`
- **`Depends(get_db)`** injects the SQLAlchemy session — this is overridden in tests by `conftest.py`
- **Register this router** in `app/main.py`:
  ```python
  from app.routes.<domain> import router as <domain>_router
  app.include_router(<domain>_router, tags=["<Domain>"])
  ```
