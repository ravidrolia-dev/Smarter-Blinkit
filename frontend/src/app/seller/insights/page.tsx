

"use client";
import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { analyticsApi, productsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import toast from "react-hot-toast";
import { Brain, RefreshCw, ShoppingBag, ArrowRight, TrendingUp } from "lucide-react";

export default function MarketInsightsPage() {
    const { user } = useAuth();
    const [insights, setInsights] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [training, setTraining] = useState(false);

    useEffect(() => {
        fetchInsights();
    }, []);

    const fetchInsights = async () => {
        setLoading(true);
        try {
            // We'll add a new endpoint or use an existing one to list general pairings
            // For now, let's assume we can fetch some representative pairings
            const res = await analyticsApi.topProducts(); // Placeholder for general insights
            // In a real scenario, we'd have a specific endpoint for "Top Global Pairings"
            // For this implementation, we'll try to fetch pairings for their top products
            const topProducts = res.data.slice(0, 5);
            const pairingPromises = topProducts.map((p: any) =>
                analyticsApi.productPairings(p.id || p._id, 3).catch(() => ({ data: [] }))
            );
            const pairingsRes = await Promise.all(pairingPromises);

            const detailedInsights = topProducts.map((p: any, idx: number) => ({
                product: p,
                pairings: pairingsRes[idx].data
            })).filter((i: any) => i.pairings.length > 0);

            setInsights(detailedInsights);
        } catch (err) {
            toast.error("Failed to load market insights");
        } finally {
            setLoading(false);
        }
    };

    const triggerTraining = async () => {
        setTraining(true);
        try {
            // Call the training endpoint
            await analyticsApi.trainPairings();
            toast.success("AI Model retraining started! Rules will update in a few seconds. 🧠");
            setTimeout(fetchInsights, 5000);
        } catch (err) {
            toast.error("Training failed to start");
        } finally {
            setTraining(false);
        }
    };

    return (
        <DashboardLayout role="seller">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                <div>
                    <h1 style={{ fontSize: 32, fontVariationSettings: "'wght' 900", color: "var(--gray-900)" }}>
                        💡 Market Insights
                    </h1>
                    <p style={{ color: "var(--gray-500)", marginTop: 4 }}>
                        AI-powered product recommendations based on global customer behavior
                    </p>
                </div>
                <button
                    onClick={triggerTraining}
                    disabled={training}
                    className="btn-primary"
                    style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 24px" }}
                >
                    {training ? <RefreshCw className="animate-spin" size={18} /> : <Brain size={18} />}
                    {training ? "Training AI..." : "Retrain Model"}
                </button>
            </div>

            {loading ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="skeleton" style={{ height: 240, borderRadius: 24 }} />
                    ))}
                </div>
            ) : insights.length === 0 ? (
                <div style={{ textAlign: "center", padding: "80px 0", backgroundColor: "white", borderRadius: 32, border: "2px dashed var(--gray-100)" }}>
                    <div style={{ fontSize: 48, marginBottom: 16 }}>🧠</div>
                    <h2 style={{ fontSize: 24, fontWeight: 800 }}>No pairing insights yet</h2>
                    <p style={{ color: "var(--gray-500)", marginBottom: 24 }}>
                        Once more orders are placed, our AI will discover products that are frequently bought together.
                    </p>
                    <button onClick={triggerTraining} className="btn-secondary">Run Initial Analysis</button>
                </div>
            ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
                    {insights.map((item, idx) => (
                        <div key={idx} style={{
                            backgroundColor: "white",
                            padding: 24,
                            borderRadius: 32,
                            boxShadow: "var(--shadow-sm)",
                            border: "1px solid var(--gray-50)"
                        }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
                                <div style={{
                                    width: 64, height: 64,
                                    backgroundColor: "var(--yellow-subtle)",
                                    borderRadius: 16,
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                    fontSize: 32
                                }}>
                                    {item.product.image_url ? <img src={item.product.image_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 16 }} /> : <ShoppingBag />}
                                </div>
                                <div>
                                    <h3 style={{ fontSize: 18, fontWeight: 900 }}>{item.product.name}</h3>
                                    <span className="badge badge-yellow">{item.product.category}</span>
                                </div>
                                <div style={{ marginLeft: "auto", textAlign: "right" }}>
                                    <div style={{ fontSize: 12, color: "var(--gray-400)", fontWeight: 700, textTransform: "uppercase" }}>Discovery Rate</div>
                                    <div style={{ fontSize: 20, fontWeight: 900, color: "var(--green)" }}><TrendingUp size={16} style={{ display: "inline", marginRight: 4 }} /> High</div>
                                </div>
                            </div>

                            <p style={{ fontSize: 14, color: "var(--gray-500)", marginBottom: 16, fontWeight: 600 }}>
                                Customers frequently buy these with {item.product.name}:
                            </p>

                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                {item.pairings.map((p: any, pIdx: number) => (
                                    <div key={pIdx} style={{
                                        display: "flex", alignItems: "center", gap: 12,
                                        padding: 12, backgroundColor: "var(--gray-50)", borderRadius: 16
                                    }}>
                                        <div style={{ width: 40, height: 40, backgroundColor: "white", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>
                                            {p.image_url ? <img src={p.image_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 8 }} /> : "🛒"}
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <p style={{ fontWeight: 700, fontSize: 14 }}>{p.name}</p>
                                            <p style={{ fontSize: 11, color: "var(--gray-400)" }}>{p.category}</p>
                                        </div>
                                        <div style={{ textAlign: "right" }}>
                                            <div style={{ fontSize: 10, color: "var(--gray-400)", fontWeight: 700 }}>CONFIDENCE</div>
                                            <div style={{ fontSize: 14, fontWeight: 900, color: "var(--yellow-dark)" }}>{(p.confidence * 100).toFixed(0)}%</div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div style={{ marginTop: 20, paddingTop: 20, borderTop: "1px dashed var(--gray-100)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: 12, color: "var(--gray-400)" }}>
                                    💡 Tip: Bundle these for a discount to increase AOV
                                </span>
                                <ArrowRight size={18} color="var(--gray-300)" />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </DashboardLayout>
    );
}
