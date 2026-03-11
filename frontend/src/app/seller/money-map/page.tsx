"use client";
import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import DashboardLayout from "@/components/DashboardLayout";
import { analyticsApi } from "@/lib/api";
import { toast } from "react-hot-toast";
import {
    Map as MapIcon,
    Zap,
    ShoppingBag,
    TrendingUp,
    Navigation,
    CircleDollarSign
} from "lucide-react";

// Dynamically import the client-only map component
const MoneyMapClient = dynamic(() => import("@/components/MoneyMapClient"), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full bg-gray-50 flex items-center justify-center rounded-[32px]">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="font-black text-gray-400 uppercase tracking-widest text-sm text-center">Loading Map Engine...</p>
            </div>
        </div>
    )
});

export default function SellerMoneyMap() {
    const [data, setData] = useState<any[]>([]);
    const [shops, setShops] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ hot_spots: 0, nearby_revenue: 0, your_revenue: 0 });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const userStr = localStorage.getItem("sb_user");
            const user = userStr ? JSON.parse(userStr) : null;
            const sellerId = user?.id || user?._id;

            const res = await analyticsApi.getMoneyMap(30, undefined, sellerId);
            const data_points = res.data.data_points || [];
            const shops_list = res.data.shops || [];

            setData(data_points);
            setShops(shops_list);

            const hot = data_points.filter((p: any) => p.demand_level === "High").length;
            const rev = data_points.reduce((s: any, p: any) => s + p.total_revenue, 0);
            const yrev = data_points.reduce((s: any, p: any) => s + (p.seller_revenue || 0), 0);
            setStats({ hot_spots: hot, nearby_revenue: rev, your_revenue: yrev });
        } catch (err) {
            toast.error("Failed to load Money Map data");
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout role="seller">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
                        <span className="bg-orange-500 p-2 rounded-2xl shadow-lg shadow-orange-100">
                            <CircleDollarSign className="w-8 h-8 text-white" />
                        </span>
                        Money Map
                    </h1>
                    <p className="text-gray-500 font-medium mt-1">Discover where customers are spending and what's trending nearby</p>
                </div>

                {/* Seller Insights Bar */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-3xl border border-orange-50 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-orange-50 rounded-2xl flex items-center justify-center">
                            <Zap className="w-7 h-7 text-orange-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">High Demand Zones</p>
                            <h3 className="text-2xl font-black text-gray-900">{stats.hot_spots} Areas nearby</h3>
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-3xl border border-blue-50 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center">
                            <TrendingUp className="w-7 h-7 text-blue-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Addressable Market</p>
                            <h3 className="text-2xl font-black text-gray-900">₹{stats.nearby_revenue.toLocaleString()}</h3>
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-3xl border border-green-50 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center">
                            <ShoppingBag className="w-7 h-7 text-green-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Your Sales</p>
                            <h3 className="text-2xl font-black text-gray-900">₹{stats.your_revenue.toLocaleString()}</h3>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                    {/* Map Area */}
                    <div className="lg:col-span-3 bg-white p-4 rounded-[40px] border border-gray-100 shadow-xl h-[600px] relative">
                        {loading && (
                            <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-[1000] flex items-center justify-center rounded-[40px]">
                                <div className="bg-white p-8 rounded-3xl shadow-2xl flex flex-col items-center gap-4 border border-gray-100">
                                    <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                                    <p className="font-black text-gray-900 uppercase tracking-widest text-sm text-center">Analyzing Market...</p>
                                </div>
                            </div>
                        )}

                        <MoneyMapClient data={data} shops={shops} role="seller" />
                    </div>

                    {/* Quick Insights Sidebar */}
                    <div className="space-y-6">
                        <div className="bg-white p-6 rounded-[32px] border border-gray-100 shadow-sm">
                            <h4 className="font-black text-gray-900 text-xs uppercase tracking-widest mb-4 flex items-center gap-2">
                                <Navigation className="w-4 h-4 text-orange-500" /> Hot Neighborhoods
                            </h4>
                            <div className="space-y-4">
                                {data.filter(p => p.demand_level === "High").slice(0, 4).map((area, i) => (
                                    <div key={i} className="group cursor-pointer">
                                        <p className="text-sm font-black text-gray-800 group-hover:text-orange-500 transition-colors">{area.area}</p>
                                        <div className="flex items-center justify-between text-[10px] text-gray-400 font-bold mt-0.5">
                                            <span>{area.total_orders} Orders</span>
                                            <span className="text-green-500">₹{area.total_revenue}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-6 rounded-[32px] text-white shadow-xl shadow-gray-200">
                            <h4 className="font-black text-orange-400 text-[10px] uppercase tracking-[0.2em] mb-3">Pro Tip</h4>
                            <p className="text-xs leading-relaxed text-gray-300 font-medium">
                                "High Demand" areas with low shop counts are perfect for running local discounts.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
