"use client";
import { useEffect, useRef, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi, inventoryApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const CATEGORIES = ["Fruits", "Vegetables", "Dairy", "Bakery", "Meat", "Snacks", "Beverages", "Spices", "Personal Care", "Household", "Other"];
const UNITS = ["piece", "kg", "g", "litre", "ml", "pack", "dozen", "box"];

export default function AddProductPage() {
    const { user } = useAuth();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [locationLoading, setLocationLoading] = useState(false);
    const [form, setForm] = useState({
        name: "", description: "", price: "", category: "Fruits", barcode: "",
        stock: "", unit: "piece", image_url: "", tags: "",
        lat: "", lng: "",
    });
    const [scanning, setScanning] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [scanStatus, setScanStatus] = useState<string>("Initializing...");
    const scanBufferRef = useRef<string[]>([]);
    const isProcessingRef = useRef<boolean>(false);

    const startScanner = async () => {
        setScanning(true);
        setScanStatus("Accessing camera...");
        scanBufferRef.current = [];
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: "environment",
                    width: { ideal: 1280, min: 640 },
                    height: { ideal: 720, min: 480 }
                }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setScanStatus("Scanning...");
            }
        } catch (err) {
            toast.error("Could not access camera");
            setScanning(false);
        }
    };

    const stopScanner = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const stream = videoRef.current.srcObject as MediaStream;
            stream.getTracks().forEach(track => track.stop());
            videoRef.current.srcObject = null;
        }
        setScanning(false);
    };

    const handleConfirmedBarcode = async (barcode: string) => {
        set("barcode", barcode);
        toast.success(`Confirmed: ${barcode}! Searching details...`, { icon: '🔍' });
        stopScanner();

        // Professional Auto-Fill with OpenFoodFacts integration
        try {
            const res = await inventoryApi.lookupBarcode(barcode);
            if (res.data.found) {
                const p = res.data.product;
                setForm(prev => ({
                    ...prev,
                    name: p.name || prev.name,
                    brand: p.brand || "",
                    category: p.category || prev.category,
                    image_url: p.image || prev.image_url,
                    barcode: barcode
                }));
                toast.success("Product details auto-filled! ✨");
            }
        } catch (err) {
            // Not found in DB or OFF - manual entry remains
            console.log("No external details found for this barcode.");
        }
    };

    useEffect(() => {
        let interval: any;
        if (scanning) {
            interval = setInterval(async () => {
                if (videoRef.current && canvasRef.current && scanning && !isProcessingRef.current) {
                    const video = videoRef.current;
                    const canvas = canvasRef.current;
                    const context = canvas.getContext("2d");

                    if (context && video.videoWidth > 0) {
                        isProcessingRef.current = true;
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        context.drawImage(video, 0, 0, canvas.width, canvas.height);
                        const base64 = canvas.toDataURL("image/jpeg", 0.4); // Lower quality for better throughput

                        try {
                            const res = await inventoryApi.scanBarcode(base64);
                            const { barcode, is_blurry, low_light } = res.data;

                            if (is_blurry) {
                                setScanStatus("Analyzing... Hold steady ✋");
                            } else if (low_light) {
                                setScanStatus("Too dark! Increase light 💡");
                            } else if (barcode) {
                                // Normalize alphanumeric barcodes to remove noise/spaces
                                const normalizedBarcode = barcode.trim().replace(/\s+/g, "").toUpperCase();

                                scanBufferRef.current.push(normalizedBarcode);
                                if (scanBufferRef.current.length > 10) scanBufferRef.current.shift();

                                // Multi-frame confirmation: Check if barcode appears 3 times in last 10 frames
                                const counts: any = {};
                                let confirmed = null;
                                for (const b of scanBufferRef.current) {
                                    counts[b] = (counts[b] || 0) + 1;
                                    if (counts[b] >= 3) {
                                        confirmed = b;
                                        break;
                                    }
                                }

                                if (confirmed) {
                                    handleConfirmedBarcode(confirmed);
                                } else {
                                    setScanStatus(`Stabilizing... (${scanBufferRef.current.filter(b => b === normalizedBarcode).length}/3)`);
                                }
                            } else {
                                setScanStatus("Searching for barcode...");
                            }
                        } catch (err: any) {
                            if (err.message === "Network Error") {
                                setScanStatus("Connection Lost! Retrying...");
                                console.error("Axios Network Error - likely payload size or server timeout");
                            } else {
                                console.error("Scan error:", err);
                            }
                        } finally {
                            isProcessingRef.current = false;
                        }
                    }
                }
            }, 500); // More conservative sampling frequency (500ms)
        }
        return () => {
            clearInterval(interval);
            if (!scanning) {
                if (videoRef.current && videoRef.current.srcObject) {
                    const stream = videoRef.current.srcObject as MediaStream;
                    stream.getTracks().forEach(track => track.stop());
                }
            }
        };
    }, [scanning]);

    const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }));

    const getLocation = () => {
        if (!navigator.geolocation) {
            toast.error("Geolocation is not supported by your browser.");
            return;
        }
        setLocationLoading(true);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                set("lat", String(pos.coords.latitude));
                set("lng", String(pos.coords.longitude));
                setLocationLoading(false);
                toast.success("Shop location captured! 📍");
            },
            (err) => {
                setLocationLoading(false);
                if (err.code === err.PERMISSION_DENIED) {
                    toast.error("Location access denied. Enable it in browser settings.");
                } else if (err.code === err.POSITION_UNAVAILABLE) {
                    toast.error("Location unavailable. Enter coordinates manually.");
                } else {
                    toast.error("Location timed out. Please try again.");
                }
            },
            { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 }
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await productsApi.create({
                name: form.name,
                description: form.description,
                price: parseFloat(form.price),
                category: form.category,
                barcode: form.barcode || undefined,
                stock: parseInt(form.stock) || 0,
                unit: form.unit,
                image_url: form.image_url || undefined,
                tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
                lat: form.lat ? parseFloat(form.lat) : undefined,
                lng: form.lng ? parseFloat(form.lng) : undefined,
            });
            toast.success("Product listed! 🎉");
            router.push("/seller/inventory");
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Failed to add product");
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout role="seller">
            <div className="max-w-2xl">
                <h1 className="text-2xl font-black mb-1">➕ Add New Product</h1>
                <p className="text-sm text-gray-500 mb-6">Fill in the details. The AI will auto-generate a search embedding!</p>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Basic Details */}
                    <div className="card-flat space-y-4">
                        <h2 className="font-bold text-gray-900">Product Details</h2>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Product Name *</label>
                                <input className="input" value={form.name} onChange={(e) => set("name", e.target.value)} required placeholder="e.g. Organic Honey" />
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Category *</label>
                                <select className="input" value={form.category} onChange={(e) => set("category", e.target.value)}>
                                    {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                                </select>
                            </div>
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Description *</label>
                            <textarea rows={3} className="input resize-none" value={form.description}
                                onChange={(e) => set("description", e.target.value)} required
                                placeholder="Describe your product (used for AI search matching)" />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Tags (comma-separated)</label>
                            <input className="input" value={form.tags} onChange={(e) => set("tags", e.target.value)}
                                placeholder="e.g. organic, cold remedy, healthy, natural" />
                        </div>
                    </div>

                    {/* Pricing & Stock */}
                    <div className="card-flat space-y-4">
                        <h2 className="font-bold text-gray-900">Pricing & Stock</h2>
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Price (₹) *</label>
                                <input type="number" min="0" step="0.01" className="input" value={form.price}
                                    onChange={(e) => set("price", e.target.value)} required placeholder="99.00" />
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Stock *</label>
                                <input type="number" min="0" className="input" value={form.stock}
                                    onChange={(e) => set("stock", e.target.value)} required placeholder="50" />
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Unit</label>
                                <select className="input" value={form.unit} onChange={(e) => set("unit", e.target.value)}>
                                    {UNITS.map((u) => <option key={u}>{u}</option>)}
                                </select>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Barcode (optional)</label>
                                <div className="flex gap-2">
                                    <input className="input font-mono flex-1" value={form.barcode} onChange={(e) => set("barcode", e.target.value)}
                                        placeholder="8901234567890" />
                                    <button
                                        type="button"
                                        onClick={scanning ? stopScanner : startScanner}
                                        className={`px-4 rounded-xl border flex items-center gap-2 transition-all ${scanning ? 'bg-red-50 border-red-200 text-red-600' : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'}`}
                                    >
                                        {scanning ? '⏹ Stop' : '📷 Scan'}
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Image URL (optional)</label>
                                <input className="input" value={form.image_url} onChange={(e) => set("image_url", e.target.value)}
                                    placeholder="https://..." />
                            </div>
                        </div>

                        {scanning && (
                            <div className="mt-4">
                                <label className="text-xs font-semibold text-gray-500 mb-2 block uppercase tracking-wide">AI-Powered Scanner</label>
                                <div className="relative rounded-2xl overflow-hidden bg-black aspect-video flex items-center justify-center border-2 border-dashed border-gray-200">
                                    <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
                                    <canvas ref={canvasRef} className="hidden" />

                                    {/* Scan Box Overlay */}
                                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10">
                                        <div className="text-white bg-black/50 px-4 py-2 rounded-full text-xs font-bold mb-4 backdrop-blur-md border border-white/20">
                                            {scanStatus}
                                        </div>
                                        <div className="w-64 h-32 border-2 border-yellow-400 rounded-2xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]">
                                            <div className="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-yellow-400 rounded-tl-lg" />
                                            <div className="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-yellow-400 rounded-tr-lg" />
                                            <div className="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-yellow-400 rounded-bl-lg" />
                                            <div className="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-yellow-400 rounded-br-lg" />

                                            {/* Scanning Line Animation */}
                                            <div className="absolute left-0 top-0 w-full h-0.5 bg-yellow-400 shadow-[0_0_15px_rgba(250,204,21,0.8)] animate-scan-line" />
                                        </div>
                                        <p className="text-white/70 text-[10px] uppercase font-black tracking-widest mt-6 drop-shadow-md">
                                            Align barcode within box
                                        </p>
                                    </div>

                                    <style dangerouslySetInnerHTML={{
                                        __html: `
                                        @keyframes scan-line {
                                            0% { top: 0%; opacity: 0; }
                                            10% { opacity: 1; }
                                            90% { opacity: 1; }
                                            100% { top: 100%; opacity: 0; }
                                        }
                                        .animate-scan-line {
                                            animation: scan-line 2s linear infinite;
                                        }
                                    ` }} />
                                </div>
                                <div className="mt-3 flex gap-4 text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                                    <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" /> Auto Resolution</div>
                                    <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" /> OpenCV Preprocessing</div>
                                    <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-pulse" /> Neural Recovery</div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="card-flat">
                        <h2 className="font-bold text-gray-900 mb-1">Shop Location</h2>
                        <p className="text-xs text-gray-500 mb-3">Your shop's GPS coordinates — used to show your products to nearby buyers.</p>
                        <div className="flex gap-3 items-end">
                            <div className="flex-1">
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Latitude</label>
                                <input className="input font-mono" value={form.lat} onChange={(e) => set("lat", e.target.value)} placeholder="19.0760" />
                            </div>
                            <div className="flex-1">
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Longitude</label>
                                <input className="input font-mono" value={form.lng} onChange={(e) => set("lng", e.target.value)} placeholder="72.8777" />
                            </div>
                            <button
                                type="button"
                                onClick={getLocation}
                                disabled={locationLoading}
                                className="btn-secondary py-3 px-4 mb-0.5 disabled:opacity-60">
                                {locationLoading ? "⏳ Locating…" : "📍 Use My Location"}
                            </button>
                        </div>
                        {form.lat && form.lng && (
                            <p className="text-xs text-green-600 mt-2 font-medium">✓ Location set: {parseFloat(form.lat).toFixed(4)}, {parseFloat(form.lng).toFixed(4)}</p>
                        )}
                    </div>

                    <div className="flex gap-3">
                        <button type="button" onClick={() => router.back()} className="btn-ghost flex-1 border border-gray-200 rounded-xl justify-center">
                            Cancel
                        </button>
                        <button type="submit" disabled={loading} className="btn-primary flex-1">
                            {loading ? "Adding…" : "🚀 List Product"}
                        </button>
                    </div>
                </form>
            </div>
        </DashboardLayout>
    );
}
