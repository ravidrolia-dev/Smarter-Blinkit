
import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
    timeout: 60000, // Increased to 60s for heavy AI fallback chains
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("sb_token");
        if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Auto-logout on 401
api.interceptors.response.use(
    (r) => r,
    (error) => {
        if (error.response?.status === 401 && typeof window !== "undefined") {
            localStorage.removeItem("sb_token");
            localStorage.removeItem("sb_user");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

// ===== Auth =====
export const authApi = {
    register: (data: any) => api.post("/auth/register", data),
    login: (email: string, password: string) => api.post("/auth/login", { email, password }),
    faceLogin: (image_b64: string) => api.post("/auth/face-login", { image_b64 }),
    enrollFace: (user_id: string, image_b64: string) => api.post("/auth/enroll-face", { user_id, image_b64 }),
    listSellers: (params?: any) => api.get("/auth/sellers", { params }),
};

// ===== Products =====
export const productsApi = {
    list: (params?: any) => api.get("/products", { params }),
    get: (id: string, params?: any) => api.get(`/products/${id}`, { params }),
    create: (data: any) => api.post("/products", data),
    update: (id: string, data: any) => api.patch(`/products/${id}`, data),
    delete: (id: string) => api.delete(`/products/${id}`),
    recommendations: (id: string) => api.get(`/products/${id}/recommendations`),
    generateBarcode: () => api.post("/inventory/generate-barcode"),
};

// ===== Search =====
export const searchApi = {
    search: (q: string, lat?: number, lng?: number) =>
        api.get("/search", { params: { q, lat, lng } }),
};

// ===== Orders =====
export const ordersApi = {
    create: (data: any) => api.post("/orders/create", data),
    pay: (order_id: string, card_name: string, card_last4: string) =>
        api.post("/orders/pay", { order_id, card_name, card_last4 }),
    myOrders: () => api.get("/orders/my-orders"),
    estimate: (data: any) => api.post("/orders/estimate", data),
};

// ===== Inventory =====
export const inventoryApi = {
    lookupBarcode: (barcode: string) => api.get(`/inventory/barcode/${barcode}`),
    scanBarcode: (image_base64: string) => api.post("/inventory/scan", { image_base64 }, { timeout: 30000 }),
    updateStock: (product_id: string, quantity_delta: number, note?: string) =>
        api.patch(`/inventory/${product_id}/stock`, { quantity_delta, note }),
    myProducts: () => api.get("/inventory/my-products"),
    getBarcodeImage: (barcode: string) => api.get(`/inventory/barcode-image/${barcode}`),
};

// ===== Agent =====
export const agentApi = {
    recipe: (meal: string, lat?: number, lng?: number) =>
        api.get("/agent/recipe", { params: { meal, lat, lng } }),
};

// ===== Analytics =====
export const analyticsApi = {
    topProducts: () => api.get("/analytics/top-products"),
    topShops: () => api.get("/analytics/top-shops"),
    categoryBreakdown: () => api.get("/analytics/category-breakdown"),
    recentOrders: (params?: any) => api.get("/analytics/recent-orders", { params }),
    moneyMap: () => api.get("/analytics/money-map"),
};
