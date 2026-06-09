# Example: GET Endpoint

This example is based on the real `GET /account/{account_id}` endpoint in `traderx-monolith/app/routes/accounts.py`.

## The clean version

The endpoint below follows best practices — it delegates entirely to the service layer:

```python
@router.get("/account/")
def list_accounts(request: Request, db: Session = Depends(get_db)):
    """List all accounts for the current tenant."""
    tenant_id = get_tenant_from_request(request)
    accounts = account_service.get_all_accounts(db, tenant_id)
    return [a.to_dict() for a in accounts]
```

**What makes this clean:**
- Extracts tenant from request
- Calls service layer function
- Returns serialized list via `to_dict()`
- No inline SQLAlchemy queries

## The anti-pattern to avoid

The `GET /account/{account_id}` endpoint in the current codebase has a cross-domain query — it directly queries the `positions` table:

```python
# ❌ DON'T DO THIS — cross-domain query
@router.get("/account/{account_id}")
def get_account(account_id: int, request: Request,
                db: Session = Depends(get_db)):
    tenant_id = get_tenant_from_request(request)
    account = account_service.get_account_by_id(db, account_id, tenant_id)
    if account is None:
        raise HTTPException(status_code=404,
                            detail=f"Account {account_id} not found")

    # ❌ Cross-domain query: directly queries positions table
    positions = db.query(Position).filter(
        Position.account_id == account_id,
        Position.tenant_id == tenant_id,
    ).all()

    result = account.to_dict()
    result["positions"] = [p.to_dict() for p in positions]
    return result
```

**What's wrong:**
- Route handler directly imports and queries `Position` model (owned by positions domain)
- Bypasses the position service layer
- Creates coupling between account routes and position data

**The correct approach:**
- Call a position service function to get positions for an account
- Or compose the response in an account service function that calls the position service
