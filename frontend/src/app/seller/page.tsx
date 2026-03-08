"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { inventoryApi, analyticsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from "recharts";
import Link from "next/link";
import { useCallback } from "react";

const COLORS = ["#FFD000", "#FFC107", "#FFAB00", "#FF8F00", "#FF6F00", "#E65100", "#BF360C"];

export default function SellerDashboard() {
    const { user } = useAuth();
    const [products, setProducts] = useState<any[]>([]);
    const [recentOrders, setRecentOrders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(new Date());

    const fetchAll = useCallback(async () => {
        try {
            const [p, ro] = await Promise.all([
                inventoryApi.myProducts(),
                analyticsApi.recentOrders({ seller_id: user?.id }),
            ]);
            setProducts(p.data);
            setRecentOrders(ro.data.slice(0, 5));
            setLastUpdate(new Date());
        } catch (err) {
            console.error("Dashboard refresh failed:", err);
        } finally {
            setLoading(false);
        }
    }, [user?.id]);

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 15000); // Live sync
        return () => clearInterval(interval);
    }, [fetchAll]);

    const totalStock = products.reduce((s, p) => s + (p.stock || 0), 0);
    const totalSold = products.reduce((s, p) => s + (p.total_sold || 0), 0);
    const lowStock = products.filter((p) => p.stock <= 5);
    const revenue = products.reduce((s, p) => s + (p.price * p.total_sold || 0), 0);

    // Personalized Analytics Logic
    const myTopProducts = [...products]
        .filter(p => p.total_sold > 0)
        .sort((a, b) => b.total_sold - a.total_sold)
        .slice(0, 5);

    const categoryMap: Record<string, number> = {};
    products.forEach(p => {
        if (p.total_sold > 0) {
            categoryMap[p.category] = (categoryMap[p.category] || 0) + p.total_sold;
        }
    });
    const myCategories = Object.entries(categoryMap).map(([name, total_sold]) => ({
        name,
        total_sold
    })).sort((a, b) => b.total_sold - a.total_sold);

    const stats = [
        { icon: "📦", label: "Total Products", value: products.length },
        { icon: "📊", label: "Units in Stock", value: totalStock.toLocaleString() },
        { icon: "✅", label: "Units Sold", value: totalSold.toLocaleString() },
        { icon: "💰", label: "Total Revenue", value: `₹${revenue.toLocaleString()}` },
    ];

    return (
        <DashboardLayout role="seller">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-black">📊 Seller Dashboard</h1>
                    <p className="text-sm text-gray-500">Welcome back, {user?.name?.split(" ")[0]}!</p>
                </div>
                <Link href="/seller/products/new" className="btn-primary">+ Add Product</Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {stats.map((s) => (
                    <div key={s.label} className="stat-card animate-fade-up">
                        <div className="stat-icon">{s.icon}</div>
                        <div>
                            <p className="text-2xl font-black text-gray-900">{s.value}</p>
                            <p className="text-xs text-gray-500">{s.label}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Low Stock Warning */}
            {lowStock.length > 0 && (
                <div className="card-flat border-red-200 border bg-red-50 mb-6">
                    <p className="font-bold text-red-700 mb-2">⚠️ Low Stock Alert ({lowStock.length} products)</p>
                    <div className="flex flex-wrap gap-2">
                        {lowStock.map((p) => (
                            <span key={p.id} className="badge badge-red">{p.name} ({p.stock} left)</span>
                        ))}
                    </div>
                    <Link href="/seller/barcode" className="btn-primary mt-3 inline-block text-sm">📷 Update via Barcode</Link>
                </div>
            )}

            {/* Personalized Analytics Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* My Top Products */}
                <div className="card">
                    <h2 className="section-title">🏆 Your Top Products</h2>
                    <p className="text-[10px] text-gray-400 mb-4">Most sold items in your store</p>
                    {myTopProducts.length > 0 ? (
                        <ResponsiveContainer width="100%" height={240}>
                            <BarChart data={myTopProducts} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                <XAxis type="number" tick={{ fontSize: 11 }} />
                                <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
                                <Tooltip contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }} />
                                <Bar dataKey="total_sold" fill="#FFD000" radius={[0, 6, 6, 0]} name="Units Sold" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-center py-12 text-gray-400">No sales data yet</div>
                    )}
                </div>

                {/* My Sales by Category */}
                <div className="card">
                    <h2 className="section-title">🏷️ Category Performance</h2>
                    <p className="text-[10px] text-gray-400 mb-4">Your sales volume by category</p>
                    {myCategories.length > 0 ? (
                        <ResponsiveContainer width="100%" height={240}>
                            <PieChart>
                                <Pie data={myCategories} dataKey="total_sold" nameKey="name" cx="50%" cy="50%"
                                    outerRadius={80} label={({ name, percent }: { name?: string; percent?: number }) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
                                    labelLine={false}>
                                    {myCategories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="text-center py-12 text-gray-400">No category sales yet</div>
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                    { href: "/seller/inventory", icon: "📦", title: "View Inventory", desc: `${products.length} products listed` },
                    { href: "/seller/barcode", icon: "📷", title: "Barcode Scanner", desc: "Scan boxes to update stock" },
                    { href: "/seller/top-picks", icon: "🏆", title: "Top Picks", desc: "Market analytics & leaderboard" },
                ].map((a) => (
                    <Link key={a.href} href={a.href} className="card flex items-center gap-4 cursor-pointer">
                        <span className="text-3xl">{a.icon}</span>
                        <div>
                            <p className="font-bold text-gray-900">{a.title}</p>
                            <p className="text-xs text-gray-500">{a.desc}</p>
                        </div>
                    </Link>
                ))}
            </div>
        </DashboardLayout>
    );
}
