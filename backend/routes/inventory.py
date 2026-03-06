from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_products_collection
from services.dependencies import require_seller, get_current_user
from services.product_generator import enhance_product_details
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional, List
from services.scanner_service import decode_barcode

router = APIRouter()

class StockUpdate(BaseModel):
    quantity_delta: int  # positive = add stock, negative = remove stock
    note: Optional[str] = None

class ScanRequest(BaseModel):
    image_base64: str

import requests

@router.post("/scan")
async def scan_barcode(req: ScanRequest, user=Depends(get_current_user)):
    """Process a captured frame and return the decoded barcode + diagnostic metadata."""
    # print(f"--- Professional Scan request received ---")
    result = await decode_barcode(req.image_base64)
    # result is a dict: {"barcode": ..., "low_light": ..., "is_blurry": ...}
    return result

import hashlib
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

@router.get("/barcode-image/{barcode_val}")
async def get_barcode_image(barcode_val: str):
    """Generate a PNG image for a given barcode string and return it as base64."""
    try:
        # Determine barcode type based on length
        if len(barcode_val) == 12:
            code_class = barcode.get_barcode_class('upca')
        elif len(barcode_val) == 13:
            code_class = barcode.get_barcode_class('ean13')
        elif len(barcode_val) == 8:
            code_class = barcode.get_barcode_class('ean8')
        else:
            code_class = barcode.get_barcode_class('code128')

        # Create barcode
        code_inst = code_class(barcode_val, writer=ImageWriter())
        
        # Save to buffer
        buffer = BytesIO()
        code_inst.write(buffer)
        
        # Convert to base64
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return {"barcode": barcode_val, "image": f"data:image/png;base64,{img_str}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid barcode format: {str(e)}")

