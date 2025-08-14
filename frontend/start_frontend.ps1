Write-Host "🚀 Starting GrantForge AI Frontend Development Server..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

# Check if Node.js is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ and try again." -ForegroundColor Red
    exit 1
}

# Check Node.js version
$nodeVersion = node --version
Write-Host "📦 Node.js version: $nodeVersion" -ForegroundColor Yellow

# Navigate to frontend directory
Set-Location $PSScriptRoot

# Install dependencies if node_modules doesn't exist
if (-not (Test-Path "node_modules")) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    npm install
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 Starting GrantForge AI Frontend..." -ForegroundColor Cyan
Write-Host "📍 Platform: React + Vite + Tailwind CSS" -ForegroundColor Yellow
Write-Host "🌐 Local URL: http://localhost:5173" -ForegroundColor Yellow
Write-Host "🔗 API Proxy: Backend will be available at /api/*" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the development server" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan

# Start the development server
npm run dev
