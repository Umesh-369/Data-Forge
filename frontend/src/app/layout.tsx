import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DataForge AI | Conversational AutoML & Data Wrangling',
  description: 'AI-assisted data wrangling platform with whitelisted pandas operation sandbox, instant diff previews, and AutoML model training.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-dark-900 text-gray-100">{children}</body>
    </html>
  );
}
