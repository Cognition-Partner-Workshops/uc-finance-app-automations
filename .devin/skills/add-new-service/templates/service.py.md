# Service Layer Template

Use this template when creating a new service module. Replace `<Domain>` and `<domain>` with the actual domain name.

## Template

```python
"""
<Domain> service — CRUD and business logic for the <domain> domain.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.models.<domain> import <Domain>
from app.utils.helpers import log_audit_event

logger = logging.getLogger(__name__)


# =============================================================================
# <Domain> CRUD
# =============================================================================

def get_<domain>_by_id(db: Session, <domain>_id: int) -> Optional[<Domain>]:
    """Get a single <domain> by ID."""
    return db.query(<Domain>).filter(
        <Domain>.id == <domain>_id,
    ).first()


def get_all_<domain>s(db: Session) -> List[<Domain>]:
    """Get all <domain>s."""
    return db.query(<Domain>).all()


def create_<domain>(db: Session, **kwargs) -> <Domain>:
    """Create a new <domain>."""
    item = <Domain>(**kwargs)
    db.add(item)
    db.commit()
    db.refresh(item)
    log_audit_event("<DOMAIN>_CREATED", f"<domain>_id={item.id}")
    logger.info("Created <domain> %d", item.id)
    return item


def update_<domain>(db: Session, <domain>_id: int,
                    **kwargs) -> Optional[<Domain>]:
    """Update an existing <domain>."""
    item = get_<domain>_by_id(db, <domain>_id)
    if item is None:
        return None

    for key, value in kwargs.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    log_audit_event("<DOMAIN>_UPDATED", f"<domain>_id={item.id}")
    logger.info("Updated <domain> %d", item.id)
    return item
```

## Notes

- **Every function** takes `db: Session` as the first argument
- **Use `log_audit_event()`** for all state-changing operations (create, update, delete)
- **Use `logger.info()`** for operational logging
- **Do NOT import models from other domains** — if you need cross-domain data, call the other domain's service functions. This avoids the circular dependency problem in `account_service.py ↔ trade_processor.py`
