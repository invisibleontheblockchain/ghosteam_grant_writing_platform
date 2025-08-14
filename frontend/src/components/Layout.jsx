import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'

// Icons (using basic SVG icons)
const DashboardIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v14l-5-3-5 3V5z" />
    </svg>
)

const OrganizationIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
)

const GrantsIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
)

const SettingsIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
)

const MenuIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
)

const CloseIcon = () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
)

const Layout = ({ children }) => {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const location = useLocation()

    const navigation = [
        {
            name: 'Dashboard',
            href: '/',
            icon: DashboardIcon,
            current: location.pathname === '/' || location.pathname === '/dashboard'
        },
        {
            name: 'Organization',
            href: '/organization',
            icon: OrganizationIcon,
            current: location.pathname === '/organization'
        },
        {
            name: 'Grant Applications',
            href: '/grants',
            icon: GrantsIcon,
            current: location.pathname === '/grants' || location.pathname.startsWith('/grants/')
        },
        {
            name: 'Settings',
            href: '/settings',
            icon: SettingsIcon,
            current: location.pathname === '/settings'
        }
    ]

    return (
        <div className="h-screen flex overflow-hidden bg-gray-50">
            {/* Mobile sidebar */}
            {sidebarOpen && (
                <div className="fixed inset-0 flex z-40 md:hidden">
                    <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
                    <motion.div
                        initial={{ x: -256 }}
                        animate={{ x: 0 }}
                        exit={{ x: -256 }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        className="relative flex-1 flex flex-col max-w-xs w-full bg-white"
                    >
                        <div className="absolute top-0 right-0 -mr-12 pt-2">
                            <button
                                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                                onClick={() => setSidebarOpen(false)}
                            >
                                <CloseIcon />
                            </button>
                        </div>
                        <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                            <div className="flex-shrink-0 flex items-center px-4">
                                <h1 className="text-xl font-bold text-gray-900">Grant Platform</h1>
                            </div>
                            <nav className="mt-5 px-2 space-y-1">
                                {navigation.map((item) => (
                                    <Link
                                        key={item.name}
                                        to={item.href}
                                        className={`nav-item ${item.current ? 'active' : ''}`}
                                        onClick={() => setSidebarOpen(false)}
                                    >
                                        <item.icon />
                                        {item.name}
                                    </Link>
                                ))}
                            </nav>
                        </div>
                    </motion.div>
                </div>
            )}

            {/* Desktop sidebar */}
            <div className="hidden md:flex md:flex-shrink-0">
                <div className="flex flex-col w-64">
                    <div className="sidebar">
                        <div className="flex items-center h-16 px-4 border-b border-gray-200">
                            <h1 className="text-xl font-bold text-gray-900">Grant Platform</h1>
                        </div>
                        <nav className="mt-5 px-2 space-y-1">
                            {navigation.map((item) => (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={`nav-item ${item.current ? 'active' : ''}`}
                                >
                                    <item.icon />
                                    {item.name}
                                </Link>
                            ))}
                        </nav>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="flex flex-col w-0 flex-1 overflow-hidden">
                {/* Mobile header */}
                <div className="md:hidden pl-1 pt-1 sm:pl-3 sm:pt-3">
                    <button
                        className="h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
                        onClick={() => setSidebarOpen(true)}
                    >
                        <MenuIcon />
                    </button>
                </div>

                {/* Main content area */}
                <main className="flex-1 relative overflow-y-auto focus:outline-none">
                    <div className="py-6">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
                            {children}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    )
}

export default Layout
