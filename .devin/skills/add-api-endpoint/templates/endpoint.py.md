# Endpoint Template

Complete template showing all four common endpoint patterns (list, get, create, update) for a domain.

## GET — List all

```python
@router.get("/<domain>/")
def list_<domain>s(request: Request, db: Session = Depends(get_db)):
    """List all <domain>s for the current tenant."""
    tenant_id = get_tenant_from_request(request)
    items = <domain>_service.get_all_<domain>s(db, tenant_id)
    return [item.to_dict() for item in items]
```

## GET — Single by ID

```python
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

## GET — With query parameters

```python
@router.get("/<domain>/search")
def search_<domain>s(request: Request, q: str = "", limit: int = 50,
                     db: Session = Depends(get_db)):
    """Search <domain>s by query string."""
    tenant_id = get_tenant_from_request(request)
    items = <domain>_service.search_<domain>s(db, tenant_id, q, limit)
    return [item.to_dict() for item in items]
```

## POST — Create

```python
class <Domain>Create(BaseModel):
    fieldName: str
    optionalField: Optional[int] = None


@router.post("/<domain>/")
def create_<domain>(body: <Domain>Create, request: Request,
                    db: Session = Depends(get_db)):
    """Create a new <domain>."""
    tenant_id = get_tenant_from_request(request)
    item = <domain>_service.create_<domain>(
        db, tenant_id,
        field_name=body.fieldName,
    )
    return item.to_dict()
```

## PUT — Update

```python
class <Domain>Update(BaseModel):
    id: int
    fieldName: str


@router.put("/<domain>/")
def update_<domain>(body: <Domain>Update, request: Request,
                    db: Session = Depends(get_db)):
    """Update an existing <domain>."""
    tenant_id = get_tenant_from_request(request)
    item = <domain>_service.update_<domain>(
        db, body.id, tenant_id,
        field_name=body.fieldName,
    )
    if item is None:
        raise HTTPException(status_code=404,
                            detail=f"<Domain> {body.id} not found")
    return item.to_dict()
```

## Required Imports

Every route file needs these imports at the top:

```python
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
```
