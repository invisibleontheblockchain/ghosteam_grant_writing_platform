import React, { useState } from 'react'

const Settings = () => {
    const [activeTab, setActiveTab] = useState('general')
    const [isLoading, setIsLoading] = useState(false)
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    })
    const [settings, setSettings] = useState({
        notifications: {
            email: true,
            deadlineReminders: true,
            statusUpdates: false,
            weeklyDigest: true
        },
        preferences: {
            theme: 'light',
            timezone: 'America/Denver',
            dateFormat: 'MM/DD/YYYY',
            currency: 'USD'
        },
        account: {
            name: 'John Doe',
            email: 'john.doe@example.org',
            phone: '(303) 555-0123',
            role: 'Administrator'
        }
    })

    const tabs = [
        { id: 'general', name: 'General', icon: '⚙️' },
        { id: 'notifications', name: 'Notifications', icon: '🔔' },
        { id: 'account', name: 'Account', icon: '👤' },
        { id: 'security', name: 'Security', icon: '🔒' }
    ]

    const handleSettingChange = (category, key, value) => {
        setSettings(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [key]: value
            }
        }))
    }

    const handlePasswordUpdate = async () => {
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            alert('New passwords do not match!')
            return
        }

        if (passwordData.newPassword.length < 8) {
            alert('Password must be at least 8 characters long!')
            return
        }

        setIsLoading(true)
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000))
            alert('Password updated successfully!')
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
        } catch (error) {
            alert('Failed to update password. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleSaveSettings = async () => {
        setIsLoading(true)
        try {
            // Simulate API call to save settings
            await new Promise(resolve => setTimeout(resolve, 1000))
            alert('Settings saved successfully!')
        } catch (error) {
            alert('Failed to save settings. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleDeleteAccount = async () => {
        if (!showDeleteConfirm) {
            setShowDeleteConfirm(true)
            return
        }

        setIsLoading(true)
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000))
            alert('Account deletion initiated. You will receive a confirmation email.')
            setShowDeleteConfirm(false)
        } catch (error) {
            alert('Failed to delete account. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleEnable2FA = async () => {
        setIsLoading(true)
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000))
            alert('2FA setup initiated. Please check your authenticator app.')
        } catch (error) {
            alert('Failed to enable 2FA. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleRevokeSession = async (sessionId) => {
        setIsLoading(true)
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 500))
            alert('Session revoked successfully!')
        } catch (error) {
            alert('Failed to revoke session. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const renderGeneral = () => (
        <div className="space-y-6">
            <div className="card">
                <h3 className="card-title">Application Preferences</h3>
                <p className="card-description">Customize how the application behaves</p>

                <div className="mt-6 space-y-6">
                    <div className="form-group">
                        <label htmlFor="theme" className="label">
                            Theme
                        </label>
                        <select
                            id="theme"
                            value={settings.preferences.theme}
                            onChange={(e) => handleSettingChange('preferences', 'theme', e.target.value)}
                            className="input"
                        >
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                            <option value="auto">Auto (System)</option>
                        </select>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="timezone" className="label">
                                Timezone
                            </label>
                            <select
                                id="timezone"
                                value={settings.preferences.timezone}
                                onChange={(e) => handleSettingChange('preferences', 'timezone', e.target.value)}
                                className="input"
                            >
                                <option value="America/New_York">Eastern Time</option>
                                <option value="America/Chicago">Central Time</option>
                                <option value="America/Denver">Mountain Time</option>
                                <option value="America/Los_Angeles">Pacific Time</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="dateFormat" className="label">
                                Date Format
                            </label>
                            <select
                                id="dateFormat"
                                value={settings.preferences.dateFormat}
                                onChange={(e) => handleSettingChange('preferences', 'dateFormat', e.target.value)}
                                className="input"
                            >
                                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="currency" className="label">
                            Default Currency
                        </label>
                        <select
                            id="currency"
                            value={settings.preferences.currency}
                            onChange={(e) => handleSettingChange('preferences', 'currency', e.target.value)}
                            className="input"
                        >
                            <option value="USD">USD - US Dollar</option>
                            <option value="EUR">EUR - Euro</option>
                            <option value="GBP">GBP - British Pound</option>
                            <option value="CAD">CAD - Canadian Dollar</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="card">
                <h3 className="card-title">Data & Privacy</h3>
                <p className="card-description">Manage your data and privacy settings</p>

                <div className="mt-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium text-gray-900">Analytics</p>
                            <p className="text-sm text-gray-500">Help improve the platform by sharing usage analytics</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                className="sr-only peer"
                                defaultChecked
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                        </label>
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium text-gray-900">Auto-save</p>
                            <p className="text-sm text-gray-500">Automatically save your work as you type</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                className="sr-only peer"
                                defaultChecked
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                        </label>
                    </div>
                </div>
            </div>
        </div>
    )

    const renderNotifications = () => (
        <div className="card">
            <h3 className="card-title">Notification Preferences</h3>
            <p className="card-description">Choose what notifications you want to receive</p>

            <div className="mt-6 space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium text-gray-900">Email Notifications</p>
                        <p className="text-sm text-gray-500">Receive notifications via email</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={settings.notifications.email}
                            onChange={(e) => handleSettingChange('notifications', 'email', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium text-gray-900">Deadline Reminders</p>
                        <p className="text-sm text-gray-500">Get notified about upcoming grant deadlines</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={settings.notifications.deadlineReminders}
                            onChange={(e) => handleSettingChange('notifications', 'deadlineReminders', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium text-gray-900">Status Updates</p>
                        <p className="text-sm text-gray-500">Notifications when grant applications status changes</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={settings.notifications.statusUpdates}
                            onChange={(e) => handleSettingChange('notifications', 'statusUpdates', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                </div>

                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium text-gray-900">Weekly Digest</p>
                        <p className="text-sm text-gray-500">Summary of your grant activities each week</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={settings.notifications.weeklyDigest}
                            onChange={(e) => handleSettingChange('notifications', 'weeklyDigest', e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                </div>
            </div>
        </div>
    )

    const renderAccount = () => (
        <div className="space-y-6">
            <div className="card">
                <h3 className="card-title">Account Information</h3>
                <p className="card-description">Update your personal account details</p>

                <div className="mt-6 space-y-6">
                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="accountName" className="label">
                                Full Name
                            </label>
                            <input
                                type="text"
                                id="accountName"
                                value={settings.account.name}
                                onChange={(e) => handleSettingChange('account', 'name', e.target.value)}
                                className="input"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="accountRole" className="label">
                                Role
                            </label>
                            <input
                                type="text"
                                id="accountRole"
                                value={settings.account.role}
                                disabled
                                className="input bg-gray-50"
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="accountEmail" className="label">
                                Email Address
                            </label>
                            <input
                                type="email"
                                id="accountEmail"
                                value={settings.account.email}
                                onChange={(e) => handleSettingChange('account', 'email', e.target.value)}
                                className="input"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="accountPhone" className="label">
                                Phone Number
                            </label>
                            <input
                                type="tel"
                                id="accountPhone"
                                value={settings.account.phone}
                                onChange={(e) => handleSettingChange('account', 'phone', e.target.value)}
                                className="input"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div className="card">
                <h3 className="card-title">Danger Zone</h3>
                <p className="card-description">Irreversible and destructive actions</p>

                <div className="mt-6 space-y-4">
                    <div className="border border-error-200 rounded-lg p-4">
                        <h4 className="font-medium text-error-900 mb-2">Delete Account</h4>
                        <p className="text-sm text-error-700 mb-4">
                            Once you delete your account, there is no going back. This will permanently delete your
                            account and remove all associated data.
                        </p>
                        <button
                            onClick={handleDeleteAccount}
                            disabled={isLoading}
                            className="btn bg-error-600 text-white hover:bg-error-700 focus:ring-error-500 disabled:opacity-50"
                        >
                            {isLoading ? 'Processing...' : showDeleteConfirm ? 'Confirm Delete' : 'Delete Account'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )

    const renderSecurity = () => (
        <div className="space-y-6">
            <div className="card">
                <h3 className="card-title">Password</h3>
                <p className="card-description">Update your account password</p>

                <div className="mt-6 space-y-6">
                    <div className="form-group">
                        <label htmlFor="currentPassword" className="label">
                            Current Password
                        </label>
                        <input
                            type="password"
                            id="currentPassword"
                            value={passwordData.currentPassword}
                            onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                            className="input"
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="newPassword" className="label">
                                New Password
                            </label>
                            <input
                                type="password"
                                id="newPassword"
                                value={passwordData.newPassword}
                                onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                                className="input"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="confirmPassword" className="label">
                                Confirm New Password
                            </label>
                            <input
                                type="password"
                                id="confirmPassword"
                                value={passwordData.confirmPassword}
                                onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                                className="input"
                            />
                        </div>
                    </div>

                    <button
                        onClick={handlePasswordUpdate}
                        disabled={isLoading}
                        className="btn-primary disabled:opacity-50"
                    >
                        {isLoading ? 'Updating...' : 'Update Password'}
                    </button>
                </div>
            </div>

            <div className="card">
                <h3 className="card-title">Two-Factor Authentication</h3>
                <p className="card-description">Add an extra layer of security to your account</p>

                <div className="mt-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium text-gray-900">Two-Factor Authentication</p>
                            <p className="text-sm text-gray-500">Secure your account with 2FA</p>
                        </div>
                        <button
                            onClick={handleEnable2FA}
                            disabled={isLoading}
                            className="btn-outline disabled:opacity-50"
                        >
                            {isLoading ? 'Setting up...' : 'Enable 2FA'}
                        </button>
                    </div>
                </div>
            </div>

            <div className="card">
                <h3 className="card-title">Active Sessions</h3>
                <p className="card-description">Manage your active login sessions</p>

                <div className="mt-6 space-y-4">
                    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">Current Session</p>
                                <p className="text-sm text-gray-500">Chrome on Windows • Last active now</p>
                            </div>
                        </div>
                        <span className="badge badge-success">Current</span>
                    </div>

                    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M10 2L3 9v6a2 2 0 002 2h10a2 2 0 002-2V9l-7-7z" />
                                </svg>
                            </div>
                            <div>
                                <p className="font-medium text-gray-900">Mobile Device</p>
                                <p className="text-sm text-gray-500">Safari on iPhone • Last active 2 hours ago</p>
                            </div>
                        </div>
                        <button
                            onClick={() => handleRevokeSession('mobile-session')}
                            disabled={isLoading}
                            className="text-error-600 hover:text-error-900 text-sm font-medium disabled:opacity-50"
                        >
                            {isLoading ? 'Revoking...' : 'Revoke'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )

    const renderContent = () => {
        switch (activeTab) {
            case 'general':
                return renderGeneral()
            case 'notifications':
                return renderNotifications()
            case 'account':
                return renderAccount()
            case 'security':
                return renderSecurity()
            default:
                return renderGeneral()
        }
    }

    return (
        <div>
            {/* Page header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
                <p className="mt-2 text-gray-600">
                    Manage your account settings and preferences
                </p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Sidebar */}
                <div className="lg:w-64 flex-shrink-0">
                    <nav className="space-y-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === tab.id
                                    ? 'bg-primary-50 text-primary-600 border border-primary-200'
                                    : 'text-gray-700 hover:bg-gray-100'
                                    }`}
                            >
                                <span className="mr-3">{tab.icon}</span>
                                {tab.name}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Main content */}
                <div className="flex-1">
                    {renderContent()}

                    {/* Save button */}
                    <div className="mt-8 flex justify-end">
                        <button
                            onClick={handleSaveSettings}
                            disabled={isLoading}
                            className="btn-primary disabled:opacity-50"
                        >
                            {isLoading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Settings
