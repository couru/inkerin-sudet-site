import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;

  return {
    title: "Inkerin Sudet — детский хоккейный клуб",
    description:
      "Ингерманландские волки — детский хоккейный клуб в Санкт-Петербурге для игроков от 5 до 14 лет.",
    authors: [{ name: "Ян Ковру" }],
    creator: "Ян Ковру",
    publisher: "Ян Ковру",
    icons: {
      icon: "/brand/crest-blue.png",
      shortcut: "/brand/crest-blue.png",
    },
    openGraph: {
      title: "Inkerin Sudet — расти в стае",
      description: "Детский хоккейный клуб в Санкт-Петербурге.",
      type: "website",
      locale: "ru_RU",
      images: [{ url: `${origin}/og.png`, width: 1536, height: 1024 }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Inkerin Sudet — расти в стае",
      description: "Детский хоккейный клуб в Санкт-Петербурге.",
      images: [`${origin}/og.png`],
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
