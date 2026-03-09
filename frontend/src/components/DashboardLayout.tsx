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
    { href: "/seller/demand", label: "📢 Demand Requests" },
    { href: "/seller/top-picks", label: "🏆 Top Picks" },
    { href: "/seller/inventory", label: "📦 Inventory" },
    { href: "/seller/barcode", label: "📷 Barcode Scanner" },
    { href: "/seller/products/new", label: "➕ Add Product" },
    { href: "/seller/orders", label: "🧾 Orders" },
];

function AddressBar() {
    const { status, location, requestLocation, refreshLocation, setManualLocation } = useLocation();
    const [address, setAddress] = useState<string | null>(null);
    const [fetching, setFetching] = useState(false);
    const [showManual, setShowManual] = useState(false);
    const [manualInput, setManualInput] = useState("");

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

    const handleManualSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!manualInput.trim()) return;
        setFetching(true);
        try {
            const resp = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(manualInput)}&format=json&limit=1`);
            const data = await resp.json();
            if (data && data.length > 0) {
                setManualLocation(parseFloat(data[0].lat), parseFloat(data[0].lon));
                setShowManual(false);
                setManualInput("");
                toast.success("Location updated!");
            } else {
                toast.error("Location not found.");
            }
        } catch {
            toast.error("Search failed.");
        } finally {
            setFetching(false);
        }
    };

    const handleRefresh = () => {
        setFetching(true);
        refreshLocation();
    };

    return (
        <div className="address-bar print:!hidden" style={{
            backgroundColor: "#fffbeb",
            borderBottom: "1px solid #fde68a",
            padding: "8px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
            fontSize: 12,
        }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 14 }}>📍</span>
                {status === "granted" && address ? (
                    <div className="flex items-center gap-2">
                        <span style={{ fontWeight: 600, color: "#92400e" }}>
                            {fetching ? "Updating…" : address}
                        </span>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setShowManual(!showManual)}
                                className="text-[10px] font-bold text-yellow-700 hover:text-yellow-900 underline"
                                style={{ background: "none", border: "none" }}>
                                Change
                            </button>
                            <span className="text-yellow-300">|</span>
                            <button
                                onClick={handleRefresh}
                                title="Refresh precision"
                                className={`text-[10px] font-bold text-yellow-700 hover:text-yellow-900 flex items-center gap-1 ${fetching ? "animate-spin" : ""}`}
                                style={{ background: "none", border: "none" }}>
                                🔄 Refresh
                            </button>
                        </div>
                    </div>
                ) : status === "requesting" || fetching ? (
                    <span style={{ color: "#92400e" }} className="flex items-center gap-2">
                        <span className="animate-spin text-xs">🔄</span>
                        {status === "requesting" ? "Detecting high accuracy location..." : "Fetching address..."}
                    </span>
                ) : (
                    <>
                        <span style={{ color: "#78350f" }}>Deliver to —</span>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={requestLocation}
                                style={{
                                    fontSize: 12, fontWeight: 700, color: "#d97706",
                                    background: "none", border: "none", cursor: "pointer",
                                    padding: 0, textDecoration: "underline",
                                }}>
                                Enable GPS location
                            </button>
                            <span className="text-gray-300">|</span>
                            <button
                                onClick={() => setShowManual(!showManual)}
                                style={{
                                    fontSize: 12, fontWeight: 700, color: "#d97706",
                                    background: "none", border: "none", cursor: "pointer",
                                    padding: 0, textDecoration: "underline",
                                }}>
                                Enter manually
                            </button>
                        </div>
                    </>
                )}
            </div>

            {showManual && (
                <form onSubmit={handleManualSubmit} className="flex gap-2">
                    <input
                        type="text"
                        value={manualInput}
                        onChange={(e) => setManualInput(e.target.value)}
                        placeholder="Enter area or city..."
                        className="px-2 py-1 border border-yellow-300 rounded text-xs outline-none focus:ring-1 focus:ring-yellow-500"
                        style={{ width: 180 }}
                    />
                    <button type="submit" className="bg-yellow-500 text-white px-2 py-1 rounded text-[10px] font-bold hover:bg-yellow-600">
                        Go
                    </button>
                </form>
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
            <nav className="navbar print:!hidden">
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
            <aside className="sidebar print:!hidden">
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

                {/* Account Settings Link */}
                <div className="mx-3 mt-auto pt-4 border-t border-gray-100">
                    <Link href="/account/settings"
                        className={`sidebar-item mb-1 ${isActive("/account/settings") ? "active" : ""}`}>
                        ⚙ Account Settings
                    </Link>
                </div>

                {/* Bottom user card */}
                {mounted && !isLoading && user && (
                    <div className="mx-3 mb-4 p-3 rounded-xl bg-yellow-50 border border-yellow-100 flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-yellow-200 border-2 border-white flex-shrink-0 overflow-hidden flex items-center justify-center text-yellow-700 font-black">
                            {user.profile_image ? (
                                <img src={user.profile_image} alt={user.name} className="w-full h-full object-cover" />
                            ) : (
                                user.name.charAt(0).toUpperCase()
                            )}
                        </div>
                        <div className="min-w-0">
                            <p className="text-xs font-bold text-gray-900 truncate">{user.name}</p>
                            <p className="text-xs text-gray-500 truncate">{user.email}</p>
                        </div>
                    </div>
                )}
            </aside>

            {/* Main Content */}
            <main className="page-with-sidebar print:!p-0 print:!m-0 print:!block print:!static">
                <div className="page-content print:!p-0 print:!m-0">{children}</div>
            </main>
        </div>
    );
}
