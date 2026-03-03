"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { inventoryApi } from "@/lib/api";
import toast from "react-hot-toast";
import Link from "next/link";

export default function InventoryPage() {
    const [products, setProducts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("");

    useEffect(() => {
        inventoryApi.myProducts()
            .then((r) => setProducts(r.data))
            .finally(() => setLoading(false));
    }, []);

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
                    <p className="text-sm text-gray-500">{products.length} products listed</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/seller/barcode" className="btn-secondary text-sm">📷 Barcode Update</Link>
                    <Link href="/seller/products/new" className="btn-primary text-sm">+ Add Product</Link>
                </div>
            </div>

            <input type="search" value={filter} onChange={(e) => setFilter(e.target.value)}
                placeholder="Search products…" className="input mb-4 max-w-xs" />

            {loading ? (
                <div className="skeleton h-80 rounded-2xl" />
            ) : (
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Category</th>
                                <th>Price</th>
                                <th>Stock</th>
                                <th>Sold</th>
                                <th>Barcode</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((p) => (
                                <tr key={p.id}>
                                    <td>
                                        <div className="font-semibold text-gray-900">{p.name}</div>
                                        <div className="text-xs text-gray-400">{p.unit}</div>
                                    </td>
                                    <td><span className="badge badge-yellow">{p.category}</span></td>
                                    <td className="font-bold">₹{p.price}</td>
                                    <td className={`font-black ${stockColor(p.stock)}`}>{p.stock}</td>
                                    <td className="text-gray-500">{p.total_sold || 0}</td>
                                    <td><code className="text-xs bg-gray-100 px-1 rounded">{p.barcode || "—"}</code></td>
                                    <td>
                                        <Link href={`/seller/barcode`}
                                            className="text-xs font-semibold text-yellow-600 hover:underline">
                                            Update Stock
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr><td colSpan={7} className="text-center py-8 text-gray-400">No products found</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </DashboardLayout>
    );
}
