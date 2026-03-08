"use client";
import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import polyline from "@mapbox/polyline";

// Fix for default Leaflet icons in Next.js
const DefaultIcon = L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

const ShopIcon = L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

const BuyerIcon = L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface Stop {
    type: "shop" | "buyer";
    name: string;
    lat: number;
    lng: number;
    items?: string[];
}

interface DeliveryRouteMapProps {
    stops: Stop[];
    geometry?: string;
    height?: string;
}

// Component to auto-fit map bounds
function SetBounds({ stops, roadPoints }: { stops: Stop[], roadPoints: [number, number][] }) {
    const map = useMap();
    useEffect(() => {
        if (stops.length > 0) {
            const allPoints = [...stops.map(s => [s.lat, s.lng] as [number, number]), ...roadPoints];
            if (allPoints.length > 0) {
                const bounds = L.latLngBounds(allPoints);
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [stops, roadPoints, map]);
    return null;
}

export default function DeliveryRouteMap({ stops, geometry, height = "400px" }: DeliveryRouteMapProps) {
    if (typeof window === "undefined") return null;

    if (!stops || stops.length === 0) {
        return (
            <div style={{ height, width: "100%", borderRadius: "16px", background: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center", border: "1px dashed #d1d5db", color: "#9ca3af", fontSize: "12px" }}>
                No route data available
            </div>
        );
    }

    // Decode geometry if available
    const roadPoints: [number, number][] = geometry ? polyline.decode(geometry) : [];

    return (
        <div style={{ height, width: "100%", borderRadius: "16px", overflow: "hidden", border: "2px solid #FFD000", position: "relative", background: "#f8fafc", zIndex: 0 }}>
            <div style={{ position: "absolute", top: 8, left: 8, zIndex: 10, background: "white", padding: "4px 8px", borderRadius: "8px", boxShadow: "0 2px 4px rgba(0,0,0,0.1)", fontSize: "10px", fontWeight: "bold" }}>
                📍 Delivery Route
            </div>
            <MapContainer
                center={[stops[0]?.lat || 26.9124, stops[0]?.lng || 75.7873]}
                zoom={13}
                scrollWheelZoom={false}
                style={{ height: "100%", width: "100%" }}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />

                {/* Visualizing the Route: Solid for road, Dashed for fallback */}
                {roadPoints.length > 0 ? (
                    <Polyline
                        positions={roadPoints}
                        pathOptions={{ color: "#FFD000", weight: 5, opacity: 0.9 }}
                    />
                ) : (
                    <Polyline
                        positions={stops.map(s => [s.lat, s.lng] as [number, number])}
                        pathOptions={{ color: "#FFD000", weight: 4, opacity: 0.7, dashArray: "10, 10" }}
                    />
                )}

                {stops.map((stop, idx) => (
                    <Marker
                        key={idx}
                        position={[stop.lat, stop.lng]}
                        icon={stop.type === "shop" ? ShopIcon : BuyerIcon}
                    >
                        <Popup>
                            <div style={{ padding: "4px" }}>
                                <strong style={{ color: "var(--yellow-primary)" }}>
                                    {stop.type === "shop" ? "🏪 Shop" : "🏡 Delivery"}
                                </strong>
                                <div style={{ fontWeight: 700, margin: "2px 0" }}>{stop.name}</div>
                                {stop.items && (
                                    <div style={{ fontSize: "11px", color: "#666" }}>
                                        Items: {stop.items.join(", ")}
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Marker>
                ))}
                <SetBounds stops={stops} roadPoints={roadPoints} />
            </MapContainer>
        </div>
    );
}
