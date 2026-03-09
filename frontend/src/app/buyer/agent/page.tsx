"use client";
import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { agentApi } from "@/lib/api";
import { useLocation } from "@/hooks/useLocation";
import toast from "react-hot-toast";

type IngredientResult = {
    ingredient: string;
    quantity: string;
    found: boolean;
    product: {
        id: string;
        name: string;
        price: number;
        seller_name: string;
        distance_km?: number;
    } | null;
};

export default function RecipeAgentPage() {
    const [meal, setMeal] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any | null>(null);
    const [added, setAdded] = useState<string[]>([]);
    const { status, location } = useLocation();

    const examples = [
        "Paneer Butter Masala", "Chicken Biryani", "Healthy Smoothie", "Pasta Carbonara", "Indian Chai"
    ];

    const handleSearch = async () => {
        if (!meal.trim()) return;
        setLoading(true);
        setResult(null);
        try {
            const res = await agentApi.recipe(meal, location?.lat, location?.lng);
            if (res.data.success) {
                setResult(res.data);
            } else {
                toast.error(res.data.message || "Failed to generate recipe.");
            }
        } catch (err: any) {
            toast.error("AI service temporarily unavailable. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const addToCart = (item: IngredientResult) => {
        if (!item.product) return;
        const cart: any[] = JSON.parse(localStorage.getItem("sb_cart") || "[]");
        const ex = cart.find((c: any) => c.id === item.product!.id);
        if (ex) ex.qty += 1;
        else cart.push({ ...item.product, name: item.product.name, qty: 1 });
        localStorage.setItem("sb_cart", JSON.stringify(cart));
        setAdded((p) => [...p, item.product!.id]);
        toast.success(`${item.product.name} added! 🛒`);
    };

    const addAllToCart = () => {
        if (!result) return;
        result.available.forEach((item: IngredientResult) => addToCart(item));
        toast.success(`Success! Added available ingredients to cart. 🎉`, { duration: 4000 });
    };

    return (
        <DashboardLayout role="buyer">
            <h1 className="text-2xl font-black mb-1">🤖 Smart Recipe Agent</h1>
            <p className="text-sm text-gray-500 mb-6">
                Enter any meal. We'll find ingredients in nearby shops and record demand for missing ones.
            </p>

            <div className="card mb-8">
                <div className="flex gap-3">
                    <input
                        type="text" value={meal} onChange={(e) => setMeal(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                        placeholder="What do you want to cook?"
                        className="input flex-1 text-base py-3"
                    />
                    <button onClick={handleSearch} disabled={loading || !meal.trim()} className="btn-primary px-8">
                        {loading ? "👩‍🍳 Cooking up..." : "Find Ingredients"}
                    </button>
                </div>
                <div className="flex flex-wrap gap-2 mt-4">
                    {examples.map((e) => (
                        <button key={e} onClick={() => setMeal(e)}
                            className="px-3 py-1.5 rounded-full text-xs font-semibold bg-yellow-50 text-yellow-700 border border-yellow-200 hover:bg-yellow-100">
                            {e}
                        </button>
                    ))}
                </div>
            </div>

            {loading && (
                <div className="card text-center py-16 animate-pulse">
                    <div className="text-6xl mb-6">🥘</div>
                    <p className="font-bold text-xl text-gray-900">AI is crafting your recipe...</p>
                    <p className="text-sm text-gray-500 mt-2">Checking inventory in nearby shops</p>
                </div>
            )}

            {result && (
                <div className="animate-fade-in">
                    {/* Header */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                        <div>
                            <h2 className="text-3xl font-black text-gray-900">{result.recipe_name}</h2>
                            <p className="text-gray-500">
                                {result.available.length} items found • {result.out_of_stock.length} out of stock
                            </p>
                        </div>
                        {result.available.length > 0 && (
                            <button onClick={addAllToCart} className="btn-primary py-3 px-6 shadow-xl shadow-yellow-200">
                                🛒 Add All Available to Cart
                            </button>
                        )}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Ingredients */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Available Section */}
                            <div>
                                <h3 className="text-sm font-bold uppercase tracking-widest text-green-600 mb-4 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                    Available in Nearby Shops
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {result.available.map((item: IngredientResult) => (
                                        <div key={item.ingredient} className="card-flat bg-white border border-gray-100 flex items-center justify-between p-4 group">
                                            <div>
                                                <p className="font-bold capitalize text-gray-900">{item.ingredient}</p>
                                                <p className="text-xs text-gray-500">{item.quantity}</p>
                                                <p className="text-[10px] text-yellow-600 font-bold mt-1">
                                                    {item.product?.seller_name} • ₹{item.product?.price}
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => addToCart(item)}
                                                className={`px-4 py-2 rounded-xl text-xs font-black transition-all ${added.includes(item.product?.id || "") ? "bg-gray-100 text-gray-400" : "bg-yellow-400 text-black hover:scale-105 active:scale-95"}`}
                                            >
                                                {added.includes(item.product?.id || "") ? "✓" : "+ ADD"}
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Out of Stock Section */}
                            {result.out_of_stock.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-bold uppercase tracking-widest text-red-500 mb-4 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-red-500 pulse"></span>
                                        Out of Stock Everywhere
                                    </h3>
                                    <div className="space-y-3">
                                        {result.out_of_stock.map((item: IngredientResult) => (
                                            <div key={item.ingredient} className="card-flat bg-red-50 border border-red-100 p-4">
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <p className="font-bold capitalize text-gray-900">{item.ingredient}</p>
                                                        <p className="text-xs text-red-500 font-medium">Currently unavailable in nearby shops</p>
                                                    </div>
                                                    <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded font-bold">Demand Recorded</span>
                                                </div>
                                                <p className="text-[10px] text-gray-500 mt-2">
                                                    💡 We have notified local sellers that this product is in high demand.
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Instructions */}
                        <div>
                            <div className="card sticky top-24">
                                <h3 className="text-lg font-black mb-4">👨‍🍳 Cooking Guide</h3>
                                <div className="space-y-4">
                                    {result.instructions.map((step: string, i: number) => (
                                        <div key={i} className="flex gap-4">
                                            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center text-xs font-black">
                                                {i + 1}
                                            </span>
                                            <p className="text-sm text-gray-600 leading-relaxed font-semibold">{step}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {!result && !loading && (
                <div className="text-center py-24">
                    <div className="text-8xl mb-6 opacity-20 filter grayscale">🍲</div>
                    <p className="text-gray-400 font-black text-xl">Your personal chef is ready.</p>
                    <p className="text-gray-300 max-w-xs mx-auto mt-2">Type a meal above, and we'll source every ingredient for you instantly.</p>
                </div>
            )}
        </DashboardLayout>
    );
}
