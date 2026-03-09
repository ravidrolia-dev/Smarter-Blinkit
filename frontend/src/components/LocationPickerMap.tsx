"use client";
import { useState, useEffect, useCallback, useMemo } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default Leaflet icons in Next.js
const DefaultIcon = L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

const DeliveryIcon = L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface LocationPickerMapProps {
    lat: number;
    lng: number;
    onChange: (lat: number, lng: number) => void;
    height?: string;
}

function MapUpdater({ center }: { center: [number, number] }) {
    const map = useMapEvents({});
    useEffect(() => {
        map.setView(center, map.getZoom());
    }, [center, map]);
    return null;
}

export default function LocationPickerMap({ lat, lng, onChange, height = "250px" }: LocationPickerMapProps) {
    const [markerPos, setMarkerPos] = useState<[number, number]>([lat, lng]);

    useEffect(() => {
        setMarkerPos([lat, lng]);
    }, [lat, lng]);

    const eventHandlers = useMemo(
        () => ({
            dragend(e: any) {
                const marker = e.target;
                if (marker != null) {
                    const { lat, lng } = marker.getLatLng();
                    setMarkerPos([lat, lng]);
                    onChange(lat, lng);
                }
            },
        }),
        [onChange]
    );

    if (typeof window === "undefined") return null;

    return (
        <div style={{ height, width: "100%", borderRadius: "16px", overflow: "hidden", border: "2px solid #FFD000", position: "relative", zIndex: 0 }}>
            <MapContainer
                center={[lat, lng]}
                zoom={16}
                style={{ height: "100%", width: "100%" }}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <Marker
                    draggable={true}
                    eventHandlers={eventHandlers}
                    position={markerPos}
                    icon={DeliveryIcon}
                />
                <MapUpdater center={[lat, lng]} />
            </MapContainer>
            <div style={{
                position: "absolute",
                bottom: 8,
                left: "50%",
                transform: "translateX(-50%)",
                zIndex: 10,
                background: "rgba(255,255,255,0.9)",
                padding: "4px 12px",
                borderRadius: "20px",
                fontSize: "10px",
                fontWeight: "bold",
                boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                pointerEvents: "none",
                whiteSpace: "nowrap"
            }}>
                📍 Drag marker to your exact house
            </div>
        </div>
    );
}
