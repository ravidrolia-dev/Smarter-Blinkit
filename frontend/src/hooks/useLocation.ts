"use client";
import { useState, useCallback, useEffect } from "react";

export type LocationStatus = "idle" | "requesting" | "granted" | "denied" | "unavailable";

export interface LocationState {
    status: LocationStatus;
    location: { lat: number; lng: number } | null;
    errorMessage: string | null;
    requestLocation: () => void;
    refreshLocation: () => void;
    setManualLocation: (lat: number, lng: number) => void;
}

const SESSION_KEY = "sb_user_location";

export function useLocation(): LocationState {
    const [status, setStatus] = useState<LocationStatus>("idle");
    const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // On mount: restore cached location from sessionStorage without re-prompting
    useEffect(() => {
        if (typeof window === "undefined") return;
        const cached = sessionStorage.getItem(SESSION_KEY);
        if (cached) {
            try {
                const parsed = JSON.parse(cached);
                if (parsed?.lat && parsed?.lng) {
                    setLocation(parsed);
                    setStatus("granted");
                }
            } catch {
                sessionStorage.removeItem(SESSION_KEY);
            }
        }
    }, []);

    const setManualLocation = useCallback((lat: number, lng: number) => {
        const loc = { lat, lng };
        setLocation(loc);
        setStatus("granted");
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(loc));
    }, []);

    const requestLocation = useCallback((force: boolean = false) => {
        if (typeof window === "undefined" || !navigator.geolocation) {
            setStatus("unavailable");
            setErrorMessage("Geolocation is not supported by your browser.");
            return;
        }

        setStatus("requesting");
        setErrorMessage(null);

        if (force) sessionStorage.removeItem(SESSION_KEY);

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                setLocation(loc);
                setStatus("granted");
                sessionStorage.setItem(SESSION_KEY, JSON.stringify(loc));
            },
            (err) => {
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        setStatus("denied");
                        setErrorMessage("Location permission denied.");
                        break;
                    case err.POSITION_UNAVAILABLE:
                        setStatus("unavailable");
                        setErrorMessage("Position unavailable.");
                        break;
                    case err.TIMEOUT:
                        setStatus("unavailable");
                        setErrorMessage("Request timed out.");
                        break;
                    default:
                        setStatus("unavailable");
                        setErrorMessage("Unknown error.");
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: force ? 0 : 30000,
            }
        );
    }, []);

    const refreshLocation = useCallback(() => requestLocation(true), [requestLocation]);

    return { status, location, errorMessage, requestLocation: () => requestLocation(false), refreshLocation, setManualLocation };
}
