"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi } from "@/lib/api";
import { useLocation } from "@/hooks/useLocation";
import toast from "react-hot-toast";
import Link from "next/link";

export default function ProductDetailsPage() {
    const { id } = useParams();
    const router = useRouter();
    const { location } = useLocation();
    const [product, setProduct] = useState<any>(null);
    const [recs, setRecs] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;
        fetchData();
    }, [id, location]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [pRes, rRes] = await Promise.all([
                productsApi.get(id as string, { lat: location?.lat, lng: location?.lng }),
                productsApi.recommendations(id as string)
            ]);
            setProduct(pRes.data);
            setRecs(rRes.data);
        } catch (err) {
            toast.error("Failed to load product details");
        } finally {
            setLoading(false);
        }
    };

    const addToCart = (p: any) => {
        const cart: any[] = JSON.parse(localStorage.getItem("sb_cart") || "[]");
        const ex = cart.find((i) => i.id === p.id);
        if (ex) ex.qty += 1; else cart.push({ ...p, qty: 1 });
        localStorage.setItem("sb_cart", JSON.stringify(cart));
        toast.success(`${p.name} added to cart! 🛒`);
    };

    if (loading) return (
        <DashboardLayout role="buyer">
            <div className="skeleton" style={{ height: 400, borderRadius: 24, marginBottom: 24 }} />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
                {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 200, borderRadius: 16 }} />)}
            </div>
        </DashboardLayout>
    );

    if (!product) return (
        <DashboardLayout role="buyer">
            <div style={{ textAlign: "center", padding: "100px 0" }}>
                <h2 style={{ fontSize: 24, fontWeight: 800 }}>Product not found</h2>
                <button onClick={() => router.back()} className="btn-secondary" style={{ marginTop: 16 }}>Go Back</button>
            </div>
        </DashboardLayout>
    );

    const isOutOfStock = product.stock <= 0;

    return (
        <DashboardLayout role="buyer">
            {/* Back Button */}
            <button onClick={() => router.back()} className="btn-ghost" style={{ marginBottom: 16, paddingLeft: 0 }}>
                ← Back to results
            </button>

            {/* Product Section */}
            <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 40,
                backgroundColor: "white",
                padding: 32,
                borderRadius: 24,
                boxShadow: "var(--shadow-sm)",
                marginBottom: 48
            }}>
                {/* Image */}
                <div style={{
                    aspectRatio: "1/1",
                    backgroundColor: "var(--yellow-subtle)",
                    borderRadius: 20,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 100,
                    overflow: "hidden"
                }}>
                    {product.image_url ? (
                        <img src={product.image_url} alt={product.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    ) : "🛒"}
                </div>

                {/* Details */}
                <div>
                    <span className="badge badge-yellow" style={{ marginBottom: 12 }}>{product.category}</span>
                    <h1 style={{ fontSize: 32, fontWeight: 900, marginBottom: 8, color: "var(--gray-900)" }}>{product.name}</h1>
                    <p style={{ fontSize: 16, color: "var(--gray-500)", marginBottom: 24, lineHeight: 1.6 }}>{product.description}</p>

                    <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 32 }}>
                        <span style={{ fontSize: 36, fontWeight: 900, color: "var(--gray-900)" }}>₹{product.price}</span>
                        <span style={{ fontSize: 16, color: "var(--gray-400)" }}>/ {product.unit}</span>
                    </div>

                    <div style={{ padding: "20px", borderRadius: 16, backgroundColor: isOutOfStock ? "#FEF2F2" : "var(--gray-50)", border: `1px solid ${isOutOfStock ? "#FECACA" : "var(--gray-100)"}`, marginBottom: 32 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                            <span style={{ fontSize: 14, fontWeight: 600, color: isOutOfStock ? "#DC2626" : "var(--gray-700)" }}>
                                {isOutOfStock ? "❌ Out of Stock" : `✅ In Stock (${product.stock} available)`}
                            </span>
                            {product.distance_km && (
                                <span style={{ fontSize: 12, color: "var(--gray-400)" }}>📍 {product.distance_km} km away</span>
                            )}
                        </div>
                        <p style={{ fontSize: 12, color: "var(--gray-400)" }}>Sold by <span style={{ fontWeight: 700, color: "var(--gray-700)" }}>{product.seller_name}</span></p>
                    </div>

                    <button
                        onClick={() => addToCart(product)}
                        disabled={isOutOfStock}
                        className="btn-primary"
                        style={{ width: "100%", padding: "16px", fontSize: 18, borderRadius: 16 }}
                    >
                        {isOutOfStock ? "Product Unavailable" : "Add to Cart 🛒"}
                    </button>
                </div>
            </div>

            {/* Recommendations Section */}
            {recs && (
                <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
                    {/* Similar Products */}
                    {(recs.similar?.length > 0 || isOutOfStock) && (
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                                <h2 style={{ fontSize: 22, fontWeight: 800 }}>🔄 {isOutOfStock ? "Out of Stock? Try these Similar Products" : "Similar Products"}</h2>
                                {recs.source === "neo4j_graph" && <span className="badge badge-yellow">Graph AI</span>}
                            </div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20 }}>
                                {recs.similar?.map((p: any) => (
                                    <ProductCard key={p.id} product={p} onAdd={addToCart} />
                                ))}
                                {recs.similar?.length === 0 && isOutOfStock && (
                                    <p style={{ color: "var(--gray-400)", gridColumn: "span 4" }}>No similar products found in this category.</p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Frequently Bought Together */}
                    {recs.bought_with?.length > 0 && (
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                                <h2 style={{ fontSize: 22, fontWeight: 800 }}>🛒 Frequently Bought Together</h2>
                                {recs.source === "neo4j_graph" && <span className="badge badge-yellow">Graph DB</span>}
                            </div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20 }}>
                                {recs.bought_with?.map((p: any) => (
                                    <ProductCard key={p.id} product={p} onAdd={addToCart} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </DashboardLayout>
    );
}

function ProductCard({ product, onAdd }: { product: any; onAdd: (p: any) => void }) {
    const id = product.id || product._id;
    return (
        <div className="product-card animate-fade-up">
            <Link href={`/buyer/product/${id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <div style={{ height: 160, display: "flex", alignItems: "center", justifyContent: "center", background: "var(--yellow-subtle)", fontSize: 40 }}>
                    {product.image_url ? <img src={product.image_url} alt={product.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🛒"}
                </div>
            </Link>
            <div style={{ padding: 16 }}>
                <Link href={`/buyer/product/${id}`} style={{ textDecoration: "none", color: "inherit" }}>
                    <p style={{ fontWeight: 700, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{product.name}</p>
                    <p style={{ fontSize: 12, color: "var(--gray-400)", marginBottom: 4 }}>{product.category}</p>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                        <span style={{ fontWeight: 900 }}>₹{product.price}</span>
                        <span style={{ fontSize: 12, color: "var(--gray-400)" }}>{product.unit}</span>
                    </div>
                </Link>
                <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => onAdd(product)} className="btn-primary" style={{ flex: 1, padding: "8px", fontSize: 12 }}>
                        + Add 🛒
                    </button>
                </div>
            </div>
        </div>
    );
}
