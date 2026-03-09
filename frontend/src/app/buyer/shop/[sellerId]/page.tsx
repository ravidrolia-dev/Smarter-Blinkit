"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi, userApi } from "@/lib/api";
import Link from "next/link";
import toast from "react-hot-toast";

export default function SellerShopPage() {
    const { sellerId } = useParams();
    const [products, setProducts] = useState<any[]>([]);
    const [seller, setSeller] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!sellerId) return;
        setLoading(true);

        const fetchData = async () => {
            try {
                const [productsRes, sellerRes] = await Promise.all([
                    productsApi.list({ seller_id: sellerId as string, limit: 100 }),
                    userApi.getPublicProfile(sellerId as string)
                ]);
                setProducts(productsRes.data);
                setSeller(sellerRes.data);
            } catch (err) {
                console.error("Shop fetch failed:", err);
                // Fallback for seller name if public profile fails
                if (products.length > 0) setSeller({ name: products[0].seller_name });
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [sellerId]);

    const sellerName = seller?.name || "Local Shop";

    return (
        <DashboardLayout role="buyer">
            <div className="mb-10 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <Link href="/buyer" className="w-12 h-12 rounded-2xl bg-white shadow-md flex items-center justify-center hover:bg-yellow-50 hover:scale-105 transition-all text-xl">
                        ⬅️
                    </Link>
                    <div className="flex items-center gap-4">
                        <div className="w-20 h-20 rounded-3xl bg-yellow-400 p-1 shadow-xl shadow-yellow-100">
                            <div className="w-full h-full rounded-[20px] bg-white overflow-hidden flex items-center justify-center text-3xl font-black text-yellow-600 border-2 border-white">
                                {seller?.profile_image ? (
                                    <img src={seller.profile_image} alt={sellerName} className="w-full h-full object-cover" />
                                ) : (
                                    sellerName.charAt(0).toUpperCase()
                                )}
                            </div>
                        </div>
                        <div>
                            <h1 className="text-4xl font-black text-gray-900 leading-tight">{sellerName}</h1>
                            <p className="text-sm font-medium text-gray-400">Trusted Local Seller • {products.length} Products</p>
                        </div>
                    </div>
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
