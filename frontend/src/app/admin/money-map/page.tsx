"use client";
import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import DashboardLayout from "@/components/DashboardLayout";
import { analyticsApi } from "@/lib/api";
import { toast } from "react-hot-toast";
import {
    TrendingUp,
    Map as MapIcon,
    AlertTriangle,
    Filter,
    ShoppingBag,
    Zap,
    History,
    PieChart as PieChartIcon
} from "lucide-react";

// Dynamically import the client-only map component
const MoneyMapClient = dynamic(() => import("@/components/MoneyMapClient"), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full bg-gray-50 flex items-center justify-center rounded-[32px]">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                <p className="font-black text-gray-400 uppercase tracking-widest text-sm text-center">Loading Map Engine...</p>
            </div>
        </div>
    )
});

export default function AdminMoneyMap() {
    const [data, setData] = useState<any[]>([]);
    const [shops, setShops] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [days, setDays] = useState(30);
    const [category, setCategory] = useState("");
    const [stats, setStats] = useState({ total_revenue: 0, total_orders: 0, opportunities: 0 });

    useEffect(() => {
        fetchData();
    }, [days, category]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await analyticsApi.getMoneyMap(days, category);
            const data_points = res.data.data_points || [];
            const shops_list = res.data.shops || [];

            setData(data_points);
            setShops(shops_list);

            // Calculate summary
            const rev = data_points.reduce((s: any, p: any) => s + p.total_revenue, 0);
            const ord = data_points.reduce((s: any, p: any) => s + p.total_orders, 0);
            const opp = data_points.filter((p: any) => p.is_opportunity).length;
            setStats({ total_revenue: rev, total_orders: ord, opportunities: opp });
        } catch (err) {
            toast.error("Failed to load Money Map data");
        } finally {
            setLoading(false);
        }
    };

    const getHeatColor = (level: string) => {
        if (level === "High") return "#ef4444"; // red
        if (level === "Medium") return "#f97316"; // orange
        return "#eab308"; // yellow
    };

    const COLORS = ["#FFD000", "#FF8A00", "#FF3D00", "#BC00FF", "#00A3FF", "#00FF85"];

    return (
        <DashboardLayout role="admin">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <div>
                        <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
                            <span className="bg-yellow-400 p-2 rounded-2xl shadow-lg shadow-yellow-100">
                                <MapIcon className="w-8 h-8 text-white" />
                            </span>
                            Money Map Analytics
                        </h1>
                        <p className="text-gray-500 font-medium mt-1">Real-time demand visualization & opportunity detection</p>
                    </div>

                    <div className="flex items-center gap-3 bg-white p-2 rounded-2xl shadow-sm border border-gray-100">
                        <div className="flex items-center gap-2 px-3 border-r border-gray-100">
                            <Filter className="w-4 h-4 text-gray-400" />
                            <select
                                value={days}
                                onChange={(e) => setDays(Number(e.target.value))}
                                className="bg-transparent border-none text-sm font-bold focus:ring-0 cursor-pointer"
                            >
                                <option value={1}>Today</option>
                                <option value={7}>Last 7 Days</option>
                                <option value={30}>Last 30 Days</option>
                                <option value={90}>Last 3 Months</option>
                            </select>
                        </div>
                        <div className="flex items-center gap-2 px-3">
                            <ShoppingBag className="w-4 h-4 text-gray-400" />
                            <select
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                className="bg-transparent border-none text-sm font-bold focus:ring-0 cursor-pointer"
                            >
                                <option value="">All Categories</option>
                                <option value="Dairy">Dairy</option>
                                <option value="Vegetables">Vegetables</option>
                                <option value="Snacks">Snacks</option>
                                <option value="Health">Health</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* KPI Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center">
                            <TrendingUp className="w-7 h-7 text-green-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Total Revenue</p>
                            <h3 className="text-2xl font-black text-gray-900">₹{stats.total_revenue.toLocaleString()}</h3>
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center">
                            <History className="w-7 h-7 text-blue-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Total Volume</p>
                            <h3 className="text-2xl font-black text-gray-900">{stats.total_orders.toLocaleString()} orders</h3>
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-3xl border border-red-50 shadow-sm flex items-center gap-5 bg-gradient-to-br from-white to-red-50/30">
                        <div className="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center">
                            <Zap className="w-7 h-7 text-red-600" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-red-400 uppercase tracking-widest mb-1">Hot Opportunities</p>
                            <h3 className="text-2xl font-black text-gray-900">{stats.opportunities} High-Demand Areas</h3>
                        </div>
                    </div>
                </div>

                {/* Map Section */}
                <div className="bg-white p-4 rounded-[40px] border border-gray-100 shadow-xl relative overflow-hidden h-[600px]">
                    {loading && (
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-[1000] flex items-center justify-center">
                            <div className="bg-white p-8 rounded-3xl shadow-2xl flex flex-col items-center gap-4 border border-gray-100">
                                <div className="w-12 h-12 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                                <p className="font-black text-gray-900 uppercase tracking-widest text-sm">Analyzing Data...</p>
                            </div>
                        </div>
                    )}

                    <MoneyMapClient data={data} shops={shops} role="admin" />
                </div>

                {/* Sidebar logic info */}
                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8 text-sm font-medium text-gray-500 bg-white p-8 rounded-[32px] border border-gray-100">
                    <div className="flex gap-4">
                        <div className="w-10 h-10 bg-yellow-50 rounded-xl flex items-center justify-center shrink-0">
                            <AlertTriangle className="w-6 h-6 text-yellow-500" />
                        </div>
                        <div>
                            <h4 className="font-black text-gray-900 mb-1 leading-none uppercase tracking-widest text-[10px]">How Opportunity Detection Works</h4>
                            <p>We flag neighborhoods where order volume exceeds certain thresholds but are served by less than 2 local shops within 1.5km. These are ideal locations for expansion.</p>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center shrink-0">
                            <PieChartIcon className="w-6 h-6 text-blue-500" />
                        </div>
                        <div>
                            <h4 className="font-black text-gray-900 mb-1 leading-none uppercase tracking-widest text-[10px]">Data Precision</h4>
                            <p>Analysis is based on exact buyer coordinates from paid orders, clustered within 110m radius to protect user privacy while maintaining actionable geographical precision.</p>
                        </div>
                    </div>
                </div>
            </div>

            <style jsx global>{`
                .premium-popup .leaflet-popup-content-wrapper {
                    border-radius: 28px;
                    padding: 4px;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
                    border: 1px solid #f1f5f9;
                }
                .premium-popup .leaflet-popup-tip {
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
                }
                .premium-popup .leaflet-popup-content {
                    margin: 8px 12px;
                }
            `}</style>
        </DashboardLayout>
    );
}
