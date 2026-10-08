# Example: POST Endpoint

This example is based on the real `POST /trade/` endpoint in `traderx-monolith/app/routes/trades.py` and `POST /accountuser/` in `accounts.py`.

## Simple create endpoint

Based on the account creation pattern:

```python
class AccountCreate(BaseModel):
    id: Optional[int] = None
    displayName: str


@router.post("/account/")
def create_account(body: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account."""
    account = account_service.upsert_account(db, body.id, body.displayName)
    return account.to_dict()
```

**Key points:**
- Pydantic model defines the expected JSON body with camelCase field names
- `Optional[int] = None` for fields that are auto-generated (like `id`)
- Service layer handles the actual creation

## Create with cross-service validation

Based on the account user creation pattern — validates against the people service before creating:

```python
@router.post("/accountuser/")
def create_account_user(body: AccountUserCreate,
                        db: Session = Depends(get_db)):
    """
    Create a new account user.
    Validates the person against the people service first.
    """
    # Validate against another service first
    if not validate_person(logon_id=body.username):
        raise HTTPException(
            status_code=404,
            detail=f"{body.username} not found in People service."
        )

    user = account_service.upsert_account_user(
        db, body.accountId, body.username
    )
    return user.to_dict()
```

**Key points:**
- Cross-service validation happens via function call (not direct DB query)
- Return 404 with a descriptive error message if validation fails
- Validation runs before the create — fail fast

## Create with complex response

Based on the trade submission pattern — returns a richer response object:

```python
@router.post("/trade/")
def submit_trade(body: TradeRequest, db: Session = Depends(get_db)):
    """Submit a new trade order."""
    result = trade_processor.process_trade(
        db, body.accountId, body.security,
        body.side, body.quantity
    )
    return result  # Returns {"success": True, "trade": {...}, "position": {...}}
```

**Key points:**
- Complex business logic lives in the service layer (`process_trade`)
- The service returns a structured dict, not just a model
- The route handler stays thin — just validates the body and delegates
