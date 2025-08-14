import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

const GrantApplications = () => {
    const navigate = useNavigate()
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState('all')

    // Mock data for grant applications
    const grants = [
        {
            id: 1,
            name: 'Educational Technology Grant',
            funder: 'Department of Education',
            status: 'In Progress',
            deadline: '2025-09-15',
            amount: '$50,000',
            lastModified: '2025-08-10',
            progress: 75
        },
        {
            id: 2,
            name: 'Community Health Initiative',
            funder: 'Health Foundation',
            status: 'Under Review',
            deadline: '2025-08-30',
            amount: '$75,000',
            lastModified: '2025-08-05',
            progress: 100
        },
        {
            id: 3,
            name: 'Environmental Sustainability Project',
            funder: 'EPA Grant Program',
            status: 'Draft',
            deadline: '2025-10-01',
            amount: '$100,000',
            lastModified: '2025-08-12',
            progress: 25
        },
        {
            id: 4,
            name: 'Youth Development Program',
            funder: 'Community Foundation',
            status: 'Approved',
            deadline: '2025-07-15',
            amount: '$30,000',
            lastModified: '2025-07-20',
            progress: 100
        },
        {
            id: 5,
            name: 'Senior Services Expansion',
            funder: 'State Aging Office',
            status: 'Rejected',
            deadline: '2025-06-30',
            amount: '$45,000',
            lastModified: '2025-07-01',
            progress: 100
        }
    ]

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
            case 'Rejected':
                return 'badge-error'
            default:
                return 'badge-secondary'
        }
    }

    const getProgressColor = (progress) => {
        if (progress >= 75) return 'bg-success-500'
        if (progress >= 50) return 'bg-warning-500'
        return 'bg-primary-500'
    }

    const filteredGrants = grants.filter(grant => {
        const matchesSearch = grant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            grant.funder.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === 'all' || grant.status.toLowerCase().replace(' ', '') === statusFilter
        return matchesSearch && matchesStatus
    })

    const statusCounts = {
        all: grants.length,
        draft: grants.filter(g => g.status === 'Draft').length,
        inprogress: grants.filter(g => g.status === 'In Progress').length,
        underreview: grants.filter(g => g.status === 'Under Review').length,
        approved: grants.filter(g => g.status === 'Approved').length,
        rejected: grants.filter(g => g.status === 'Rejected').length
    }

    const handleNewApplication = () => {
        // Generate a new ID for the grant (in a real app, this would be handled by the backend)
        const newGrantId = 'new-' + Date.now()
        // Navigate to the grant workspace with new application parameter
        navigate(`/grants/${newGrantId}?new=true`)
    }

    return (
        <div>
            {/* Page header */}
            <div className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Grant Applications</h1>
                    <p className="mt-2 text-gray-600">
                        Manage and track your grant applications
                    </p>
                </div>
                <button onClick={handleNewApplication} className="btn-primary">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    New Application
                </button>
            </div>

            {/* Stats overview */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
                <div className="card text-center">
                    <p className="text-2xl font-bold text-gray-900">{statusCounts.all}</p>
                    <p className="text-sm text-gray-600">Total</p>
                </div>
                <div className="card text-center">
                    <p className="text-2xl font-bold text-gray-600">{statusCounts.draft}</p>
                    <p className="text-sm text-gray-600">Draft</p>
                </div>
                <div className="card text-center">
                    <p className="text-2xl font-bold text-warning-600">{statusCounts.inprogress}</p>
                    <p className="text-sm text-gray-600">In Progress</p>
                </div>
                <div className="card text-center">
                    <p className="text-2xl font-bold text-primary-600">{statusCounts.underreview}</p>
                    <p className="text-sm text-gray-600">Under Review</p>
                </div>
                <div className="card text-center">
                    <p className="text-2xl font-bold text-success-600">{statusCounts.approved}</p>
                    <p className="text-sm text-gray-600">Approved</p>
                </div>
                <div className="card text-center">
                    <p className="text-2xl font-bold text-error-600">{statusCounts.rejected}</p>
                    <p className="text-sm text-gray-600">Rejected</p>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-6">
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                        <label htmlFor="search" className="label">
                            Search Applications
                        </label>
                        <input
                            type="text"
                            id="search"
                            placeholder="Search by grant name or funder..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="input"
                        />
                    </div>
                    <div className="sm:w-48">
                        <label htmlFor="status" className="label">
                            Filter by Status
                        </label>
                        <select
                            id="status"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="input"
                        >
                            <option value="all">All Status</option>
                            <option value="draft">Draft</option>
                            <option value="inprogress">In Progress</option>
                            <option value="underreview">Under Review</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Grants list */}
            <div className="space-y-4">
                {filteredGrants.length === 0 ? (
                    <div className="card text-center py-12">
                        <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No grant applications found</h3>
                        <p className="text-gray-600 mb-4">Try adjusting your search criteria or create a new application.</p>
                        <button onClick={handleNewApplication} className="btn-primary">
                            Create New Application
                        </button>
                    </div>
                ) : (
                    filteredGrants.map((grant) => (
                        <div key={grant.id} className="card hover:shadow-md transition-shadow">
                            <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="text-lg font-semibold text-gray-900 truncate">
                                            {grant.name}
                                        </h3>
                                        <span className={`badge ${getStatusBadge(grant.status)} ml-4 flex-shrink-0`}>
                                            {grant.status}
                                        </span>
                                    </div>

                                    <p className="text-gray-600 mb-3">{grant.funder}</p>

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                        <div>
                                            <p className="text-sm text-gray-500">Amount</p>
                                            <p className="font-medium text-gray-900">{grant.amount}</p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-gray-500">Deadline</p>
                                            <p className="font-medium text-gray-900">
                                                {new Date(grant.deadline).toLocaleDateString()}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-sm text-gray-500">Last Modified</p>
                                            <p className="font-medium text-gray-900">
                                                {new Date(grant.lastModified).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Progress bar */}
                                    <div className="mb-4">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-sm text-gray-500">Progress</span>
                                            <span className="text-sm font-medium text-gray-900">{grant.progress}%</span>
                                        </div>
                                        <div className="progress-bar">
                                            <div
                                                className={`progress-fill ${getProgressColor(grant.progress)}`}
                                                style={{ width: `${grant.progress}%` }}
                                            />
                                        </div>
                                    </div>

                                    <div className="flex justify-end space-x-3">
                                        {grant.status === 'Draft' && (
                                            <button className="btn-outline text-sm">
                                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                </svg>
                                                Edit
                                            </button>
                                        )}
                                        <Link
                                            to={`/grants/${grant.id}`}
                                            className="btn-primary text-sm"
                                        >
                                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                            View
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

export default GrantApplications
