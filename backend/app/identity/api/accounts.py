from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.identity.models.account import AccountType
from app.identity.security import get_current_identity
from app.identity.services.account_service import AccountService

router = APIRouter(
    prefix="/accounts",
    tags=["NIAM Accounts"],
    dependencies=[Depends(get_current_identity)],
)


@router.post("/")
async def create_account(
    identity_id: str,
    account_type: str = "human",
    email: str | None = None,
    phone: str | None = None,
    username: str | None = None,
    password: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    account = await service.create_account(
        identity_id=identity_id,
        account_type=AccountType(account_type),
        email=email,
        phone=phone,
        username=username,
        password=password,
    )
    return {"uuid": account.uuid, "id": account.id}


@router.post("/{account_uuid}/lock")
async def lock_account(
    account_uuid: str,
    reason: str = "manual",
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    account = await service.repo.get_by_uuid(account_uuid)
    if not account:
        return {"error": "not_found"}
    success = await service.lock_account(account.id, reason)
    return {"success": success}


@router.post("/{account_uuid}/unlock")
async def unlock_account(
    account_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    account = await service.repo.get_by_uuid(account_uuid)
    if not account:
        return {"error": "not_found"}
    success = await service.unlock_account(account.id)
    return {"success": success}
