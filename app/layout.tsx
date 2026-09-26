import type { Metadata } from "next";
import "./globals.css";
import "./soullink.css";

export const metadata: Metadata = {
  title: "Soul Link · John & Eddie",
  description: "Gemeinsame Live-Teams, verbundene Fänge und dauerhafte Partnersperren.",
  referrer: "no-referrer",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className="antialiased">{children}</body>
    </html>
  );
}
