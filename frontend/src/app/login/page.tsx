"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import toast from "react-hot-toast";

export default function LoginPage() {
    const [tab, setTab] = useState<"password" | "face">("password");
    const [role, setRole] = useState<"buyer" | "seller">("buyer");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [faceCapturing, setFaceCapturing] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const { login } = useAuth();
    const router = useRouter();

    const handlePasswordLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const res = await authApi.login(email, password);
            login(res.data.access_token, res.data.user);
            toast.success(`Welcome back, ${res.data.user.name}! 👋`);
        } catch (err: any) {
            let detail = err.response?.data?.detail || "Login failed";
            if (typeof detail !== "string") detail = JSON.stringify(detail);
            toast.error(detail);
        } finally {
            setLoading(false);
        }
    };

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
            streamRef.current = stream;
            if (videoRef.current) videoRef.current.srcObject = stream;
            setFaceCapturing(true);
        } catch {
            toast.error("Camera access denied. Please allow camera.");
        }
    };

    const stopCamera = () => {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        setFaceCapturing(false);
    };

    const handleFaceLogin = async () => {
        if (!videoRef.current || !canvasRef.current) return;
        setLoading(true);

        try {
            const canvas = canvasRef.current;
            const ctx = canvas.getContext("2d");
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;

            // Capture 1 frame for fast processing
            ctx?.drawImage(videoRef.current, 0, 0);
            const frame = canvas.toDataURL("image/jpeg", 0.8);

            stopCamera();
            const res = await authApi.faceLogin(frame);
            login(res.data.access_token, res.data.user);

            toast.success(`Face recognized! Welcome ${res.data.user.name} 😊`);
        } catch (err: any) {
            let detail = err.response?.data?.detail || "Face not recognized";
            if (typeof detail !== "string") detail = JSON.stringify(detail);
            toast.error(detail);
            // If it failed, restart camera so they can try again
            if (!faceCapturing) startCamera();
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => () => stopCamera(), []);

    return (
        <div className="min-h-screen flex hero">
            {/* Left Panel */}
            <div className="hidden lg:flex flex-col justify-between w-1/2 p-12">
                <div className="flex items-center gap-3">
                    <span className="text-3xl">⚡</span>
                    <h1 className="text-2xl font-black text-gray-900">Smarter<span className="text-white">BlinkIt</span></h1>
                </div>
                <div>
                    <h2 className="text-5xl font-black text-gray-900 leading-tight mb-4">
                        Shop smarter,<br />not harder.
                    </h2>
                    <p className="text-gray-700 text-lg max-w-sm">
                        Tell us what you want to cook, and we'll fill your cart from the nearest shops — in seconds.
                    </p>
                    <div className="mt-8 flex gap-4">
                        {["🤖 AI Shopping", "📦 Instant Delivery", "🏪 Local Shops"].map((f) => (
                            <span key={f} className="bg-white/60 backdrop-blur px-3 py-1.5 rounded-full text-sm font-semibold text-gray-800">
                                {f}
                            </span>
                        ))}
                    </div>
                </div>
                <p className="text-sm text-gray-600">© 2024 Smarter BlinkIt</p>
            </div>

            {/* Right Panel — Login Form */}
            <div className="flex-1 flex items-center justify-center p-6">
                <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 animate-fade-up">
                    <h2 className="text-2xl font-black mb-1">Sign In</h2>
                    <p className="text-sm text-gray-500 mb-6">Welcome back! Choose your role to continue.</p>

                    {/* Role Selector */}
                    <div className="flex gap-2 p-1 bg-gray-100 rounded-xl mb-6">
                        {(["buyer", "seller"] as const).map((r) => (
                            <button key={r} onClick={() => setRole(r)} suppressHydrationWarning
                                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all capitalize ${role === r ? "bg-white shadow text-gray-900" : "text-gray-500"
                                    }`}>
                                {r === "buyer" ? "🛒 Buyer" : "🏪 Seller"}
                            </button>
                        ))}
                    </div>

                    {/* Method Tabs */}
                    <div className="flex gap-2 mb-6">
                        <button onClick={() => setTab("password")}
                            className={`flex-1 py-2 text-sm font-semibold rounded-xl border-2 transition-all ${tab === "password" ? "border-yellow-400 bg-yellow-50 text-gray-900" : "border-gray-200 text-gray-500"
                                }`}>
                            🔑 Password
                        </button>
                        <button onClick={() => { setTab("face"); if (!faceCapturing) startCamera(); }}
                            className={`flex-1 py-2 text-sm font-semibold rounded-xl border-2 transition-all ${tab === "face" ? "border-yellow-400 bg-yellow-50 text-gray-900" : "border-gray-200 text-gray-500"
                                }`}>
                            😊 Face ID
                        </button>
                    </div>

                    {tab === "password" ? (
                        <form onSubmit={handlePasswordLogin} className="space-y-4">
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Email</label>
                                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                                    className="input" placeholder="you@example.com" required />
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Password</label>
                                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                                    className="input" placeholder="••••••••" required />
                            </div>
                            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
                                {loading ? "Signing in…" : "Sign In →"}
                            </button>
                        </form>
                    ) : (
                        <div className="space-y-4">
                            <div className="relative rounded-2xl overflow-hidden bg-gray-900 aspect-video">
                                <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
                                {!faceCapturing && (
                                    <div className="absolute inset-0 flex items-center justify-center text-white text-sm">
                                        Camera not active
                                    </div>
                                )}
                                {/* Face guide overlay */}
                                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                    <div className="w-40 h-48 rounded-full border-4 border-yellow-400 border-dashed opacity-70 animate-pulse" />
                                </div>
                            </div>
                            <canvas ref={canvasRef} className="hidden" />
                            <div className="flex gap-2">
                                {!faceCapturing
                                    ? <button onClick={startCamera} className="btn-secondary flex-1">📷 Start Camera</button>
                                    : <button onClick={handleFaceLogin} disabled={loading} className="btn-primary flex-1">
                                        {loading ? "Verifying…" : "😊 Recognize Me"}
                                    </button>
                                }
                            </div>
                        </div>
                    )}

                    <div className="divider mt-6"><span>New here?</span></div>
                    <Link href="/register" className="btn-secondary w-full text-center block mt-3">
                        Create Account
                    </Link>
                </div>
            </div>
        </div>
    );
}
