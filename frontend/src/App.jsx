import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'

// Components
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import OrganizationProfile from './pages/OrganizationProfile'
import GrantApplications from './pages/GrantApplications'
import GrantWorkspace from './pages/GrantWorkspace'
import Settings from './pages/Settings'

// Utility function for page transitions
const pageVariants = {
    initial: {
        opacity: 0,
        y: 20,
    },
    in: {
        opacity: 1,
        y: 0,
    },
    out: {
        opacity: 0,
        y: -20,
    },
}

const pageTransition = {
    type: 'tween',
    ease: 'anticipate',
    duration: 0.4,
}

function App() {
    return (
        <div className="min-h-screen bg-gray-50">
            <Layout>
                <Routes>
                    <Route
                        path="/"
                        element={
                            <motion.div
                                initial="initial"
                                animate="in"
                                exit="out"
                                variants={pageVariants}
                                transition={pageTransition}
                            >
                                <Dashboard />
                            </motion.div>
                        }
                    />
                    <Route
                        path="/dashboard"
                        element={<Navigate to="/" replace />}
                    />
                    <Route
                        path="/organization"
                        element={
                            <motion.div
                                initial="initial"
                                animate="in"
                                exit="out"
                                variants={pageVariants}
                                transition={pageTransition}
                            >
                                <OrganizationProfile />
                            </motion.div>
                        }
                    />
                    <Route
                        path="/grants"
                        element={
                            <motion.div
                                initial="initial"
                                animate="in"
                                exit="out"
                                variants={pageVariants}
                                transition={pageTransition}
                            >
                                <GrantApplications />
                            </motion.div>
                        }
                    />
                    <Route
                        path="/grants/:grantId"
                        element={
                            <motion.div
                                initial="initial"
                                animate="in"
                                exit="out"
                                variants={pageVariants}
                                transition={pageTransition}
                            >
                                <GrantWorkspace />
                            </motion.div>
                        }
                    />
                    <Route
                        path="/settings"
                        element={
                            <motion.div
                                initial="initial"
                                animate="in"
                                exit="out"
                                variants={pageVariants}
                                transition={pageTransition}
                            >
                                <Settings />
                            </motion.div>
                        }
                    />
                    {/* Catch all route - redirect to dashboard */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Layout>
        </div>
    )
}

export default App
