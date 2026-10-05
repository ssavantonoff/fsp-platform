import type { Metadata } from "next";
import { AuthProvider, Header } from "@/components/auth";
import "./globals.css";

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
      <body>
        <AuthProvider>
          <Header />
          <main>{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
