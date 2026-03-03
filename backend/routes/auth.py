from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr
from database import get_users_collection
from services.jwt_utils import get_password_hash, verify_password, create_access_token
from services.face_auth import encode_face_from_base64, compare_face
from bson import ObjectId
from typing import Optional

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str  # "buyer" or "seller"
    phone: Optional[str] = None
    face_image_b64: Optional[str] = None  # Optional face enrollment at registration

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class FaceLoginRequest(BaseModel):
    image_b64: str  # base64 webcam frame

def format_user(user):
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "phone": user.get("phone"),
        "created_at": user.get("created_at")
    }

@router.post("/register", status_code=201)
async def register(req: RegisterRequest):
    users = get_users_collection()

    # Check existing
    existing = await users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ["buyer", "seller"]:
        raise HTTPException(status_code=400, detail="Role must be 'buyer' or 'seller'")

    # Process face encoding if provided
    face_encoding = None
    if req.face_image_b64:
        face_encoding = encode_face_from_base64(req.face_image_b64)

    user_doc = {
        "email": req.email,
        "name": req.name,
        "role": req.role,
        "phone": req.phone,
        "hashed_password": get_password_hash(req.password),
        "face_encoding": face_encoding,
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
    """Authenticate user using face recognition from a webcam frame."""
    users = get_users_collection()

    # Iterate through users who have face encodings
    cursor = users.find({"face_encoding": {"$ne": None}})
    async for user in cursor:
        if compare_face(user["face_encoding"], req.image_b64):
            token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
            return {"access_token": token, "token_type": "bearer", "user": format_user(user)}

    raise HTTPException(status_code=401, detail="Face not recognized. Please use password login.")

@router.post("/enroll-face")
async def enroll_face(data: dict = Body(...)):
    """Allow a logged-in user to enroll their face after registration."""
    user_id = data.get("user_id")
    image_b64 = data.get("image_b64")

    if not user_id or not image_b64:
        raise HTTPException(status_code=400, detail="user_id and image_b64 required")

    encoding = encode_face_from_base64(image_b64)
    if not encoding:
        raise HTTPException(status_code=400, detail="No face detected in image")

    users = get_users_collection()
    await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"face_encoding": encoding}}
    )
    return {"message": "Face enrolled successfully"}
