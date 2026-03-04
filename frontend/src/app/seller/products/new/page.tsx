"use client";
import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { productsApi } from "@/lib/api";
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
                                <input className="input font-mono" value={form.barcode} onChange={(e) => set("barcode", e.target.value)}
                                    placeholder="8901234567890" />
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Image URL (optional)</label>
                                <input className="input" value={form.image_url} onChange={(e) => set("image_url", e.target.value)}
                                    placeholder="https://..." />
                            </div>
                        </div>
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
