import React, { useState, useEffect } from 'react'
import { useParams, Link, useSearchParams } from 'react-router-dom'
import { grantsAPI, fileAPI, aiAPI } from '../services/api'

const GrantWorkspace = () => {
    const { grantId } = useParams()
    const [searchParams] = useSearchParams()
    const [activeTab, setActiveTab] = useState('overview')

    // Check if this is a new application
    const isNewApplication = searchParams.get('new') === 'true'
    const [isLoading, setIsLoading] = useState(false)
    const [uploadingFiles, setUploadingFiles] = useState(false)
    const [editingSection, setEditingSection] = useState(null)
    const [sectionContent, setSectionContent] = useState({
        'Project Summary': '',
        'Project Goals': '',
        'Evaluation Plan': '',
        'Statement of Need': isNewApplication ? '' : 'The growing digital divide in underserved communities has created significant barriers to educational equity and economic opportunity...'
    })
    const [grantDocuments, setGrantDocuments] = useState([])
    const [grantData, setGrantData] = useState(null)

    // Load grant data and documents on component mount
    useEffect(() => {
        if (!isNewApplication) {
            loadGrantData()
            loadGrantDocuments()
        } else {
            // For new applications, initialize with empty state
            setGrantData({
                id: grantId,
                name: 'New Grant Application',
                funder: 'Select a Funding Organization',
                status: 'Draft',
                deadline: 'Not Set',
                amount: 'Not Set',
                lastModified: new Date().toISOString().split('T')[0],
                progress: 0,
                description: 'Complete the steps below to build your grant application.'
            })
        }
    }, [grantId, isNewApplication])

    const loadGrantData = async () => {
        try {
            setIsLoading(true)
            const actualGrantId = grantId.startsWith('new-') ? '1' : grantId
            const response = await grantsAPI.getById(actualGrantId)
            setGrantData(response.data)
        } catch (error) {
            console.error('Failed to load grant data:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const loadGrantDocuments = async () => {
        try {
            const actualGrantId = grantId.startsWith('new-') ? '1' : grantId
            const response = await grantsAPI.getDocuments(actualGrantId)

            // Filter documents by grant_id to ensure proper isolation
            const filteredDocs = (response.data || []).filter(doc =>
                doc.grant_id == actualGrantId || (!doc.grant_id && isNewApplication)
            )

            setGrantDocuments(filteredDocs)
        } catch (error) {
            console.error('Failed to load grant documents:', error)
            setGrantDocuments([])
        }
    }

    const handleUploadDocument = (uploadType = 'files') => {
        const fileInput = document.createElement('input')
        fileInput.type = 'file'
        fileInput.accept = '.pdf,.doc,.docx,.txt,.md,.jpg,.jpeg,.png'
        fileInput.multiple = true

        // Enable folder upload if specified
        if (uploadType === 'folder') {
            fileInput.webkitdirectory = true
            fileInput.directory = true
        }

        fileInput.onchange = async (event) => {
            const files = event.target.files
            if (files.length > 0) {
                setUploadingFiles(true)

                try {
                    console.log(`Starting upload of ${files.length} file(s)${uploadType === 'folder' ? ' from folder' : ''}...`)

                    const uploadPromises = Array.from(files).map(async (file) => {
                        console.log(`Uploading file: ${file.name} (${file.size} bytes)`)

                        const actualGrantId = grantId.startsWith('new-') ? '1' : grantId
                        const formData = new FormData()
                        formData.append('file', file)
                        formData.append('category', 'grant_documents')
                        formData.append('grant_id', actualGrantId)

                        // Preserve folder structure by sending the relative path
                        if (uploadType === 'folder' && file.webkitRelativePath) {
                            formData.append('folder_path', file.webkitRelativePath)
                        }

                        const response = await fetch('/api/files/upload', {
                            method: 'POST',
                            body: formData
                        })

                        if (response.ok) {
                            const result = await response.json()
                            return {
                                success: true,
                                filename: result.filename,
                                document_id: result.document_id,
                                file_size: file.size,
                                upload_date: new Date().toISOString(),
                                folder_path: file.webkitRelativePath || null
                            }
                        } else {
                            throw new Error(`Upload failed for ${file.name}`)
                        }
                    })

                    const results = await Promise.all(uploadPromises)
                    const successfulUploads = results.filter(r => r.success)

                    // Add successful uploads to the documents list immediately
                    setGrantDocuments(prev => [...prev, ...successfulUploads])

                    if (successfulUploads.length === files.length) {
                        alert(`✅ Successfully uploaded ${successfulUploads.length} file(s)${uploadType === 'folder' ? ' from folder' : ''}!`)
                    } else {
                        alert(`⚠️ Uploaded ${successfulUploads.length} of ${files.length} files. Some uploads failed.`)
                    }

                    // Refresh from server to ensure consistency
                    loadGrantDocuments()

                } catch (error) {
                    console.error('Upload error:', error)
                    alert('❌ Upload failed. Please try again.')
                } finally {
                    setUploadingFiles(false)
                }
            }
        }

        fileInput.click()
    }

    const handleUploadDocumentByType = (documentType) => {
        const fileInput = document.createElement('input')
        fileInput.type = 'file'
        fileInput.accept = '.pdf,.doc,.docx,.txt,.md,.jpg,.jpeg,.png'
        fileInput.multiple = true

        fileInput.onchange = async (event) => {
            const files = event.target.files
            if (files.length > 0) {
                setUploadingFiles(true)

                try {
                    console.log(`Starting upload of ${files.length} file(s) to ${documentType}...`)

                    const uploadPromises = Array.from(files).map(async (file) => {
                        console.log(`Uploading file: ${file.name} (${file.size} bytes)`)

                        const actualGrantId = grantId.startsWith('new-') ? '1' : grantId
                        const formData = new FormData()
                        formData.append('file', file)
                        formData.append('document_type', documentType)
                        formData.append('grant_id', actualGrantId)

                        const response = await fetch('/api/files/upload', {
                            method: 'POST',
                            body: formData
                        })

                        if (response.ok) {
                            const result = await response.json()
                            return {
                                success: true,
                                filename: result.filename,
                                document_id: result.document_id,
                                vector_document_id: result.vector_document_id,
                                document_type: result.document_type,
                                chunks_processed: result.chunks_processed,
                                file_size: file.size,
                                upload_date: new Date().toISOString(),
                                category: documentType
                            }
                        } else {
                            const errorData = await response.json()
                            throw new Error(`Upload failed for ${file.name}: ${errorData.error}`)
                        }
                    })

                    const results = await Promise.all(uploadPromises)
                    const successfulUploads = results.filter(r => r.success)

                    // Add successful uploads to the documents list immediately
                    setGrantDocuments(prev => [...prev, ...successfulUploads])

                    if (successfulUploads.length === files.length) {
                        const docTypeName = documentType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
                        alert(`✅ Successfully uploaded ${successfulUploads.length} ${docTypeName} file(s)! Vector processing completed with ${successfulUploads.reduce((acc, upload) => acc + upload.chunks_processed, 0)} chunks processed.`)
                    } else {
                        alert(`⚠️ Uploaded ${successfulUploads.length} of ${files.length} files. Some uploads failed.`)
                    }

                    // Refresh from server to ensure consistency
                    loadGrantDocuments()

                } catch (error) {
                    console.error('Upload error:', error)
                    alert(`❌ Upload failed: ${error.message}`)
                } finally {
                    setUploadingFiles(false)
                }
            }
        }

        fileInput.click()
    }

    const handleGenerateGrant = async () => {
        if (grantDocuments.length === 0) {
            alert('⚠️ Please upload some documents first to provide context for AI generation.')
            return
        }

        try {
            setIsLoading(true)

            // Use the correct grant ID (convert new- format to actual ID)
            const actualGrantId = grantId.startsWith('new-') ? '1' : grantId

            // Use the enhanced generation endpoint
            const response = await fetch(`/api/grants/${actualGrantId}/generate-enhanced`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    funder: (grantData?.funder && grantData.funder !== 'Select a Funding Organization')
                        ? grantData.funder
                        : 'region_16_opioid_council',
                    useVectorContext: true
                })
            })

            if (response.ok) {
                const result = await response.json()

                if (result.success) {
                    alert(`✅ Grant generated successfully! Used context from ${result.context_used.grant_requirements + result.context_used.organization_context + result.context_used.project_specifications} documents.`)

                    // Update section content with generated content
                    setSectionContent(result.sections)

                    // Switch to application tab to show results
                    setActiveTab('application')

                    // Reload grant data to reflect updated progress
                    loadGrantData()
                } else {
                    alert('❌ Grant generation failed. Please try again.')
                }
            } else {
                const errorData = await response.json()
                alert(`❌ Grant generation failed: ${errorData.error}`)
            }
        } catch (error) {
            console.error('Grant generation failed:', error)
            alert('❌ Grant generation failed. Please check your uploaded documents and try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleDeleteDocument = async (documentId, filename) => {
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return
        }

        try {
            const response = await fetch(`/api/files/${documentId}`, {
                method: 'DELETE'
            })

            if (response.ok) {
                // Remove from local state immediately
                setGrantDocuments(prev => prev.filter(doc => doc.id !== documentId))
                alert('✅ File deleted successfully!')

                // Refresh from server to ensure consistency
                loadGrantDocuments()
            } else {
                const errorData = await response.json()
                alert(`❌ Failed to delete file: ${errorData.error}`)
            }
        } catch (error) {
            console.error('Delete error:', error)
            alert('❌ Failed to delete file. Please try again.')
        }
    }

    const handleDeleteAllDocuments = async () => {
        if (grantDocuments.length === 0) {
            alert('No documents to delete.')
            return
        }

        if (!confirm(`Are you sure you want to delete ALL ${grantDocuments.length} documents? This action cannot be undone.`)) {
            return
        }

        try {
            const actualGrantId = grantId.startsWith('new-') ? '1' : grantId
            const response = await fetch(`/api/grants/${actualGrantId}/documents`, {
                method: 'DELETE'
            })

            if (response.ok) {
                const result = await response.json()
                // Clear local state immediately
                setGrantDocuments([])
                alert(`✅ ${result.message}`)

                // Refresh from server to ensure consistency
                loadGrantDocuments()
            } else {
                const errorData = await response.json()
                alert(`❌ Failed to delete documents: ${errorData.error}`)
            }
        } catch (error) {
            console.error('Delete all error:', error)
            alert('❌ Failed to delete documents. Please try again.')
        }
    }

    const handleSaveSection = async () => {
        try {
            setIsLoading(true)
            const sectionName = editingSection
            const content = sectionContent[sectionName]

            await grantsAPI.saveSection(grantId, sectionName, { content })
            setEditingSection(null)
            alert('✅ Section saved successfully!')

            if (grantData) {
                loadGrantData() // Refresh to update progress
            }
        } catch (error) {
            console.error('Failed to save section:', error)
            alert('❌ Failed to save section. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    // Simplified mock grant data
    const grant = grantData || {
        id: grantId,
        name: 'New Grant Application',
        funder: 'Select a Funding Organization',
        status: 'Draft',
        deadline: 'Not Set',
        amount: 'Not Set',
        lastModified: new Date().toISOString().split('T')[0],
        progress: 0,
        description: 'Complete the steps below to build your grant application.'
    }

    const tabs = [
        { id: 'overview', name: 'Overview', icon: '📋' },
        { id: 'documents', name: 'Documents', icon: '📄' },
        { id: 'application', name: 'Application', icon: '📝' },
        { id: 'budget', name: 'Budget', icon: '💰' }
    ]

    const renderOverview = () => (
        <div className="space-y-6">
            {/* Quick Start Section for New Applications */}
            {isNewApplication && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-blue-900 mb-4">🚀 Quick Start Guide</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white p-4 rounded-lg border border-blue-100">
                            <div className="text-2xl mb-2">📄</div>
                            <h4 className="font-medium text-gray-900">1. Upload Documents</h4>
                            <p className="text-sm text-gray-600 mb-3">Add organization info, project details, letters of support</p>
                            <button
                                onClick={() => setActiveTab('documents')}
                                className="text-blue-600 text-sm font-medium hover:text-blue-800"
                            >
                                Upload Files →
                            </button>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-blue-100">
                            <div className="text-2xl mb-2">⚡</div>
                            <h4 className="font-medium text-gray-900">2. Generate Content</h4>
                            <p className="text-sm text-gray-600 mb-3">Use AI to create your application from uploaded docs</p>
                            <button
                                onClick={handleGenerateGrant}
                                disabled={grantDocuments.length === 0}
                                className="text-blue-600 text-sm font-medium hover:text-blue-800 disabled:text-gray-400"
                            >
                                Generate Grant →
                            </button>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-blue-100">
                            <div className="text-2xl mb-2">✏️</div>
                            <h4 className="font-medium text-gray-900">3. Review & Edit</h4>
                            <p className="text-sm text-gray-600 mb-3">Customize sections and finalize your application</p>
                            <button
                                onClick={() => setActiveTab('application')}
                                className="text-blue-600 text-sm font-medium hover:text-blue-800"
                            >
                                Edit Application →
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card">
                    <h3 className="card-title">Grant Details</h3>
                    <div className="space-y-4 mt-4">
                        <div>
                            <label className="text-sm font-medium text-gray-500">Funding Organization</label>
                            <p className="text-gray-900">{grant.funder}</p>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-500">Requested Amount</label>
                            <p className="text-gray-900">{grant.amount}</p>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-500">Application Deadline</label>
                            <p className="text-gray-900">{grant.deadline !== 'Not Set' ? new Date(grant.deadline).toLocaleDateString() : 'Not Set'}</p>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-500">Status</label>
                            <span className="badge badge-warning">{grant.status}</span>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <h3 className="card-title">Progress & Documents</h3>
                    <div className="mt-4">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-sm text-gray-500">Application Completion</span>
                            <span className="text-sm font-medium text-gray-900">{grant.progress}%</span>
                        </div>
                        <div className="progress-bar">
                            <div
                                className="progress-fill bg-primary-600"
                                style={{ width: `${grant.progress}%` }}
                            />
                        </div>

                        {/* Real-time Document Counter */}
                        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-700">📄 Uploaded Documents</span>
                                <span className="text-lg font-bold text-blue-600">{grantDocuments.length}</span>
                            </div>
                            {grantDocuments.length > 0 && (
                                <div className="mt-2 text-xs text-gray-500">
                                    Latest: {grantDocuments[grantDocuments.length - 1]?.filename}
                                </div>
                            )}
                        </div>

                        {/* AI Generation Status */}
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-700">⚡ AI Generation</span>
                                <span className={`text-sm font-medium ${grantDocuments.length > 0 ? 'text-green-600' : 'text-gray-400'}`}>
                                    {grantDocuments.length > 0 ? 'Ready' : 'Need Docs'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card">
                <h3 className="card-title">Project Description</h3>
                <p className="mt-4 text-gray-700">{grant.description}</p>
            </div>

            {/* Simplified AI Generation Section */}
            <div className="card">
                <div className="flex justify-between items-center">
                    <div>
                        <h3 className="card-title">🤖 AI Grant Generation</h3>
                        <p className="card-description">
                            Upload documents, then generate your complete grant application with AI
                        </p>
                    </div>
                    <button
                        onClick={handleGenerateGrant}
                        disabled={isLoading || grantDocuments.length === 0}
                        className="btn-primary disabled:opacity-50"
                    >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        {isLoading ? 'Generating...' : 'Generate Grant'}
                    </button>
                </div>

                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    {grantDocuments.length === 0 ? (
                        <div className="flex items-center text-yellow-800">
                            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            Upload documents first to enable AI generation
                        </div>
                    ) : (
                        <div className="flex items-center text-green-800">
                            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            Ready to generate with {grantDocuments.length} document(s)
                        </div>
                    )}
                </div>
            </div>
        </div>
    )

    const renderDocuments = () => (
        <div className="space-y-6">
            {/* Three-Tier Upload System */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Grant Documents */}
                <div className="card">
                    <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div>
                            <h4 className="font-semibold text-gray-900">Grant Documents</h4>
                            <p className="text-sm text-gray-500">RFPs, Application Questions, Guidelines</p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                            <strong>Purpose:</strong> Upload RFP documents, application questions, attachment checklists,
                            and funder guidelines. These provide the exact requirements for your grant application.
                        </div>

                        <button
                            onClick={() => handleUploadDocumentByType('grant_documents')}
                            disabled={uploadingFiles}
                            className="w-full btn-outline disabled:opacity-50 text-sm"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            Upload Grant Docs
                        </button>

                        <div className="text-xs text-center text-gray-500">
                            {grantDocuments.filter(d => d.category === 'grant_documents').length} files uploaded
                        </div>
                    </div>
                </div>

                {/* Organization Documents */}
                <div className="card">
                    <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div>
                            <h4 className="font-semibold text-gray-900">Organization Documents</h4>
                            <p className="text-sm text-gray-500">Past Grants, Impact Data, Leadership Info</p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                            <strong>Purpose:</strong> Upload past won grants, program data, leadership bios, and impact reports.
                            These provide organizational context and credibility.
                        </div>

                        <button
                            onClick={() => handleUploadDocumentByType('organization_documents')}
                            disabled={uploadingFiles}
                            className="w-full btn-outline disabled:opacity-50 text-sm"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                            Upload Org Docs
                        </button>

                        <div className="text-xs text-center text-gray-500">
                            {grantDocuments.filter(d => d.category === 'organization_documents').length} files uploaded
                        </div>
                    </div>
                </div>

                {/* Application Outlines */}
                <div className="card">
                    <div className="flex items-center mb-4">
                        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                            <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h4a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div>
                            <h4 className="font-semibold text-gray-900">Application Outlines</h4>
                            <p className="text-sm text-gray-500">Project Specs, Budgets, Timelines</p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                            <strong>Purpose:</strong> Upload your project outlines, budget details, timelines, and specific
                            deliverables. AI will follow these specifications exactly.
                        </div>

                        <button
                            onClick={() => handleUploadDocumentByType('application_outlines')}
                            disabled={uploadingFiles}
                            className="w-full btn-outline disabled:opacity-50 text-sm"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Upload Outlines
                        </button>

                        <div className="text-xs text-center text-gray-500">
                            {grantDocuments.filter(d => d.category === 'application_outlines').length} files uploaded
                        </div>
                    </div>
                </div>
            </div>

            {/* Combined Document Library */}
            <div className="card">
                <div className="flex justify-between items-center">
                    <h3 className="card-title">📄 Document Library</h3>
                    <div className="flex space-x-2">
                        {grantDocuments.length > 0 && (
                            <button
                                onClick={handleDeleteAllDocuments}
                                className="btn-outline text-red-600 border-red-300 hover:bg-red-50 disabled:opacity-50 text-sm"
                                title="Delete all documents"
                            >
                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1-1H8a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                Delete All
                            </button>
                        )}
                        <button
                            onClick={() => handleUploadDocument('files')}
                            disabled={uploadingFiles}
                            className="btn-outline disabled:opacity-50"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            {uploadingFiles ? 'Uploading...' : 'Upload Files'}
                        </button>
                        <button
                            onClick={() => handleUploadDocument('folder')}
                            disabled={uploadingFiles}
                            className="btn-primary disabled:opacity-50"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                            {uploadingFiles ? 'Uploading...' : 'Upload Folder'}
                        </button>
                    </div>
                </div>

                {/* Real-time Document List */}
                <div className="mt-6">
                    {grantDocuments.length === 0 ? (
                        <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded yet</h3>
                            <p className="text-gray-500 mb-4">Upload organization info, project details, budgets, or letters of support</p>
                            <div className="flex justify-center space-x-3">
                                <button onClick={() => handleUploadDocument('files')} className="btn-primary">
                                    Upload Files
                                </button>
                                <button onClick={() => handleUploadDocument('folder')} className="btn-outline">
                                    Upload Folder
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <div className="text-sm text-gray-600 mb-4">
                                {grantDocuments.length} document(s) uploaded • Ready for AI generation
                            </div>
                            {grantDocuments.map((doc, index) => (
                                <div key={doc.document_id || index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                            {doc.folder_path ? (
                                                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                                                </svg>
                                            ) : (
                                                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                                                </svg>
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900">{doc.filename}</p>
                                            <p className="text-sm text-gray-500">
                                                {doc.folder_path && (
                                                    <span className="text-blue-600 mr-2">📁 {doc.folder_path.split('/')[0]}</span>
                                                )}
                                                {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown size'} •
                                                {doc.upload_date ? ` Uploaded ${new Date(doc.upload_date).toLocaleDateString()}` : ' Recently uploaded'}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <span className="badge badge-success">✓ Uploaded</span>
                                        <button
                                            onClick={() => handleDeleteDocument(doc.id, doc.original_filename || doc.filename)}
                                            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                            title="Delete file"
                                        >
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1-1H8a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Upload Progress Indicator */}
                {uploadingFiles && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center">
                            <svg className="animate-spin w-5 h-5 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span className="text-blue-800 font-medium">Uploading files...</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )

    const renderApplication = () => (
        <div className="space-y-6">
            <div className="card">
                <div className="flex justify-between items-center">
                    <div>
                        <h3 className="card-title">Grant Application Sections</h3>
                        <p className="card-description">Complete all sections of the grant application</p>
                    </div>
                    <button
                        onClick={handleGenerateGrant}
                        disabled={isLoading || grantDocuments.length === 0}
                        className="btn-primary disabled:opacity-50"
                    >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        {isLoading ? 'Generating...' : 'Regenerate Content'}
                    </button>
                </div>

                {Object.keys(sectionContent).length === 0 || Object.values(sectionContent).every(content => !content) ? (
                    <div className="mt-6 text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No content generated yet</h3>
                        <p className="text-gray-500 mb-4">Upload documents and generate your grant application to see content here</p>
                        <button
                            onClick={handleGenerateGrant}
                            disabled={grantDocuments.length === 0}
                            className="btn-primary disabled:opacity-50"
                        >
                            Generate Grant Application
                        </button>
                    </div>
                ) : (
                    <div className="mt-6 space-y-6">
                        {Object.entries(sectionContent).filter(([_, content]) => content).map(([sectionName, content]) => (
                            <div key={sectionName} className="border border-gray-200 rounded-lg">
                                <div className="border-l-4 border-primary-500 bg-gray-50 px-6 py-4">
                                    <div className="flex justify-between items-center">
                                        <h4 className="font-medium text-gray-900">{sectionName}</h4>
                                        <button
                                            onClick={() => setEditingSection(sectionName)}
                                            className="btn-outline text-sm"
                                        >
                                            Edit Section
                                        </button>
                                    </div>
                                </div>
                                <div className="px-6 py-4">
                                    <div className="prose max-w-none">
                                        {content.split('\n').map((paragraph, index) => (
                                            paragraph.trim() ? (
                                                <p key={index} className="mb-3 text-gray-700 leading-relaxed">
                                                    {paragraph}
                                                </p>
                                            ) : (
                                                <br key={index} />
                                            )
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )

    const renderContent = () => {
        switch (activeTab) {
            case 'overview':
                return renderOverview()
            case 'documents':
                return renderDocuments()
            case 'application':
                return renderApplication()
            case 'budget':
                return <div className="card"><p className="text-gray-500">Budget planning coming soon...</p></div>
            default:
                return renderOverview()
        }
    }

    return (
        <div>
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
                    <Link to="/grants" className="hover:text-gray-900">Grant Applications</Link>
                    <span>/</span>
                    <span className="text-gray-900">{grant.name}</span>
                </div>
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">{grant.name}</h1>
                        <p className="mt-2 text-gray-600">{grant.funder}</p>
                    </div>
                    <div className="flex space-x-3">
                        <button className="btn-outline">
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                            </svg>
                            Share
                        </button>
                        <button className="btn-primary">
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Export
                        </button>
                    </div>
                </div>
            </div>

            {/* Simplified Tabs */}
            <div className="border-b border-gray-200 mb-8">
                <nav className="-mb-px flex space-x-8">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${activeTab === tab.id
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            <span className="mr-2">{tab.icon}</span>
                            {tab.name}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Content */}
            {renderContent()}

            {/* Section Editor Modal */}
            {editingSection && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-gray-200">
                            <div className="flex justify-between items-center">
                                <h2 className="text-xl font-semibold text-gray-900">Edit {editingSection}</h2>
                                <button
                                    onClick={() => setEditingSection(null)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <div className="p-6">
                            <textarea
                                value={sectionContent[editingSection] || ''}
                                onChange={(e) => setSectionContent(prev => ({
                                    ...prev,
                                    [editingSection]: e.target.value
                                }))}
                                rows={12}
                                className="textarea w-full"
                                placeholder={`Enter your ${editingSection.toLowerCase()} content here...`}
                            />
                        </div>

                        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
                            <button
                                onClick={() => setEditingSection(null)}
                                className="btn-outline"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSaveSection}
                                className="btn-primary"
                            >
                                Save Section
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default GrantWorkspace
