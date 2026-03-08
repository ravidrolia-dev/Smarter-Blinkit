"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { ordersApi } from "@/lib/api";
import dynamic from "next/dynamic";
import Link from "next/link";

const DeliveryRouteMap = dynamic(() => import("@/components/DeliveryRouteMap"), {
    ssr: false,
    loading: () => <div className="h-64 bg-gray-50 animate-pulse rounded-[2.5rem] flex items-center justify-center text-gray-400 text-xs font-medium">Loading Full Route Map...</div>
});

const PrintStyles = () => (
    <style jsx global>{`
        @media print {
            @page { margin: 10mm; }
            body { 
                background: white !important; 
                margin: 0 !important; 
                padding: 0 !important;
            }
            /* Robustly hide everything except the invoice */
            .navbar, .sidebar, .address-bar, .print\\:hidden, 
            nav, aside, header, footer, button, .btn-primary {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                margin: 0 !important;
            }
            .page-with-sidebar {
                margin: 0 !important;
                padding: 0 !important;
                display: block !important;
                position: static !important;
            }
            .page-content {
                padding: 0 !important;
                margin: 0 !important;
            }
            /* Ensure the invoice container is top-level */
            .invoice-print-container {
                display: block !important;
                position: static !important;
                width: 100% !important;
                padding: 0 !important;
            }
        }
    `}</style>
);

