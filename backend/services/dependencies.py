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
    role = payload.get("role")
    
    # Stateless authentication: Trust the cryptographically signed JWT payload
    # instead of hitting MongoDB Atlas on every video frame scan request.
    return {
        "_id": ObjectId(user_id),
        "id": str(user_id),
        "role": role
    }

async def require_buyer(current_user=Depends(get_current_user)):
    if current_user.get("role") != "buyer":
        raise HTTPException(status_code=403, detail="Buyer access required")
    return current_user

async def require_seller(current_user=Depends(get_current_user)):
    if current_user.get("role") != "seller":
        raise HTTPException(status_code=403, detail="Seller access required")
    return current_user
