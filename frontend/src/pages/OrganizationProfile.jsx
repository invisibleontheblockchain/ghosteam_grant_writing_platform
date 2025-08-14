import React, { useState, useEffect } from 'react'
import { organizationAPI } from '../services/api'

const OrganizationProfile = () => {
    const [formData, setFormData] = useState({
        name: 'Sober AF Entertainment',
        type: 'nonprofit',
        address: '123 Main Street',
        city: 'Colorado Springs',
        state: 'CO',
        zipCode: '80902',
        phone: '(303) 888-9019',
        email: 'duke@soberafe.com',
        website: 'https://www.soberafe.com',
        taxId: '83-0685262',
        mission: 'To provide educational resources and support to underserved communities through sober entertainment and activities.',
        yearEstablished: '2018',
        annualBudget: '485000',
        staffSize: '8',
        contactPerson: 'Daniel Rumely',
        contactTitle: 'Executive Director',
        contactPhone: '(303) 888-9019',
        contactEmail: 'duke@soberafe.com'
    })

    const [isEditing, setIsEditing] = useState(false)
    const [originalData, setOriginalData] = useState({})
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [successMessage, setSuccessMessage] = useState('')

    // Load organization profile on component mount
    useEffect(() => {
        loadOrganizationProfile()
    }, [])

    const loadOrganizationProfile = async () => {
        try {
            setLoading(true)
            const response = await organizationAPI.getProfile()
            const profileData = response.data
            setFormData(profileData)
            setOriginalData(profileData)
        } catch (error) {
            console.error('Failed to load organization profile:', error)
            // Use default SAFE data if API fails (fallback for development)
            setOriginalData(formData)
        } finally {
            setLoading(false)
        }
    }

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: value
        }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            setLoading(true)
            setError('')
            setSuccessMessage('')

            await organizationAPI.updateProfile(formData)
            setOriginalData(formData)
            setIsEditing(false)
            setSuccessMessage('Organization profile updated successfully!')

            // Clear success message after 3 seconds
            setTimeout(() => setSuccessMessage(''), 3000)
        } catch (error) {
            console.error('Failed to save organization profile:', error)
            setError('Failed to save organization profile. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const handleCancel = () => {
        setFormData(originalData)
        setIsEditing(false)
        setError('')
        setSuccessMessage('')
    }

    return (
        <div>
            {/* Page header */}
            <div className="mb-8">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Organization Profile</h1>
                        <p className="mt-2 text-gray-600">
                            Manage your organization's information for grant applications.
                        </p>
                    </div>
                    {!isEditing && (
                        <button
                            onClick={() => setIsEditing(true)}
                            disabled={loading}
                            className="btn-primary disabled:opacity-50"
                        >
                            {loading ? 'Loading...' : 'Edit Profile'}
                        </button>
                    )}
                </div>

                {/* Status messages */}
                {error && (
                    <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                        <div className="flex">
                            <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <p className="text-red-800">{error}</p>
                        </div>
                    </div>
                )}

                {successMessage && (
                    <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
                        <div className="flex">
                            <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <p className="text-green-800">{successMessage}</p>
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
                {/* Basic Information */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Basic Information</h2>
                        <p className="card-description">
                            Core details about your organization
                        </p>
                    </div>

                    <div className="space-y-6">
                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="name" className="label">
                                    Organization Name *
                                </label>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="type" className="label">
                                    Organization Type *
                                </label>
                                <select
                                    id="type"
                                    name="type"
                                    value={formData.type}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                >
                                    <option value="nonprofit">Non-Profit</option>
                                    <option value="forprofit">For-Profit</option>
                                    <option value="government">Government</option>
                                    <option value="educational">Educational Institution</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="mission" className="label">
                                Mission Statement *
                            </label>
                            <textarea
                                id="mission"
                                name="mission"
                                value={formData.mission}
                                onChange={handleInputChange}
                                disabled={!isEditing}
                                rows={4}
                                className="textarea"
                                placeholder="Describe your organization's mission and purpose..."
                                required
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="yearEstablished" className="label">
                                    Year Established
                                </label>
                                <input
                                    type="number"
                                    id="yearEstablished"
                                    name="yearEstablished"
                                    value={formData.yearEstablished}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    min="1800"
                                    max={new Date().getFullYear()}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="taxId" className="label">
                                    Tax ID / EIN
                                </label>
                                <input
                                    type="text"
                                    id="taxId"
                                    name="taxId"
                                    value={formData.taxId}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    placeholder="XX-XXXXXXX"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Contact Information */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Contact Information</h2>
                        <p className="card-description">
                            Address and contact details
                        </p>
                    </div>

                    <div className="space-y-6">
                        <div className="form-group">
                            <label htmlFor="address" className="label">
                                Street Address *
                            </label>
                            <input
                                type="text"
                                id="address"
                                name="address"
                                value={formData.address}
                                onChange={handleInputChange}
                                disabled={!isEditing}
                                className="input"
                                required
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="city" className="label">
                                    City *
                                </label>
                                <input
                                    type="text"
                                    id="city"
                                    name="city"
                                    value={formData.city}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="state" className="label">
                                    State *
                                </label>
                                <input
                                    type="text"
                                    id="state"
                                    name="state"
                                    value={formData.state}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    maxLength={2}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="zipCode" className="label">
                                    ZIP Code *
                                </label>
                                <input
                                    type="text"
                                    id="zipCode"
                                    name="zipCode"
                                    value={formData.zipCode}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="phone" className="label">
                                    Phone Number *
                                </label>
                                <input
                                    type="tel"
                                    id="phone"
                                    name="phone"
                                    value={formData.phone}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="email" className="label">
                                    Email Address *
                                </label>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="website" className="label">
                                Website
                            </label>
                            <input
                                type="url"
                                id="website"
                                name="website"
                                value={formData.website}
                                onChange={handleInputChange}
                                disabled={!isEditing}
                                className="input"
                                placeholder="https://www.example.org"
                            />
                        </div>
                    </div>
                </div>

                {/* Organization Details */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Organization Details</h2>
                        <p className="card-description">
                            Additional information about your organization
                        </p>
                    </div>

                    <div className="space-y-6">
                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="annualBudget" className="label">
                                    Annual Budget ($)
                                </label>
                                <input
                                    type="number"
                                    id="annualBudget"
                                    name="annualBudget"
                                    value={formData.annualBudget}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    min="0"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="staffSize" className="label">
                                    Number of Staff Members
                                </label>
                                <input
                                    type="number"
                                    id="staffSize"
                                    name="staffSize"
                                    value={formData.staffSize}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    min="0"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Primary Contact */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Primary Contact</h2>
                        <p className="card-description">
                            Main contact person for grant applications
                        </p>
                    </div>

                    <div className="space-y-6">
                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="contactPerson" className="label">
                                    Contact Person *
                                </label>
                                <input
                                    type="text"
                                    id="contactPerson"
                                    name="contactPerson"
                                    value={formData.contactPerson}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="contactTitle" className="label">
                                    Title *
                                </label>
                                <input
                                    type="text"
                                    id="contactTitle"
                                    name="contactTitle"
                                    value={formData.contactTitle}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="contactPhone" className="label">
                                    Contact Phone *
                                </label>
                                <input
                                    type="tel"
                                    id="contactPhone"
                                    name="contactPhone"
                                    value={formData.contactPhone}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="contactEmail" className="label">
                                    Contact Email *
                                </label>
                                <input
                                    type="email"
                                    id="contactEmail"
                                    name="contactEmail"
                                    value={formData.contactEmail}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className="input"
                                    required
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action buttons */}
                {isEditing && (
                    <div className="flex justify-end space-x-4">
                        <button
                            type="button"
                            onClick={handleCancel}
                            disabled={loading}
                            className="btn-outline disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary disabled:opacity-50"
                        >
                            {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                )}
            </form>
        </div>
    )
}

export default OrganizationProfile
