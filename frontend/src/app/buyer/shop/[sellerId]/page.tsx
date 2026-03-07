"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi } from "@/lib/api";
import Link from "next/link";
import toast from "react-hot-toast";

export default function SellerShopPage() {
    const { sellerId } = useParams();
    const [products, setProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [sellerName, setSellerName] = useState("Shop");

    useEffect(() => {
        if (!sellerId) return;
        setLoading(true);
        productsApi.list({ seller_id: sellerId, limit: 100 })
            .then((res) => {
                setProducts(res.data);
                if (res.data.length > 0) {
                    setSellerName(res.data[0].seller_name || "Local Shop");
                }
            })
            .catch((err) => {
                console.error("Shop fetch failed:", err);
                toast.error("Could not load shop products");
            })
            .finally(() => setLoading(false));
    }, [sellerId]);

    return (
        <DashboardLayout role="buyer">
            <div className="mb-8 flex items-center gap-4">
                <Link href="/buyer" className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center hover:bg-yellow-50 transition-colors">
                    ⬅️
                </Link>
                <div>
                    <h1 className="text-3xl font-black text-gray-900">{sellerName}</h1>
                    <p className="text-gray-500">Browsing all products from this seller</p>
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="skeleton h-64 rounded-3xl" />
                    ))}
                </div>
            ) : products.length === 0 ? (
                <div className="card text-center py-20">
                    <span className="text-6xl mb-4 block">📦</span>
                    <h2 className="text-xl font-bold text-gray-800">No products found</h2>
                    <p className="text-gray-500">This seller hasn't listed any items yet.</p>
                </div>
            ) : (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 stagger">
                    {products.map((p) => (
                        <ProductCard key={p.id} product={p} />
                    ))}
                </div>
            )}
        </DashboardLayout>
    );
}

// Reusable Product Card (keeping it consistent with Dashboard)
function ProductCard({ product }: { product: any }) {
    const addToCart = (e: React.MouseEvent) => {
        e.preventDefault();
        const cart: any[] = JSON.parse(localStorage.getItem("sb_cart") || "[]");
        const existing = cart.find((i) => i.id === product.id);
        if (existing) { existing.qty += 1; }
        else { cart.push({ ...product, qty: 1 }); }
        localStorage.setItem("sb_cart", JSON.stringify(cart));
        toast.success(`${product.name} added to cart!`);
    };

    return (
        <div className="product-card animate-fade-up h-full flex flex-col">
            <Link href={`/buyer/product/${product.id}`} className="flex-grow no-underline text-inherit">
                <div className="product-card-img flex items-center justify-center text-5xl bg-yellow-50">
                    {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                    ) : (
                        <span>{getCategoryEmoji(product.category)}</span>
                    )}
                </div>
                <div className="product-card-body">
                    <p className="font-bold text-gray-900 text-sm truncate">{product.name}</p>
                    <p className="text-xs text-gray-400 mb-3 truncate">{product.category}</p>
                    <div className="flex items-center justify-between mt-auto">
                        <span className="font-black text-gray-900 text-lg">₹{product.price}</span>
                        <button onClick={addToCart}
                            className="text-xs font-bold px-4 py-2 rounded-xl transition-all shadow-sm hover:scale-105"
                            style={{ background: "var(--yellow-primary)", color: "#111" }}>
                            + Add
                        </button>
                    </div>
                </div>
            </Link>
        </div>
    );
}

function getCategoryEmoji(cat: string) {
    const map: any = {
        fruits: "🍎", dairy: "🥛", bakery: "🍞", meat: "🥩", snacks: "🍿",
        vegetables: "🥦", beverages: "🧃", spices: "🌶️", smartphones: "📱",
        laptops: "💻", beauty: "💄", "health & wellness": "💊",
        "bakery & cakes": "🍰", "womens-dresses": "👗", household: "🧹",
        default: "🛒"
    };
    return map[cat?.toLowerCase()] || map.default;
}
