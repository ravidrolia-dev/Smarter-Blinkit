"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import toast from "react-hot-toast";

export default function RegisterPage() {
    const [step, setStep] = useState(1); // 1=info, 2=face
    const [role, setRole] = useState<"buyer" | "seller">("buyer");
    const [form, setForm] = useState({ name: "", email: "", password: "", phone: "" });
    const [loading, setLoading] = useState(false);
    const [faceB64, setFaceB64] = useState<string | null>(null);
    const [cameraOn, setCameraOn] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const { login } = useAuth();

    // Auto-start camera when reaching Face ID step
    useEffect(() => {
        if (step === 2 && !cameraOn && !faceB64) {
            startCamera();
        }
    }, [step]);

    const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }));

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            streamRef.current = stream;
            if (videoRef.current) videoRef.current.srcObject = stream;
            setCameraOn(true);
        } catch { toast.error("Camera access denied"); }
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;
        const canvas = canvasRef.current;
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);
        setFaceB64(canvas.toDataURL("image/jpeg", 0.8));
        streamRef.current?.getTracks().forEach((t) => t.stop());
        setCameraOn(false);
        toast.success("Photo captured! ✅");
    };

    const handleRegister = async () => {
        setLoading(true);
        try {
            const res = await authApi.register({
                ...form,
                role,
                face_image_b64: faceB64 || undefined,
            });
            login(res.data.access_token, res.data.user);
            toast.success(`Account created! Welcome, ${res.data.user.name} 🎉`);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Registration failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex hero">
            <div className="hidden lg:flex flex-col justify-center w-1/2 p-12">
                <span className="text-3xl mb-6">⚡</span>
                <h1 className="text-5xl font-black text-gray-900 mb-4">Join the<br />revolution.</h1>
                <p className="text-gray-700 text-lg">Whether you buy groceries or sell them, Smarter BlinkIt has you covered.</p>
                <div className="mt-8 space-y-3">
                    {[
                        { icon: "🤖", t: "AI fills your cart from a meal description" },
                        { icon: "📍", t: "Nearest shops deliver directly to you" },
                        { icon: "🔒", t: "Face ID login for instant access" },
                        { icon: "📊", t: "Sellers get real-time inventory insights" },
                    ].map((f) => (
                        <div key={f.t} className="flex items-center gap-3 bg-white/60 backdrop-blur rounded-xl px-4 py-3">
                            <span className="text-xl">{f.icon}</span>
                            <span className="text-sm font-medium text-gray-800">{f.t}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="flex-1 flex items-center justify-center p-6">
                <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 animate-fade-up">
                    {/* Progress */}
                    <div className="flex gap-2 mb-6">
                        {[1, 2].map((s) => (
                            <div key={s} className={`flex-1 h-1.5 rounded-full transition-all ${step >= s ? "bg-yellow-400" : "bg-gray-100"}`} />
                        ))}
                    </div>

                    {step === 1 ? (
                        <>
                            <h2 className="text-2xl font-black mb-1">Create Account</h2>
                            <p className="text-sm text-gray-500 mb-6">Fill in your details to get started</p>

                            <div className="flex gap-2 p-1 bg-gray-100 rounded-xl mb-5">
                                {(["buyer", "seller"] as const).map((r) => (
                                    <button key={r} onClick={() => setRole(r)}
                                        className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all capitalize ${role === r ? "bg-white shadow text-gray-900" : "text-gray-500"
                                            }`}>
                                        {r === "buyer" ? "🛒 Buyer" : "🏪 Seller"}
                                    </button>
                                ))}
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Full Name</label>
                                    <input className="input" placeholder="Ravi Drolia" value={form.name} onChange={(e) => set("name", e.target.value)} />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Email</label>
                                    <input className="input" type="email" placeholder="ravi@example.com" value={form.email} onChange={(e) => set("email", e.target.value)} />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Phone (optional)</label>
                                    <input className="input" placeholder="+91 98765 43210" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-gray-500 mb-1 block uppercase tracking-wide">Password</label>
                                    <input className="input" type="password" placeholder="Min 8 characters" value={form.password} onChange={(e) => set("password", e.target.value)} />
                                </div>
                                <button className="btn-primary w-full" onClick={() => setStep(2)}
                                    disabled={!form.name || !form.email || !form.password}>
                                    Next: Face ID Setup →
                                </button>
                            </div>
                        </>
                    ) : (
                        <>
                            <h2 className="text-2xl font-black mb-1">Face ID Setup</h2>
                            <p className="text-sm text-gray-500 mb-6">Optional — lets you login with just your face later</p>

                            <div className="relative rounded-2xl overflow-hidden bg-gray-900 aspect-video mb-4">
                                <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
                                {faceB64 && (
                                    <img src={faceB64} alt="captured" className="absolute inset-0 w-full h-full object-cover" />
                                )}
                                {!cameraOn && !faceB64 && (
                                    <div className="absolute inset-0 flex items-center justify-center text-white/60 text-sm flex-col gap-2">
                                        <span className="text-4xl">📷</span>
                                        <span>Camera not active</span>
                                    </div>
                                )}
                                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                    <div className="w-36 h-44 rounded-full border-4 border-yellow-400 border-dashed opacity-60" />
                                </div>
                            </div>
                            <canvas ref={canvasRef} className="hidden" />

                            <div className="flex gap-2 mb-4">
                                {!cameraOn && !faceB64
                                    ? <button onClick={startCamera} className="btn-secondary flex-1">📷 Open Camera</button>
                                    : cameraOn
                                        ? <button onClick={capturePhoto} className="btn-primary flex-1">📸 Capture</button>
                                        : <button onClick={() => { setFaceB64(null); startCamera(); }} className="btn-secondary flex-1">🔄 Retake</button>
                                }
                            </div>

                            <div className="flex gap-2">
                                <button onClick={() => { setFaceB64(null); handleRegister(); }} className="btn-ghost flex-1 justify-center border border-gray-200 rounded-xl" disabled={loading}>
                                    Skip for now
                                </button>
                                <button onClick={handleRegister} disabled={loading} className="btn-primary flex-1">
                                    {loading ? "Creating…" : "🎉 Create Account"}
                                </button>
                            </div>
                        </>
                    )}

                    <div className="divider mt-6"><span>Already have an account?</span></div>
                    <Link href="/login" className="btn-secondary w-full text-center block mt-3">Sign In</Link>
                </div>
            </div>
        </div>
    );
}
