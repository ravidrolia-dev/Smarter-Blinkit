"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi, analyticsApi, authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useLocation } from "@/hooks/useLocation";
import Link from "next/link";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function BuyerDashboard() {
    const { user } = useAuth();
    const [topProducts, setTopProducts] = useState<any[]>([]);
    const [featured, setFeatured] = useState<any[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [sellers, setSellers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [coords, setCoords] = useState<{ lat: number, lng: number } | null>(null);

    const hour = new Date().getHours();
    const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

    const { status, location, requestLocation } = useLocation();

    useEffect(() => {
        setLoading(true);
        // Fetch products (Primary)
        productsApi.list({ limit: 8 })
            .then((res) => setFeatured(res.data.slice(0, 8)))
            .catch((err) => console.error("Featured products fail:", err))
            .finally(() => setLoading(false));

        // Fetch top products for chart
        analyticsApi.topProducts()
            .then((res) => setTopProducts(res.data.slice(0, 6)))
            .catch((err) => console.error("Top products fail:", err));

        // Fetch categories
        analyticsApi.categoryBreakdown()
            .then((res) => setCategories(res.data.slice(0, 6)))
            .catch((err) => console.error("Categories fail:", err));
    }, []);

    // Sync sellers when location changes
    useEffect(() => {
        if (location) {
            setCoords(location);
            authApi.listSellers({ lat: location.lat, lng: location.lng, radius_km: 15 })
                .then((res) => setSellers(res.data))
                .catch((err) => console.error("Sellers fail:", err));
        }
    }, [location]);

    const quickCategories = [
        { icon: "📱", name: "Smartphones" },
        { icon: "🍰", name: "Bakery & Cakes" },
        { icon: "🍿", name: "Snacks" },
        { icon: "💊", name: "Health & Wellness" },
        { icon: "👗", name: "Womens-Dresses" },
        { icon: "💄", name: "Beauty" },
        { icon: "🥦", name: "Fruits & Vegetables" },
        { icon: "🥛", name: "Dairy" },
    ];

    return (
        <DashboardLayout role="buyer">
            {/* Hero Banner */}
            <div className="hero rounded-3xl p-8 mb-6 relative overflow-hidden">
                <div className="relative z-10">
                    <p className="text-sm font-semibold text-gray-700 mb-1">{greeting}, {user?.name?.split(" ")[0]}! 👋</p>
                    <h1 className="text-3xl font-black text-gray-900 mb-2">What are you cooking today?</h1>
                    <p className="text-gray-700 mb-4 max-w-sm">Tell our AI and it'll fill your cart from nearby shops!</p>
                    <Link href="/buyer/agent" className="btn-primary">🤖 Try Recipe Agent</Link>
                </div>
                <div className="absolute right-8 top-4 text-8xl opacity-20 rotate-12">🛒</div>
            </div>

            {/* Quick Category Chips */}
            <div className="mb-6">
                <h2 className="section-title">Browse by Category</h2>
                <div className="grid grid-cols-4 md:grid-cols-8 gap-2 stagger">
                    {quickCategories.map((cat) => (
                        <Link key={cat.name}
                            href={`/buyer/search?q=${cat.name}`}
                            className="card animate-fade-up flex flex-col items-center gap-1 py-3 hover:!shadow-yellow-200 cursor-pointer">
                            <span className="text-2xl">{cat.icon}</span>
                            <span className="text-xs font-semibold text-gray-700">{cat.name}</span>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Featured Products */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <h2 className="section-title">Featured Products</h2>
                        <p className="section-sub">Fresh picks from local shops near you</p>
                    </div>
                    <Link href="/buyer/search?q=popular" className="btn-ghost text-xs">See all →</Link>
                </div>
                {loading ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[...Array(8)].map((_, i) => (
                            <div key={i} className="skeleton h-52 rounded-2xl" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger">
                        {featured.map((p) => (
                            <ProductCard key={p.id || p._id} product={p} />
                        ))}
                    </div>
                )}
            </div>

            {/* Shop by Seller */}
            {sellers.length > 0 && (
                <div className="mb-6">
                    <h2 className="section-title">Shop by Seller</h2>
                    <p className="section-sub">Trusted local shops from your area</p>
                    <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar stagger">
                        {sellers.map((s) => (
                            <Link key={s.id} href={`/buyer/shop/${s.id}`}
                                className="card flex-shrink-0 w-48 py-4 flex flex-col items-center gap-2 hover:border-yellow-400 border-2 border-transparent transition-all">
                                <div className="w-16 h-16 rounded-full bg-yellow-100 flex items-center justify-center text-3xl">
                                    🏪
                                </div>
                                <div className="text-center">
                                    <p className="font-bold text-gray-900 truncate w-40">{s.name}</p>
                                    <p className="text-[10px] text-gray-400 truncate w-40">{s.address || "Jaipur, Rajasthan"}</p>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Trending Chart */}
            {topProducts.length > 0 && (
                <div className="card mb-6">
                    <h2 className="section-title mb-4">🔥 Trending This Week</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={topProducts}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                            <YAxis tick={{ fontSize: 11 }} />
                            <Tooltip
                                contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }}
                            />
                            <Bar dataKey="total_sold" fill="#FFD000" radius={[6, 6, 0, 0]} name="Units Sold" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Quick Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                    { href: "/buyer/search", icon: "🔍", title: "Smart Search", desc: "\"I have a cold\" → Honey, Ginger Tea" },
                    { href: "/buyer/agent", icon: "🤖", title: "Recipe Agent", desc: "Type a meal, get all ingredients" },
                    { href: "/buyer/orders", icon: "📦", title: "Track Orders", desc: "View your order history" },
                ].map((item) => (
                    <Link key={item.href} href={item.href}
                        className="card flex items-start gap-4 cursor-pointer">
                        <span className="text-3xl">{item.icon}</span>
                        <div>
                            <p className="font-bold text-gray-900">{item.title}</p>
                            <p className="text-xs text-gray-500">{item.desc}</p>
                        </div>
                    </Link>
                ))}
            </div>
        </DashboardLayout>
    );
}

function ProductCard({ product }: { product: any }) {
    const addToCart = (e: React.MouseEvent) => {
        e.preventDefault();
        const cart: any[] = JSON.parse(localStorage.getItem("sb_cart") || "[]");
        const existing = cart.find((i) => i.id === (product.id || product._id));
        if (existing) { existing.qty += 1; }
        else { cart.push({ ...product, id: product.id || product._id, qty: 1 }); }
        localStorage.setItem("sb_cart", JSON.stringify(cart));
        const toast_mod = require("react-hot-toast").default;
        toast_mod.success(`${product.name} added to cart!`);
    };

    const id = product.id || product._id;
    return (
        <div className="product-card animate-fade-up">
            <Link href={`/buyer/product/${id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <div className="product-card-img flex items-center justify-center text-5xl bg-yellow-50">
                    {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                    ) : (
                        <span>{getCategoryEmoji(product.category)}</span>
                    )}
                </div>
                <div className="product-card-body">
                    <p className="font-bold text-gray-900 text-sm truncate">{product.name}</p>
                    <p className="text-xs text-gray-400 mb-2 truncate">{product.category}</p>
                    <div className="flex items-center justify-between">
                        <span className="font-black text-gray-900">₹{product.price}</span>
                        <button onClick={addToCart}
                            className="text-xs font-bold px-3 py-1.5 rounded-lg transition-all"
                            style={{ background: "var(--yellow-primary)", color: "#111" }}>
                            + Add
                        </button>
                    </div>
                    {product.distance_km && (
                        <p className="text-xs text-gray-400 mt-1">📍 {product.distance_km} km away</p>
                    )}
                </div>
            </Link>
        </div>
    );
}

function getCategoryEmoji(cat: string) {
    const map: any = {
        fruits: "🍎",
        dairy: "🥛",
        bakery: "🍞",
        meat: "🥩",
        snacks: "🍿",
        vegetables: "🥦",
        beverages: "🧃",
        spices: "🌶️",
        smartphones: "📱",
        laptops: "💻",
        beauty: "💄",
        "health & wellness": "💊",
        "bakery & cakes": "🍰",
        "womens-dresses": "👗",
        "womens-bags": "👜",
        "womens-shoes": "👠",
        household: "🧹",
        "personal care": "🧴",
        default: "🛒"
    };
    return map[cat?.toLowerCase()] || map.default;
}
