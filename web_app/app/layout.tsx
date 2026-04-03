import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Sidebar from '@/components/Sidebar'
import { Suspense } from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TaskFlow',
  description: 'AI-powered task management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex">
          <Suspense fallback={<div className="w-64 bg-gray-900 h-screen" />}>
            <Sidebar />
          </Suspense>
          <main className="flex-1 min-h-screen bg-gray-50 ml-64">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
