import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GroundStack",
  description: "Grounded answers for developer communities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
