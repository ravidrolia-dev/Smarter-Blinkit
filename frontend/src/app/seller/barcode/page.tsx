"use client";
import { useEffect, useRef, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { inventoryApi } from "@/lib/api";
import toast from "react-hot-toast";

export default function BarcodeScanner() {
    const [scanning, setScanning] = useState(false);
    const [scannedCode, setScannedCode] = useState<string | null>(null);
    const [product, setProduct] = useState<any | null>(null);
    const [delta, setDelta] = useState(0);
    const [loading, setLoading] = useState(false);
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
                    width: { ideal: 1920, min: 1280 },
                    height: { ideal: 1080, min: 720 }
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

    const handleConfirmedBarcode = (barcode: string) => {
        stopScanner();
        handleBarcode(barcode);
        toast.success(`Confirmed: ${barcode}!`, { icon: '🎯' });
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
                        const base64 = canvas.toDataURL("image/jpeg", 0.4);

                        try {
                            const res = await inventoryApi.scanBarcode(base64);
                            const { barcode, is_blurry, low_light } = res.data;

                            if (is_blurry) {
                                setScanStatus("Analyzing... Keep steady ✋");
                            } else if (low_light) {
                                setScanStatus("Too dark! Increase light 💡");
                            } else if (barcode) {
                                // Normalize alphanumeric barcodes to remove noise/spaces
                                const normalizedBarcode = barcode.trim().replace(/\s+/g, "").toUpperCase();

                                scanBufferRef.current.push(normalizedBarcode);
                                if (scanBufferRef.current.length > 10) scanBufferRef.current.shift();

                                const counts: any = {};
                                let confirmed = null;
                                for (const b of scanBufferRef.current) {
                                    counts[b] = (counts[b] || 0) + 1;
                                    if (counts[b] >= 3) { confirmed = b; break; }
                                }

                                if (confirmed) {
                                    handleConfirmedBarcode(confirmed);
                                } else {
                                    setScanStatus(`Focusing... (${scanBufferRef.current.filter(b => b === normalizedBarcode).length}/3)`);
                                }
                            } else {
                                setScanStatus("Searching for barcode...");
                            }
                        } catch (err: any) {
                            if (err.message === "Network Error") {
                                setScanStatus("Connection problem! Retrying...");
                                console.error("Axios Network Error - likely payload size or server timeout");
                            } else {
                                console.error("Scan error:", err);
                            }
                        } finally {
                            isProcessingRef.current = false;
                        }
                    }
                }
            }, 500);
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

    useEffect(() => () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const stream = videoRef.current.srcObject as MediaStream;
            stream.getTracks().forEach(track => track.stop());
        }
    }, []);

    const handleBarcode = async (code: string) => {
        setScannedCode(code);
        setLoading(true);
        try {
            const res = await inventoryApi.lookupBarcode(code);
            setProduct(res.data.product);
            toast.success(`Found: ${res.data.product.name}`);
        } catch {
            toast.error(`No product found for barcode: ${code}`);
            setProduct(null);
        } finally { setLoading(false); }
    };

    const handleManualBarcode = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        const code = fd.get("barcode") as string;
        if (code) handleBarcode(code);
    };

    const updateStock = async () => {
        if (!product || delta === 0) return;
        setLoading(true);
        try {
            const res = await inventoryApi.updateStock(product.id, delta);
            toast.success(`Stock updated: ${res.data.old_stock} → ${res.data.new_stock} units`);
            setProduct({ ...product, stock: res.data.new_stock });
            setDelta(0);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Update failed");
        } finally { setLoading(false); }
    };

    return (
        <DashboardLayout role="seller">
            <h1 className="section-title" style={{ fontSize: 24 }}>📷 Barcode Scanner</h1>
            <p style={{ fontSize: 14, color: "var(--gray-500)", marginBottom: 24 }}>Scan a product barcode to instantly update inventory</p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                {/* Camera Scanner */}
                <div className="card-flat">
                    <h2 className="section-title" style={{ marginBottom: 16 }}>Camera Scanner</h2>
                    <div className="relative rounded-2xl overflow-hidden bg-black aspect-video flex items-center justify-center border-2 border-dashed border-gray-200 mb-4">
                        <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
                        <canvas ref={canvasRef} className="hidden" />

                        {!scanning && (
                            <div className="flex flex-col items-center gap-2 z-10 text-white/40">
                                <span className="text-4xl text-gray-700">📷</span>
                                <span className="text-sm font-bold uppercase tracking-wider text-gray-500">Camera inactive</span>
                            </div>
                        )}

                        {scanning && (
                            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10">
                                <div className="text-white bg-black/50 px-4 py-2 rounded-full text-[10px] font-black mb-3 backdrop-blur-md border border-white/20 uppercase tracking-widest">
                                    {scanStatus}
                                </div>
                                <div className="w-56 h-28 border-2 border-yellow-400 rounded-xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]">
                                    <div className="absolute -top-1 -left-1 w-4 h-4 border-t-4 border-l-4 border-yellow-400 rounded-tl-md" />
                                    <div className="absolute -top-1 -right-1 w-4 h-4 border-t-4 border-r-4 border-yellow-400 rounded-tr-md" />
                                    <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-4 border-l-4 border-yellow-400 rounded-bl-md" />
                                    <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-4 border-r-4 border-yellow-400 rounded-br-md" />
                                    <div className="absolute left-0 top-0 w-full h-0.5 bg-yellow-400 shadow-[0_0_10px_rgba(250,204,21,0.8)] animate-scan-line" />
                                </div>
                            </div>
                        )}

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
                    <div style={{ display: "flex", gap: 8 }}>
                        {!scanning
                            ? <button onClick={startScanner} className="btn-primary" style={{ flex: 1 }}>📷 Start Camera</button>
                            : <button onClick={stopScanner} className="btn-secondary" style={{ flex: 1 }}>⏹ Stop</button>
                        }
                    </div>

                    <div className="divider" style={{ marginTop: 16 }}><span>or enter manually</span></div>

                    <form onSubmit={handleManualBarcode} style={{ display: "flex", gap: 8, marginTop: 8 }}>
                        <input name="barcode" className="input" style={{ flex: 1 }} placeholder="Enter barcode (e.g. 8901234567890)" />
                        <button type="submit" className="btn-primary" style={{ padding: "12px 16px" }}>Look Up</button>
                    </form>
                </div>

                {/* Product Info + Stock Update */}
                <div className="card-flat">
                    <h2 className="section-title" style={{ marginBottom: 16 }}>Product Info</h2>
                    {loading ? (
                        <div className="skeleton" style={{ height: 160 }} />
                    ) : product ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                            <div style={{ padding: 16, borderRadius: 12, background: "var(--yellow-subtle)", border: "1px solid var(--yellow-light)" }}>
                                <p style={{ fontSize: 12, color: "var(--gray-400)", marginBottom: 4 }}>Scanned: <code style={{ fontFamily: "monospace", background: "var(--gray-100)", padding: "1px 4px", borderRadius: 4 }}>{scannedCode}</code></p>
                                <p style={{ fontWeight: 900, fontSize: 18, color: "var(--gray-900)" }}>{product.name}</p>
                                <p style={{ fontSize: 14, color: "var(--gray-500)" }}>{product.category} · ₹{product.price}/{product.unit}</p>
                                <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
                                    <span style={{ fontSize: 32, fontWeight: 900 }}>{product.stock}</span>
                                    <span style={{ fontSize: 14, color: "var(--gray-500)" }}>units currently in stock</span>
                                </div>
                            </div>

                            <div>
                                <p style={{ fontSize: 11, fontWeight: 600, color: "var(--gray-500)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>Adjust Stock</p>
                                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <button onClick={() => setDelta((d) => d - 1)}
                                        style={{ width: 40, height: 40, borderRadius: 10, border: "none", background: "var(--gray-100)", fontWeight: 700, fontSize: 18, cursor: "pointer" }}>−</button>
                                    <div style={{ flex: 1, textAlign: "center" }}>
                                        <span style={{ fontSize: 28, fontWeight: 900, color: delta > 0 ? "var(--green)" : delta < 0 ? "var(--red)" : "var(--gray-300)" }}>
                                            {delta > 0 ? `+${delta}` : delta}
                                        </span>
                                        <p style={{ fontSize: 12, color: "var(--gray-400)" }}>units to {delta >= 0 ? "add" : "remove"}</p>
                                    </div>
                                    <button onClick={() => setDelta((d) => d + 1)}
                                        style={{ width: 40, height: 40, borderRadius: 10, border: "none", background: "var(--gray-100)", fontWeight: 700, fontSize: 18, cursor: "pointer" }}>+</button>
                                </div>
                                {delta !== 0 && (
                                    <p style={{ textAlign: "center", fontSize: 14, color: "var(--gray-500)", marginTop: 8 }}>
                                        New stock: <strong>{product.stock + delta}</strong> units
                                    </p>
                                )}
                            </div>

                            <button onClick={updateStock} disabled={delta === 0 || loading} className="btn-primary" style={{ width: "100%" }}>
                                {loading ? "Updating…" : "✅ Update Stock"}
                            </button>
                        </div>
                    ) : (
                        <div style={{ textAlign: "center", padding: "48px 0", color: "var(--gray-300)" }}>
                            <span style={{ fontSize: 48, display: "block", marginBottom: 12 }}>📦</span>
                            <p style={{ color: "var(--gray-400)", fontWeight: 600 }}>Scan a barcode to see product details</p>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
