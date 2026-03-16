import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexoraAI Realtime Assistant",
  description: "Futuristic realtime personal AI assistant interface for NexoraAI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
