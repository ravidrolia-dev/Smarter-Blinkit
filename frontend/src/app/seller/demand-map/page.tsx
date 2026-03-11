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
    Target
} from "lucide-react";

// Dynamically import Leaflet components
const MapContainer = dynamic(() => import("react-leaflet").then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then(mod => mod.Popup), { ssr: false });
const Circle = dynamic(() => import("react-leaflet").then(mod => mod.Circle), { ssr: false });

import "leaflet/dist/leaflet.css";
import L from "leaflet";

const DefaultIcon = typeof window !== 'undefined' ? L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41]
}) : null;

export default function SellerDemandMap() {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ hot_spots: 0, nearby_revenue: 0 });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const res = await analyticsApi.getMoneyMap(30);
            setData(res.data.data_points);

            const hot = res.data.data_points.filter((p: any) => p.demand_level === "High").length;
            const rev = res.data.data_points.reduce((s: any, p: any) => s + p.total_revenue, 0);
            setStats({ hot_spots: hot, nearby_revenue: rev });
        } catch (err) {
            toast.error("Failed to load demand data");
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
                            <Target className="w-8 h-8 text-white" />
                        </span>
                        Local Demand Map
                    </h1>
                    <p className="text-gray-500 font-medium mt-1">Discover where customers are buying and what's trending nearby</p>
                </div>

                {/* Seller Insights Bar */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-3xl border border-orange-50 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-orange-50 rounded-2xl flex items-center justify-center">
                            <Zap className="w-7 h-7 text-orange-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">High Demand Zones</p>
                            <h3 className="text-2xl font-black text-gray-900">{stats.hot_spots} Areas nearby</h3>
                        </div>
                    </div>
                    <div className="bg-white p-6 rounded-3xl border border-green-50 shadow-sm flex items-center gap-5">
                        <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center">
                            <TrendingUp className="w-7 h-7 text-green-500" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Addressable Market</p>
                            <h3 className="text-2xl font-black text-gray-900">₹{stats.nearby_revenue.toLocaleString()} monthly</h3>
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
                                    <p className="font-black text-gray-900 uppercase tracking-widest text-sm text-center">Identifying Demand...</p>
                                </div>
                            </div>
                        )}

                        <MapContainer
                            center={[26.9124, 75.7873]}
                            zoom={13}
                            style={{ height: "100%", width: "100%", borderRadius: "32px" }}
                            className="z-0"
                        >
                            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                            {data.map((point, idx) => (
                                <div key={idx}>
                                    <Circle
                                        center={[point.lat, point.lng]}
                                        radius={500}
                                        pathOptions={{
                                            fillColor: point.demand_level === "High" ? "#f97316" : "#fbbf24",
                                            color: "transparent",
                                            fillOpacity: 0.3
                                        }}
                                    />
                                    <Marker position={[point.lat, point.lng]} icon={DefaultIcon || undefined}>
                                        <Popup>
                                            <div className="p-2 w-48">
                                                <h3 className="font-black text-gray-900 text-sm mb-1">{point.area}</h3>
                                                <p className="text-[10px] text-gray-500 mb-3">
                                                    Demand: <span className={`font-bold ${point.demand_level === "High" ? "text-orange-500" : "text-yellow-600"}`}>{point.demand_level}</span>
                                                </p>

                                                <div className="border-t border-gray-100 pt-2">
                                                    <p className="text-[9px] font-black text-gray-400 uppercase tracking-tighter mb-2">Trendings Here:</p>
                                                    <ul className="space-y-1">
                                                        {point.top_products.map((p: string, i: number) => (
                                                            <li key={i} className="text-[10px] font-bold text-gray-600 flex items-center gap-2">
                                                                <div className="w-1 h-1 bg-orange-400 rounded-full" /> {p}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            </div>
                                        </Popup>
                                    </Marker>
                                </div>
                            ))}
                        </MapContainer>
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
                            <button className="mt-4 w-full bg-white text-gray-900 font-black py-2 rounded-xl text-xs hover:bg-orange-400 hover:text-white transition-all">
                                Analyze Trends
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
