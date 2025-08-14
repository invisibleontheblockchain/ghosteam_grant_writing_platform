# 🚀 Grant Writing Platform - Quick Start Guide

Your grant writing platform is now ready to run! This guide will get you up and running in minutes.

## ✅ What's Been Implemented

### **Frontend (React)**
- ✅ **Organization Profile** - Real API integration for saving/loading org data
- ✅ **Grant Workspace** - File upload, AI generation, section editing
- ✅ **Dashboard** - Real-time stats and grant management
- ✅ **File Upload System** - Multi-file support with progress tracking
- ✅ **AI Grant Generation** - Connected to your existing engine

### **Backend (Flask)**
- ✅ **REST API** - Complete API for all frontend functionality
- ✅ **Database** - SQLite with organizations, grants, documents tables
- ✅ **File Upload** - Real file processing and storage
- ✅ **Grant Engine Integration** - Your `generate_grant_v2.py` wrapped as API
- ✅ **Real-time Generation** - AI-powered grant creation

## 🏃‍♂️ Quick Start (3 Steps)

### **Step 1: Start the Backend**
```bash
# Run this in your main directory
python start_backend.py
```

The backend will:
- Install dependencies automatically
- Create SQLite database
- Start API server on http://localhost:5000
- Pre-populate with SAFE organization data

### **Step 2: Start the Frontend**
```bash
# In a new terminal, go to frontend directory
cd frontend
npm install
npm run dev
```

The frontend will start on http://localhost:5173

### **Step 3: Test File Upload & Grant Generation**

1. **Open the platform**: http://localhost:5173
2. **Check Organization Profile**: Pre-loaded with SAFE data
3. **Create a Grant**: Go to Grant Workspace
4. **Upload Documents**: Add your context files (PDFs, Word docs)
5. **Generate Grant**: Click the "Generate Grant" button
6. **Review Results**: AI-generated content appears in Application tab

## 🎯 Key Features Now Working

### **File Upload & Context Integration**
- Upload PDFs, Word docs, markdown files
- Files stored and linked to grants
- Context used in AI generation

### **AI Grant Generation**
- Uses your existing `generate_grant_v2.py` engine
- Generates complete grant sections
- Budget calculations and scope planning
- Timeline synchronization

### **Real Data Persistence**
- Organization profile saves to database
- Grant sections persist across sessions
- Document management and tracking

## 📁 Directory Structure

```
grant_platform/
├── app.py                    # Flask backend server
├── start_backend.py          # Backend startup script
├── backend_requirements.txt  # Python dependencies
├── grant_platform.db        # SQLite database (auto-created)
├── uploads/                  # File storage (auto-created)
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/           # Updated with real API calls
│   │   └── services/api.js  # Connected to backend
├── engines/                  # Your existing grant engine
└── scripts/                  # Your existing scripts
```

## 🔧 API Endpoints Available

### **Core Functionality**
- `GET/PUT /api/organization/profile` - Organization management
- `POST /api/files/upload` - File upload
- `POST /api/grants/{id}/generate` - AI grant generation
- `GET /api/analytics/dashboard` - Dashboard stats

### **Grant Management**
- `GET/POST /api/grants` - List/create grants
- `PUT /api/grants/{id}/sections/{section}` - Save sections
- `GET /api/grants/{id}/documents` - Document management

## 🎉 What You Can Do Now

### **Immediate Capabilities**
1. **Upload context documents** (your winning grants, RFPs)
2. **Generate complete grants** using AI
3. **Edit and refine** grant sections
4. **Save progress** automatically
5. **Export results** (basic functionality)

### **Ready for Production**
- Real database persistence
- File storage system
- API-driven architecture
- Error handling and validation

## 🔍 Testing Your Setup

### **Backend Health Check**
Visit: http://localhost:5000/api/health
Should return: `{"status": "ok", "message": "Grant Platform API is running"}`

### **Frontend Connection**
1. Dashboard should load real stats (initially zeros)
2. Organization Profile should show SAFE data
3. File upload should work without errors
4. Grant generation should create content

## 🚨 Troubleshooting

### **Backend Issues**
- **Port 5000 in use**: Change port in `app.py` line 524
- **Missing dependencies**: Run `pip install -r backend_requirements.txt`
- **Engine import errors**: Check your `engines/` directory path

### **Frontend Issues**
- **API connection failed**: Check backend is running on port 5000
- **CORS errors**: Flask-CORS should handle this automatically
- **File upload fails**: Check `uploads/` directory permissions

## 🔄 What's Next

Your platform is now **production-ready** for:
- File upload and context integration
- AI-powered grant generation
- Real data persistence
- Multi-user workflows (with auth added)

The foundation is complete - you can now focus on refining the AI generation or adding advanced features!

## 📞 Need Help?

- **Backend logs**: Check terminal running `start_backend.py`
- **Frontend logs**: Check browser developer console
- **Database**: SQLite browser to inspect `grant_platform.db`
- **Files**: Check `uploads/` directory for uploaded files

---

**🎊 Congratulations! Your grant writing platform is live and ready to generate grants with real file upload and AI integration!**
