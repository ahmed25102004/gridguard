import type { Metadata } from "next";
import "./globals.css";
import { DashboardProvider } from "../components/layout/DashboardContext";
import { DashboardShell } from "../components/layout/DashboardShell";

export const metadata: Metadata = {
  title: "GridGuard - High-Voltage Grid Asset Intelligence",
  description: "Enterprise electrical asset inventory, PostGIS spatial radar, and predictive telemetry diagnostics.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-blue-600 selection:text-white">
        <DashboardProvider>
          <DashboardShell>{children}</DashboardShell>
        </DashboardProvider>
      </body>
    </html>
  );
}
