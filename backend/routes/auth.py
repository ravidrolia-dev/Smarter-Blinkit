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

    # Check existing (wrapped in try-except to handle IP whitelist errors gracefully)
    try:
        existing = await users.find_one({"email": req.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    except HTTPException:
        raise
    except Exception as e:
        if "ServerSelectionTimeoutError" in type(e).__name__:
            raise HTTPException(
                status_code=503,
                detail="MongoDB Connection Failed: Please whitelist your IP address (0.0.0.0/0) in MongoDB Atlas Network Access."
            )
        raise HTTPException(status_code=500, detail="Database error occurred.")


    if req.role not in ["buyer", "seller"]:
        raise HTTPException(status_code=400, detail="Role must be 'buyer' or 'seller'")

    # Process face encoding if provided (runs in thread pool — non-blocking)
    face_encoding = None
    if req.face_image_b64:
        face_encoding = await encode_face_from_base64(req.face_image_b64)

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
    # Encode the incoming image first (runs in thread pool)
    new_encoding = await encode_face_from_base64(req.image_b64)
    if not new_encoding:
        raise HTTPException(status_code=400, detail="No face detected in image. Please try again in better lighting.")

    users = get_users_collection()
    cursor = users.find({"face_encoding": {"$ne": None}})
    
    best_match_user = None
    min_distance = 10.0
    
    # 1. Find the absolute closest matching face in the DB using Cosine Distance
    async for user in cursor:
        distance = compare_face(user["face_encoding"], new_encoding)
        if distance < min_distance:
            min_distance = distance
            best_match_user = user

    print(f"Best match distance: {min_distance:.4f} for user: {best_match_user['email'] if best_match_user else 'None'}")

    # 2. Check if the closest match is within a safe cosine distance threshold
    # ArcFace threshold is 0.68. The threshold distance < 0.60 is slightly stricter to avoid false positives.
    if best_match_user and min_distance < 0.60:
        token = create_access_token({"sub": str(best_match_user["_id"]), "role": best_match_user["role"]})
        return {"access_token": token, "token_type": "bearer", "user": format_user(best_match_user)}

    raise HTTPException(status_code=401, detail="Face not recognized or match too weak. Please try again or use password login.")

@router.post("/enroll-face")
async def enroll_face(data: dict = Body(...)):
    """Allow a logged-in user to enroll their face after registration."""
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
