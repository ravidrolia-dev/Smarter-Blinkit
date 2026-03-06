"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useLocation } from "@/hooks/useLocation";
import { useState, useEffect } from "react";
import toast from "react-hot-toast";

const buyerNav = [
    { href: "/buyer", label: "🏠 Dashboard", exact: true },
    { href: "/buyer/search", label: "🔍 Smart Search" },
    { href: "/buyer/agent", label: "🤖 Recipe Agent" },
    { href: "/buyer/cart", label: "🛒 Cart" },
    { href: "/buyer/orders", label: "📦 My Orders" },
];

const sellerNav = [
    { href: "/seller", label: "📊 Dashboard", exact: true },
    { href: "/seller/inventory", label: "📦 Inventory" },
    { href: "/seller/barcode", label: "📷 Barcode Scanner" },
    { href: "/seller/products/new", label: "➕ Add Product" },
    { href: "/seller/orders", label: "🧾 Orders" },
];

function AddressBar() {
    const { status, location, requestLocation } = useLocation();
    const [address, setAddress] = useState<string | null>(null);
    const [fetching, setFetching] = useState(false);

    // Reverse geocode whenever we get a location
    useEffect(() => {
        if (!location) return;
        setFetching(true);
        fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${location.lat}&lon=${location.lng}&format=json&addressdetails=1`,
            { headers: { "Accept-Language": "en" } }
        )
            .then((r) => r.json())
            .then((data) => {
                const a = data.address;
                // Build a short human-readable address
                const parts = [
                    a.road || a.suburb || a.neighbourhood,
                    a.city || a.town || a.village || a.county,
                    a.state,
                ].filter(Boolean);
                setAddress(parts.join(", "));
            })
            .catch(() => setAddress(`${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`))
            .finally(() => setFetching(false));
    }, [location]);

    return (
        <div className="address-bar" style={{
            backgroundColor: "#fffbeb",
            borderBottom: "1px solid #fde68a",
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 12,
        }}>
            <span style={{ fontSize: 14 }}>📍</span>
            {status === "granted" && address ? (
                <span style={{ fontWeight: 600, color: "#92400e" }}>
                    {fetching ? "Loading address…" : address}
                </span>
            ) : status === "granted" && fetching ? (
                <span style={{ color: "#92400e" }}>Fetching address…</span>
            ) : status === "requesting" ? (
                <span style={{ color: "#92400e" }}>Detecting location…</span>
            ) : status === "denied" ? (
                <span style={{ color: "#b91c1c" }}>Location access denied — </span>
            ) : (
                <>
                    <span style={{ color: "#78350f" }}>Deliver to —</span>
                    <button
                        onClick={requestLocation}
                        style={{
                            fontSize: 12, fontWeight: 700, color: "#d97706",
                            background: "none", border: "none", cursor: "pointer",
                            padding: 0, textDecoration: "underline",
                        }}>
                        Enable location
                    </button>
                </>
            )}
        </div>
    );
}

export default function DashboardLayout({ children, role }: { children: React.ReactNode; role: "buyer" | "seller" }) {
    const pathname = usePathname();
    const { user, logout, isLoading } = useAuth();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const nav = role === "buyer" ? buyerNav : sellerNav;

    const isActive = (href: string, exact?: boolean) =>
        exact ? pathname === href : pathname.startsWith(href);

    return (
        <div>
            {/* Navbar */}
            <nav className="navbar">
                <div className="navbar-logo">
                    <span>⚡</span>
                    <span>Smarter<span>BlinkIt</span></span>
                </div>

                <div className="flex items-center gap-3">
                    {mounted && !isLoading && user && (
                        <div className="hidden md:flex items-center gap-1 bg-gray-100 rounded-full px-3 py-1.5">
                            <span className="text-xs text-gray-500">Signed in as</span>
                            <span className="text-xs font-bold text-gray-900">{user.name}</span>
                            <span className="badge badge-yellow ml-1">{user.role}</span>
                        </div>
                    )}
                    {role === "buyer"
                        ? <Link href="/seller" className="btn-ghost text-xs hidden md:flex">Switch to Seller</Link>
                        : <Link href="/buyer" className="btn-ghost text-xs hidden md:flex">Switch to Buyer</Link>
                    }
                    <button onClick={() => { logout(); toast.success("Logged out!"); }}
                        className="btn-ghost text-red-500 hover:bg-red-50"
                        suppressHydrationWarning={true}>
                        Logout
                    </button>
                </div>
            </nav>

            {/* Address strip — shown below the navbar */}
            <AddressBar />

            {/* Sidebar */}
            <aside className="sidebar">
                <div className="px-4 mb-4">
                    <p className="text-xs font-bold uppercase tracking-widest text-gray-400">
                        {role === "buyer" ? "Buyer Portal" : "Seller Portal"}
                    </p>
                </div>
                <nav className="flex-1 space-y-0.5">
                    {nav.map((item) => (
                        <Link key={item.href} href={item.href}
                            className={`sidebar-item ${isActive(item.href, item.exact) ? "active" : ""}`}>
                            {item.label}
                        </Link>
                    ))}
                </nav>

                {/* Bottom user card */}
                {mounted && !isLoading && user && (
                    <div className="mx-3 mt-4 p-3 rounded-xl bg-yellow-50 border border-yellow-100">
                        <p className="text-xs font-bold text-gray-900">{user.name}</p>
                        <p className="text-xs text-gray-500 truncate">{user.email}</p>
                    </div>
                )}
            </aside>

            {/* Main Content */}
            <main className="page-with-sidebar">
                <div className="page-content">{children}</div>
            </main>
        </div>
    );
}
