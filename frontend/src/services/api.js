import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

// Create axios instance with base configuration
const api = axios.create({
    baseURL: API_BASE_URL ? `${API_BASE_URL}/api` : '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('authToken')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('authToken')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// Organization API
export const organizationAPI = {
    // Get organization profile
    getProfile: () => api.get('/organization/profile'),

    // Update organization profile
    updateProfile: (data) => api.put('/organization/profile', data),

    // Upload organization documents
    uploadDocument: (file, type) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('type', type)

        return api.post('/organization/documents', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Get organization documents
    getDocuments: () => api.get('/organization/documents'),

    // Delete organization document
    deleteDocument: (documentId) => api.delete(`/organization/documents/${documentId}`),
}

// Grants API
export const grantsAPI = {
    // Get all grants
    getAll: (params = {}) => api.get('/grants', { params }),

    // Get single grant
    getById: (id) => api.get(`/grants/${id}`),

    // Create new grant
    create: (data) => api.post('/grants', data),

    // Update grant
    update: (id, data) => api.put(`/grants/${id}`, data),

    // Delete grant
    delete: (id) => api.delete(`/grants/${id}`),

    // Submit grant application
    submit: (id) => api.post(`/grants/${id}/submit`),

    // Generate grant content using AI
    generateContent: (id, sectionType, prompt) => api.post(`/grants/${id}/generate`, {
        sectionType,
        prompt,
    }),

    // Get grant suggestions
    getSuggestions: (id, section) => api.get(`/grants/${id}/suggestions/${section}`),

    // Save grant section
    saveSection: (id, section, data) => api.put(`/grants/${id}/sections/${section}`, data),

    // Upload grant documents
    uploadDocuments: (id, files) => {
        const formData = new FormData()
        files.forEach((file, index) => {
            formData.append(`files[${index}]`, file)
        })

        return api.post(`/grants/${id}/documents`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Get grant documents
    getDocuments: (id) => api.get(`/grants/${id}/documents`),

    // Delete grant document
    deleteDocument: (id, documentId) => api.delete(`/grants/${id}/documents/${documentId}`),

    // Duplicate grant
    duplicate: (id) => api.post(`/grants/${id}/duplicate`),

    // Export grant as PDF
    exportPDF: (id) => api.get(`/grants/${id}/export/pdf`, {
        responseType: 'blob',
    }),

    // Get grant analytics
    getAnalytics: (id) => api.get(`/grants/${id}/analytics`),
}

// File upload API
export const fileAPI = {
    // Upload single file
    uploadSingle: (file, category = 'general') => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('category', category)

        return api.post('/files/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Upload multiple files
    uploadMultiple: (files, category = 'general') => {
        const formData = new FormData()
        files.forEach((file, index) => {
            formData.append(`files[${index}]`, file)
        })
        formData.append('category', category)

        return api.post('/files/upload-multiple', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Get file details
    getFile: (fileId) => api.get(`/files/${fileId}`),

    // Delete file
    deleteFile: (fileId) => api.delete(`/files/${fileId}`),

    // Download file
    downloadFile: (fileId) => api.get(`/files/${fileId}/download`, {
        responseType: 'blob',
    }),
}

// AI Writing Assistant API
export const aiAPI = {
    // Generate text content
    generateText: (prompt, context = {}) => api.post('/ai/generate-text', {
        prompt,
        context,
    }),

    // Improve existing text
    improveText: (text, instructions = '') => api.post('/ai/improve-text', {
        text,
        instructions,
    }),

    // Check grammar and style
    checkGrammar: (text) => api.post('/ai/check-grammar', { text }),

    // Get writing suggestions
    getSuggestions: (text, sectionType) => api.post('/ai/suggestions', {
        text,
        sectionType,
    }),

    // Generate outline
    generateOutline: (grantType, requirements) => api.post('/ai/generate-outline', {
        grantType,
        requirements,
    }),

    // Analyze grant requirements
    analyzeRequirements: (rfpText) => api.post('/ai/analyze-requirements', {
        rfpText,
    }),

    // Generate budget
    generateBudget: (projectDescription, duration, requestedAmount) => api.post('/ai/generate-budget', {
        projectDescription,
        duration,
        requestedAmount,
    }),
}

// Templates API
export const templatesAPI = {
    // Get all templates
    getAll: (category = null) => api.get('/templates', {
        params: category ? { category } : {},
    }),

    // Get template by ID
    getById: (id) => api.get(`/templates/${id}`),

    // Create new template
    create: (data) => api.post('/templates', data),

    // Update template
    update: (id, data) => api.put(`/templates/${id}`, data),

    // Delete template
    delete: (id) => api.delete(`/templates/${id}`),

    // Use template for grant
    useTemplate: (templateId, grantId) => api.post(`/templates/${templateId}/use`, {
        grantId,
    }),
}

// Analytics API
export const analyticsAPI = {
    // Get dashboard stats
    getDashboardStats: () => api.get('/analytics/dashboard'),

    // Get grant statistics
    getGrantStats: (dateRange = '30d') => api.get('/analytics/grants', {
        params: { dateRange },
    }),

    // Get success metrics
    getSuccessMetrics: () => api.get('/analytics/success-metrics'),

    // Get productivity metrics
    getProductivityMetrics: () => api.get('/analytics/productivity'),

    // Track user activity
    trackActivity: (action, metadata = {}) => api.post('/analytics/track', {
        action,
        metadata,
        timestamp: new Date().toISOString(),
    }),
}

// Search API
export const searchAPI = {
    // Global search
    globalSearch: (query, filters = {}) => api.get('/search', {
        params: { query, ...filters },
    }),

    // Search grants
    searchGrants: (query, filters = {}) => api.get('/search/grants', {
        params: { query, ...filters },
    }),

    // Search templates
    searchTemplates: (query, category = null) => api.get('/search/templates', {
        params: { query, category },
    }),

    // Search documents
    searchDocuments: (query, grantId = null) => api.get('/search/documents', {
        params: { query, grantId },
    }),
}

// Settings API
export const settingsAPI = {
    // Get user settings
    getUserSettings: () => api.get('/settings/user'),

    // Update user settings
    updateUserSettings: (settings) => api.put('/settings/user', settings),

    // Get organization settings
    getOrgSettings: () => api.get('/settings/organization'),

    // Update organization settings
    updateOrgSettings: (settings) => api.put('/settings/organization', settings),

    // Get notification preferences
    getNotificationSettings: () => api.get('/settings/notifications'),

    // Update notification preferences
    updateNotificationSettings: (settings) => api.put('/settings/notifications', settings),
}

// Enhanced Document Processing API
export const documentProcessingAPI = {
    // Analyze document using enhanced processing
    analyzeDocument: (file, grantId, documentType = null) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('grant_id', grantId)
        if (documentType) formData.append('document_type', documentType)

        return api.post('/documents/analyze', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Get dynamic tabs for a grant
    getDynamicTabs: (grantId) => api.get(`/grants/${grantId}/dynamic-tabs`),

    // Query grant context from vector database
    queryContext: (grantId, query, contextType = 'all') => api.post(`/grants/${grantId}/context-query`, {
        query,
        context_type: contextType,
    }),

    // Search documents in vector database
    searchDocuments: (query, documentType = 'grant_documents', grantId = null, limit = 5) => api.post('/documents/search', {
        query,
        document_type: documentType,
        grant_id: grantId,
        limit,
    }),

    // Get document summary
    getDocumentSummary: (documentType, grantId = null) => api.get(`/documents/summary/${documentType}`, {
        params: grantId ? { grant_id: grantId } : {},
    }),

    // Get all document categories
    getDocumentCategories: (grantId = null) => api.get('/documents/categories', {
        params: grantId ? { grant_id: grantId } : {},
    }),
}

// Enhanced Tab Management API
export const tabManagementAPI = {
    // Create a new tab
    createTab: (grantId, tabName, tabType = 'other') => api.post(`/grants/${grantId}/tabs`, {
        tab_name: tabName,
        tab_type: tabType,
    }),

    // Update an existing tab
    updateTab: (grantId, tabId, updates) => api.put(`/grants/${grantId}/tabs/${tabId}`, updates),

    // Delete a tab
    deleteTab: (grantId, tabId) => api.delete(`/grants/${grantId}/tabs/${tabId}`),

    // Create a new section within a tab
    createSection: (grantId, tabId, sectionTitle, questionText = '') => api.post(`/grants/${grantId}/tabs/${tabId}/sections`, {
        section_title: sectionTitle,
        question_text: questionText,
    }),

    // Update a section
    updateSection: (grantId, tabId, sectionId, updates) => api.put(`/grants/${grantId}/tabs/${tabId}/sections/${sectionId}`, updates),

    // Delete a section
    deleteSection: (grantId, tabId, sectionId) => api.delete(`/grants/${grantId}/tabs/${tabId}/sections/${sectionId}`),
}

// Enhanced AI Regeneration API
export const regenerationAPI = {
    // Regenerate content with user notes
    regenerateContent: (grantId, type, targetId = null, userNotes = '') => api.post(`/grants/${grantId}/regenerate`, {
        type, // 'section', 'tab', or 'full'
        target_id: targetId,
        user_notes: userNotes,
    }),

    // Generate enhanced grant content with vector context
    generateEnhanced: (grantId, funder = 'region_16_opioid_council') => api.post(`/grants/${grantId}/generate-enhanced`, {
        funder,
    }),

    // Generate with three-tier system
    generateThreeTier: (grantId, funder = 'region_16_opioid_council') => api.post(`/grants/${grantId}/generate-three-tier`, {
        funder,
    }),
}

// Three-Tier Vector Database API
export const threeTierAPI = {
    // Create three-tier application
    createApplication: (grantId, applicationName) => api.post(`/grants/${grantId}/create-application`, {
        application_name: applicationName,
    }),

    // Upload to specific tier
    uploadToTier: (grantId, tier, file, documentType = '', description = '') => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('document_type', documentType)
        formData.append('description', description)

        return api.post(`/grants/${grantId}/upload-tier/${tier}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Get tier summary
    getTierSummary: (grantId) => api.get(`/grants/${grantId}/tier-summary`),

    // Query all tiers
    queryAllTiers: (grantId, query, nResultsPerTier = 5) => api.post(`/grants/${grantId}/query-tiers`, {
        query,
        n_results_per_tier: nResultsPerTier,
    }),
}

// Enhanced File Upload API (extends fileAPI)
export const enhancedFileAPI = {
    ...fileAPI,

    // Upload to grant documents tier
    uploadGrantDocuments: (file, grantId) => {
        const formData = new FormData()
        formData.append('file', file)
        if (grantId) formData.append('grant_id', grantId)

        return api.post('/files/upload/grant-documents', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Upload to organization documents tier
    uploadOrganizationDocuments: (file, grantId) => {
        const formData = new FormData()
        formData.append('file', file)
        if (grantId) formData.append('grant_id', grantId)

        return api.post('/files/upload/organization-documents', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Upload to application outlines tier
    uploadApplicationOutlines: (file, grantId) => {
        const formData = new FormData()
        formData.append('file', file)
        if (grantId) formData.append('grant_id', grantId)

        return api.post('/files/upload/application-outlines', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Upload with document type
    uploadWithType: (file, documentType, grantId) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('document_type', documentType)
        if (grantId) formData.append('grant_id', grantId)

        return api.post('/files/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
    },

    // Delete all grant documents
    deleteAllGrantDocuments: (grantId) => api.delete(`/grants/${grantId}/documents`),
}

// System Status API
export const systemAPI = {
    // Get processing stats
    getProcessingStats: () => api.get('/system/processing-stats'),

    // Health check
    healthCheck: () => api.get('/health'),
}

// Export all APIs including enhanced ones
export default {
    organization: organizationAPI,
    grants: grantsAPI,
    files: enhancedFileAPI,
    ai: aiAPI,
    templates: templatesAPI,
    analytics: analyticsAPI,
    search: searchAPI,
    settings: settingsAPI,
    // Enhanced APIs
    documentProcessing: documentProcessingAPI,
    tabManagement: tabManagementAPI,
    regeneration: regenerationAPI,
    threeTier: threeTierAPI,
    system: systemAPI,
}
