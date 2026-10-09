import type { Metadata } from "next";
import localFont from "next/font/local";
import { AuthProvider, Header } from "@/components/auth";
import "./globals.css";

const interfaceFont = localFont({
  src: [
    { path: "../fonts/JetBrainsMono-Regular.ttf", weight: "400", style: "normal" },
    { path: "../fonts/JetBrainsMono-Bold.ttf", weight: "700", style: "normal" },
  ],
  variable: "--font-interface",
  display: "swap",
});
const accentFont = localFont({
  src: "../fonts/TDAText.ttf",
  weight: "400",
  variable: "--font-accent",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: "FSP Platform",
  description: "Профили IT-кандидатов и работодателей",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className={`${interfaceFont.variable} ${accentFont.variable}`}>
        <a className="skip-link" href="#main-content">К содержимому</a>
        <AuthProvider>
          <Header />
          <main id="main-content">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
