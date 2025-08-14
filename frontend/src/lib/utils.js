import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs) {
    return twMerge(clsx(inputs))
}

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes) {
    if (!bytes) return '0 Bytes'

    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Get file type from filename
 */
export function getFileType(filename) {
    if (!filename) return 'unknown'

    const extension = filename.split('.').pop()?.toLowerCase()

    const fileTypes = {
        // Documents
        pdf: 'pdf',
        doc: 'doc',
        docx: 'doc',

        // Spreadsheets
        xls: 'xls',
        xlsx: 'xls',
        csv: 'xls',

        // Text
        txt: 'txt',
        rtf: 'txt',

        // Images
        jpg: 'image',
        jpeg: 'image',
        png: 'image',
        gif: 'image',

        // Other
        zip: 'archive',
        rar: 'archive',
    }

    return fileTypes[extension] || 'default'
}

/**
 * Format date in a readable format
 */
export function formatDate(date) {
    if (!date) return ''

    const d = new Date(date)
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    })
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date) {
    if (!date) return ''

    const now = new Date()
    const past = new Date(date)
    const diffInSeconds = Math.floor((now - past) / 1000)

    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`
    if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`
    return `${Math.floor(diffInSeconds / 31536000)} years ago`
}

/**
 * Generate a unique ID
 */
export function generateId() {
    return Math.random().toString(36).substr(2, 9)
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
    let timeout
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout)
            func(...args)
        }
        clearTimeout(timeout)
        timeout = setTimeout(later, wait)
    }
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text, maxLength = 100) {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength).trim() + '...'
}

/**
 * Validate email format
 */
export function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
}

/**
 * Format currency
 */
export function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency,
    }).format(amount)
}

/**
 * Get grant status color
 */
export function getGrantStatusColor(status) {
    const statusColors = {
        draft: 'bg-gray-100 text-gray-800',
        'in-progress': 'bg-warning-100 text-warning-800',
        'under-review': 'bg-primary-100 text-primary-800',
        submitted: 'bg-success-100 text-success-800',
        approved: 'bg-success-100 text-success-800',
        rejected: 'bg-error-100 text-error-800',
        'needs-revision': 'bg-warning-100 text-warning-800',
    }

    return statusColors[status] || statusColors.draft
}

/**
 * Calculate completion percentage
 */
export function calculateCompletionPercentage(sections) {
    if (!sections || sections.length === 0) return 0

    const completedSections = sections.filter(section => section.completed)
    return Math.round((completedSections.length / sections.length) * 100)
}

/**
 * Validate required fields
 */
export function validateRequiredFields(data, requiredFields) {
    const errors = {}

    requiredFields.forEach(field => {
        if (!data[field] || (typeof data[field] === 'string' && data[field].trim() === '')) {
            errors[field] = 'This field is required'
        }
    })

    return {
        isValid: Object.keys(errors).length === 0,
        errors,
    }
}

/**
 * Handle async errors
 */
export function handleAsyncError(error) {
    console.error('Async error:', error)

    if (error.response) {
        // Server responded with error status
        return error.response.data?.message || 'Server error occurred'
    } else if (error.request) {
        // Request made but no response
        return 'Network error - please check your connection'
    } else {
        // Other error
        return error.message || 'An unexpected error occurred'
    }
}

/**
 * Deep clone object
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj
    if (obj instanceof Date) return new Date(obj)
    if (obj instanceof Array) return obj.map(item => deepClone(item))
    if (typeof obj === 'object') {
        const clonedObj = {}
        Object.keys(obj).forEach(key => {
            clonedObj[key] = deepClone(obj[key])
        })
        return clonedObj
    }
}

/**
 * Export data as JSON file
 */
export function exportAsJSON(data, filename = 'export.json') {
    const jsonString = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
}

/**
 * Check if user has permission
 */
export function hasPermission(userRole, requiredPermission) {
    const rolePermissions = {
        admin: ['read', 'write', 'delete', 'manage'],
        editor: ['read', 'write'],
        viewer: ['read'],
    }

    const permissions = rolePermissions[userRole] || []
    return permissions.includes(requiredPermission)
}
