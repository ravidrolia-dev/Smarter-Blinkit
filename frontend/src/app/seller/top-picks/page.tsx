"use client";
import { useEffect, useState, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { analyticsApi, inventoryApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from "recharts";

const COLORS = ["#FFD000", "#FFC107", "#FFAB00", "#FF8F00", "#FF6F00", "#E65100", "#BF360C"];

export default function TopPicks() {
    const { user } = useAuth();
    const [topProducts, setTopProducts] = useState<any[]>([]);
    const [topShops, setTopShops] = useState<any[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const fetchAnalytics = useCallback(async () => {
        try {
            const [tp, ts, cat] = await Promise.all([
                analyticsApi.topProducts(),
                analyticsApi.topShops(),
                analyticsApi.categoryBreakdown(),
            ]);
            setTopProducts(tp.data.slice(0, 8));
            setTopShops(ts.data.slice(0, 10)); // Show more on dedicated page
            setCategories(cat.data.slice(0, 10));
            setLastUpdate(new Date());
        } catch (err) {
            console.error("Top Picks refresh failed:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAnalytics();
        const interval = setInterval(fetchAnalytics, 30000); // 30s for heavy analytics
        return () => clearInterval(interval);
    }, [fetchAnalytics]);

    return (
        <DashboardLayout role="seller">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-black">🏆 Top Picks & Insights</h1>
                    <p className="text-sm text-gray-500">
                        Market-wide trends and top performing shops
                        {lastUpdate && <span className="ml-2 text-[10px] text-gray-400">· Sync: {lastUpdate.toLocaleTimeString()}</span>}
                    </p>
                </div>
                <button onClick={fetchAnalytics} className="btn-ghost text-xs">↻ Refresh Insights</button>
            </div>

            {loading && !lastUpdate ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="skeleton h-64 rounded-2xl" />
                    <div className="skeleton h-64 rounded-2xl" />
                    <div className="skeleton h-96 rounded-2xl md:col-span-2" />
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Top Products */}
                        <div className="card">
                            <h2 className="section-title">🔥 Top Products by Sales</h2>
                            <p className="text-[10px] text-gray-400 mb-4">High demand across all categories</p>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={topProducts} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                    <XAxis type="number" tick={{ fontSize: 11 }} />
                                    <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }} />
                                    <Bar dataKey="total_sold" fill="#FFD000" radius={[0, 6, 6, 0]} name="Units Sold" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Sales by Category */}
                        <div className="card">
                            <h2 className="section-title">🏷️ Category Volume</h2>
                            <p className="text-[10px] text-gray-400 mb-4">Total units sold per category</p>
                            {categories.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie data={categories} dataKey="total_sold" nameKey="_id" cx="50%" cy="50%"
                                            outerRadius={100} label={({ name, percent }: { name?: string; percent?: number }) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
                                            labelLine={false}>
                                            {categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-center py-20 text-gray-400 font-medium">Insufficient sales data</div>
                            )}
                        </div>
                    </div>

                    {/* Shop Leaderboard - Full View */}
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="section-title">🥇 Top Shops Leaderboard</h2>
                            <span className="badge badge-yellow text-xs px-3">Live Rankings</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
                            {topShops.length > 0 ? topShops.map((shop, i) => (
                                <div key={shop._id} className="flex items-center gap-4 group">
                                    <span className={`w-10 h-10 rounded-full flex items-center justify-center font-black text-sm flex-shrink-0 transition-transform group-hover:scale-110 ${i === 0 ? "bg-yellow-400" : i === 1 ? "bg-gray-200" : i === 2 ? "bg-orange-200" : "bg-gray-100"
                                        }`}>{i + 1}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between mb-1.5">
                                            <p className="font-bold text-gray-900 truncate">{shop.seller_name || "Nexus Shop"}</p>
                                            <p className="font-black text-gray-900 text-sm">{shop.total_sales.toLocaleString()} sold</p>
                                        </div>
                                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                            <div className="h-full bg-yellow-400 rounded-full transition-all duration-700"
                                                style={{ width: `${Math.min(100, (shop.total_sales / (topShops[0]?.total_sales || 1)) * 100)}%` }} />
                                        </div>
                                        <p className="text-[10px] text-gray-400 mt-1">Estimated Revenue: ₹{shop.total_revenue?.toLocaleString()}</p>
                                    </div>
                                </div>
                            )) : <p className="text-center text-gray-400 py-12 md:col-span-2 italic">Ranking will update as shops fulfill more orders...</p>}
                        </div>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
