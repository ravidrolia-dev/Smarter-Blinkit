"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi, ordersApi } from "@/lib/api";
import { useLocation } from "@/hooks/useLocation";
import toast from "react-hot-toast";
import Link from "next/link";
import { Star } from "lucide-react";

export default function ProductDetailsPage() {
    const { id } = useParams();
    const router = useRouter();
    const { location } = useLocation();
    const [product, setProduct] = useState<any>(null);
    const [recs, setRecs] = useState<any>(null);
    const [reviews, setReviews] = useState<any[]>([]);
    const [hasPurchased, setHasPurchased] = useState(false);
    const [eligibleOrderId, setEligibleOrderId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [submittingReview, setSubmittingReview] = useState(false);
    const [newReview, setNewReview] = useState({ rating: 5, text: "" });

    useEffect(() => {
        if (!id) return;
        fetchData();
    }, [id, location]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [pRes, rRes, revRes] = await Promise.all([
                productsApi.get(id as string, { lat: location?.lat, lng: location?.lng }),
                productsApi.recommendations(id as string),
                productsApi.listReviews(id as string)
            ]);
            setProduct(pRes.data);
            setRecs(rRes.data);
            setReviews(revRes.data);

            // Check if user has purchased this product
            const ordersRes = await ordersApi.myOrders();
            const pastOrder = ordersRes.data.find((o: any) =>
                (o.status === "delivered" || o.status === "paid") &&
                o.items.some((item: any) => item.product_id === id)
            );
            if (pastOrder) {
                setHasPurchased(true);
                setEligibleOrderId(pastOrder.id);
            }
        } catch (err) {
            toast.error("Failed to load product details");
        } finally {
            setLoading(false);
        }
    };

    const submitReview = async () => {
        if (!newReview.text.trim()) return toast.error("Please write a review");
        setSubmittingReview(true);
        try {
            await productsApi.addReview(id as string, {
                order_id: eligibleOrderId,
                rating: newReview.rating,
                review_text: newReview.text,
                product_id: id as string
            });
            toast.success("Review submitted! Thank you! ⭐");
            setNewReview({ rating: 5, text: "" });
            // Refresh data to show new review and updated rating
            fetchData();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Failed to submit review");
        } finally {
            setSubmittingReview(false);
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
                    <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                        <span className="badge badge-yellow">{product.category}</span>
                        {product.is_bestseller && <span className="badge" style={{ backgroundColor: "#F97316", color: "white" }}>🔥 Bestseller</span>}
                    </div>
                    <h1 style={{ fontSize: 32, fontWeight: 900, marginBottom: 8, color: "var(--gray-900)" }}>{product.name}</h1>

                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                        <div style={{ display: "flex", color: "#F59E0B" }}>
                            {[...Array(5)].map((_, i) => (
                                <Star key={i} size={18} fill={i < Math.round(product.rating) ? "#F59E0B" : "none"} />
                            ))}
                        </div>
                        <span style={{ fontWeight: 700, fontSize: 16 }}>{product.rating || 0}</span>
                        <span style={{ color: "var(--gray-400)", fontSize: 14 }}>({product.review_count || 0} reviews)</span>
                    </div>

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

            {/* Reviews Section */}
            <div style={{ marginBottom: 48 }}>
                <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 24 }}>Customer Reviews ({reviews.length})</h2>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 40 }}>
                    {/* Review List */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {reviews.length === 0 ? (
                            <p style={{ color: "var(--gray-400)" }}>No reviews yet. Be the first to review!</p>
                        ) : (
                            reviews.map((rev) => (
                                <div key={rev.id} style={{ padding: 20, borderRadius: 16, backgroundColor: "white", border: "1px solid var(--gray-100)" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                                        <div style={{ display: "flex", color: "#F59E0B", gap: 2 }}>
                                            {[...Array(5)].map((_, i) => (
                                                <Star key={i} size={14} fill={i < rev.rating ? "#F59E0B" : "none"} />
                                            ))}
                                        </div>
                                        <span style={{ fontSize: 12, color: "var(--gray-400)" }}>{new Date(rev.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <p style={{ fontWeight: 600, marginBottom: 4 }}>{rev.user_name}</p>
                                    <p style={{ fontSize: 14, color: "var(--gray-600)" }}>{rev.review_text}</p>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Add Review Form */}
                    {hasPurchased && (
                        <div style={{ padding: 24, borderRadius: 20, backgroundColor: "var(--yellow-subtle)", height: "fit-content" }}>
                            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Rate this product</h3>
                            <div style={{ marginBottom: 16 }}>
                                <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Your Rating</p>
                                <div style={{ display: "flex", gap: 8 }}>
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <button
                                            key={star}
                                            onClick={() => setNewReview({ ...newReview, rating: star })}
                                            style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
                                        >
                                            <Star size={24} fill={star <= newReview.rating ? "#F59E0B" : "none"} color="#F59E0B" />
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div style={{ marginBottom: 20 }}>
                                <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Your Review</p>
                                <textarea
                                    value={newReview.text}
                                    onChange={(e) => setNewReview({ ...newReview, text: e.target.value })}
                                    placeholder="Tell us what you liked about this product..."
                                    style={{
                                        width: "100%",
                                        height: 100,
                                        padding: 12,
                                        borderRadius: 12,
                                        border: "1px solid var(--gray-200)",
                                        fontSize: 14,
                                        resize: "none"
                                    }}
                                />
                            </div>
                            <button
                                onClick={submitReview}
                                disabled={submittingReview}
                                className="btn-primary"
                                style={{ width: "100%", padding: 12 }}
                            >
                                {submittingReview ? "Submitting..." : "Submit Review"}
                            </button>
                        </div>
                    )}
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
                <div style={{ height: 160, display: "flex", alignItems: "center", justifyContent: "center", background: "var(--yellow-subtle)", fontSize: 40, position: "relative" }}>
                    {product.is_bestseller && (
                        <span style={{ position: "absolute", top: 8, left: 8, backgroundColor: "#F97316", color: "white", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700 }}>
                            🔥 BESTSELLER
                        </span>
                    )}
                    {product.image_url ? <img src={product.image_url} alt={product.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🛒"}
                </div>
            </Link>
            <div style={{ padding: 16 }}>
                <Link href={`/buyer/product/${id}`} style={{ textDecoration: "none", color: "inherit" }}>
                    <p style={{ fontWeight: 700, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{product.name}</p>
                    <p style={{ fontSize: 12, color: "var(--gray-400)", marginBottom: 4 }}>{product.category}</p>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <span style={{ fontWeight: 900 }}>₹{product.price}</span>
                            {product.rating > 0 && (
                                <span style={{ fontSize: 11, color: "#F59E0B", display: "flex", alignItems: "center", gap: 2, background: "#FFFBEB", padding: "1px 6px", borderRadius: 4 }}>
                                    ★ {product.rating}
                                </span>
                            )}
                        </div>
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
