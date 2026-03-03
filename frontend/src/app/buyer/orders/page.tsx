"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ordersApi } from "@/lib/api";

export default function BuyerOrdersPage() {
    const [orders, setOrders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        ordersApi.myOrders().then((r) => setOrders(r.data)).catch(() => { }).finally(() => setLoading(false));
    }, []);

    const statusColor: Record<string, string> = {
        pending: "badge-gray", paid: "badge-green", processing: "badge-yellow",
        delivered: "badge-green", cancelled: "badge-red",
    };

    return (
        <DashboardLayout role="buyer">
            <h1 className="text-2xl font-black mb-1">📦 My Orders</h1>
            <p className="text-sm text-gray-500 mb-6">Track all your orders here</p>

            {loading ? (
                <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="skeleton h-24 rounded-2xl" />)}</div>
            ) : orders.length === 0 ? (
                <div className="text-center py-20 text-gray-400">
                    <span className="text-5xl block mb-3">📦</span>
                    <p className="font-semibold">No orders yet</p>
                    <a href="/buyer/search" className="btn-primary mt-4 inline-block">Start Shopping</a>
                </div>
            ) : (
                <div className="space-y-4">
                    {orders.map((order) => (
                        <div key={order.id} className="card-flat">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="text-xs text-gray-400">Order #{order.id?.slice(-8)}</p>
                                    <p className="font-bold text-gray-900">₹{order.total_amount?.toFixed(2)}</p>
                                </div>
                                <span className={`badge ${statusColor[order.status] || "badge-gray"} capitalize`}>
                                    {order.status}
                                </span>
                            </div>
                            <div className="space-y-1">
                                {order.items?.map((item: any, i: number) => (
                                    <div key={i} className="flex items-center justify-between text-sm">
                                        <span className="text-gray-700">{item.product_name} × {item.quantity}</span>
                                        <span className="text-gray-500">₹{(item.price * item.quantity).toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                            <p className="text-xs text-gray-400 mt-3 pt-2 border-t">📍 {order.delivery_address}</p>
                        </div>
                    ))}
                </div>
            )}
        </DashboardLayout>
    );
}
