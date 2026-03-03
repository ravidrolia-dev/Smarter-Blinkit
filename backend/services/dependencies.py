from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_users_collection
from services.jwt_utils import decode_token
from bson import ObjectId

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    users = get_users_collection()
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["id"] = str(user["_id"])
    return user

async def require_buyer(current_user=Depends(get_current_user)):
    if current_user.get("role") != "buyer":
        raise HTTPException(status_code=403, detail="Buyer access required")
    return current_user

async def require_seller(current_user=Depends(get_current_user)):
    if current_user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Seller access required")
    return current_user
