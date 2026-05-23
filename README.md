# 🏛️ Digital Gram Panchayat Services

A full-stack digital portal for Gram Panchayat services with Flask backend, MySQL database,
and a modern government-style frontend.

---

## 📁 Project Structure

```
Digital_gram_panchayat_upgraded/
│
├── backend/
│   ├── app.py                  ← Flask API (ALL routes — upgraded)
│   └── ml/
│       ├── complaint_model.joblib
│       └── train_model.py
│
├── database/
│   └── schema.sql              ← All tables including new ones
│
├── frontend/
│   ├── index.html              ← Login / Register page (upgraded UI)
│   ├── dashboard.html          ← User dashboard (upgraded)
│   ├── admin.html              ← Admin dashboard (upgraded)
│   ├── css/
│   │   └── style.css           ← Government-style CSS (upgraded)
│   ├── js/
│   │   └── app.js              ← Shared JS + service form config
│   ├── uploads/                ← User-uploaded documents (auto-created)
│   └── certificates/           ← Generated PDFs (auto-created)
│
└── requirements.txt            ← Python dependencies
```

---

## 🚀 Setup Instructions (VS Code)

### Step 1 — Install Python dependencies
Open terminal in VS Code and run:
```bash
pip install flask flask-cors mysql-connector-python joblib scikit-learn reportlab werkzeug
```

### Step 2 — Set up the Database
1. Start XAMPP → Start Apache + MySQL
2. Open phpMyAdmin at http://localhost/phpmyadmin
3. Click SQL tab at the top
4. Copy everything from database/schema.sql and paste it
5. Click Go — all tables and seed data are created

### Step 3 — Run the Flask server
```bash
cd backend
python app.py
```
Server runs at: http://localhost:5000

### Step 4 — Open the Frontend
- In VS Code: right-click frontend/index.html → Open with Live Server
- OR just double-click index.html to open in browser

---

## 🔐 Default Login Credentials

| Role  | Email                        | Password  |
|-------|------------------------------|-----------|
| Admin | admin@grampanchayat.gov      | admin123  |
| User  | Register from the login page |           |

---

## ✨ New Features Added

### 1. Service Application Forms
- Each service has its own dynamic form with all required fields
- File uploads: Photo, Aadhaar, Ration Card, Other Documents
- Data stored in service_applications_details table
- 7 services supported: Birth, Death, Income, Water, Electricity, Residence, Caste

### 2. Certificate Download (PDF)
- ReportLab generates a government-style certificate
- Certificate number auto-generated (format: GP/BIRTH/2024/12345)
- Available for download only when application is Approved
- Download Certificate button appears in My Applications table

### 3. Admin Approval System
- Admin can view full application details including uploaded documents
- One-click Approve or Reject
- Approving auto-creates a certificate record
- Filter applications by status and search by name/service

### 4. Government Schemes Module
- Admin can add schemes with title, description, eligibility, benefits, poster
- 5 pre-loaded schemes (PM Kisan, PMAY, NREGA, Ayushman Bharat, Ujjwala)
- Citizens see all schemes in their dashboard Schemes tab
- Admin can remove schemes

### 5. Upgraded UI/UX
- Government blue/green theme
- Fixed Navbar with all navigation links
- Sidebar dashboard with icons
- Service cards grid layout
- Responsive tables with status badges
- Animated modal for application forms
- Toast notifications
- Mobile responsive with hamburger menu and sidebar toggle

---

## 🗄️ New Database Tables

service_applications_details  - Stores detailed form data for each application
certificates                  - Stores certificate numbers and file paths
schemes                       - Government scheme notifications

---

## 📡 API Endpoints Reference

### Public Endpoints
POST   /api/register                       Register new user
POST   /api/login                          Login
GET    /api/services                       Get all services
GET    /api/schemes                        Get all active schemes
GET    /api/schemes/latest                 Get latest 3 schemes

### User Endpoints
POST   /api/applications                   Submit application with file uploads
GET    /api/applications/user/:id          Get my applications (with cert status)
GET    /api/certificates/download/:app_id  Download certificate PDF
POST   /api/complaints                     Submit complaint
GET    /api/complaints/user/:id            Get my complaints

### Admin Endpoints
GET    /api/admin/applications             All applications with details
GET    /api/admin/applications/:id/details Full form data for one application
PUT    /api/admin/applications/:id         Approve or Reject application
GET    /api/admin/complaints               All complaints
PUT    /api/admin/complaints/:id           Update complaint status
GET    /api/admin/analytics                Dashboard statistics
POST   /api/admin/schemes                  Add new scheme
DELETE /api/admin/schemes/:id              Remove scheme

---

## 🛠️ Troubleshooting

Flask server won't start:
  Run: pip install reportlab werkzeug

File uploads not saving:
  The frontend/uploads/ folder is auto-created by Flask on startup.
  Check that XAMPP has write permissions to the project folder.

Certificate PDF won't download:
  The application must have status = Approved first.
  Admin must approve it from admin.html → Applications tab.

CORS error in browser console:
  Ensure Flask is running on port 5000.
  Check API_BASE in frontend/js/app.js equals http://localhost:5000/api

Login not working:
  Make sure you ran schema.sql in phpMyAdmin first.
  The default admin user is inserted by the schema seed data.

---

## 📦 Python Dependencies

flask                    Web framework
flask-cors               Cross-origin requests for frontend
mysql-connector-python   MySQL database connection
joblib + scikit-learn    ML complaint urgency classification
reportlab                Government-style PDF certificate generation
werkzeug                 Secure file upload handling
