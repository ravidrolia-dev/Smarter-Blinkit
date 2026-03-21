"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { demandApi } from "@/lib/api";
import Link from "next/link";
import toast from "react-hot-toast";

export default function SellerDemandPage() {
    const [demands, setDemands] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchDemand = async () => {
        try {
            const res = await demandApi.list();
            setDemands(res.data);
        } catch (err) {
            toast.error("Failed to load demand requests.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDemand();
    }, []);

    const totalRequests = demands.reduce((acc: number, curr: any) => acc + curr.buyer_count, 0);
    const highDemandItems = demands.filter((d: any) => d.buyer_count > 1).length;

    return (
        <DashboardLayout role="seller">
            <div className="bg-mesh min-h-full -m-6 p-6">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
                    <div>
                        <h1 className="text-4xl font-black tracking-tight text-gradient mb-2">Demand Hub</h1>
                        <p className="text-gray-500 font-medium">Capture missing market opportunities in real-time.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={fetchDemand}
                            className="bg-white border border-gray-200 shadow-sm px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-gray-50 transition-colors"
                        >
                            <span className={loading ? "animate-spin" : ""}>🔄</span> Refresh
                        </button>
                    </div>
                </div>

                {/* Stats Summary */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
                    <div className="glass-card p-6 border-l-4 border-yellow-400">
                        <p className="text-xs uppercase font-black text-gray-400 mb-1 tracking-widest">Potential Buyers</p>
                        <h3 className="text-3xl font-black">{totalRequests}</h3>
                        <p className="text-[10px] text-green-600 font-bold mt-1">Waiting for products</p>
                    </div>
                    <div className="glass-card p-6 border-l-4 border-orange-400">
                        <p className="text-xs uppercase font-black text-gray-400 mb-1 tracking-widest">Trending Items</p>
                        <h3 className="text-3xl font-black">{demands.length}</h3>
                        <p className="text-[10px] text-orange-600 font-bold mt-1">Unique products requested</p>
                    </div>
                    <div className="glass-card p-6 border-l-4 border-red-500">
                        <p className="text-xs uppercase font-black text-gray-400 mb-1 tracking-widest">High Priority</p>
                        <h3 className="text-3xl font-black">{highDemandItems}</h3>
                        <p className="text-[10px] text-red-600 font-bold mt-1">Critical supply gaps</p>
                    </div>
                </div>

                {loading ? (
                    <div className="flex flex-col gap-4">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="glass-card h-24 animate-pulse bg-gray-100/50"></div>
                        ))}
                    </div>
                ) : demands.length > 0 ? (
                    <div className="flex flex-col gap-4 stagger">
                        {demands.map((d) => (
                            <div key={d.id} className="glass-card group p-4 md:p-6 flex flex-col md:flex-row items-start md:items-center gap-6 animate-fade-up">
                                {/* Left Section: Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className={`px-2 py-0.5 rounded-full text-[9px] font-black tracking-widest uppercase shrink-0 ${d.buyer_count > 1 ? "bg-red-100 text-red-600 animate-pulse-soft" : "bg-yellow-100 text-yellow-700"
                                            }`}>
                                            {d.buyer_count > 1 ? "🔥 High Priority" : "⭐ New Request"}
                                        </div>
                                        <span className="text-[10px] font-bold text-gray-400 shrink-0">
                                            {Math.floor((Date.now() - new Date(d.last_requested).getTime()) / (1000 * 60 * 60 * 24))}d ago
                                        </span>
                                    </div>
                                    <h2 className="text-xl font-black capitalize group-hover:text-yellow-600 transition-colors truncate">
                                        {d.product_name}
                                    </h2>
                                    <p className="text-xs text-gray-400 font-medium">Requested by {d.buyer_count} local customers</p>
                                </div>

                                {/* Center Section: Visual Data */}
                                <div className="hidden lg:block w-48 shrink-0">
                                    <div className="flex justify-between items-center mb-1.5">
                                        <span className="text-[9px] font-black uppercase text-gray-400">Demand Volume</span>
                                        <span className="text-xs font-black text-gray-900">{Math.min(100, d.buyer_count * 20)}%</span>
                                    </div>
                                    <div className="demand-heat-bar">
                                        <div
                                            className="demand-heat-fill"
                                            style={{ width: `${Math.min(100, d.buyer_count * 20)}%` }}
                                        ></div>
                                    </div>
                                </div>

                                {/* Right Section: Action */}
                                <div className="w-full md:w-auto shrink-0 self-stretch md:self-auto flex items-center">
                                    <Link
                                        href={`/seller/products/new?name=${encodeURIComponent(d.product_name)}`}
                                        className="btn-primary w-full md:w-48 py-3 text-[11px] font-black tracking-widest group-hover:scale-[1.02] transition-transform shadow-lg flex items-center justify-center gap-2"
                                    >
                                        FULFILL DEMAND
                                        <span className="group-hover:translate-x-1 transition-transform">→</span>
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="glass-card text-center py-32 border-dashed border-2 bg-transparent">
                        <div className="w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce">
                            <span className="text-4xl text-yellow-600">📡</span>
                        </div>
                        <h3 className="text-2xl font-black mb-2">Scanning for Demand...</h3>
                        <p className="text-gray-400 max-w-sm mx-auto font-medium">
                            The local market is currently satisfied. New requests from the Recipe Agent will appear here in real-time.
                        </p>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
