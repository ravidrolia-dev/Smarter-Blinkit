"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

interface User {
    id: string;
    email: string;
    name: string;
    role: "buyer" | "seller";
    phone?: string;
    profile_image?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string, user: User) => void;
    logout: () => void;
    refreshUser: () => Promise<void>;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const storedToken = localStorage.getItem("sb_token");
        const storedUser = localStorage.getItem("sb_user");
        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
        setIsLoading(false);
    }, []);

    const refreshUser = async () => {
        const storedToken = localStorage.getItem("sb_token");
        if (!storedToken) return;

        try {
            const { userApi } = await import("./api");
            const res = await userApi.getProfile();
            if (res.data) {
                const updatedUser = res.data;
                localStorage.setItem("sb_user", JSON.stringify(updatedUser));
                setUser(updatedUser);
            }
        } catch (err) {
            console.error("Failed to refresh user:", err);
        }
    };

    const login = (token: string, user: User) => {
        localStorage.setItem("sb_token", token);
        localStorage.setItem("sb_user", JSON.stringify(user));
        setToken(token);
        setUser(user);
        router.push(user.role === "buyer" ? "/buyer" : "/seller");
    };

    const logout = () => {
        localStorage.removeItem("sb_token");
        localStorage.removeItem("sb_user");
        setToken(null);
        setUser(null);
        router.push("/login");
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, refreshUser, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextType {
    const ctx = useContext(AuthContext);
    if (!ctx) return {
        user: null,
        token: null,
        login: () => { },
        logout: () => { },
        refreshUser: async () => { },
        isLoading: true
    };
    return ctx;
}
