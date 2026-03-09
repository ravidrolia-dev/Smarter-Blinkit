import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { Providers } from "./Providers";

export const metadata: Metadata = {
  title: "Smarter BlinkIt — Smart Marketplace",
  description: "AI-powered grocery marketplace with intent search, recipe agent, and instant delivery from local shops.",
  keywords: "grocery, delivery, AI shopping, local shops, marketplace",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body suppressHydrationWarning>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: {
                background: "#fff",
                color: "#111827",
                borderRadius: "12px",
                boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
                fontFamily: "Inter, sans-serif",
                fontWeight: 500,
                fontSize: "14px",
                padding: "12px 16px",
              },
              success: {
                iconTheme: { primary: "#FFD000", secondary: "#111827" },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