export default function OrderDetailsPage() {
    const { id } = useParams();
    const router = useRouter();
    const [order, setOrder] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (id) {
            ordersApi.get(id as string)
                .then((r) => setOrder(r.data))
                .catch(() => router.push("/buyer/orders"))
                .finally(() => setLoading(false));
        }
    }, [id, router]);

    const statusMap: Record<string, { color: string, step: number, label: string, icon: string }> = {
        pending: { color: "#9ca3af", step: 1, label: "Order Placed", icon: "📝" },
        paid: { color: "#10b981", step: 2, label: "Payment Confirmed", icon: "💰" },
        processing: { color: "#f59e0b", step: 3, label: "Processing at Shop", icon: "🏪" },
        shipped: { color: "#3b82f6", step: 4, label: "Out for Delivery", icon: "🚚" },
        delivered: { color: "#10b981", step: 5, label: "Delivered", icon: "🏡" },
        cancelled: { color: "#ef4444", step: 0, label: "Cancelled", icon: "❌" }
    };

    if (loading) return (
        <DashboardLayout role="buyer">
            <div className="skeleton h-8 w-48 mb-6 rounded-xl" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 skeleton h-[600px] rounded-[3rem]" />
                <div className="skeleton h-[600px] rounded-[3rem]" />
            </div>
        </DashboardLayout>
    );

    if (!order) return null;

    const currentStatus = statusMap[order.status] || statusMap.pending;

    return (
        <DashboardLayout role="buyer">
            <PrintStyles />
            {/* Standard Screen UI */}
            <div className="print:hidden">
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/buyer/orders" className="w-12 h-12 flex items-center justify-center bg-gray-100 rounded-2xl hover:bg-gray-200 transition-all text-xl">←</Link>
                    <div>
                        <h1 className="text-3xl font-[900] text-gray-900 tracking-tight">Order Details</h1>
                        <p className="text-sm text-gray-500">ID: <span className="font-mono text-gray-400">#{id?.slice(-8)}</span> • {new Date(order.created_at || Date.now()).toLocaleDateString()}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                    <div className="lg:col-span-2 space-y-8">
                        <div className="bg-white rounded-[2.5rem] shadow-xl shadow-gray-100 border border-gray-100 p-8">
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-4">
                                    <span className="text-4xl">{currentStatus.icon}</span>
                                    <div>
                                        <p className="text-sm font-bold text-gray-400 uppercase tracking-widest leading-none mb-1">Current Status</p>
                                        <h2 className="text-2xl font-black text-gray-900">{currentStatus.label}</h2>
                                    </div>
                                </div>
                                <span className="px-6 py-2 rounded-full text-xs font-black uppercase tracking-widest"
                                    style={{ backgroundColor: `${currentStatus.color}15`, color: currentStatus.color, border: `1px solid ${currentStatus.color}30` }}>
                                    {order.status}
                                </span>
                            </div>

                            <div className="relative pt-8 pb-4">
                                <div className="absolute top-0 left-0 w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-yellow-400 transition-all duration-1000" style={{ width: `${(currentStatus.step / 5) * 100}%` }} />
                                </div>
                                <div className="flex justify-between mt-4">
                                    {Object.values(statusMap).filter(s => s.step > 0).sort((a, b) => a.step - b.step).map((s) => (
                                        <div key={s.step} className="flex flex-col items-center gap-2">
                                            <div className={`w-3 h-3 rounded-full border-4 ${s.step <= currentStatus.step ? 'bg-yellow-400 border-yellow-100' : 'bg-white border-gray-100'}`} />
                                            <span className={`text-[10px] font-black uppercase tracking-widest text-center ${s.step <= currentStatus.step ? 'text-gray-900' : 'text-gray-300'}`}>
                                                {s.label.split(' ')[0]}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-[2.5rem] shadow-xl shadow-gray-100 border border-gray-100 overflow-hidden">
                            <div className="p-8 border-b border-gray-50 flex items-center justify-between">
                                <h3 className="text-lg font-black text-gray-900 tracking-tight">🗺️ Live Delivery Path</h3>
                                <div className="flex gap-4 text-[10px] font-black uppercase tracking-widest text-gray-400">
                                    <span>📏 {order.route_distance_km || '--'} km</span>
                                    <span>⏱️ {order.route_time_minutes || '--'} mins</span>
                                </div>
                            </div>
                            <div className="h-[400px]">
                                {order.route_stops ? (
                                    <DeliveryRouteMap
                                        stops={order.route_stops}
                                        geometry={order.route_geometry}
                                        height="100%"
                                    />
                                ) : (
                                    <div className="h-full flex items-center justify-center bg-gray-50 text-gray-400 font-bold uppercase tracking-widest text-sm">
                                        No Route Data Available
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-8">
                        <div className="bg-white rounded-[2.5rem] shadow-xl shadow-gray-100 border border-gray-100 p-8">
                            <h3 className="text-lg font-black text-gray-900 tracking-tight mb-6">📝 Order Summary</h3>
                            <div className="space-y-4 mb-8">
                                {order.items?.map((item: any, i: number) => (
                                    <div key={i} className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center text-lg">🛍️</div>
                                        <div className="flex-1">
                                            <p className="font-bold text-gray-900 text-sm leading-tight">{item.product_name}</p>
                                            <p className="text-[10px] font-bold text-gray-400">QTY: {item.quantity} • ₹{item.price}</p>
                                        </div>
                                        <p className="font-black text-gray-900 text-sm">₹{(item.price * item.quantity).toFixed(2)}</p>
                                    </div>
                                ))}
                            </div>
                            <div className="pt-6 border-t border-gray-100 space-y-2">
                                <div className="flex justify-between text-xs text-gray-500 font-bold uppercase tracking-widest">
                                    <span>Subtotal</span>
                                    <span>₹{(order.total_amount || 0).toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between text-xs text-gray-500 font-bold uppercase tracking-widest">
                                    <span>Delivery Fee</span>
                                    <span className="text-green-500">FREE</span>
                                </div>
                                <div className="flex justify-between pt-4 text-xl font-black text-gray-900">
                                    <span>Total</span>
                                    <span>₹{(order.total_amount || 0).toFixed(2)}</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-yellow-400 rounded-[2.5rem] p-8 text-yellow-950 shadow-2xl shadow-yellow-100">
                            <div className="flex items-center gap-3 mb-4">
                                <span className="text-2xl">🏡</span>
                                <h3 className="font-black tracking-tight uppercase tracking-widest text-xs">Delivery Address</h3>
                            </div>
                            <p className="font-bold text-sm mb-6 leading-relaxed">
                                {order.delivery_address}
                            </p>
                            <div className="bg-yellow-500/20 rounded-2xl p-4 border border-yellow-950/10">
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] mb-1">Delivery Instructions</p>
                                <p className="text-xs font-semibold">Please leave at the front door and ring the bell.</p>
                            </div>
                        </div>

                        <button
                            onClick={() => window.print()}
                            className="w-full py-4 bg-gray-900 text-white rounded-[1.5rem] font-bold text-sm tracking-widest uppercase hover:bg-black transition-all shadow-xl shadow-gray-200"
                        >
                            🖨️ Print Invoice
                        </button>
                    </div>
                </div>
            </div>

            {/* Print-Only Dedicated Invoice Layout */}
            <div className="hidden print:block p-0 bg-white text-black min-h-screen invoice-print-container">
                <div className="flex justify-between items-start border-b-4 border-black pb-8 mb-12">
                    <div>
                        <h1 className="text-5xl font-black tracking-tighter mb-2">SmarterBlinkit</h1>
                        <p className="text-sm font-bold uppercase tracking-widest text-gray-500">Official Invoice</p>
                    </div>
                    <div className="text-right">
                        <p className="text-2xl font-black mb-1">INVOICE #{(id as string)?.slice(-8).toUpperCase()}</p>
                        <p className="text-sm font-semibold text-gray-600">Date: {new Date(order.created_at || Date.now()).toLocaleDateString()}</p>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-12 mb-12">
                    <div>
                        <h4 className="text-xs font-black uppercase tracking-widest text-gray-400 mb-4">Customer Details</h4>
                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                            <p className="font-bold text-lg mb-1">{order.buyer_name || "Valued Customer"}</p>
                            <p className="text-sm text-gray-600 leading-relaxed font-medium">{order.delivery_address}</p>
                        </div>
                    </div>
                    <div>
                        <h4 className="text-xs font-black uppercase tracking-widest text-gray-400 mb-4">Order Status</h4>
                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                            <p className="font-black text-lg uppercase tracking-wider">{order.status}</p>
                            <p className="text-xs text-gray-500 font-bold uppercase tracking-widest mt-1">Payment ID: {order.payment_id || "demo-txn"}</p>
                        </div>
                    </div>
                </div>

                <div className="mb-12">
                    <h4 className="text-xs font-black uppercase tracking-widest text-gray-400 mb-4">Itemized Breakdown</h4>
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b-2 border-black">
                                <th className="py-4 text-xs font-black uppercase tracking-widest">Product</th>
                                <th className="py-4 text-xs font-black uppercase tracking-widest text-center">Qty</th>
                                <th className="py-4 text-xs font-black uppercase tracking-widest text-right">Price</th>
                                <th className="py-4 text-xs font-black uppercase tracking-widest text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {order.items?.map((item: any, i: number) => (
                                <tr key={i}>
                                    <td className="py-4 font-bold text-gray-800">{item.product_name}</td>
                                    <td className="py-4 font-bold text-center text-gray-600">{item.quantity}</td>
                                    <td className="py-4 font-bold text-right text-gray-600">₹{item.price.toFixed(2)}</td>
                                    <td className="py-4 font-black text-right text-gray-900">₹{(item.price * item.quantity).toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex justify-end pt-8 border-t-2 border-black">
                    <div className="w-64 space-y-3">
                        <div className="flex justify-between text-sm font-bold text-gray-500 uppercase tracking-widest">
                            <span>Subtotal</span>
                            <span>₹{(order.total_amount || 0).toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-sm font-bold text-gray-500 uppercase tracking-widest">
                            <span>Shipping</span>
                            <span className="text-green-600">₹0.00</span>
                        </div>
                        <div className="flex justify-between pt-4 border-t border-gray-100">
                            <span className="text-lg font-black uppercase tracking-widest">Total</span>
                            <span className="text-3xl font-black tracking-tighter">₹{(order.total_amount || 0).toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                <div className="mt-24 pt-12 border-t border-gray-100 text-center">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.3em] mb-2">Thank you for shopping with SmarterBlinkit</p>
                    <p className="text-[8px] text-gray-300 font-medium italic">This is a platform-generated document. No signature required.</p>
                </div>
            </div>
        </DashboardLayout>
    );
}
