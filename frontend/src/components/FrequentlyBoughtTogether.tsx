
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
    isSidebar?: boolean;
}

export default function FrequentlyBoughtTogether({
    productId,
    cartIds,
    title = "Frequently Bought Together",
    subtitle = "Customers who bought this also bought these items",
    maxItems = 4,
    isSidebar = false
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
            for (const p of pairings) {
                const cart = JSON.parse(localStorage.getItem('sb_cart') || '[]');
                const existing = cart.find((item: any) => item.product_id === p.id);
                if (existing) {
                    existing.qty += 1;
                } else {
                    cart.push({
                        id: p.id,
                        name: p.name,
                        price: p.price,
                        qty: 1,
                        image_url: p.image_url,
                        category: p.category
                    });
                }
                localStorage.setItem('sb_cart', JSON.stringify(cart));
            }

            window.dispatchEvent(new Event('cartUpdated'));
            toast.success(`Added ${pairings.length} items to cart!`);
        } catch (err) {
            toast.error("Failed to add items to cart");
        } finally {
            setAdding(false);
        }
    };

    const addToCart = (p: Product) => {
        try {
            const cart = JSON.parse(localStorage.getItem('sb_cart') || '[]');
            const existing = cart.find((item: any) => item.id === p.id);
            if (existing) {
                existing.qty += 1;
            } else {
                cart.push({
                    id: p.id,
                    name: p.name,
                    price: p.price,
                    qty: 1,
                    image_url: p.image_url,
                    category: p.category
                });
            }
            localStorage.setItem('sb_cart', JSON.stringify(cart));
            window.dispatchEvent(new Event('cartUpdated'));
            toast.success(`Added ${p.name} to cart!`);
        } catch (err) {
            toast.error("Failed to add item");
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center p-8">
            <Loader2 className="w-6 h-6 text-orange-500 animate-spin" />
        </div>
    );

    if (pairings.length === 0) return null;

    return (
        <section className={`${isSidebar ? 'mt-4 py-4 border-t' : 'mt-12 py-12 border-t'} border-gray-100`}>
            <div className={`flex ${isSidebar ? 'flex-col' : 'flex-col md:flex-row md:items-end'} justify-between gap-4 mb-6`}>
                <div className="flex-1">
                    <h2 className={`${isSidebar ? 'text-lg' : 'text-3xl'} font-black text-gray-900 tracking-tight leading-none`}>
                        {title}
                    </h2>
                    <p className={`${isSidebar ? 'text-[10px]' : 'text-gray-500'} font-medium mt-1 text-gray-500`}>
                        {subtitle}
                    </p>
                </div>
                <button
                    onClick={addAllToCart}
                    disabled={adding}
                    className={`flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white ${isSidebar ? 'px-4 py-2 text-xs w-full' : 'px-6 py-3'} rounded-xl font-black transition-all shadow-lg shadow-orange-200 disabled:opacity-50`}
                >
                    {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className={isSidebar ? 'w-4 h-4' : 'w-5 h-5'} />}
                    {isSidebar ? 'Add All' : 'Add All to Cart'}
                </button>
            </div>

            <div className={`grid ${isSidebar ? 'grid-cols-2 gap-3' : 'grid-cols-2 md:grid-cols-4 gap-6'}`}>
                {pairings.map((product) => (
                    <div 
                        key={product.id} 
                        onClick={() => addToCart(product)}
                        className={`group bg-white rounded-2xl border border-gray-100 ${isSidebar ? 'p-2' : 'p-4'} hover:border-orange-200 transition-all hover:shadow-lg hover:shadow-orange-50 cursor-pointer`}
                    >
                        <div className={`relative aspect-square rounded-xl overflow-hidden bg-gray-50 ${isSidebar ? 'mb-2' : 'mb-4'}`}>
                            <img
                                src={product.image_url}
                                alt={product.name}
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                            />
                            {!isSidebar && (
                                <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-2 py-1 rounded-lg text-[10px] font-black text-orange-600 uppercase">
                                    Popular Pair
                                </div>
                            )}
                        </div>
                        <h3 className={`${isSidebar ? 'text-xs leading-tight h-8' : 'font-bold h-6'} font-bold text-gray-900 line-clamp-2 mb-1`}>
                            {product.name}
                        </h3>
                        {!isSidebar && (
                            <p className="text-sm text-gray-500 font-medium mb-3">{product.category}</p>
                        )}
                        <div className="flex items-center justify-between mt-auto">
                            <span className={`${isSidebar ? 'text-sm' : 'text-lg'} font-black text-gray-900`}>₹{product.price}</span>
                            <div className={`${isSidebar ? 'w-6 h-6 rounded-lg' : 'w-8 h-8 rounded-xl'} bg-orange-50 flex items-center justify-center text-orange-500 group-hover:bg-orange-500 group-hover:text-white transition-colors`}>
                                <Plus className={isSidebar ? 'w-4 h-4' : 'w-5 h-5'} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
