import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "GroundStack | Source-backed technical answers",
    template: "%s | GroundStack",
  },
  description:
    "Ask questions against approved technical documentation and inspect the sources supporting every answer.",
  applicationName: "GroundStack",
  openGraph: {
    title: "GroundStack | Source-backed technical answers",
    description:
      "Ask questions against approved technical documentation and inspect the sources supporting every answer.",
    type: "website",
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
