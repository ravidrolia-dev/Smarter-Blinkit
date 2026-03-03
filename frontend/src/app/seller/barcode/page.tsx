"use client";
import { useEffect, useRef, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { inventoryApi } from "@/lib/api";
import toast from "react-hot-toast";
import Quagga from "@ericblade/quagga2";

export default function BarcodeScanner() {
    const [scanning, setScanning] = useState(false);
    const [scannedCode, setScannedCode] = useState<string | null>(null);
    const [product, setProduct] = useState<any | null>(null);
    const [delta, setDelta] = useState(0);
    const [loading, setLoading] = useState(false);
    const scannerRef = useRef<HTMLDivElement>(null);

    const startScanner = () => {
        if (!scannerRef.current) return;
        Quagga.init({
            inputStream: {
                type: "LiveStream" as any,
                target: scannerRef.current,
                constraints: { facingMode: "environment" },
            } as any,
            decoder: { readers: ["ean_reader", "ean_8_reader", "code_128_reader", "code_39_reader", "upc_reader"] },
            locate: true,
        }, (err: any) => {
            if (err) { toast.error("Camera error: " + err.message); return; }
            Quagga.start();
            setScanning(true);
        });

        Quagga.onDetected((result: any) => {
            const code = result.codeResult.code;
            Quagga.stop();
            setScanning(false);
            handleBarcode(code);
        });
    };

    const stopScanner = () => {
        try { Quagga.stop(); } catch { }
        setScanning(false);
    };

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

    useEffect(() => () => { try { Quagga.stop(); } catch { } }, []);

    return (
        <DashboardLayout role="seller">
            <h1 className="section-title" style={{ fontSize: 24 }}>📷 Barcode Scanner</h1>
            <p style={{ fontSize: 14, color: "var(--gray-500)", marginBottom: 24 }}>Scan a product barcode to instantly update inventory</p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                {/* Camera Scanner */}
                <div className="card-flat">
                    <h2 className="section-title" style={{ marginBottom: 16 }}>Camera Scanner</h2>
                    <div ref={scannerRef}
                        style={{ position: "relative", borderRadius: 16, overflow: "hidden", background: "#111", aspectRatio: "16/9", marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        {!scanning && (
                            <div style={{ color: "rgba(255,255,255,0.4)", display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                                <span style={{ fontSize: 36 }}>📷</span>
                                <span style={{ fontSize: 14 }}>Camera not active</span>
                            </div>
                        )}
                        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
                            <div style={{ width: "75%", height: 80, border: "3px dashed var(--yellow-primary)", borderRadius: 8, opacity: 0.7 }} />
                        </div>
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
