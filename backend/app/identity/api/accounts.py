from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/accounts", tags=["NIAM Accounts"])


@router.post("/")
def create_account() -> None:
    """Direct public account creation is disabled; use the review-gated intake route."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Direct account creation is disabled. Submit a review request instead.",
    )


@router.post("/{account_uuid}/lock")
def lock_account(account_uuid: str) -> None:
    """Unscoped account mutation is disabled until a governed admin permission exists."""
    del account_uuid
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Direct account mutation is disabled.",
    )


@router.post("/{account_uuid}/unlock")
def unlock_account(account_uuid: str) -> None:
    """Unscoped account mutation is disabled until a governed admin permission exists."""
    del account_uuid
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Direct account mutation is disabled.",
    )
