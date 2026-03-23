"use client";
import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ordersApi, userApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useLocation } from "@/hooks/useLocation";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import dynamic from "next/dynamic";
import FrequentlyBoughtTogether from "@/components/FrequentlyBoughtTogether";

const DeliveryRouteMap = dynamic(() => import("@/components/DeliveryRouteMap"), {
    ssr: false,
    loading: () => <div className="h-48 bg-gray-50 animate-pulse rounded-2xl flex items-center justify-center text-gray-400 text-xs font-medium">Loading Map...</div>
});

const LocationPickerMap = dynamic(() => import("@/components/LocationPickerMap"), {
    ssr: false,
    loading: () => <div className="h-48 bg-gray-100 animate-pulse rounded-2xl" />
});

type CartItem = {
    id: string; name: string; price: number; qty: number;
    seller_id: string; seller_name?: string; unit?: string;
};

// ─── Demo Payment Modal ──────────────────────────────────────────────────────
function PaymentModal({
    total, orderId, onSuccess, onClose
}: {
    total: number; orderId: string;
    onSuccess: (txnId: string) => void; onClose: () => void;
}) {
    const [cardName, setCardName] = useState("");
    const [cardNumber, setCardNumber] = useState("");
    const [expiry, setExpiry] = useState("");
    const [cvv, setCvv] = useState("");
    const [step, setStep] = useState<"form" | "processing" | "success">("form");
    const [txnId, setTxnId] = useState("");

    // Format card number display
    const formatCard = (v: string) =>
        v.replace(/\D/g, "").slice(0, 16).replace(/(.{4})/g, "$1 ").trim();

    const handlePay = async () => {
        if (!cardName || cardNumber.replace(/\s/g, "").length < 16 || !expiry || !cvv) {
            toast.error("Please fill all payment details");
            return;
        }
        setStep("processing");
        // Simulate 2-second processing
        await new Promise((r) => setTimeout(r, 2000));
        try {
            const last4 = cardNumber.replace(/\s/g, "").slice(-4);
            const res = await ordersApi.pay(orderId, cardName, last4);
            setTxnId(res.data.transaction_id);
            setStep("success");
            setTimeout(() => onSuccess(res.data.transaction_id), 2000);
        } catch (err: any) {
            setStep("form");
            toast.error(err.response?.data?.detail || "Payment failed");
        }
    };

    return (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && step === "form" && onClose()}>
            <div className="modal-box">
                {step === "form" && (
                    <>
                        {/* Header */}
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--gray-900)" }}>Demo Payment</h2>
                                <p style={{ fontSize: 13, color: "var(--gray-500)", marginTop: 2 }}>
                                    Secure demo checkout — no real charges
                                </p>
                            </div>
                            <button onClick={onClose}
                                style={{ width: 32, height: 32, borderRadius: 8, background: "var(--gray-100)", border: "none", cursor: "pointer", fontSize: 16 }}>
                                ✕
                            </button>
                        </div>

                        {/* Amount banner */}
                        <div style={{
                            background: "var(--yellow-subtle)", border: "1.5px solid var(--yellow-light)",
                            borderRadius: 12, padding: "12px 16px", marginBottom: 20,
                            display: "flex", alignItems: "center", justifyContent: "space-between"
                        }}>
                            <span style={{ fontSize: 13, color: "var(--gray-500)", fontWeight: 500 }}>Amount to pay</span>
                            <span style={{ fontSize: 22, fontWeight: 900, color: "var(--gray-900)" }}>₹{total.toFixed(2)}</span>
                        </div>

                        {/* Card preview */}
                        <div style={{
                            background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%)",
                            borderRadius: 16, padding: "20px 24px", marginBottom: 20, color: "white",
                            position: "relative", overflow: "hidden"
                        }}>
                            <div style={{
                                position: "absolute", top: -20, right: -20, width: 120, height: 120,
                                borderRadius: "50%", background: "rgba(255,208,0,0.1)"
                            }} />
                            <p style={{ fontSize: 11, opacity: 0.6, marginBottom: 14, letterSpacing: "0.1em", textTransform: "uppercase" }}>Demo Card</p>
                            <p style={{ fontSize: 20, letterSpacing: "0.15em", fontWeight: 600, marginBottom: 16, fontFamily: "monospace" }}>
                                {cardNumber || "•••• •••• •••• ••••"}
                            </p>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                                <div>
                                    <p style={{ fontSize: 10, opacity: 0.5, marginBottom: 2 }}>CARD HOLDER</p>
                                    <p style={{ fontSize: 14, fontWeight: 600 }}>{cardName || "YOUR NAME"}</p>
                                </div>
                                <div style={{ textAlign: "right" }}>
                                    <p style={{ fontSize: 10, opacity: 0.5, marginBottom: 2 }}>EXPIRES</p>
                                    <p style={{ fontSize: 14, fontWeight: 600 }}>{expiry || "MM/YY"}</p>
                                </div>
                            </div>
                        </div>

                        {/* Form fields */}
                        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
                            <div>
                                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--gray-500)", display: "block", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                    Cardholder Name
                                </label>
                                <input className="input" value={cardName}
                                    onChange={(e) => setCardName(e.target.value)}
                                    placeholder="Ravi Drolia" />
                            </div>
                            <div>
                                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--gray-500)", display: "block", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                    Card Number
                                </label>
                                <input className="input" value={cardNumber}
                                    onChange={(e) => setCardNumber(formatCard(e.target.value))}
                                    placeholder="4111 1111 1111 1111" maxLength={19}
                                    style={{ fontFamily: "monospace", letterSpacing: "0.05em" }} />
                            </div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                                <div>
                                    <label style={{ fontSize: 11, fontWeight: 600, color: "var(--gray-500)", display: "block", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                        Expiry
                                    </label>
                                    <input className="input" value={expiry}
                                        onChange={(e) => {
                                            const v = e.target.value.replace(/\D/g, "").slice(0, 4);
                                            setExpiry(v.length > 2 ? `${v.slice(0, 2)}/${v.slice(2)}` : v);
                                        }}
                                        placeholder="MM/YY" maxLength={5} />
                                </div>
                                <div>
                                    <label style={{ fontSize: 11, fontWeight: 600, color: "var(--gray-500)", display: "block", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                        CVV
                                    </label>
                                    <input className="input" value={cvv}
                                        onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").slice(0, 3))}
                                        placeholder="•••" maxLength={3} type="password" />
                                </div>
                            </div>
                        </div>

                        <button onClick={handlePay} className="btn-primary" style={{ width: "100%", padding: "14px", fontSize: 16 }}>
                            Pay ₹{total.toFixed(2)} →
                        </button>
                        <p style={{ textAlign: "center", fontSize: 12, color: "var(--gray-400)", marginTop: 10 }}>
                            🔒 Demo mode — no real charges · Any card number works
                        </p>
                    </>
                )}

                {step === "processing" && (
                    <div style={{ textAlign: "center", padding: "20px 0" }}>
                        <div style={{ fontSize: 56, marginBottom: 16 }} className="animate-spin-slow">⚡</div>
                        <h3 style={{ fontSize: 20, fontWeight: 800, color: "var(--gray-900)", marginBottom: 8 }}>Processing Payment…</h3>
                        <p style={{ fontSize: 14, color: "var(--gray-500)" }}>Please wait while we confirm your order</p>
                        {/* Progress bar */}
                        <div style={{ height: 4, background: "var(--gray-100)", borderRadius: 99, marginTop: 24, overflow: "hidden" }}>
                            <div style={{
                                height: "100%", background: "var(--yellow-primary)", borderRadius: 99,
                                animation: "shimmer 1.5s ease infinite",
                                width: "60%",
                            }} />
                        </div>
                    </div>
                )}

                {step === "success" && (
                    <div style={{ textAlign: "center", padding: "20px 0" }}>
                        <div style={{
                            width: 72, height: 72, borderRadius: "50%", background: "#DCFCE7",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 36, margin: "0 auto 16px"
                        }}>✅</div>
                        <h3 style={{ fontSize: 22, fontWeight: 800, color: "var(--gray-900)", marginBottom: 8 }}>Payment Successful!</h3>
                        <p style={{ fontSize: 14, color: "var(--gray-500)", marginBottom: 16 }}>Your order has been placed.</p>
                        <div style={{
                            background: "var(--gray-50)", borderRadius: 12, padding: "12px 16px",
                            fontFamily: "monospace", fontSize: 13, color: "var(--gray-700)", wordBreak: "break-all"
                        }}>
                            <span style={{ color: "var(--gray-400)", fontSize: 11 }}>Transaction ID</span>
                            <br />{txnId}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── Cart Page ────────────────────────────────────────────────────────────────
export default function CartPage() {
    const [cart, setCart] = useState<CartItem[]>([]);
    const [address, setAddress] = useState("");
    const [loadingOrder, setLoadingOrder] = useState(false);
    const [orderId, setOrderId] = useState<string | null>(null);
    const [showPayModal, setShowPayModal] = useState(false);
    const [total, setTotal] = useState(0);
    const [estimate, setEstimate] = useState<{
        total_distance_km: number;
        estimated_time_minutes: number;
        optimal_route_summary: string;
        stops: any[];
        geometry?: string;
    } | null>(null);
    const [loadingEstimate, setLoadingEstimate] = useState(false);
    const [detecting, setDetecting] = useState(false);
    const [manualCoords, setManualCoords] = useState<{ lat: number, lng: number } | null>(null);
    const [savedAddresses, setSavedAddresses] = useState<any[]>([]);
    const { status, location, requestLocation, refreshLocation } = useLocation();
    const { user } = useAuth();
    const router = useRouter();

    useEffect(() => {
        const load = () => {
            const stored = JSON.parse(localStorage.getItem("sb_cart") || "[]");
            setCart(stored);
        };
        load();
        fetchSavedAddresses();

        window.addEventListener('cartUpdated', load);
        return () => window.removeEventListener('cartUpdated', load);
    }, []);

    const fetchSavedAddresses = async () => {
        try {
            const res = await userApi.getAddresses();
            setSavedAddresses(res.data);

            // Auto-select default address if available and no location detected yet
            const def = res.data.find((a: any) => a.is_default);
            if (def && !manualCoords) {
                setAddress(def.full_address);
                setManualCoords({ lat: def.lat, lng: def.lng });
            }
        } catch (err) {
            console.error("Failed to fetch saved addresses");
        }
    };

    useEffect(() => {
        setTotal(cart.reduce((s, i) => s + i.price * i.qty, 0));
    }, [cart]);

    // Auto-detect address logic (and update on marker drag)
    useEffect(() => {
        const targetLat = manualCoords?.lat || location?.lat;
        const targetLng = manualCoords?.lng || location?.lng;

        if (!targetLat || !targetLng) return;

        setDetecting(true);
        fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${targetLat}&lon=${targetLng}&format=json&addressdetails=1`,
            { headers: { "Accept-Language": "en" } }
        )
            .then((r) => r.json())
            .then((data) => {
                const a = data.address;
                const parts = [
                    a.road || a.suburb || a.neighbourhood,
                    a.city || a.town || a.village || a.county,
                    a.state,
                ].filter(Boolean);
                setAddress(parts.join(", "));
                if (!manualCoords) toast.success("Location detected!");
            })
            .catch(() => {
                setAddress(`${targetLat.toFixed(4)}, ${targetLng.toFixed(4)}`);
            })
            .finally(() => setDetecting(false));
    }, [location, manualCoords]);

    // Delivery estimation logic
    useEffect(() => {
        if (!address.trim() || cart.length === 0) {
            setEstimate(null);
            return;
        }

        const currentLat = manualCoords?.lat || location?.lat;
        const currentLng = manualCoords?.lng || location?.lng;

        const timer = setTimeout(async () => {
            if (address.trim().length < 3) return; // Don't estimate for very short/empty addresses
            
            setLoadingEstimate(true);
            try {
                const res = await ordersApi.estimate({
                    items: cart.map((i) => ({ product_id: i.id, quantity: i.qty })),
                    delivery_address: address,
                    buyer_lat: currentLat,
                    buyer_lng: currentLng
                });
                setEstimate(res.data);
            } catch (err: any) {
                console.error("Estimation failed:", err);
                const msg = err.response?.data?.detail;
                if (msg) {
                    toast.error(msg, { id: 'est-error' });
                }
                setEstimate(null);
            } finally {
                setLoadingEstimate(false);
            }
        }, 1200);

        return () => clearTimeout(timer);
    }, [address, cart, location, manualCoords]);

    const saveCart = (c: CartItem[]) => {
        setCart(c);
        localStorage.setItem("sb_cart", JSON.stringify(c));
    };

    const updateQty = (id: string, delta: number) => {
        saveCart(cart.map((i) => i.id === id ? { ...i, qty: Math.max(0, i.qty + delta) } : i).filter((i) => i.qty > 0));
    };

    const remove = (id: string) => saveCart(cart.filter((i) => i.id !== id));

    // Smart split: group by shop
    const shopGroups = cart.reduce((g: Record<string, CartItem[]>, i) => {
        const k = i.seller_name || i.seller_id || "Unknown Shop";
        (g[k] = g[k] || []).push(i);
        return g;
    }, {});

    const handleProceedToPayment = async () => {
        if (!address.trim()) return toast.error("Please enter a delivery address");
        if (cart.length === 0) return toast.error("Your cart is empty");
        setLoadingOrder(true);
        try {
            const currentLat = manualCoords?.lat || location?.lat;
            const currentLng = manualCoords?.lng || location?.lng;

            const res = await ordersApi.create({
                items: cart.map((i) => ({ product_id: i.id, quantity: i.qty })),
                delivery_address: address,
                buyer_lat: currentLat,
                buyer_lng: currentLng,
                route_stops: estimate?.stops,
                route_distance_km: estimate?.total_distance_km,
                route_time_minutes: estimate?.estimated_time_minutes,
                route_geometry: estimate?.geometry,
            });
            setOrderId(res.data.order_id);
            setShowPayModal(true);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Could not create order");
        } finally {
            setLoadingOrder(false);
        }
    };

    const handlePaymentSuccess = (txnId: string) => {
        localStorage.removeItem("sb_cart");
        toast.success(`🎉 Order placed! TXN: ${txnId.slice(0, 20)}…`, { duration: 5000 });
        setShowPayModal(false);
        router.push("/buyer/orders");
    };

    if (cart.length === 0) return (
        <DashboardLayout role="buyer">
            <div style={{ textAlign: "center", padding: "80px 0" }}>
                <span style={{ fontSize: 72, display: "block", marginBottom: 16 }}>🛒</span>
                <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8 }}>Cart is empty</h2>
                <p style={{ color: "var(--gray-500)", marginBottom: 24 }}>Browse products or let the Recipe Agent fill it!</p>
                <a href="/buyer/search" className="btn-primary">Start Shopping →</a>
            </div>
        </DashboardLayout>
    );

    return (
        <DashboardLayout role="buyer">
            {showPayModal && orderId && (
                <PaymentModal
                    total={total} orderId={orderId}
                    onSuccess={handlePaymentSuccess}
                    onClose={() => setShowPayModal(false)}
                />
            )}

            <h1 style={{ fontSize: 24, fontWeight: 900, marginBottom: 4 }}>🛒 Your Cart</h1>
            <p style={{ fontSize: 14, color: "var(--gray-500)", marginBottom: 24 }}>
                {cart.length} item{cart.length !== 1 ? "s" : ""}
                {Object.keys(shopGroups).length > 1 && (
                    <span className="badge badge-yellow" style={{ marginLeft: 8 }}>
                        ⚡ Smart Split: {Object.keys(shopGroups).length} shops
                    </span>
                )}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 24, alignItems: "start" }}>
                {/* Cart Items — grouped by shop */}
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {Object.entries(shopGroups).map(([shopName, items]) => (
                        <div key={shopName} className="card-flat">
                            <p style={{ fontSize: 12, fontWeight: 700, color: "var(--gray-400)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                🏪 {shopName}
                            </p>
                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                {items.map((item) => (
                                    <div key={item.id} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                        <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--yellow-subtle)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, flexShrink: 0 }}>🛒</div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <p style={{ fontWeight: 700, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.name}</p>
                                            <p style={{ fontSize: 12, color: "var(--gray-400)" }}>₹{item.price} / {item.unit || "piece"}</p>
                                        </div>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <button onClick={() => updateQty(item.id, -1)}
                                                style={{ width: 28, height: 28, borderRadius: "50%", border: "none", background: "var(--gray-100)", fontWeight: 700, cursor: "pointer", fontSize: 14 }}>−</button>
                                            <span style={{ fontWeight: 700, width: 24, textAlign: "center" }}>{item.qty}</span>
                                            <button onClick={() => updateQty(item.id, 1)}
                                                style={{ width: 28, height: 28, borderRadius: "50%", border: "none", background: "var(--gray-100)", fontWeight: 700, cursor: "pointer", fontSize: 14 }}>+</button>
                                        </div>
                                        <span style={{ fontWeight: 900, fontSize: 14, width: 64, textAlign: "right" }}>₹{item.price * item.qty}</span>
                                        <button onClick={() => remove(item.id)}
                                            style={{ color: "var(--gray-300)", background: "none", border: "none", fontSize: 18, cursor: "pointer" }}>✕</button>
                                    </div>
                                ))}
                                <div style={{ borderTop: "1px solid var(--gray-100)", paddingTop: 8, textAlign: "right", fontSize: 14, fontWeight: 700, color: "var(--gray-700)" }}>
                                    Shop subtotal: ₹{items.reduce((s, i) => s + i.price * i.qty, 0).toFixed(2)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Sidebar */}
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {/* Delivery Summary (New Feature) */}
                    <div className="card-flat" style={{ borderLeft: estimate ? "4px solid var(--yellow-primary)" : "1px solid var(--gray-100)" }}>
                        <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                            🚚 Delivery Summary
                        </h3>

                        {loadingEstimate ? (
                            <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--gray-400)", fontSize: 13 }}>
                                <div className="animate-spin" style={{ width: 14, height: 14, border: "2px solid var(--gray-200)", borderTopColor: "var(--yellow-primary)", borderRadius: "50%" }} />
                                Calculating best route...
                            </div>
                        ) : estimate ? (
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                                <div style={{ background: "var(--gray-50)", padding: "10px 12px", borderRadius: 12 }}>
                                    <p style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase" }}>Distance</p>
                                    <p style={{ fontSize: 18, fontWeight: 900 }}>{estimate.total_distance_km}<span style={{ fontSize: 12, fontWeight: 500 }}> km</span></p>
                                </div>
                                <div style={{ background: "var(--gray-50)", padding: "10px 12px", borderRadius: 12 }}>
                                    <p style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase" }}>Est. Time</p>
                                    <p style={{ fontSize: 18, fontWeight: 900 }}>{estimate.estimated_time_minutes}<span style={{ fontSize: 12, fontWeight: 500 }}> min</span></p>
                                </div>
                                <div style={{ gridColumn: "span 2", borderTop: "1px dashed var(--gray-200)", paddingTop: 8 }}>
                                    <p style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase", marginBottom: 4 }}>Optimized Route</p>
                                    <p style={{ fontSize: 12, color: "var(--gray-700)", lineHeight: 1.4 }}>
                                        {estimate.optimal_route_summary.split(" -> ").map((step, idx, arr) => (
                                            <span key={idx}>
                                                {step === "Your Home" ? "🏠 " : "🏪 "}
                                                <span style={{ fontWeight: 600 }}>{step}</span>
                                                {idx < arr.length - 1 && <span style={{ color: "var(--gray-300)", margin: "0 4px" }}>➔</span>}
                                            </span>
                                        ))}
                                    </p>
                                </div>
                                <div style={{ gridColumn: "span 2", marginTop: 12, border: "2px solid #FFD000", padding: "12px", borderRadius: 20, background: "white" }}>
                                    <div style={{ fontSize: "10px", fontWeight: "bold", color: "#6b7280", marginBottom: 12, textAlign: "center", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                        🗺️ Visual Delivery Journey
                                    </div>
                                    <DeliveryRouteMap stops={estimate.stops} geometry={estimate.geometry} height="240px" />
                                </div>
                            </div>
                        ) : (
                            <p style={{ fontSize: 13, color: "var(--gray-400)", fontStyle: "italic" }}>
                                Enter address to see delivery estimate
                            </p>
                        )}
                    </div>

                    <div className="card-flat">
                        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Order Summary</h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 14 }}>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "var(--gray-500)" }}>Subtotal</span><span>₹{total.toFixed(2)}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ color: "var(--gray-500)" }}>Delivery</span>
                                <span style={{ color: "var(--green)", fontWeight: 600 }}>FREE</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 900, fontSize: 18, borderTop: "1px solid var(--gray-100)", paddingTop: 8, marginTop: 4 }}>
                                <span>Total</span><span>₹{total.toFixed(2)}</span>
                            </div>
                        </div>

                        {/* Saved Addresses Quick Selection */}
                        {savedAddresses.length > 0 && (
                            <div style={{ marginTop: 24, marginBottom: 8 }}>
                                <p style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
                                    Select Saved Address
                                </p>
                                <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 8, scrollbarWidth: "none" }} className="custom-scrollbar">
                                    {savedAddresses.map((addr) => (
                                        <button
                                            key={addr.id}
                                            onClick={() => {
                                                setAddress(addr.full_address);
                                                setManualCoords({ lat: addr.lat, lng: addr.lng });
                                                toast.success(`Location set to ${addr.label}`);
                                            }}
                                            style={{
                                                flexShrink: 0,
                                                padding: "10px 14px",
                                                borderRadius: 14,
                                                border: "1.5px solid",
                                                borderColor: address === addr.full_address ? "var(--yellow-primary)" : "var(--gray-100)",
                                                background: address === addr.full_address ? "var(--yellow-subtle)" : "white",
                                                transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                                                display: "flex",
                                                flexDirection: "column",
                                                alignItems: "flex-start",
                                                gap: 2,
                                                cursor: "pointer",
                                                boxShadow: address === addr.full_address ? "0 4px 12px rgba(255,208,0,0.15)" : "none"
                                            }}
                                        >
                                            <span style={{ fontSize: 12, fontWeight: 900, color: address === addr.full_address ? "var(--yellow-dark)" : "var(--gray-900)" }}>
                                                {addr.label === "Home" ? "🏠" : addr.label === "Office" ? "🏢" : "📍"} {addr.label}
                                            </span>
                                            <span style={{ fontSize: 10, color: "var(--gray-400)", maxWidth: 100, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                {addr.full_address}
                                            </span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div style={{ marginTop: 16 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 8 }}>
                                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--gray-500)", textTransform: "uppercase", letterSpacing: "0.05em", margin: 0 }}>
                                    Exact Delivery Location
                                </label>
                                <div style={{ display: "flex", gap: 8 }}>
                                    <button
                                        onClick={refreshLocation}
                                        disabled={detecting}
                                        style={{
                                            fontSize: 11, fontWeight: 700, color: "var(--yellow-dark)",
                                            background: "none", border: "none", cursor: "pointer",
                                            padding: 0, display: "flex", alignItems: "center", gap: 3
                                        }}>
                                        {detecting ? "⌛ Detecting..." : "📍 Use My Location"}
                                    </button>
                                </div>
                            </div>

                            <div style={{ marginBottom: 12 }}>
                                <LocationPickerMap
                                    lat={manualCoords?.lat || location?.lat || 26.8500}
                                    lng={manualCoords?.lng || location?.lng || 75.8200}
                                    onChange={(lat, lng) => setManualCoords({ lat, lng })}
                                    height="200px"
                                />
                            </div>

                            <textarea value={address} onChange={(e) => setAddress(e.target.value)}
                                rows={2} className="input" style={{ resize: "none", fontSize: "13px" }}
                                placeholder="Edit address if needed..." />
                        </div>

                        {/* People often add (Last minute upsell) */}
                        <div style={{ marginTop: 20 }}>
                            <FrequentlyBoughtTogether
                                cartIds={cart.map(i => i.id)}
                                title="People often add"
                                subtitle="Items commonly bought together"
                                maxItems={2}
                                isSidebar={true}
                            />
                        </div>
                        <button onClick={handleProceedToPayment} disabled={loadingOrder}
                            className="btn-primary" style={{ width: "100%", marginTop: 16, padding: "14px", fontSize: 16 }}>
                            {loadingOrder ? "Creating order…" : `Pay ₹${total.toFixed(2)} →`}
                        </button>
                        <p style={{ textAlign: "center", fontSize: 12, color: "var(--gray-400)", marginTop: 8 }}>
                            🔒 Demo payment — no real charges
                        </p>
                    </div>

                    {Object.keys(shopGroups).length > 1 && (
                        <div style={{ background: "var(--yellow-subtle)", border: "1px solid var(--yellow-light)", borderRadius: 16, padding: 16 }}>
                            <p style={{ fontSize: 14, fontWeight: 700, color: "#92400E", marginBottom: 4 }}>⚡ Smart Cart Split Active</p>
                            <p style={{ fontSize: 13, color: "#78350F" }}>
                                Your order will be split across {Object.keys(shopGroups).length} shops for fastest delivery.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Smart Product Pairing (Cart-based) */}
            <FrequentlyBoughtTogether
                cartIds={cart.map(i => i.id)}
                title="Customers also buy"
                subtitle="Items frequently purchased with your cart contents"
            />
        </DashboardLayout>
    );
}
