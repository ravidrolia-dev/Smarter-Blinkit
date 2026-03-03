"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { inventoryApi, analyticsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer } from "recharts";
import Link from "next/link";

export default function SellerDashboard() {
    const { user } = useAuth();
    const [products, setProducts] = useState<any[]>([]);
    const [topProducts, setTopProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([inventoryApi.myProducts(), analyticsApi.topProducts()])
            .then(([p, t]) => {
                setProducts(p.data);
                setTopProducts(t.data.slice(0, 5));
            }).finally(() => setLoading(false));
    }, []);

    const totalStock = products.reduce((s, p) => s + (p.stock || 0), 0);
    const totalSold = products.reduce((s, p) => s + (p.total_sold || 0), 0);
    const lowStock = products.filter((p) => p.stock <= 5);
    const revenue = products.reduce((s, p) => s + (p.price * p.total_sold || 0), 0);

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

            {/* Sales Chart */}
            {topProducts.length > 0 && (
                <div className="card mb-6">
                    <h2 className="section-title mb-4">🔥 Top Selling Products</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={topProducts}>
                            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                            <Tooltip contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }} />
                            <Bar dataKey="total_sold" fill="#FFD000" radius={[6, 6, 0, 0]} name="Units Sold" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                    { href: "/seller/inventory", icon: "📦", title: "View Inventory", desc: `${products.length} products listed` },
                    { href: "/seller/barcode", icon: "📷", title: "Barcode Scanner", desc: "Scan boxes to update stock" },
                    { href: "/seller/products/new", icon: "➕", title: "Add Product", desc: "List a new item for sale" },
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
