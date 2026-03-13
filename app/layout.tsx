import './globals.css'
import Link from 'next/link'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'Auralytics',
  description: 'Auralytics UI',
  icons: {
    icon: '/favicon.png',
  },
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <header className="sticky top-0 z-40 border-b bg-white">
          <div className="mx-auto max-w-7xl px-4 py-3 flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2 font-semibold text-gray-900">
              <img src="/favicon.png" alt="Auralytics Logo" className="h-6 w-6 rounded" />
              <span>Auralytics</span>
            </Link>
            <nav className="ml-auto flex items-center gap-3 text-sm">
              <Link className="px-3 py-1 rounded-md hover:bg-gray-100" href="/chatbot">Support Bot</Link>
              <Link className="px-3 py-1 rounded-md hover:bg-gray-100" href="/sales">Pitch Assistant</Link>
              <Link className="px-3 py-1 rounded-md hover:bg-gray-100" href="/support">Agent Console</Link>
              <Link className="px-3 py-1 rounded-md hover:bg-gray-100" href="/dashboard">Recommendations</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-4">{children}</main>
      </body>
    </html>
  )
}
