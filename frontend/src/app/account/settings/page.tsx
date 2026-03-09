"use client";
import { useState, useEffect, useRef } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { userApi, authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import toast from "react-hot-toast";
import dynamic from "next/dynamic";
import { useLocation } from "@/hooks/useLocation";
import axios from "axios";

const LocationPickerMap = dynamic(() => import("@/components/LocationPickerMap"), {
    ssr: false,
    loading: () => <div className="h-[250px] w-full bg-gray-100 animate-pulse rounded-2xl flex items-center justify-center text-gray-400 font-bold">Loading Map...</div>
});

export default function AccountSettingsPage() {
    const { user, refreshUser } = useAuth();
    const [loading, setLoading] = useState(false);
    const [profile, setProfile] = useState({ name: "", phone: "", profile_image: "" });
    const [password, setPassword] = useState({ current: "", new: "", confirm: "" });
    const { location: currentLoc, requestLocation: detectLocation, status: locStatus } = useLocation();
    const [addresses, setAddresses] = useState<any[]>([]);
    const [showAddressModal, setShowAddressModal] = useState(false);
    const [newAddress, setNewAddress] = useState({
        label: "",
        full_address: "",
        is_default: false,
        lat: 26.9124,
        lng: 75.7873
    });

    // Face Lock State
    const [faceFrame, setFaceFrame] = useState<string | null>(null);
    const [cameraOn, setCameraOn] = useState(false);
    const [enrollingFace, setEnrollingFace] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);

    useEffect(() => {
        if (user) {
            setProfile({
                name: user.name || "",
                phone: user.phone || "",
                profile_image: user.profile_image || ""
            });
            fetchAddresses();
        }
    }, [user]);

    const fetchAddresses = async () => {
        try {
            const res = await userApi.getAddresses();
            setAddresses(res.data);
        } catch (err) {
            console.error("Failed to fetch addresses");
        }
    };

    const handleProfileUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await userApi.updateProfile(profile);
            toast.success("Profile updated!");
            refreshUser?.();
        } catch (err) {
            toast.error("Failed to update profile");
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (password.new !== password.confirm) {
            return toast.error("Passwords do not match");
        }
        setLoading(true);
        try {
            await userApi.updatePassword({
                current_password: password.current,
                new_password: password.new
            });
            toast.success("Password updated!");
            setPassword({ current: "", new: "", confirm: "" });
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Failed to update password");
        } finally {
            setLoading(false);
        }
    };

    const handleAddAddress = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await userApi.addAddress(newAddress);
            toast.success("Address added!");
            setShowAddressModal(false);
            setNewAddress({ label: "", full_address: "", is_default: false, lat: 26.9124, lng: 75.7873 });
            fetchAddresses();
        } catch (err) {
            toast.error("Failed to add address");
        }
    };

    const handleDeleteAddress = async (id: string) => {
        try {
            await userApi.deleteAddress(id);
            toast.success("Address deleted");
            fetchAddresses();
        } catch (err) {
            toast.error("Failed to delete address");
        }
    };

    const setAddressDefault = async (id: string) => {
        const addr = addresses.find(a => a.id === id);
        if (!addr) return;
        try {
            await userApi.updateAddress(id, { ...addr, is_default: true });
            fetchAddresses();
            toast.success("Default address updated");
        } catch (err) {
            toast.error("Failed to update default address");
        }
    };

    const handleLocationDetect = async () => {
        detectLocation();
    };

    useEffect(() => {
        if (currentLoc && showAddressModal) {
            setNewAddress(prev => ({ ...prev, lat: currentLoc.lat, lng: currentLoc.lng }));
            reverseGeocode(currentLoc.lat, currentLoc.lng);
        }
    }, [currentLoc, showAddressModal]);

    const reverseGeocode = async (lat: number, lng: number) => {
        try {
            const res = await axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
            if (res.data && res.data.display_name) {
                setNewAddress(prev => ({ ...prev, full_address: res.data.display_name }));
            }
        } catch (err) {
            console.error("Reverse geocoding failed:", err);
        }
    };

    // Face Lock Logic
    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            streamRef.current = stream;
            if (videoRef.current) videoRef.current.srcObject = stream;
            setCameraOn(true);
            setFaceFrame(null);
        } catch { toast.error("Camera access denied"); }
    };

    const stopCamera = () => {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        setCameraOn(false);
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        ctx?.drawImage(videoRef.current, 0, 0);

        const frame = canvas.toDataURL("image/jpeg", 0.8);
        setFaceFrame(frame);
        stopCamera();
        toast.success("Face captured! ✅");
    };

    const handleEnrollFace = async () => {
        if (!faceFrame || !user) return;
        setEnrollingFace(true);
        try {
            await authApi.enrollFace(user.id, faceFrame);
            toast.success("Face Lock updated successfully!");
            setFaceFrame(null);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Face enrollment failed");
        } finally {
            setEnrollingFace(false);
        }
    };

    if (!user) return <div className="p-8">Loading...</div>;

    const userRole = user.role === "seller" ? "seller" : "buyer";

    return (
        <DashboardLayout role={userRole}>
            <div className="max-w-4xl mx-auto py-8">
                <h1 className="text-3xl font-black mb-8">⚙ Account Settings</h1>

                <div className="space-y-8">
                    {/* Profile Information */}
                    <section className="card">
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                            👤 Profile Information
                        </h2>
                        <form onSubmit={handleProfileUpdate} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Full Name</label>
                                    <input
                                        type="text"
                                        value={profile.name}
                                        onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                                        className="input"
                                        placeholder="Enter your name"
                                    />
                                </div>
                                <div>
                                    <label className="label">Phone Number</label>
                                    <input
                                        type="text"
                                        value={profile.phone}
                                        onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                                        className="input"
                                        placeholder="+91 XXXXX XXXXX"
                                    />
                                </div>
                            </div>
                            <div className="flex items-center gap-6 mt-2">
                                <div className="w-20 h-20 rounded-full border-4 border-yellow-100 overflow-hidden bg-gray-100 flex items-center justify-center text-2xl font-black text-gray-400">
                                    {profile.profile_image ? (
                                        <img src={profile.profile_image} alt="Preview" className="w-full h-full object-cover" />
                                    ) : (
                                        "?"
                                    )}
                                </div>
                                <div className="flex-1">
                                    <label className="label">Profile Picture URL</label>
                                    <input
                                        type="text"
                                        value={profile.profile_image}
                                        onChange={(e) => setProfile({ ...profile, profile_image: e.target.value })}
                                        className="input"
                                        placeholder="https://example.com/photo.jpg"
                                    />
                                </div>
                            </div>
                            <button type="submit" disabled={loading} className="btn-primary px-6">
                                {loading ? "Saving..." : "Save Changes"}
                            </button>
                        </form>
                    </section>

                    {/* Email Information */}
                    <section className="card bg-gray-50 border-dashed">
                        <h2 className="text-xl font-bold mb-2">📧 Email Information</h2>
                        <p className="text-sm text-gray-500 mb-4">Email cannot be changed for security reasons.</p>
                        <div className="bg-white p-3 rounded-lg border border-gray-200 inline-block">
                            <span className="font-mono text-gray-700">{user.email}</span>
                        </div>
                    </section>

                    {/* Address Management */}
                    <section className="card">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                🏠 Address Management
                            </h2>
                            <button onClick={() => setShowAddressModal(true)} className="btn-secondary text-xs py-2">
                                + Add New Address
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {addresses.length === 0 ? (
                                <p className="text-sm text-gray-400 col-span-2 py-4">No saved addresses yet.</p>
                            ) : (
                                addresses.map((addr: any) => (
                                    <div key={addr.id} className={`p-4 rounded-xl border-2 transition-all ${addr.is_default ? "border-yellow-400 bg-yellow-50" : "border-gray-100 bg-white"}`}>
                                        <div className="flex justify-between items-start mb-2">
                                            <span className="text-xs font-black uppercase tracking-wider text-gray-400">
                                                {addr.label}
                                                {addr.is_default && <span className="ml-2 text-yellow-600">★ DEFAULT</span>}
                                            </span>
                                            <button onClick={() => handleDeleteAddress(addr.id)} className="text-red-400 hover:text-red-600">
                                                🗑
                                            </button>
                                        </div>
                                        <p className="text-sm font-semibold text-gray-700 mb-4">{addr.full_address}</p>
                                        {!addr.is_default && (
                                            <button onClick={() => setAddressDefault(addr.id)} className="text-xs font-bold text-yellow-600 underline">
                                                Set as Default
                                            </button>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </section>

                    {/* Security */}
                    <section className="card">
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                            🔒 Security
                        </h2>
                        <form onSubmit={handlePasswordUpdate} className="space-y-4 max-w-md">
                            <div>
                                <label className="label">Current Password</label>
                                <input
                                    type="password"
                                    value={password.current}
                                    onChange={(e) => setPassword({ ...password, current: e.target.value })}
                                    className="input"
                                    required
                                />
                            </div>
                            <div>
                                <label className="label">New Password</label>
                                <input
                                    type="password"
                                    value={password.new}
                                    onChange={(e) => setPassword({ ...password, new: e.target.value })}
                                    className="input"
                                    required
                                />
                            </div>
                            <div>
                                <label className="label">Confirm New Password</label>
                                <input
                                    type="password"
                                    value={password.confirm}
                                    onChange={(e) => setPassword({ ...password, confirm: e.target.value })}
                                    className="input"
                                    required
                                />
                            </div>
                            <button type="submit" disabled={loading} className="btn-primary px-6">
                                Update Password
                            </button>
                        </form>

                        <div className="mt-10 pt-8 border-t border-gray-100">
                            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                                🔐 Face Lock Management
                            </h3>
                            <p className="text-xs text-gray-500 mb-6 font-medium">
                                Enrolling your face allows you to log in instantly using biometric verification.
                            </p>

                            <div className="flex flex-col md:flex-row gap-8 items-start">
                                <div className="w-full md:w-64 aspect-[4/3] bg-gray-900 rounded-2xl overflow-hidden relative shadow-2xl border-4 border-white">
                                    <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
                                    {faceFrame && (
                                        <img src={faceFrame} alt="Captured" className="absolute inset-0 w-full h-full object-cover" />
                                    )}
                                    {!cameraOn && !faceFrame && (
                                        <div className="absolute inset-0 flex items-center justify-center text-white/40 text-xs flex-col gap-3">
                                            <span className="text-5xl">📷</span>
                                            <span className="font-bold tracking-tight">Camera Inactive</span>
                                        </div>
                                    )}
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <div className="w-28 h-36 rounded-[2rem] border-2 border-yellow-400 border-dashed opacity-40 shadow-[0_0_20px_rgba(255,208,0,0.2)]" />
                                    </div>
                                    {cameraOn && (
                                        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-black/60 backdrop-blur rounded-full flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                                            <span className="text-[10px] text-white font-bold uppercase tracking-wider">Live</span>
                                        </div>
                                    )}
                                </div>
                                <canvas ref={canvasRef} className="hidden" />

                                <div className="flex-1 space-y-4">
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-black text-gray-800 uppercase tracking-wide">Quick Settings</h4>
                                        <p className="text-xs text-gray-400 leading-relaxed">
                                            Ensure your face is well-lit and centered within the frame for best recognition accuracy.
                                        </p>
                                    </div>

                                    {!cameraOn && !faceFrame ? (
                                        <button onClick={startCamera} className="btn-secondary w-full md:w-auto py-3 px-8 shadow-lg shadow-gray-100 font-black">
                                            📷 Setup/Update Face Lock
                                        </button>
                                    ) : cameraOn ? (
                                        <button onClick={capturePhoto} className="btn-primary w-full md:w-auto py-3 px-8 shadow-xl shadow-yellow-200 font-black">
                                            📸 Take Photo
                                        </button>
                                    ) : (
                                        <div className="flex flex-col gap-3">
                                            <button
                                                onClick={handleEnrollFace}
                                                disabled={enrollingFace}
                                                className="btn-primary w-full py-4 shadow-xl shadow-yellow-300 font-black text-lg"
                                            >
                                                {enrollingFace ? "Enrolling..." : "✅ Enroll My Face"}
                                            </button>
                                            <button onClick={startCamera} className="btn-ghost w-full border border-gray-200 font-bold py-3">
                                                🔄 Retake Photo
                                            </button>
                                        </div>
                                    )}

                                    <div className="p-3 bg-blue-50 rounded-xl flex items-start gap-3 border border-blue-100">
                                        <span className="text-blue-500">ℹ️</span>
                                        <p className="text-[10px] text-blue-700 font-medium">
                                            Your biometric data never leaves this device. Only a mathematical representation (encoding) is stored on our secure servers.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Notifications */}
                    <section className="card">
                        <h2 className="text-xl font-bold mb-6">🔔 Notification Preferences</h2>
                        <div className="space-y-4">
                            {[
                                { id: "order", label: "Order Updates", desc: "Get notified when your order status changes." },
                                { id: "delivery", label: "Delivery Updates", desc: "Real-time updates on your delivery partner location." },
                                { id: "demand", label: "Product Availability", desc: "Notify me when a high-demand product is added." }
                            ].map(pref => (
                                <div key={pref.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors">
                                    <div>
                                        <p className="font-bold text-gray-900">{pref.label}</p>
                                        <p className="text-xs text-gray-500">{pref.desc}</p>
                                    </div>
                                    <input type="checkbox" defaultChecked className="w-5 h-5 accent-yellow-500" />
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Danger Zone */}
                    <section className="card border-red-100 bg-red-50/30">
                        <h2 className="text-xl font-bold mb-4 text-red-600 flex items-center gap-2">
                            ⚠️ Danger Zone
                        </h2>
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 border border-red-200 rounded-2xl bg-white">
                            <div>
                                <h3 className="font-black text-gray-900">Delete Account</h3>
                                <p className="text-xs text-gray-500">Permanently remove your account and all associated data. This action is irreversible.</p>
                            </div>
                            <button
                                onClick={async () => {
                                    if (confirm("Are you absolutely sure you want to delete your account? This will erase everything and cannot be undone.")) {
                                        try {
                                            setLoading(true);
                                            await userApi.deleteAccount();
                                            toast.success("Account deleted successfully");
                                            localStorage.clear();
                                            window.location.href = "/register";
                                        } catch (err: any) {
                                            toast.error(err.response?.data?.detail || "Failed to delete account");
                                        } finally {
                                            setLoading(false);
                                        }
                                    }
                                }}
                                disabled={loading}
                                className="bg-red-500 hover:bg-red-600 text-white font-black py-3 px-6 rounded-xl transition-all shadow-lg shadow-red-100 whitespace-nowrap"
                            >
                                {loading ? "Deleting..." : "Delete Account"}
                            </button>
                        </div>
                    </section>
                </div>
            </div>

            {/* Address Modal */}
            {showAddressModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl animate-fade-up">
                        <h3 className="text-2xl font-black mb-6">Add New Address</h3>
                        <form onSubmit={handleAddAddress} className="space-y-4 max-h-[80vh] overflow-y-auto pr-2 custom-scrollbar">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Label (e.g. Home, Office)</label>
                                    <input
                                        type="text"
                                        value={newAddress.label}
                                        onChange={(e) => setNewAddress({ ...newAddress, label: e.target.value })}
                                        className="input"
                                        placeholder="Home"
                                        required
                                    />
                                </div>
                                <div className="flex flex-col justify-end pb-2">
                                    <button
                                        type="button"
                                        onClick={handleLocationDetect}
                                        disabled={locStatus === "requesting"}
                                        className="btn-secondary py-3 text-xs flex items-center justify-center gap-2"
                                    >
                                        {locStatus === "requesting" ? "⌛ Detecting..." : "📍 Detect Location"}
                                    </button>
                                </div>
                            </div>

                            <div className="mb-4">
                                <label className="label">Exact Location</label>
                                <LocationPickerMap
                                    lat={newAddress.lat}
                                    lng={newAddress.lng}
                                    onChange={(lat, lng) => {
                                        setNewAddress(prev => ({ ...prev, lat, lng }));
                                        reverseGeocode(lat, lng);
                                    }}
                                />
                            </div>

                            <div>
                                <label className="label">Full Address (Auto-filled or Manual)</label>
                                <textarea
                                    value={newAddress.full_address}
                                    onChange={(e) => setNewAddress({ ...newAddress, full_address: e.target.value })}
                                    className="input min-h-[80px] text-xs leading-relaxed"
                                    placeholder="Flat No, Building, Area, City..."
                                    required
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    id="is_default"
                                    checked={newAddress.is_default}
                                    onChange={(e) => setNewAddress({ ...newAddress, is_default: e.target.checked })}
                                    className="w-4 h-4 accent-yellow-500"
                                />
                                <label htmlFor="is_default" className="text-sm font-bold text-gray-700">Set as default address</label>
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button type="button" onClick={() => {
                                    setShowAddressModal(false);
                                    setNewAddress({ label: "", full_address: "", is_default: false, lat: 26.9124, lng: 75.7873 });
                                }} className="btn-ghost flex-1">
                                    Cancel
                                </button>
                                <button type="submit" className="btn-primary flex-1">
                                    Add Address
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
