"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { inventoryApi, productsApi } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";

const CATEGORIES = ["Groceries", "Snacks", "Beverages", "Dairies", "Vegetables", "Fruits", "Meat", "Essentials", "Bakery", "Personal Care"];

export default function InventoryPage() {
    const [products, setProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("");

    // Edit state
    const [editingProduct, setEditingProduct] = useState<any | null>(null);
    const [editForm, setEditForm] = useState<any>({});
    const [saving, setSaving] = useState(false);

    // Print state
    const [printingProduct, setPrintingProduct] = useState<any | null>(null);
    const [barcodeImg, setBarcodeImg] = useState<string | null>(null);
    const [labelCount, setLabelCount] = useState(8);
    const [loadingImg, setLoadingImg] = useState(false);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        setLoading(true);
        try {
            const r = await inventoryApi.myProducts();
            setProducts(r.data);
        } catch (err) {
            toast.error("Failed to load products");
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (p: any) => {
        setEditingProduct(p);
        setEditForm({ ...p });
    };

    const handleSaveEdit = async () => {
        if (!editingProduct) return;
        setSaving(true);
        try {
            await productsApi.update(editingProduct.id, {
                name: editForm.name,
                price: parseFloat(editForm.price),
                stock: parseInt(editForm.stock),
                category: editForm.category,
                description: editForm.description,
                unit: editForm.unit
            });
            toast.success("Product updated! ✨");
            setEditingProduct(null);
            fetchProducts();
        } catch (err) {
            toast.error("Update failed");
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this product?")) return;
        try {
            await productsApi.delete(id);
            toast.success("Product deleted");
            fetchProducts();
        } catch (err) {
            toast.error("Delete failed");
        }
    };

    const handlePrint = async (p: any) => {
        setPrintingProduct(p);
        setBarcodeImg(null); // Reset
        if (!p.barcode) return;

        setLoadingImg(true);
        try {
            const res = await inventoryApi.getBarcodeImage(p.barcode);
            setBarcodeImg(res.data.image);
        } catch (err) {
            toast.error("Failed to load barcode preview");
        } finally {
            setLoadingImg(false);
        }
    };

    const handleActualPrint = () => {
        window.print();
        setPrintingProduct(null);
    };

    const filtered = products.filter((p) =>
        p.name.toLowerCase().includes(filter.toLowerCase()) ||
        p.category?.toLowerCase().includes(filter.toLowerCase())
    );

    const stockColor = (s: number) => s <= 0 ? "text-red-500" : s <= 5 ? "text-orange-500" : "text-green-600";

    return (
        <DashboardLayout role="seller">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-black">📦 Inventory</h1>
                    <p className="text-sm text-gray-500">{products.length} products listed in your shop</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/seller/barcode" className="btn-secondary text-sm">📷 Scanner Update</Link>
                    <Link href="/seller/products/new" className="px-5 py-2.5 rounded-xl bg-yellow-400 text-black font-black text-sm hover:bg-yellow-500 transition-all flex items-center gap-2">
                        <span>➕</span> Add New Product
                    </Link>
                </div>
            </div>

            <div className="flex gap-4 mb-6">
                <div className="relative flex-1 max-w-md">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
                    <input type="search" value={filter} onChange={(e) => setFilter(e.target.value)}
                        placeholder="Search by name or category…" className="input pl-10" />
                </div>
            </div>

            {loading ? (
                <div className="flex flex-col gap-4">
                    <div className="skeleton h-12 rounded-xl" />
                    <div className="skeleton h-12 rounded-xl" />
                    <div className="skeleton h-12 rounded-xl" />
                </div>
            ) : (
                <div className="table-wrapper text-right">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b border-gray-100 uppercase text-[10px] font-black tracking-widest text-gray-400">
                                <th className="pb-4 pl-4">Product Info</th>
                                <th className="pb-4">Category</th>
                                <th className="pb-4 text-center">Stock</th>
                                <th className="pb-4 text-right">Selling Price</th>
                                <th className="pb-4 pr-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {filtered.map((p) => (
                                <tr key={p.id} className="group hover:bg-gray-50/50 transition-colors">
                                    <td className="py-4 pl-4">
                                        <div className="flex items-center gap-3">
                                            {p.image_url ? (
                                                <img src={p.image_url} alt="" className="w-10 h-10 rounded-lg object-cover bg-gray-100 flex-shrink-0" />
                                            ) : (
                                                <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-xl flex-shrink-0">📦</div>
                                            )}
                                            <div>
                                                <div className="font-bold text-gray-900 leading-tight">{p.name}</div>
                                                <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider mt-0.5">{p.unit} · {p.barcode || "NO BARCODE"}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td><span className="badge badge-yellow text-[10px]">{p.category}</span></td>
                                    <td className="text-center">
                                        <div className={`font-black text-lg ${stockColor(p.stock)}`}>{p.stock}</div>
                                        <div className="text-[10px] text-gray-400 font-bold uppercase">{p.total_sold || 0} sold</div>
                                    </td>
                                    <td className="text-right font-black text-gray-900 pr-10">₹{p.price}</td>
                                    <td className="pr-4 py-4">
                                        <div className="flex items-center justify-end gap-2">
                                            <button onClick={() => handlePrint(p)} className="p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-all" title="Print Barcode">🖨️</button>
                                            <button onClick={() => handleEdit(p)} className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all" title="Edit Product">✏️</button>
                                            <button onClick={() => handleDelete(p.id)} className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-all" title="Delete Product">🗑️</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Edit Modal */}
            {editingProduct && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h2 className="text-xl font-black">✏️ Edit Product</h2>
                            <button onClick={() => setEditingProduct(null)} className="text-gray-400">✕</button>
                        </div>
                        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="text-[10px] font-black uppercase text-gray-400 mb-1 block">Full Name</label>
                                    <input className="input" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black uppercase text-gray-400 mb-1 block">Price (₹)</label>
                                    <input type="number" className="input" value={editForm.price} onChange={(e) => setEditForm({ ...editForm, price: e.target.value })} />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black uppercase text-gray-400 mb-1 block">Inventory Stock</label>
                                    <input type="number" className="input" value={editForm.stock} onChange={(e) => setEditForm({ ...editForm, stock: e.target.value })} />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black uppercase text-gray-400 mb-1 block">Category</label>
                                    <select className="input" value={editForm.category} onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}>
                                        {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                                    </select>
                                </div>
                                <div className="col-span-2">
                                    <label className="text-[10px] font-black uppercase text-gray-400 mb-1 block">Description</label>
                                    <textarea className="input h-24 py-3" value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} />
                                </div>
                            </div>
                        </div>
                        <div className="p-6 bg-gray-50 flex gap-3">
                            <button onClick={() => setEditingProduct(null)} className="btn-ghost bg-white border border-gray-200 flex-1">Cancel</button>
                            <button onClick={handleSaveEdit} disabled={saving} className="btn-primary flex-1">
                                {saving ? "Saving…" : "✨ Save Changes"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Label Studio (Print Modal) */}
            {printingProduct && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-3xl w-full max-w-sm shadow-2xl overflow-hidden">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                            <h2 className="text-xl font-black">🖨️ Label Studio</h2>
                            <button onClick={() => setPrintingProduct(null)} className="text-gray-400">✕</button>
                        </div>
                        <div className="p-8 flex flex-col items-center">
                            <div className="w-full flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50 mb-6">
                                <p className="font-bold text-gray-900 text-sm mb-1">{printingProduct.name}</p>
                                <p className="text-xs font-black mb-3 text-gray-500">₹{printingProduct.price}</p>

                                <div className="bg-white p-3 rounded-lg shadow-sm border min-h-[80px] flex items-center justify-center w-full">
                                    {loadingImg ? (
                                        <div className="h-10 w-32 bg-gray-100 animate-pulse rounded" />
                                    ) : barcodeImg ? (
                                        <img src={barcodeImg} alt="Barcode" className="h-14 object-contain" />
                                    ) : (
                                        <div className="flex flex-col items-center gap-3 py-2">
                                            {printingProduct.barcode ? (
                                                <button
                                                    onClick={async () => {
                                                        setLoadingImg(true);
                                                        try {
                                                            const res = await inventoryApi.getBarcodeImage(printingProduct.barcode);
                                                            setBarcodeImg(res.data.image);
                                                        } catch (err) { toast.error("Failed to generate preview"); }
                                                        finally { setLoadingImg(false); }
                                                    }}
                                                    className="px-5 py-2.5 bg-blue-600 text-white text-[10px] font-black uppercase rounded-xl hover:bg-blue-700 transition-all flex items-center gap-2">
                                                    🔄 Generate Preview
                                                </button>
                                            ) : (
                                                <div className="text-[10px] text-red-400 font-bold uppercase tracking-widest text-center italic">
                                                    No Barcode Assigned.<br />Please edit product to add one.
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                                <p className="text-[10px] font-bold text-gray-400 mt-2 uppercase tracking-widest">{printingProduct.barcode || "PENDING"}</p>
                            </div>

                            <label className="text-xs font-black uppercase text-gray-400 mb-2 block self-start">Number of labels</label>
                            <input type="number" min="1" max="100" className="input text-center text-xl font-black py-4 mb-6" value={labelCount} onChange={(e) => setLabelCount(parseInt(e.target.value) || 1)} />

                            <button
                                onClick={handleActualPrint}
                                disabled={!barcodeImg}
                                className="btn-primary w-full py-4 text-sm font-black uppercase tracking-widest disabled:opacity-50">
                                {barcodeImg ? "Confirm & Print" : "Generate Preview First"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Hidden Print Layout */}
            {printingProduct && (
                <div className="hidden print:block print:absolute print:inset-0 print:bg-white print:z-[1000]">
                    <div className="flex flex-wrap gap-4 p-4">
                        {Array.from({ length: labelCount }).map((_, i) => (
                            <div key={i} className="border border-gray-300 p-4 inline-flex flex-col items-center justify-center bg-white w-[60mm] h-[40mm] rounded-sm">
                                <div className="text-center font-bold text-[12px] mb-1 leading-tight">{printingProduct.name}</div>
                                <div className="text-center text-[13px] font-black mb-1">₹{printingProduct.price}</div>
                                {barcodeImg && <img src={barcodeImg} alt="Barcode" className="h-[18mm] object-contain" />}
                                <div className="text-[8px] text-gray-400 mt-2 uppercase tracking-widest font-bold font-sans">BLINKIT SMART LABEL</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
