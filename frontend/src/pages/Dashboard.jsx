import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { grantsAPI, analyticsAPI } from '../services/api'

const Dashboard = () => {
    const [stats, setStats] = useState([
        {
            name: 'Total Grants',
            value: '0',
            description: 'Active grant applications'
        },
        {
            name: 'In Progress',
            value: '0',
            description: 'Currently being worked on'
        },
        {
            name: 'Submitted',
            value: '0',
            description: 'Awaiting review'
        },
        {
            name: 'Approved',
            value: '0',
            description: 'Successfully funded'
        }
    ])

    const [recentGrants, setRecentGrants] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    // Load dashboard data on component mount
    useEffect(() => {
        loadDashboardData()
    }, [])

    const loadDashboardData = async () => {
        try {
            setLoading(true)
            setError('')

            // Load dashboard statistics
            const statsResponse = await analyticsAPI.getDashboardStats()
            if (statsResponse.data) {
                setStats([
                    {
                        name: 'Total Grants',
                        value: statsResponse.data.totalGrants?.toString() || '0',
                        description: 'Active grant applications'
                    },
                    {
                        name: 'In Progress',
                        value: statsResponse.data.inProgress?.toString() || '0',
                        description: 'Currently being worked on'
                    },
                    {
                        name: 'Submitted',
                        value: statsResponse.data.submitted?.toString() || '0',
                        description: 'Awaiting review'
                    },
                    {
                        name: 'Approved',
                        value: statsResponse.data.approved?.toString() || '0',
                        description: 'Successfully funded'
                    }
                ])
            }

            // Load recent grants
            const grantsResponse = await grantsAPI.getAll({ limit: 5, sortBy: 'lastModified' })
            if (grantsResponse.data) {
                setRecentGrants(grantsResponse.data)
            }

        } catch (error) {
            console.error('Failed to load dashboard data:', error)
            setError('Failed to load dashboard data')

            // Use fallback mock data for development
            setRecentGrants([
                {
                    id: 1,
                    name: 'Educational Technology Grant',
                    status: 'In Progress',
                    deadline: '2025-09-15',
                    amount: '$50,000'
                },
                {
                    id: 2,
                    name: 'Community Health Initiative',
                    status: 'Under Review',
                    deadline: '2025-08-30',
                    amount: '$75,000'
                },
                {
                    id: 3,
                    name: 'Environmental Sustainability Project',
                    status: 'Draft',
                    deadline: '2025-10-01',
                    amount: '$100,000'
                }
            ])
        } finally {
            setLoading(false)
        }
    }

    const getStatusBadge = (status) => {
        switch (status) {
            case 'In Progress':
                return 'badge-warning'
            case 'Under Review':
                return 'badge-primary'
            case 'Draft':
                return 'badge-secondary'
            case 'Approved':
                return 'badge-success'
            default:
                return 'badge-secondary'
        }
    }

    return (
        <div>
            {/* Page header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="mt-2 text-gray-600">
                    Welcome back! Here's an overview of your grant applications.
                </p>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {stats.map((stat) => (
                    <div key={stat.name} className="card">
                        <h3 className="text-sm font-medium text-gray-500">{stat.name}</h3>
                        <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
                        <p className="mt-1 text-sm text-gray-600">{stat.description}</p>
                    </div>
                ))}
            </div>

            {/* Quick actions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <Link to="/grants" className="card hover:shadow-md transition-shadow">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-lg font-medium text-gray-900">New Grant Application</h3>
                            <p className="text-sm text-gray-600">Start a new grant application</p>
                        </div>
                    </div>
                </Link>

                <Link to="/organization" className="card hover:shadow-md transition-shadow">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-lg font-medium text-gray-900">Organization Profile</h3>
                            <p className="text-sm text-gray-600">Update your organization details</p>
                        </div>
                    </div>
                </Link>

                <Link to="/settings" className="card hover:shadow-md transition-shadow">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                        <div className="ml-4">
                            <h3 className="text-lg font-medium text-gray-900">Settings</h3>
                            <p className="text-sm text-gray-600">Configure platform settings</p>
                        </div>
                    </div>
                </Link>
            </div>

            {/* Recent grants */}
            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">Recent Grant Applications</h2>
                    <p className="card-description">Your most recent grant applications and their status</p>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead>
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Grant Name
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Deadline
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Amount
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {recentGrants.map((grant) => (
                                <tr key={grant.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">{grant.name}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`badge ${getStatusBadge(grant.status)}`}>
                                            {grant.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(grant.deadline).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {grant.amount}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <Link
                                            to={`/grants/${grant.id}`}
                                            className="text-primary-600 hover:text-primary-900"
                                        >
                                            View
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="mt-4 flex justify-end">
                    <Link to="/grants" className="btn-primary">
                        View All Grants
                    </Link>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
