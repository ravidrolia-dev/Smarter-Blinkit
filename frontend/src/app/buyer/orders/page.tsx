"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ordersApi } from "@/lib/api";
import dynamic from "next/dynamic";
import Link from "next/link";

const DeliveryRouteMap = dynamic(() => import("@/components/DeliveryRouteMap"), {
    ssr: false,
    loading: () => <div className="h-40 bg-gray-50 animate-pulse rounded-xl flex items-center justify-center text-gray-400 text-xs font-medium">Loading Route Map...</div>
});

export default function BuyerOrdersPage() {
    const [orders, setOrders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        ordersApi.myOrders().then((r) => setOrders(r.data)).catch(() => { }).finally(() => setLoading(false));
    }, []);

    const filteredOrders = orders.filter(o =>
        o.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        o.items?.some((i: any) => i.product_name.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const statusMap: Record<string, { color: string, step: number }> = {
        pending: { color: "#9ca3af", step: 1 },
        paid: { color: "#10b981", step: 2 },
        processing: { color: "#f59e0b", step: 3 },
        shipped: { color: "#3b82f6", step: 4 },
        delivered: { color: "#10b981", step: 5 },
        cancelled: { color: "#ef4444", step: 0 }
    };

    return (
        <DashboardLayout role="buyer">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-[900] tracking-tight text-gray-900 mb-1">📦 My Orders</h1>
                    <p className="text-sm text-gray-500">Track and manage your recent deliveries</p>
                </div>
                <div className="relative flex-1 max-w-md">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
                    <input
                        type="text"
                        placeholder="Search by Order ID or products..."
                        className="w-full pl-10 pr-4 py-3 rounded-2xl border-none bg-gray-100 focus:ring-2 focus:ring-yellow-400 font-medium transition-all"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {loading ? (
                <div className="grid gap-6">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-48 rounded-[2rem]" />)}</div>
            ) : filteredOrders.length === 0 ? (
                <div className="text-center py-24 bg-gray-50 rounded-[3rem] border-2 border-dashed border-gray-200">
                    <span className="text-6xl block mb-4 animate-bounce">📦</span>
                    <h3 className="text-xl font-bold text-gray-900">No matching orders</h3>
                    <p className="text-gray-500 mb-6">Try adjusting your search or start a new shopping spree</p>
                    <a href="/buyer/search" className="btn-primary px-8 py-3 rounded-2xl inline-block hover:scale-105 transition-transform">Browse Products</a>
                </div>
            ) : (
                <div className="grid gap-8">
                    {filteredOrders.map((order) => (
                        <div key={order.id} className="group bg-white rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.05)] border border-gray-100 overflow-hidden hover:shadow-[0_30px_60px_rgba(0,0,0,0.08)] transition-all duration-500">
                            <div className="flex flex-col lg:flex-row">
                                {/* Left Content: Order Info */}
                                <div className="flex-1 p-8 lg:p-10">
                                    <div className="flex items-start justify-between mb-8">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="px-3 py-1 bg-gray-100 text-gray-500 rounded-full text-[10px] font-bold uppercase tracking-widest">Order ID</span>
                                                <p className="text-sm font-mono text-gray-400">#{order.id?.slice(-8)}</p>
                                            </div>
                                            <p className="text-3xl font-[900] text-gray-900">₹{order.total_amount?.toFixed(2)}</p>
                                        </div>
                                        <div className="flex flex-col items-end gap-2">
                                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Status</span>
                                            <span className="px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest transition-all"
                                                style={{ backgroundColor: `${statusMap[order.status]?.color}15`, color: statusMap[order.status]?.color, border: `1px solid ${statusMap[order.status]?.color}30` }}>
                                                {order.status}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="space-y-4 mb-8">
                                        {order.items?.map((item: any, i: number) => (
                                            <div key={i} className="flex items-center gap-4 bg-gray-50 p-4 rounded-2xl group-hover:bg-white group-hover:shadow-sm transition-all border border-transparent group-hover:border-gray-100">
                                                <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-lg shadow-sm">🛒</div>
                                                <div className="flex-1">
                                                    <p className="font-bold text-gray-900">{item.product_name}</p>
                                                    <p className="text-xs text-gray-400">{item.quantity} unit{item.quantity > 1 ? 's' : ''} • <span className="text-gray-500 font-semibold">₹{item.price}</span></p>
                                                </div>
                                                <p className="font-black text-gray-900">₹{(item.price * item.quantity).toFixed(2)}</p>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="flex items-center gap-2 text-xs text-gray-400 bg-gray-50 p-3 rounded-xl border border-gray-100">
                                        <span className="text-base">📍</span>
                                        <span className="flex-1 truncate">{order.delivery_address}</span>
                                    </div>
                                </div>

                                {/* Right Content: Delivery Map & Stepper */}
                                <div className="lg:w-[450px] bg-gray-50/50 p-8 border-t lg:border-t-0 lg:border-l border-gray-100 flex flex-col">
                                    {/* Mini Stepper */}
                                    <div className="mb-6">
                                        <div className="flex items-center justify-between mb-4">
                                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Journey Progress</p>
                                            {order.route_distance_km && <span className="text-[10px] font-black text-yellow-600 bg-yellow-100 px-2 py-0.5 rounded-md">🏁 {order.route_distance_km}km</span>}
                                        </div>
                                        <div className="flex gap-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                            {[1, 2, 3, 4, 5].map((s) => (
                                                <div
                                                    key={s}
                                                    className={`flex-1 transition-all duration-1000 ${s <= (statusMap[order.status]?.step || 0) ? 'bg-yellow-400' : 'bg-transparent'}`}
                                                />
                                            ))}
                                        </div>
                                    </div>

                                    <div className="flex-1 relative rounded-3xl overflow-hidden border-2 border-white shadow-xl bg-white min-h-[220px]">
                                        {order.route_stops && order.route_stops.length > 0 ? (
                                            <DeliveryRouteMap
                                                stops={order.route_stops}
                                                geometry={order.route_geometry}
                                                height="100%"
                                            />
                                        ) : (
                                            <div className="h-full flex flex-col items-center justify-center text-center p-6 bg-gray-50">
                                                <span className="text-3xl mb-2">🗺️</span>
                                                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Optimizing Route...</p>
                                            </div>
                                        )}
                                    </div>

                                    <div className="mt-6 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-gray-400">
                                        <div className="flex items-center gap-4">
                                            <span>⏱️ {order.route_time_minutes || '--'} mins</span>
                                            <span>🏪 {order.route_stops?.filter((s: any) => s.type === 'shop').length || 0} stops</span>
                                        </div>
                                        <Link href={`/buyer/orders/${order.id}`} className="text-yellow-600 hover:text-yellow-700 underline underline-offset-4 font-black">Details →</Link>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </DashboardLayout>
    );
}
