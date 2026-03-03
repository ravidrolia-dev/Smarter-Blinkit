from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

# ----- USER MODELS -----
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str  # "buyer" or "seller"
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: Optional[str] = None
    hashed_password: str
    face_encoding: Optional[List[float]] = None
    face_image_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserPublic(UserBase):
    id: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic

# ----- PRODUCT MODELS -----
class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [lng, lat]

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category: str
    barcode: Optional[str] = None
    stock: int = 0
    unit: str = "piece"  # kg, piece, litre, etc.
    image_url: Optional[str] = None
    tags: List[str] = []

class ProductCreate(ProductBase):
    seller_id: str
    location: Optional[Location] = None

class ProductInDB(ProductCreate):
    id: Optional[str] = None
    embedding: Optional[List[float]] = None
    rating: float = 0.0
    total_sold: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductPublic(ProductBase):
    id: str
    seller_id: str
    rating: float
    total_sold: int
    distance_km: Optional[float] = None

# ----- ORDER MODELS -----
class CartItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float
    seller_id: str
    shop_name: Optional[str] = None

class OrderBase(BaseModel):
    items: List[CartItem]
    buyer_id: str
    total_amount: float
    delivery_address: str
    buyer_location: Optional[Location] = None

class OrderCreate(OrderBase):
    pass

class OrderInDB(OrderBase):
    id: Optional[str] = None
    status: str = "pending"  # pending, paid, processing, delivered, cancelled
    payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    shop_groups: Optional[dict] = None  # smart cart split result

class OrderPublic(OrderInDB):
    pass

# ----- SHOP MODELS -----
class ShopBase(BaseModel):
    name: str
    owner_id: str
    address: str
    location: Location
    phone: Optional[str] = None
    rating: float = 0.0
    category: str = "general"

class ShopCreate(ShopBase):
    pass

class ShopInDB(ShopBase):
    id: Optional[str] = None
    is_active: bool = True
    total_sales: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
