"use client";
import { useState, useCallback, useEffect } from "react";

export type LocationStatus = "idle" | "requesting" | "granted" | "denied" | "unavailable";

export interface LocationState {
    status: LocationStatus;
    location: { lat: number; lng: number } | null;
    errorMessage: string | null;
    requestLocation: () => void;
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

    const requestLocation = useCallback(() => {
        if (typeof window === "undefined" || !navigator.geolocation) {
            setStatus("unavailable");
            setErrorMessage("Geolocation is not supported by your browser.");
            return;
        }

        setStatus("requesting");
        setErrorMessage(null);

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                setLocation(loc);
                setStatus("granted");
                // Cache for this session so we don't re-prompt on every page navigation
                sessionStorage.setItem(SESSION_KEY, JSON.stringify(loc));
            },
            (err) => {
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        setStatus("denied");
                        setErrorMessage("Location permission denied. Enable it in browser settings to see nearby stores.");
                        break;
                    case err.POSITION_UNAVAILABLE:
                        setStatus("unavailable");
                        setErrorMessage("Location unavailable. Please try again or enter your location manually.");
                        break;
                    case err.TIMEOUT:
                        setStatus("unavailable");
                        setErrorMessage("Location request timed out. Please try again.");
                        break;
                    default:
                        setStatus("unavailable");
                        setErrorMessage("An unknown error occurred while fetching location.");
                }
            },
            {
                enableHighAccuracy: false,
                timeout: 8000,
                maximumAge: 5 * 60 * 1000, // 5 minutes
            }
        );
    }, []);

    return { status, location, errorMessage, requestLocation };
}
