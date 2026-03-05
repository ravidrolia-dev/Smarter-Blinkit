"use client";
import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { searchApi } from "@/lib/api";
import { useLocation } from "@/hooks/useLocation";
import toast from "react-hot-toast";
import Link from "next/link";

// ─── Inner component that uses useSearchParams ─────────────────────────────
function SearchInner() {
    const params = useSearchParams();
    const [query, setQuery] = useState(params.get("q") || "");
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const { location } = useLocation();

    useEffect(() => {
        const q = params.get("q");
        if (q) doSearch(q);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const doSearch = async (q: string) => {
        if (!q.trim()) return;
        setLoading(true);
        try {
            const res = await searchApi.search(q, location?.lat, location?.lng);
            setResults(res.data.results);
            if (res.data.results.length === 0) toast("No products found.", { icon: "🔍" });
        } catch { toast.error("Search failed"); }
        finally { setLoading(false); }
    };

    const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); doSearch(query); };

    const intents = [
        "I have a cold", "Make pasta for 2", "Healthy breakfast",
        "Party snacks", "Morning chai", "Baby food",
    ];

    const addToCart = (product: any) => {
        const cart: any[] = JSON.parse(localStorage.getItem("sb_cart") || "[]");
        const ex = cart.find((i) => i.id === product.id);
        if (ex) ex.qty += 1; else cart.push({ ...product, qty: 1 });
        localStorage.setItem("sb_cart", JSON.stringify(cart));
        toast.success(`${product.name} added! 🛒`);
    };

    return (
        <>
            <h1 style={{ fontSize: 24, fontWeight: 900, marginBottom: 4 }}>🔍 Smart Search</h1>
            <p style={{ fontSize: 14, color: "var(--gray-500)", marginBottom: 12 }}>
                Search by intent — type what you need, not just a product name.
            </p>


            <form onSubmit={handleSubmit} style={{ position: "relative", marginBottom: 16 }}>
                <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
                    placeholder='Try "I have a cold" or "make pizza tonight"'
                    className="input-search" style={{ paddingRight: 112, fontSize: 16, paddingTop: 16, paddingBottom: 16, boxShadow: "var(--shadow-md)" }} />
                <button type="submit" className="btn-primary"
                    style={{ position: "absolute", right: 8, top: 8, padding: "10px 20px", borderRadius: 999, fontSize: 14 }}>
                    {loading ? "…" : "Search"}
                </button>
            </form>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 24 }}>
                {intents.map((i) => (
                    <button key={i} onClick={() => { setQuery(i); doSearch(i); }}
                        style={{ padding: "6px 14px", borderRadius: 999, fontSize: 12, fontWeight: 600, background: "var(--yellow-light)", color: "#78350F", border: "none", cursor: "pointer" }}>
                        {i}
                    </button>
                ))}
            </div>

            {loading ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
                    {[...Array(8)].map((_, i) => <div key={i} className="skeleton" style={{ height: 210, borderRadius: 16 }} />)}
                </div>
            ) : results.length > 0 ? (
                <>
                    <p style={{ fontSize: 13, color: "var(--gray-500)", marginBottom: 12 }}>
                        {results.length} results for "<strong>{query}</strong>"
                    </p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }} className="stagger">
                        {results.map((p) => (
                            <div key={p.id} className="product-card animate-fade-up">
                                <Link href={`/buyer/product/${p.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                                    <div style={{ height: 144, display: "flex", alignItems: "center", justifyContent: "center", background: "var(--yellow-subtle)", fontSize: 40 }}>
                                        {p.image_url ? <img src={p.image_url} alt={p.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🛒"}
                                    </div>
                                    <div style={{ padding: 16 }}>
                                        <p style={{ fontWeight: 700, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name}</p>
                                        <p style={{ fontSize: 12, color: "var(--gray-400)", marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.description?.slice(0, 40)}</p>
                                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                            <span style={{ fontWeight: 900 }}>₹{p.price}</span>
                                            <span style={{ fontSize: 12, color: "var(--gray-400)" }}>{p.unit}</span>
                                        </div>
                                        {p.distance_km && <p style={{ fontSize: 12, color: "var(--gray-400)", marginTop: 4 }}>📍 {p.distance_km} km</p>}
                                        {p._score && (
                                            <div style={{ marginTop: 8, height: 4, background: "var(--yellow-light)", borderRadius: 99, overflow: "hidden" }}>
                                                <div style={{ height: "100%", background: "var(--yellow-primary)", width: `${Math.round(p._score * 100)}%`, borderRadius: 99 }} />
                                            </div>
                                        )}
                                    </div>
                                </Link>
                                <div style={{ padding: "0 16px 16px" }}>
                                    <button onClick={() => addToCart(p)} className="btn-primary"
                                        style={{ width: "100%", padding: "8px", fontSize: 12 }}>
                                        + Add to Cart
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            ) : query && !loading ? (
                <div style={{ textAlign: "center", padding: "64px 0", color: "var(--gray-400)" }}>
                    <span style={{ fontSize: 48, display: "block", marginBottom: 12 }}>🔍</span>
                    <p style={{ fontWeight: 600 }}>No results for "{query}"</p>
                    <p style={{ fontSize: 14, marginTop: 4 }}>Try different keywords or browse categories</p>
                </div>
            ) : null}
        </>
    );
}

// ─── Page wrapper with Suspense for useSearchParams ────────────────────────
export default function SearchPage() {
    return (
        <DashboardLayout role="buyer">
            <Suspense fallback={<div className="skeleton" style={{ height: 200, borderRadius: 16 }} />}>
                <SearchInner />
            </Suspense>
        </DashboardLayout>
    );
}
