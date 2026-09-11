import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://groundstack.example.com"),
  title: {
    default: "GroundStack",
    template: "%s | GroundStack",
  },
  description: "Grounded answers for developer communities",
  applicationName: "GroundStack",
  openGraph: {
    title: "GroundStack",
    description:
      "A portfolio-ready document-grounded AI support app with citations.",
    type: "website",
  },
  alternates: {
    canonical: "/",
  },
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
