from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr
from database import get_users_collection
from services.jwt_utils import get_password_hash, verify_password, create_access_token
from services.face_auth import encode_face_from_base64, compare_face
from bson import ObjectId
from typing import Optional
import numpy as np

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str  # "buyer" or "seller"
    phone: Optional[str] = None
    face_image_b64: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class FaceLoginRequest(BaseModel):
    image_b64: str

def format_user(user):
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "phone": user.get("phone"),
        "profile_image": user.get("profile_image"),
        "created_at": user.get("created_at"),
        "address": user.get("address")
    }

@router.get("/sellers")
async def list_sellers(lat: Optional[float] = None, lng: Optional[float] = None, radius_km: float = 15.0):
    """List all users who are registered as sellers, optionally filtered by proximity."""
    users_col = get_users_collection()
    query = {"role": "seller"}
    
    if lat is not None and lng is not None:
        query["location"] = {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": radius_km * 1000 # convert to meters
            }
        }
    
    cursor = users_col.find(query, {"hashed_password": 0, "face_encoding": 0})
    sellers = await cursor.to_list(length=100)
    return [format_user(s) for s in sellers]

@router.post("/register", status_code=201)
async def register(req: RegisterRequest):
    users = get_users_collection()

    # Check existing
    existing = await users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ["buyer", "seller"]:
        raise HTTPException(status_code=400, detail="Role must be 'buyer' or 'seller'")

    # Process single face encoding if provided
    face_encoding = None
    if req.face_image_b64:
        print(f"DEBUG: Processing face_image_b64 for {req.email}, len={len(req.face_image_b64)}")
        face_encoding = await encode_face_from_base64(req.face_image_b64)
        if not face_encoding:
            print(f"DEBUG: Face detection failed for {req.email}")
            raise HTTPException(status_code=400, detail="Face not detected. Stay still and try again.")
        print(f"DEBUG: Face encoding successful for {req.email}, length={len(face_encoding)}")
    else:
        print(f"DEBUG: No face_image_b64 provided for {req.email}")

    user_doc = {
        "email": req.email,
        "name": req.name,
        "role": req.role,
        "phone": req.phone,
        "hashed_password": get_password_hash(req.password),
        "face_encoding": face_encoding,
        "profile_image": None,
        "is_active": True,
    }

    result = await users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token({"sub": str(result.inserted_id), "role": req.role})
    return {"access_token": token, "token_type": "bearer", "user": format_user(user_doc)}

@router.post("/login")
async def login(req: LoginRequest):
    users = get_users_collection()
    user = await users.find_one({"email": req.email})

    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "user": format_user(user)}

@router.post("/face-login")
async def face_login(req: FaceLoginRequest):
    """Authenticate user using legacy single-frame template matching."""
    encoding = await encode_face_from_base64(req.image_b64)
    if not encoding:
        raise HTTPException(status_code=400, detail="No face detected in capture.")

    # Match against all users with stored encodings
    users = get_users_collection()
    cursor = users.find({"face_encoding": {"$ne": None}})
    
    best_user = None
    best_score = -1.0

    async for user in cursor:
        score = compare_face(user["face_encoding"], encoding)
        # lowered to 0.55 to be much more tolerant of angles/lighting for simple template matching
        if score > 0.55 and score > best_score:
            best_score = score
            best_user = user

    if best_user:
        token = create_access_token({"sub": str(best_user["_id"]), "role": best_user["role"]})
        return {"access_token": token, "token_type": "bearer", "user": format_user(best_user)}

    raise HTTPException(status_code=401, detail="Face not recognized.")

@router.post("/enroll-face")
async def enroll_face(data: dict = Body(...)):
    """Allow a logged-in user to enroll their face (Legacy single frame)."""
    user_id = data.get("user_id")
    image_b64 = data.get("image_b64")

    if not user_id or not image_b64:
        raise HTTPException(status_code=400, detail="user_id and image_b64 required")

    encoding = await encode_face_from_base64(image_b64)
    if not encoding:
        raise HTTPException(status_code=400, detail="No face detected in image")

    users = get_users_collection()
    await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"face_encoding": encoding}}
    )
    return {"message": "Face enrolled successfully"}
