# SQLAlchemy Model Template

Use this template when creating a new domain model. Replace `<Domain>` and `<domain>` with the actual domain name.

## Template

```python
"""
<Domain> SQLAlchemy model.
"""

from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from app.config import *  # noqa: F401,F403 — intentional global config import


class <Domain>(Base):
    __tablename__ = "<domain>s"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, default=DEFAULT_TENANT)
    # Add domain-specific columns here, e.g.:
    # name = Column(String(100), nullable=False)
    # status = Column(String(20), nullable=False, default="active")
    # created = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "tenantId": self.tenant_id,
            # Map snake_case columns to camelCase keys:
            # "name": self.name,
            # "status": self.status,
        }
```

## Notes

- **`tenant_id`** is required on every model for multi-tenant row filtering
- **`DEFAULT_TENANT`** comes from the wildcard config import — this is the existing pattern
- **`to_dict()`** must use **camelCase** keys to match the frontend expectations
- For composite primary keys, see `AccountUser` in `app/models/account.py` as a reference
- For DateTime columns, use `from app.utils.helpers import now_utc` for default values
