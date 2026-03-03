"use client";
import { useEffect, useState, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { analyticsApi } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from "recharts";

const COLORS = ["#FFD000", "#FFC107", "#FFAB00", "#FF8F00", "#FF6F00", "#E65100", "#BF360C"];

export default function Storeboard() {
    const [topProducts, setTopProducts] = useState<any[]>([]);
    const [topShops, setTopShops] = useState<any[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [recentOrders, setRecentOrders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(new Date());

    const fetchAll = useCallback(async () => {
        try {
            const [tp, ts, cat, ro] = await Promise.all([
                analyticsApi.topProducts(),
                analyticsApi.topShops(),
                analyticsApi.categoryBreakdown(),
                analyticsApi.recentOrders(),
            ]);
            setTopProducts(tp.data.slice(0, 8));
            setTopShops(ts.data.slice(0, 5));
            setCategories(cat.data.slice(0, 7));
            setRecentOrders(ro.data.slice(0, 8));
            setLastUpdate(new Date());
        } catch { }
        finally { setLoading(false); }
    }, []);

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 15000); // Auto-refresh every 15s
        return () => clearInterval(interval);
    }, [fetchAll]);

    return (
        <DashboardLayout role="seller">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-black">📺 Live Storeboard</h1>
                    <p className="text-sm text-gray-500">
                        Real-time sales analytics · Auto-refreshing every 15s
                        <span className="ml-2 badge badge-green animate-pulse-yellow">🟢 Live</span>
                    </p>
                </div>
                <div className="text-xs text-gray-400">
                    Last updated: {lastUpdate.toLocaleTimeString()}
                    <button onClick={fetchAll} className="btn-ghost ml-2 text-xs">↻ Refresh</button>
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-2 gap-4">
                    {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-40 rounded-2xl" />)}
                </div>
            ) : (
                <>
                    {/* Top Products Chart */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div className="card">
                            <h2 className="section-title">🔥 Top Products by Sales</h2>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={topProducts} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                    <XAxis type="number" tick={{ fontSize: 11 }} />
                                    <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }} />
                                    <Bar dataKey="total_sold" fill="#FFD000" radius={[0, 6, 6, 0]} name="Units Sold" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="card">
                            <h2 className="section-title">🏷️ Sales by Category</h2>
                            {categories.length > 0 ? (
                                <ResponsiveContainer width="100%" height={240}>
                                    <PieChart>
                                        <Pie data={categories} dataKey="total_sold" nameKey="_id" cx="50%" cy="50%"
                                            outerRadius={90} label={({ name, percent }: { name?: string; percent?: number }) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
                                            labelLine={false}>
                                            {categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-center py-12 text-gray-400">No sales data yet</div>
                            )}
                        </div>
                    </div>

                    {/* Top Shops Leaderboard */}
                    <div className="card mb-6">
                        <h2 className="section-title mb-4">🏆 Top Shops Leaderboard</h2>
                        <div className="space-y-3">
                            {topShops.length > 0 ? topShops.map((shop, i) => (
                                <div key={shop._id} className="flex items-center gap-4">
                                    <span className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-sm flex-shrink-0 ${i === 0 ? "bg-yellow-400" : i === 1 ? "bg-gray-200" : i === 2 ? "bg-orange-200" : "bg-gray-100"
                                        }`}>{i + 1}</span>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-bold text-sm truncate">{shop.seller_name || "Shop"}</p>
                                        <div className="h-2 bg-gray-100 rounded-full mt-1">
                                            <div className="h-2 bg-yellow-400 rounded-full transition-all"
                                                style={{ width: `${Math.min(100, (shop.total_sales / (topShops[0]?.total_sales || 1)) * 100)}%` }} />
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-black text-gray-900 text-sm">{shop.total_sales} sold</p>
                                        <p className="text-xs text-gray-400">₹{shop.total_revenue?.toFixed(0)}</p>
                                    </div>
                                </div>
                            )) : <p className="text-center text-gray-400 py-4">No data — place some orders first!</p>}
                        </div>
                    </div>

                    {/* Recent Orders Feed */}
                    <div className="card">
                        <h2 className="section-title mb-4">⚡ Recent Orders</h2>
                        {recentOrders.length === 0
                            ? <p className="text-center text-gray-400 py-4">No orders yet</p>
                            : (
                                <div className="space-y-2">
                                    {recentOrders.map((order) => (
                                        <div key={order.id} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
                                            <span className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-sm">✅</span>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-semibold truncate">{order.buyer_name}</p>
                                                <p className="text-xs text-gray-400">{order.items?.length} items · {order.delivery_address?.slice(0, 30)}…</p>
                                            </div>
                                            <span className="font-black text-gray-900">₹{order.total_amount?.toFixed(2)}</span>
                                        </div>
                                    ))}
                                </div>
                            )
                        }
                    </div>
                </>
            )}
        </DashboardLayout>
    );
}
