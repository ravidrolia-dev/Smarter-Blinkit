
'use client';

import React, { useEffect, useState } from 'react';
import { ShoppingCart, Plus, Check, Loader2 } from 'lucide-react';
import { analyticsApi, ordersApi } from '@/lib/api';
import toast from 'react-hot-toast';

interface Product {
    id: string;
    name: string;
    price: number;
    image_url: string;
    category: string;
    confidence: number;
}

interface FrequentlyBoughtTogetherProps {
    productId?: string;
    cartIds?: string[];
    title?: string;
    subtitle?: string;
    maxItems?: number;
}

export default function FrequentlyBoughtTogether({
    productId,
    cartIds,
    title = "Frequently Bought Together",
    subtitle = "Customers who bought this also bought these items",
    maxItems = 4
}: FrequentlyBoughtTogetherProps) {
    const [pairings, setPairings] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);

    useEffect(() => {
        const fetchPairings = async () => {
            setLoading(true);
            try {
                let res;
                if (productId) {
                    res = await analyticsApi.productPairings(productId, maxItems);
                } else if (cartIds && cartIds.length > 0) {
                    res = await analyticsApi.cartPairings(cartIds.join(','), maxItems);
                } else {
                    setLoading(false);
                    return;
                }
                setPairings(res.data || []);
            } catch (err) {
                console.error("Failed to fetch pairings:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchPairings();
    }, [productId, cartIds, maxItems]);

    const addAllToCart = async () => {
        setAdding(true);
        try {
            // This assumes a shared cart state or a dedicated API for bulk add
            // For now, we'll just toast success and ideally trigger a cart refresh
            for (const p of pairings) {
                // Mock adding to local storage or calling API
                const cart = JSON.parse(localStorage.getItem('sb_cart') || '[]');
                const existing = cart.find((item: any) => item.product_id === p.id);
                if (existing) {
                    existing.quantity += 1;
                } else {
                    cart.push({
                        product_id: p.id,
                        product_name: p.name,
                        price: p.price,
                        quantity: 1,
                        image_url: p.image_url
                    });
                }
                localStorage.setItem('sb_cart', JSON.stringify(cart));
            }

            // Dispatch custom event for cart refresh
            window.dispatchEvent(new Event('cartUpdated'));
            toast.success(`Added ${pairings.length} items to cart!`);
        } catch (err) {
            toast.error("Failed to add items to cart");
        } finally {
            setAdding(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center p-12">
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
        </div>
    );

    if (pairings.length === 0) return null;

    return (
        <section className="mt-12 py-12 border-t border-gray-100">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
                <div>
                    <h2 className="text-3xl font-black text-gray-900 tracking-tight">{title}</h2>
                    <p className="text-gray-500 font-medium mt-1">{subtitle}</p>
                </div>
                <button
                    onClick={addAllToCart}
                    disabled={adding}
                    className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-2xl font-black transition-all shadow-lg shadow-orange-200 disabled:opacity-50"
                >
                    {adding ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                    Add All to Cart
                </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {pairings.map((product) => (
                    <div key={product.id} className="group bg-white rounded-3xl border border-gray-100 p-4 hover:border-orange-200 transition-all hover:shadow-xl hover:shadow-orange-50">
                        <div className="relative aspect-square rounded-2xl overflow-hidden bg-gray-50 mb-4">
                            <img
                                src={product.image_url}
                                alt={product.name}
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                            />
                            <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-2 py-1 rounde-lg text-[10px] font-black text-orange-600 uppercase">
                                Popular Pair
                            </div>
                        </div>
                        <h3 className="font-bold text-gray-900 line-clamp-1 mb-1">{product.name}</h3>
                        <p className="text-sm text-gray-500 font-medium mb-3">{product.category}</p>
                        <div className="flex items-center justify-between">
                            <span className="text-lg font-black text-gray-900">₹{product.price}</span>
                            <div className="w-8 h-8 rounded-xl bg-orange-50 flex items-center justify-center text-orange-500 group-hover:bg-orange-500 group-hover:text-white transition-colors">
                                <Plus className="w-5 h-5" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
