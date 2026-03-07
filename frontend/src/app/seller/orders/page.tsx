"use client";
import { useEffect, useState, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { analyticsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function Storeboard() {
    const { user } = useAuth();
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
                analyticsApi.recentOrders({ seller_id: user?.id }),
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
                    <h1 className="text-2xl font-black">⚡ Recent Orders</h1>
                    <p className="text-sm text-gray-500">
                        Live order feed · Auto-refreshing every 15s
                    </p>
                </div>
                <div className="text-xs text-gray-400">
                    Last sync: {lastUpdate.toLocaleTimeString()}
                    <button onClick={fetchAll} className="btn-ghost ml-2 text-xs">↻ Sync</button>
                </div>
            </div>

            {loading ? (
                <div className="space-y-4">
                    {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-20 rounded-2xl" />)}
                </div>
            ) : (
                <div className="card">
                    {recentOrders.length === 0
                        ? <div className="text-center py-20">
                            <span className="text-6xl mb-4 block">📦</span>
                            <p className="text-gray-400">No orders yet — stats will appear on Dashboard once sales start!</p>
                        </div>
                        : (
                            <div className="space-y-2">
                                {recentOrders.map((order) => (
                                    <div key={order.id} className="flex items-center gap-4 py-4 border-b border-gray-50 last:border-0 hover:bg-gray-50/50 transition-colors px-2 rounded-xl">
                                        <span className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-lg">✅</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                                <p className="font-bold text-gray-900 truncate">{order.buyer_name}</p>
                                                <span className="font-black text-gray-900">₹{order.total_amount?.toFixed(2)}</span>
                                            </div>
                                            <p className="text-xs text-gray-400 truncate">{order.items?.length} items · {order.delivery_address?.slice(0, 50)}…</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )
                    }
                </div>
            )}
        </DashboardLayout>
    );
}
