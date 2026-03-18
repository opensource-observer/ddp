import type { Metadata } from 'next';
import Sidebar from '@/components/Sidebar';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'Developer Data Portal',
    template: '%s | Developer Data Portal',
  },
  description: 'Open-source developer analytics across Ethereum and beyond',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 flex flex-col overflow-y-auto bg-white pt-14 md:pt-0">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
