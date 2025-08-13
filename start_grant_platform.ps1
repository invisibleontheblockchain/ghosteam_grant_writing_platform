# GhostTeam Grant Writing Platform Startup Script
Write-Host "🚀 Starting GhostTeam Grant Writing Platform..." -ForegroundColor Green

# Check if we're in the right directory
if (!(Test-Path "config/settings.py")) {
    Write-Host "❌ Error: Please run this script from the ghosteam_grant_writing_platform directory" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check for environment variables
Write-Host "🔐 Checking environment configuration..." -ForegroundColor Yellow

if (!$env:OPENAI_API_KEY) {
    Write-Host "⚠️  Warning: OPENAI_API_KEY not set. AI features will be disabled." -ForegroundColor Yellow
    Write-Host "   Set it with: `$env:OPENAI_API_KEY='your-api-key-here'" -ForegroundColor Gray
}

if (!$env:SECRET_KEY) {
    Write-Host "🔑 Setting development SECRET_KEY..." -ForegroundColor Yellow
    $env:SECRET_KEY = "dev-secret-key-$(Get-Random)"
}

if (!$env:FLASK_ENV) {
    Write-Host "🏗️  Setting FLASK_ENV to development..." -ForegroundColor Yellow
    $env:FLASK_ENV = "development"
}

Write-Host ""
Write-Host "✅ GhostTeam Grant Writing Platform Ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Platform Summary:" -ForegroundColor Cyan
Write-Host "   • AI-Powered Grant Writing Assistant" -ForegroundColor White
Write-Host "   • RAG-Enhanced Content Generation" -ForegroundColor White
Write-Host "   • SAFE Knowledge Base Pre-loaded" -ForegroundColor White
Write-Host "   • Comprehensive Workflow Management" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Current Configuration:" -ForegroundColor Cyan
Write-Host "   • Environment: $env:FLASK_ENV" -ForegroundColor White
Write-Host "   • AI Enabled: $(if ($env:OPENAI_API_KEY) { 'Yes' } else { 'No' })" -ForegroundColor White
Write-Host "   • Security: Development Mode" -ForegroundColor White
Write-Host ""
Write-Host "📁 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Review PLATFORM_SUMMARY.md for complete overview" -ForegroundColor White
Write-Host "   2. Implement database models (Phase 2)" -ForegroundColor White
Write-Host "   3. Build RAG engine (Phase 3)" -ForegroundColor White
Write-Host "   4. Create web interface (Phase 4)" -ForegroundColor White
Write-Host ""
Write-Host "🌟 Ready to revolutionize grant writing!" -ForegroundColor Green
Write-Host ""

# Keep the terminal open
Read-Host "Press Enter to continue..."
