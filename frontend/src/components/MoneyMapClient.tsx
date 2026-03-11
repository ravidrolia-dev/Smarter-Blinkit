"use client";
import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { ShoppingBag, Zap, AlertTriangle, PieChart as PieChartIcon } from "lucide-react";
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from "recharts";

// Fix Leaflet marker icon issue
const DefaultIcon = typeof window !== 'undefined' ? L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41]
}) : null;

const COLORS = ["#FFD000", "#FF8A00", "#FF3D00", "#BC00FF", "#00A3FF", "#00FF85"];

interface MoneyMapClientProps {
    data: any[];
    shops: any[];
    role: "admin" | "seller";
}

export default function MoneyMapClient({ data, shops, role }: MoneyMapClientProps) {
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    if (!isMounted) return null;

    const getHeatColor = (level: string) => {
        if (level === "High") return "#ef4444"; // red
        if (level === "Medium") return "#f97316"; // orange
        return "#eab308"; // yellow
    };

    return (
        <MapContainer
            center={[26.9124, 75.7873]}
            zoom={13}
            style={{ height: "100%", width: "100%", borderRadius: "32px" }}
            className="z-0"
        >
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

            {/* Current Shops */}
            {shops.map((shop, idx) => (
                <Marker
                    key={`shop-${idx}`}
                    position={[shop.lat, shop.lng]}
                    icon={L.divIcon({
                        className: "custom-div-icon",
                        html: `<div style="background-color: #94a3b8; width: ${role === 'admin' ? 12 : 10}px; height: ${role === 'admin' ? 12 : 10}px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>`,
                        iconSize: [12, 12],
                        iconAnchor: [6, 6]
                    })}
                >
                    <Popup>
                        <div className="p-1">
                            <p className="text-[9px] font-black uppercase text-gray-400">Existing Shop</p>
                            <p className="text-sm font-bold text-gray-800">{shop.name}</p>
                        </div>
                    </Popup>
                </Marker>
            ))}

            {data.map((point, idx) => (
                <div key={idx}>
                    <Circle
                        center={[point.lat, point.lng]}
                        radius={500}
                        pathOptions={{
                            fillColor: getHeatColor(point.demand_level),
                            color: "transparent",
                            fillOpacity: 0.3
                        }}
                    />

                    <Marker position={[point.lat, point.lng]} icon={DefaultIcon || undefined}>
                        <Popup className="premium-popup">
                            <div className={`${role === 'admin' ? 'w-64' : 'w-48'} p-2`}>
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-black text-lg text-gray-900">{point.area}</h3>
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${point.demand_level === "High" ? "bg-red-100 text-red-600" :
                                        point.demand_level === "Medium" ? "bg-orange-100 text-orange-600" :
                                            "bg-yellow-100 text-yellow-600"
                                        }`}>
                                        {point.demand_level} Demand
                                    </span>
                                </div>

                                <div className="grid grid-cols-2 gap-3 mb-4">
                                    <div className="bg-gray-50 p-2 rounded-xl">
                                        <p className="text-[10px] font-bold text-gray-400 uppercase">{role === 'seller' ? 'Your Orders' : 'Orders'}</p>
                                        <p className="text-sm font-black">{role === 'seller' ? point.seller_orders : point.total_orders}</p>
                                    </div>
                                    <div className="bg-gray-50 p-2 rounded-xl">
                                        <p className="text-[10px] font-bold text-gray-400 uppercase">{role === 'seller' ? 'Your Revenue' : 'Revenue'}</p>
                                        <p className="text-sm font-black">₹{role === 'seller' ? point.seller_revenue : point.total_revenue}</p>
                                    </div>
                                </div>

                                {role === 'seller' && (
                                    <div className="mb-4">
                                        <div className="flex items-center justify-between mb-1">
                                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Market Share</p>
                                            <p className="text-[10px] font-black text-orange-500">{point.market_share}%</p>
                                        </div>
                                        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-orange-500 rounded-full transition-all duration-1000"
                                                style={{ width: `${point.market_share}%` }}
                                            />
                                        </div>
                                        <p className="text-[9px] text-gray-400 mt-1 font-medium">Total Area Revenue: ₹{point.total_revenue}</p>
                                    </div>
                                )}

                                {point.is_opportunity && (
                                    <div className="bg-red-50 p-3 rounded-2xl border border-red-100 mb-4 flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
                                        <p className="text-[11px] leading-tight text-red-700 font-bold">
                                            <span className="block text-red-800">Opportunity Zone!</span>
                                            High demand with only {point.nearby_shops} nearby shops.
                                        </p>
                                    </div>
                                )}

                                <div className="mb-4">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-1">
                                        <ShoppingBag className="w-3 h-3" /> Top Products
                                    </p>
                                    <div className="flex flex-wrap gap-1">
                                        {point.top_products.map((p: string, i: number) => (
                                            <span key={i} className="text-[9px] bg-white border border-gray-100 px-2 py-1 rounded-lg font-bold text-gray-600 shadow-sm">
                                                {p}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {role === 'admin' && point.category_breakdown && (
                                    <div>
                                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2 flex items-center gap-1">
                                            <PieChartIcon className="w-3 h-3" /> Category Sales
                                        </p>
                                        <div className="h-24 w-full">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <PieChart>
                                                    <Pie
                                                        data={Object.entries(point.category_breakdown).map(([name, value]) => ({ name, value }))}
                                                        innerRadius={15}
                                                        outerRadius={30}
                                                        paddingAngle={5}
                                                        dataKey="value"
                                                    >
                                                        {Object.entries(point.category_breakdown).map((entry, index) => (
                                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                        ))}
                                                    </Pie>
                                                    <Tooltip
                                                        contentStyle={{ fontSize: '10px', borderRadius: '12px' }}
                                                    />
                                                </PieChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Marker>
                </div>
            ))}
        </MapContainer>
    );
}
