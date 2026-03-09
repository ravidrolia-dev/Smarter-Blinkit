from fastapi import APIRouter, HTTPException, Depends, status, Body, Header
from pydantic import BaseModel, EmailStr
from database import get_users_collection
from services.jwt_utils import get_password_hash, verify_password, decode_token
from bson import ObjectId
from typing import List, Optional
import uuid
import logging
import os
from datetime import datetime

# Setup logging
DEBUG_LOG = "a:\\console\\Smarter-Blinkit\\backend\\debug_user.log"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_write(msg):
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(f"{datetime.now()} - {msg}\n")
    except:
        pass

router = APIRouter()

# Models
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class Address(BaseModel):
    id: str = ""
    label: str
    full_address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_default: bool = False

# Helper to get user from token
async def get_user_from_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        logger.warning("Failed to decode token")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    role = payload.get("role")
    
    if not user_id:
        logger.warning("Token payload missing 'sub'")
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    return user_id, role

@router.get("/profile")
async def get_profile(authorization: str = Header(None)):
    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        logger.error(f"Error finding user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "phone": user.get("phone"),
        "role": user["role"],
        "profile_image": user.get("profile_image"),
        "addresses": user.get("addresses", [])
    }

@router.get("/public/{user_id}")
async def get_public_profile(user_id: str):
    """Fetch public-facing profile information for any user (e.g., a seller)."""
    users = get_users_collection()
    try:
        user = await users.find_one({"_id": ObjectId(user_id)}, {"hashed_password": 0, "face_encoding": 0, "email": 0, "phone": 0, "addresses": 0})
    except Exception as e:
        logger.error(f"Error finding user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "role": user["role"],
        "profile_image": user.get("profile_image")
    }

@router.put("/profile")
async def update_profile(update: UserProfileUpdate, authorization: str = Header(None)):
    debug_write(f"Received profile update request: {update}")
    try:
        user_id, _ = await get_user_from_auth(authorization)
        debug_write(f"Authorized user: {user_id}")
        users = get_users_collection()
        
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        if not update_data:
            debug_write("No data provided for update")
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        debug_write(f"Updating user {user_id} with data: {update_data}")
        result = await users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        debug_write(f"Update result: matched={result.matched_count}, modified={result.modified_count}")
        
        if result.matched_count == 0:
            debug_write("User not found in DB")
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Profile updated successfully"}
    except Exception as e:
        debug_write(f"CRITICAL ERROR in update_profile: {str(e)}")
        import traceback
        debug_write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.put("/password")
async def update_password(update: PasswordUpdate, authorization: str = Header(None)):
    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user or not verify_password(update.current_password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect current password")
    
    hashed_password = get_password_hash(update.new_password)
    await users.update_one({"_id": ObjectId(user_id)}, {"$set": {"hashed_password": hashed_password}})
    return {"message": "Password updated successfully"}

@router.get("/addresses")
async def get_addresses(authorization: str = Header(None)):
    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    user = await users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return []
    return user.get("addresses", [])

@router.post("/address")
async def add_address(data: dict = Body(...), authorization: str = Header(None)):
    debug_write(f"Received raw add_address request body: {data}")
    try:
        address = Address(**data)
    except Exception as e:
        debug_write(f"Pydantic validation failed for address: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    
    address.id = str(uuid.uuid4())
    debug_write(f"Assigned new address ID: {address.id}")
    
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Ensure addresses is a list
        existing_addresses = user.get("addresses", [])
        if not isinstance(existing_addresses, list):
            existing_addresses = []

        # If set as default, unset others first
        if address.is_default and existing_addresses:
            await users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"addresses.$[elem].is_default": False}},
                array_filters=[{"elem.is_default": True}]
            )
        elif not existing_addresses:
            # First address is default by... default
            address.is_default = True

        await users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"addresses": address.dict()}}
        )
        debug_write(f"Address added successfully for user {user_id}")
        return {"message": "Address added", "address_id": address.id}
        
    except Exception as e:
        debug_write(f"Error in add_address: {str(e)}")
        import traceback
        debug_write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/address/{address_id}")
async def update_saved_address(address_id: str, update: Address, authorization: str = Header(None)):
    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    
    if update.is_default:
        await users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"addresses.$[].is_default": False}}
        )
    
    result = await users.update_one(
        {"_id": ObjectId(user_id), "addresses.id": address_id},
        {"$set": {
            "addresses.$.label": update.label,
            "addresses.$.full_address": update.full_address,
            "addresses.$.lat": update.lat,
            "addresses.$.lng": update.lng,
            "addresses.$.is_default": update.is_default
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Address not found")
        
    return {"message": "Address updated"}

@router.delete("/address/{address_id}")
async def delete_address(address_id: str, authorization: str = Header(None)):
    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    
    await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"addresses": {"id": address_id}}}
    )
    return {"message": "Address deleted"}

@router.delete("/me")
async def delete_account(authorization: str = Header(None)):
    user_id, _ = await get_user_from_auth(authorization)
    users = get_users_collection()
    
    result = await users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"message": "Account deleted successfully"}
