"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

interface User {
    id: string;
    email: string;
    name: string;
    role: "buyer" | "seller";
    phone?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string, user: User) => void;
    logout: () => void;
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
        <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextType {
    const ctx = useContext(AuthContext);
    // Return a safe no-op context when rendered outside AuthProvider (e.g. during SSR prerender)
    if (!ctx) return { user: null, token: null, login: () => { }, logout: () => { }, isLoading: true };
    return ctx;
}