@router.post("/generate-barcode")
async def generate_barcode(seller=Depends(require_seller)):
    """Generate a unique sequential UPC-A barcode and return the string + PNG image base64."""
    products_col = get_products_collection()
    
    # 1. Generate a deterministic 6-digit prefix from the seller's ObjectId
    seller_id_str = str(seller["_id"])
    hash_object = hashlib.sha256(seller_id_str.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    seller_prefix = str(hash_int)[:6].zfill(6) # e.g., '123456'
    
    # 2. Sequential counter: get total number of products this seller already owns
    product_count = await products_col.count_documents({"seller_id": seller_id_str})
    # Increment by 1 so the first product is 00001
    counter = product_count + 1 
    # Max out at 99999 for the 5-digit requirement
    if counter > 99999:
        raise HTTPException(status_code=400, detail="Maximum barcode generation limit reached for this seller.")
        
    sequential_suffix = str(counter).zfill(5)
    
    # 3. Combine to form the 11-digit base (python-barcode calculates the 12th check digit)
    base_code = f"{seller_prefix}{sequential_suffix}"
    
    try:
        # Create UPC-A barcode class
        UPCA = barcode.get_barcode_class('upca')
        
        # We pass the 11 digit base, the lib will calculate checksum 
        upc_code = UPCA(base_code, writer=ImageWriter())
        
        # 4. Generate PNG Image in Memory with requested readability parameters
        # module_width=0.3, module_height=15.0, quiet_zone=6.0
        options = {
            'module_width': 0.3,
            'module_height': 15.0,
            'quiet_zone': 6.0,
            'font_size': 12,
            'text_distance': 4.0,
            'format': 'PNG'
        }
        
        buffer = BytesIO()
        upc_code.write(buffer, options=options)
        
        # Get base64 string
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        data_uri = f"data:image/png;base64,{img_b64}"
        
        return {
            "barcode": upc_code.get_fullcode(), # Returns full 12 digit string
            "image_b64": data_uri
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Barcode generation error: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Failed to generate barcode: {str(e)}")

@router.get("/barcode/{barcode}")
async def lookup_by_barcode(barcode: str, user=Depends(get_current_user)):
    """Look up a product using its barcode, with OpenFoodFacts fallback."""
    products_col = get_products_collection()
    
    # Normalization for UPC-A/EAN-13 compatibility
    # If 13 digits and starts with '0', it's likely a padded UPC-A
    search_barcodes = [barcode]
    if len(barcode) == 13 and barcode.startswith("0"):
        search_barcodes.append(barcode[1:])
    elif len(barcode) == 12:
        search_barcodes.append("0" + barcode)
    
    # 1. Check current user's inventory (if they are a seller)
    product = await products_col.find_one({
        "barcode": {"$in": search_barcodes},
        "seller_id": str(user["_id"])
    })
    
    if product:
        product["id"] = str(product.pop("_id"))
        product.pop("embedding", None)
        return {"found": True, "owned": True, "product": product}

    # 2. Check global database (other sellers)
    product = await products_col.find_one({"barcode": {"$in": search_barcodes}})
    if product:
        product["id"] = str(product.pop("_id"))
        product.pop("embedding", None)
        return {"found": True, "owned": False, "product": product}

    # 3. OpenFoodFacts Fallback (Professional Auto-Fill)
    try:
        off_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(off_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                off_prod = data.get("product", {})
                # Extract a better description
                desc = off_prod.get("generic_name") or off_prod.get("ingredients_text") or f"High quality {off_prod.get('product_name')} from {off_prod.get('brands')}"
                
                # Cleanup categories to match our CATEGORIES list if possible
                cat_list = off_prod.get("categories", "").split(",")
                top_cat = cat_list[0].strip() if cat_list else "Essentials"

                # Generate tags
                tags = off_prod.get("labels", "").split(",") + off_prod.get("categories", "").split(",")
                tags = [t.strip() for t in tags if t.strip()][:5]

                # AI Enhancement: Polish raw OFF data into professional details
                raw_prod = {
                    "name": off_prod.get("product_name"),
                    "brand": off_prod.get("brands"),
                    "category": top_cat,
                    "tags": tags,
                    "description": desc
                }
                enhanced = await enhance_product_details(raw_prod)

                return {
                    "found": True, 
                    "owned": False, 
                    "external": True,
                    "product": {
                        "name": enhanced.get("name", raw_prod["name"]),
                        "brand": off_prod.get("brands", "Unknown Brand"),
                        "description": enhanced.get("description", raw_prod["description"]),
                        "category": enhanced.get("category", raw_prod["category"]),
                        "tags": enhanced.get("tags", raw_prod["tags"]),
                        "image": off_prod.get("image_url"),
                        "barcode": barcode,
                        "price": 0,
                        "stock": 10,
                        "unit": "piece"
                    }
                }
    except Exception as e:
        print(f"OpenFoodFacts lookup failed: {e}")

    raise HTTPException(status_code=404, detail=f"No product with barcode {barcode}")

@router.patch("/{product_id}/stock")
async def update_stock(product_id: str, req: StockUpdate, seller=Depends(require_seller)):
    """Update stock for a product. Used by barcode scanner after scanning a box."""
    products_col = get_products_collection()

    product = await products_col.find_one({
        "_id": ObjectId(product_id),
        "seller_id": str(seller["_id"])
    })
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not yours")

    new_stock = product["stock"] + req.quantity_delta
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")

    await products_col.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"stock": new_stock}}
    )
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "old_stock": product["stock"],
        "delta": req.quantity_delta,
        "new_stock": new_stock
    }

@router.get("/my-products")
async def seller_inventory(seller=Depends(require_seller)):
    """List all products for the current seller with their stock levels."""
    products_col = get_products_collection()
    cursor = products_col.find({"seller_id": str(seller["_id"])}).sort("name", 1)
    products = await cursor.to_list(length=200)
    for p in products:
        p["id"] = str(p.pop("_id"))
        p.pop("embedding", None)
    return products
