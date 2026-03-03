"use client";
import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { agentApi } from "@/lib/api";
import toast from "react-hot-toast";

type IngredientResult = {
    ingredient: string;
    needed_quantity: string;
    found: boolean;
    product: {
        id: string; name: string; price: number; stock: number;
        seller_id: string; distance_km?: number;
    } | null;
};

export default function RecipeAgentPage() {
    const [meal, setMeal] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any | null>(null);
    const [added, setAdded] = useState<string[]>([]);
    const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);

    const examples = [
        "Make Pizza for 4 people", "Pasta dinner for 2",
        "Chicken curry for family", "Pancakes for breakfast", "Biryani for 6",
    ];

    useState(() => {
        navigator.geolocation?.getCurrentPosition(
            (p) => setLocation({ lat: p.coords.latitude, lng: p.coords.longitude }),
            () => { }
        );
    });

    const handleSearch = async () => {
        if (!meal.trim()) return;
        setLoading(true);
        setResult(null);
        try {
            const res = await agentApi.recipe(meal, location?.lat, location?.lng);
            setResult(res.data);
        } catch {
            toast.error("Agent failed. Check your Gemini API key.");
        } finally {
            setLoading(false);
        }
    };

    const addToCart = (item: IngredientResult) => {
        if (!item.product) return;
        const cart: any[] = JSON.parse(localStorage.getItem("sb_cart") || "[]");
        const ex = cart.find((c) => c.id === item.product!.id);
        if (ex) ex.qty += 1;
        else cart.push({ ...item.product, name: item.product.name, qty: 1 });
        localStorage.setItem("sb_cart", JSON.stringify(cart));
        setAdded((p) => [...p, item.product!.id]);
        toast.success(`${item.product.name} added! 🛒`);
    };

    const addAllToCart = () => {
        if (!result) return;
        result.found.forEach((item: IngredientResult) => addToCart(item));
        toast.success(`All ${result.found.length} items added to cart! 🎉`, { duration: 4000 });
    };

    return (
        <DashboardLayout role="buyer">
            <h1 className="text-2xl font-black mb-1">🤖 Recipe Agent</h1>
            <p className="text-sm text-gray-500 mb-6">
                Describe a meal — the AI will find all ingredients from nearby shops and fill your cart.
            </p>

            {/* Input */}
            <div className="card mb-6">
                <div className="flex gap-3">
                    <input
                        type="text" value={meal} onChange={(e) => setMeal(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                        placeholder="e.g. Make Pizza for 4 people"
                        className="input flex-1 text-base"
                    />
                    <button onClick={handleSearch} disabled={loading || !meal.trim()} className="btn-primary px-6">
                        {loading ? "🧠 Thinking…" : "🚀 Find Ingredients"}
                    </button>
                </div>
                <div className="flex flex-wrap gap-2 mt-4">
                    {examples.map((e) => (
                        <button key={e} onClick={() => setMeal(e)}
                            className="px-3 py-1.5 rounded-full text-xs font-semibold bg-yellow-100 text-gray-800 hover:bg-yellow-200 transition-all">
                            {e}
                        </button>
                    ))}
                </div>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="card text-center py-12">
                    <div className="text-5xl mb-4 animate-spin-slow inline-block">🧠</div>
                    <p className="font-bold text-gray-900">AI is analyzing your recipe…</p>
                    <p className="text-sm text-gray-500 mt-1">Parsing ingredients and finding nearby stock</p>
                </div>
            )}

            {/* Results */}
            {result && !loading && (
                <>
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h2 className="section-title">Ingredients for "{result.meal}"</h2>
                            <p className="section-sub">
                                <span className="text-green-600 font-semibold">{result.found?.length} found</span>
                                {result.not_found?.length > 0 && (
                                    <span className="text-red-500 font-semibold ml-2">{result.not_found?.length} not available</span>
                                )}
                            </p>
                        </div>
                        {result.found?.length > 0 && (
                            <button onClick={addAllToCart} className="btn-primary">
                                🛒 Add All to Cart ({result.found.length})
                            </button>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        {result.found?.map((item: IngredientResult) => (
                            <div key={item.ingredient} className="card-flat flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-yellow-100 flex items-center justify-center text-2xl flex-shrink-0">
                                    🥦
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="font-bold text-sm capitalize">{item.ingredient}</p>
                                    <p className="text-xs text-gray-500">Need: {item.needed_quantity}</p>
                                    {item.product && (
                                        <p className="text-xs text-gray-400 truncate">
                                            {item.product.name} • ₹{item.product.price}
                                            {item.product.distance_km && ` • ${item.product.distance_km}km`}
                                        </p>
                                    )}
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <span className="badge badge-green">✓ Found</span>
                                    <button
                                        onClick={() => addToCart(item)}
                                        disabled={added.includes(item.product?.id || "")}
                                        className="text-xs font-bold px-3 py-1.5 rounded-lg disabled:opacity-50 transition-all"
                                        style={{ background: added.includes(item.product?.id || "") ? "#e5e7eb" : "var(--yellow-primary)" }}>
                                        {added.includes(item.product?.id || "") ? "✓ Added" : "+ Add"}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {result.not_found?.length > 0 && (
                        <div className="card-flat border border-red-100">
                            <p className="text-sm font-bold text-red-600 mb-3">❌ Not Available Nearby</p>
                            <div className="flex flex-wrap gap-2">
                                {result.not_found.map((item: IngredientResult) => (
                                    <span key={item.ingredient} className="badge badge-red capitalize">
                                        {item.ingredient} ({item.needed_quantity})
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Empty State */}
            {!result && !loading && (
                <div className="text-center py-16 text-gray-300">
                    <span className="text-7xl block mb-4">🤖</span>
                    <p className="font-bold text-gray-400 text-lg">AI Recipe Agent is ready!</p>
                    <p className="text-sm text-gray-300 mt-1">Enter a meal above to get started</p>
                </div>
            )}
        </DashboardLayout>
    );
}
