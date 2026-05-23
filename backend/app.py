# =============================================================
# Digital Gram Panchayat - UPGRADED Backend (app.py)
# =============================================================
# NEW FEATURES ADDED:
#   - Service application forms with file uploads
#   - Certificate PDF generation (ReportLab)
#   - Admin approve/reject with auto-certificate creation
#   - Government schemes CRUD
#   - All existing routes PRESERVED (login/register unchanged)
# =============================================================

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import joblib
import os
import io
import random
import string
from datetime import datetime

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# File upload handling
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# -----------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gram_panchayat',
    'user': 'root',
    'password': '',     # Change this to your MySQL password
    'port': 3306
}

# Upload folder — create it if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Certificates folder
CERT_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'certificates')
os.makedirs(CERT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}

# Panchayat info used on certificates
PANCHAYAT_NAME   = "Shri Ram Gram Panchayat"
PANCHAYAT_DIST   = "District: Raipur, State: Chhattisgarh"
PANCHAYAT_STATE  = "Government of India"


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_cert_number(service_id):
    """Generate a unique certificate number like GP/BIRTH/2024/00123"""
    labels = {1: 'BIRTH', 2: 'DEATH', 3: 'INCOME',
              4: 'WATER', 5: 'ELEC', 6: 'RES', 7: 'CASTE'}
    label = labels.get(service_id, 'CERT')
    year  = datetime.now().year
    rand  = ''.join(random.choices(string.digits, k=5))
    return f"GP/{label}/{year}/{rand}"


# -----------------------------------------------------------------
# Load ML model (existing - unchanged)
# -----------------------------------------------------------------
model_path = os.path.join(os.path.dirname(__file__), 'ml', 'complaint_model.joblib')
try:
    complaint_model = joblib.load(model_path)
    print("✅ ML model loaded")
except Exception:
    complaint_model = None
    print("⚠️ ML model not loaded")


# ==================================================================
# EXISTING ROUTES — UNCHANGED
# ==================================================================

@app.route('/api/health', methods=['GET'])
@app.route('/api/ping', methods=['GET'])
def health():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'status': 'ok', 'message': 'Database connected'})
    return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500


# --- User Registration (UNCHANGED) ---
@app.route('/api/register', methods=['POST'])
def register():
    data     = request.json
    name     = data.get('name')
    email    = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')",
            (name, email, password)
        )
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# --- User Login (UNCHANGED) ---
@app.route('/api/login', methods=['POST'])
def login():
    data     = request.json
    email    = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, role FROM users WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()
        if user:
            return jsonify({'message': 'Login successful', 'user': user}), 200
        return jsonify({'error': 'Invalid email or password'}), 401
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# --- Get Services (UNCHANGED) ---
@app.route('/api/services', methods=['GET'])
def get_services():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM services")
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# --- Get User Applications (UNCHANGED, but adds cert info) ---
@app.route('/api/applications/user/<int:user_id>', methods=['GET'])
def get_user_applications(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # LEFT JOIN certificates so we know if a cert was issued
        query = """
            SELECT a.id, s.service_name, a.status, a.date,
                   c.certificate_number, c.id as cert_id
            FROM applications a
            JOIN services s ON a.service_id = s.id
            LEFT JOIN certificates c ON c.application_id = a.id
            WHERE a.user_id = %s
            ORDER BY a.date DESC
        """
        cursor.execute(query, (user_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# --- Complaints (UNCHANGED) ---
@app.route('/api/complaints', methods=['POST'])
def submit_complaint():
    data    = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    urgency_level = 'normal'
    if complaint_model:
        try:
            urgency_level = complaint_model.predict([message])[0]
        except Exception:
            pass

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO complaints (user_id, message, urgency_level) VALUES (%s, %s, %s)",
            (user_id, message, urgency_level)
        )
        conn.commit()
        return jsonify({'message': 'Complaint registered', 'urgency_assigned': urgency_level}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


@app.route('/api/complaints/user/<int:user_id>', methods=['GET'])
def get_user_complaints(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, message, status, urgency_level, date FROM complaints WHERE user_id=%s ORDER BY date DESC",
            (user_id,)
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# ==================================================================
# NEW ROUTE 1 — Submit Service Application Form (with file uploads)
# ==================================================================
@app.route('/api/applications', methods=['POST'])
def apply_service():
    """
    Accepts multipart/form-data with all form fields + uploaded files.
    Steps:
      1. Insert into `applications` to get application_id
      2. Save uploaded files to /frontend/uploads/
      3. Insert detailed form data into `service_applications_details`
    """
    # Get form fields
    user_id    = request.form.get('user_id')
    service_id = request.form.get('service_id')

    if not user_id or not service_id:
        return jsonify({'error': 'user_id and service_id are required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Step 1: Create base application record
        cursor.execute(
            "INSERT INTO applications (user_id, service_id) VALUES (%s, %s)",
            (user_id, service_id)
        )
        conn.commit()
        application_id = cursor.lastrowid

        # Step 2: Save uploaded files
        def save_file(field_name):
            """Helper: saves uploaded file, returns filename or None"""
            if field_name in request.files:
                f = request.files[field_name]
                if f and f.filename and allowed_file(f.filename):
                    fname = f"app{application_id}_{secure_filename(f.filename)}"
                    f.save(os.path.join(UPLOAD_FOLDER, fname))
                    return fname
            return None

        photo_path       = save_file('photo')
        aadhar_path      = save_file('aadhar_card')
        ration_card_path = save_file('ration_card')
        other_doc_path   = save_file('other_doc')

        # Step 3: Insert detailed form data
        cursor.execute("""
            INSERT INTO service_applications_details (
                application_id, user_id, service_id,
                full_name, father_name, mother_name, date_of_birth,
                gender, address, village, district, state, pincode,
                mobile, aadhar_number,
                annual_income, occupation,
                deceased_name, date_of_death, cause_of_death,
                request_details,
                photo_path, aadhar_path, ration_card_path, other_doc_path
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s,
                %s, %s, %s, %s
            )
        """, (
            application_id, user_id, service_id,
            request.form.get('full_name'), request.form.get('father_name'),
            request.form.get('mother_name'), request.form.get('date_of_birth') or None,
            request.form.get('gender'), request.form.get('address'),
            request.form.get('village'), request.form.get('district'),
            request.form.get('state'), request.form.get('pincode'),
            request.form.get('mobile'), request.form.get('aadhar_number'),
            request.form.get('annual_income') or None, request.form.get('occupation'),
            request.form.get('deceased_name'), request.form.get('date_of_death') or None,
            request.form.get('cause_of_death'),
            request.form.get('request_details'),
            photo_path, aadhar_path, ration_card_path, other_doc_path
        ))
        conn.commit()

        return jsonify({
            'message': 'Application submitted successfully!',
            'application_id': application_id
        }), 201

    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# ==================================================================
# NEW ROUTE 2 — Download Certificate PDF
# ==================================================================
@app.route('/api/certificates/download/<int:application_id>', methods=['GET'])
def download_certificate(application_id):
    """
    Generate and return a PDF certificate for an approved application.
    If certificate was already generated, regenerate from stored data.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify the application is Approved
        cursor.execute("""
            SELECT a.id, a.status, a.user_id, a.service_id,
                   s.service_name, u.name as user_name, u.email,
                   sad.full_name, sad.father_name, sad.date_of_birth,
                   sad.address, sad.village, sad.district, sad.state,
                   sad.mobile, sad.aadhar_number,
                   sad.annual_income, sad.occupation,
                   sad.deceased_name, sad.date_of_death,
                   sad.request_details, sad.gender
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN services s ON a.service_id = s.id
            LEFT JOIN service_applications_details sad ON sad.application_id = a.id
            WHERE a.id = %s
        """, (application_id,))
        app_data = cursor.fetchone()

        if not app_data:
            return jsonify({'error': 'Application not found'}), 404
        if app_data['status'] != 'Approved':
            return jsonify({'error': 'Certificate only available for approved applications'}), 403

        # Get or create certificate number
        cursor.execute("SELECT * FROM certificates WHERE application_id = %s", (application_id,))
        cert = cursor.fetchone()
        if not cert:
            cert_number = generate_cert_number(app_data['service_id'])
            cursor.execute("""
                INSERT INTO certificates (application_id, user_id, service_id, certificate_number)
                VALUES (%s, %s, %s, %s)
            """, (application_id, app_data['user_id'], app_data['service_id'], cert_number))
            conn.commit()
        else:
            cert_number = cert['certificate_number']

        # Generate PDF in memory
        pdf_buffer = generate_certificate_pdf(app_data, cert_number)

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Certificate_{cert_number.replace('/', '_')}.pdf"
        )

    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


def generate_certificate_pdf(data, cert_number):
    """
    Creates a government-style certificate PDF using ReportLab.
    Returns an io.BytesIO buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    styles   = getSampleStyleSheet()
    elements = []

    # ---------- Color Palette ----------
    GOV_BLUE  = colors.HexColor('#003580')
    GOV_GREEN = colors.HexColor('#006400')
    GOLD      = colors.HexColor('#C8860A')
    LIGHT_BG  = colors.HexColor('#F0F4FF')

    # ---------- Custom Styles ----------
    header_style = ParagraphStyle(
        'Header', parent=styles['Normal'],
        fontSize=9, alignment=TA_CENTER,
        textColor=GOV_BLUE, spaceAfter=2
    )
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=18, fontName='Helvetica-Bold',
        alignment=TA_CENTER, textColor=GOV_BLUE,
        spaceBefore=6, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold',
        alignment=TA_CENTER, textColor=GOLD,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=16,
        spaceAfter=6
    )
    field_label = ParagraphStyle(
        'FieldLabel', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold',
        textColor=GOV_BLUE
    )

    # ---------- Header Section ----------
    elements.append(Paragraph("भारत सरकार | GOVERNMENT OF INDIA", header_style))
    elements.append(Paragraph(PANCHAYAT_STATE, header_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=GOV_BLUE, spaceAfter=4))
    elements.append(Paragraph(PANCHAYAT_NAME.upper(), title_style))
    elements.append(Paragraph(PANCHAYAT_DIST, header_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))

    # ---------- Certificate Title ----------
    service_name = data.get('service_name', 'Certificate')
    elements.append(Paragraph(f"✦ {service_name.upper()} ✦", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))

    # ---------- Certificate Number & Date ----------
    cert_table = Table([
        [Paragraph(f"Certificate No: <b>{cert_number}</b>", body_style),
         Paragraph(f"Date: <b>{datetime.now().strftime('%d %B, %Y')}</b>", 
                   ParagraphStyle('R', parent=body_style, alignment=TA_RIGHT))]
    ], colWidths=[9*cm, 9*cm])
    cert_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('ROUNDEDCORNERS', [5]),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(cert_table)
    elements.append(Spacer(1, 0.5*cm))

    # ---------- Applicant Details Table ----------
    applicant_name = data.get('full_name') or data.get('user_name', 'N/A')
    rows = [
        ['Field', 'Details'],
        ['Applicant Full Name', applicant_name],
        ["Father's Name", data.get('father_name') or 'N/A'],
        ['Date of Birth', str(data.get('date_of_birth') or 'N/A')],
        ['Gender', data.get('gender') or 'N/A'],
        ['Address', data.get('address') or 'N/A'],
        ['Village / Ward', data.get('village') or 'N/A'],
        ['District', data.get('district') or 'N/A'],
        ['State', data.get('state') or 'N/A'],
        ['Mobile Number', data.get('mobile') or 'N/A'],
        ['Aadhaar Number', data.get('aadhar_number') or 'N/A'],
    ]

    # Add service-specific rows
    service_id = data.get('service_id')
    if service_id == 3:  # Income
        rows.append(['Annual Income', f"Rs. {data.get('annual_income') or 'N/A'}"])
        rows.append(['Occupation', data.get('occupation') or 'N/A'])
    elif service_id == 2:  # Death
        rows.append(['Deceased Name', data.get('deceased_name') or 'N/A'])
        rows.append(['Date of Death', str(data.get('date_of_death') or 'N/A')])
    elif service_id in [4, 5]:  # Water/Electricity
        rows.append(['Request Details', data.get('request_details') or 'N/A'])

    detail_table = Table(rows, colWidths=[6*cm, 12*cm])
    detail_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',   (0,0), (-1,0), GOV_BLUE),
        ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 10),
        # Alternating rows
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('FONTNAME',     (0,1), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,1), (-1,-1), 9),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING',      (0,0), (-1,-1), 7),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 0.7*cm))

    # ---------- Declaration ----------
    declaration = (
        f"This is to certify that the above-mentioned person is a resident under the jurisdiction "
        f"of <b>{PANCHAYAT_NAME}</b> and the information mentioned above is verified and found correct "
        f"as per the records available with this office."
    )
    elements.append(Paragraph(declaration, body_style))
    elements.append(Spacer(1, 1.0*cm))

    # ---------- Signature Section ----------
    sig_table = Table([
        [Paragraph("Applicant's Signature", 
                   ParagraphStyle('Sig', parent=body_style, alignment=TA_CENTER)),
         Paragraph("", body_style),
         Paragraph("Gram Panchayat Officer", 
                   ParagraphStyle('Sig', parent=body_style, alignment=TA_CENTER))],
        [Paragraph("________________________", 
                   ParagraphStyle('SigLine', parent=body_style, alignment=TA_CENTER)),
         Paragraph("", body_style),
         Paragraph("________________________", 
                   ParagraphStyle('SigLine', parent=body_style, alignment=TA_CENTER))],
        [Paragraph(applicant_name, 
                   ParagraphStyle('SigName', parent=body_style, alignment=TA_CENTER, fontSize=8)),
         Paragraph("", body_style),
         Paragraph(f"Seal & Signature\n{PANCHAYAT_NAME}", 
                   ParagraphStyle('SigName', parent=body_style, alignment=TA_CENTER, fontSize=8))]
    ], colWidths=[6*cm, 6*cm, 6*cm])
    elements.append(sig_table)

    # ---------- Footer ----------
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=GOV_BLUE))
    elements.append(Paragraph(
        f"This is a computer-generated certificate. | {PANCHAYAT_NAME} | {datetime.now().strftime('%Y')}",
        ParagraphStyle('Footer', parent=body_style, fontSize=7, 
                       alignment=TA_CENTER, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==================================================================
# ADMIN ROUTES — UPGRADED (approve triggers certificate)
# ==================================================================

# Admin: Get all applications with details
@app.route('/api/admin/applications', methods=['GET'])
def admin_get_all_applications():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.id, u.name as applicant_name, s.service_name,
                   a.status, a.date,
                   sad.full_name, sad.mobile, sad.address,
                   c.certificate_number
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN services s ON a.service_id = s.id
            LEFT JOIN service_applications_details sad ON sad.application_id = a.id
            LEFT JOIN certificates c ON c.application_id = a.id
            ORDER BY a.date DESC
        """)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: View a single application's full details
@app.route('/api/admin/applications/<int:app_id>/details', methods=['GET'])
def admin_get_application_details(app_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.id, a.status, s.service_name, u.name as user_name, u.email,
                   sad.*
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN services s ON a.service_id = s.id
            LEFT JOIN service_applications_details sad ON sad.application_id = a.id
            WHERE a.id = %s
        """, (app_id,))
        return jsonify(cursor.fetchone()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: Approve / Reject application
@app.route('/api/admin/applications/<int:app_id>', methods=['PUT'])
def admin_update_application(app_id):
    data   = request.json
    status = data.get('status')

    if status not in ['Pending', 'Approved', 'Rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE applications SET status=%s WHERE id=%s", (status, app_id))
        conn.commit()

        # If Approved, auto-create certificate record
        if status == 'Approved':
            cursor.execute("SELECT service_id, user_id FROM applications WHERE id=%s", (app_id,))
            app_row = cursor.fetchone()
            cursor.execute("SELECT id FROM certificates WHERE application_id=%s", (app_id,))
            if not cursor.fetchone():
                cert_number = generate_cert_number(app_row['service_id'])
                cursor.execute("""
                    INSERT INTO certificates (application_id, user_id, service_id, certificate_number)
                    VALUES (%s, %s, %s, %s)
                """, (app_id, app_row['user_id'], app_row['service_id'], cert_number))
                conn.commit()

        return jsonify({'message': f'Application {status} successfully'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: Get all complaints (UNCHANGED)
@app.route('/api/admin/complaints', methods=['GET'])
def admin_get_all_complaints():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id, u.name as complainer_name, c.message,
                   c.status, c.urgency_level, c.date 
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            ORDER BY FIELD(c.urgency_level,'urgent','normal'), c.date DESC
        """)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: Update complaint status (UNCHANGED)
@app.route('/api/admin/complaints/<int:complaint_id>', methods=['PUT'])
def admin_update_complaint(complaint_id):
    data   = request.json
    status = data.get('status')
    if status not in ['Pending', 'In Progress', 'Resolved']:
        return jsonify({'error': 'Invalid status'}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE complaints SET status=%s WHERE id=%s", (status, complaint_id))
        conn.commit()
        return jsonify({'message': 'Complaint status updated'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: Analytics (UNCHANGED)
@app.route('/api/admin/analytics', methods=['GET'])
def admin_analytics():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='user'")
        total_users = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM applications")
        total_applications = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM complaints")
        total_complaints = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM complaints WHERE urgency_level='urgent'")
        urgent_complaints = cursor.fetchone()['count']
        cursor.execute("SELECT status, COUNT(*) as count FROM applications GROUP BY status")
        applications_by_status = cursor.fetchall()
        cursor.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status")
        complaints_by_status = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) as count FROM schemes WHERE is_active=1")
        total_schemes = cursor.fetchone()['count']

        return jsonify({
            'total_users': total_users,
            'total_applications': total_applications,
            'total_complaints': total_complaints,
            'urgent_complaints': urgent_complaints,
            'total_schemes': total_schemes,
            'applications_by_status': applications_by_status,
            'complaints_by_status': complaints_by_status
        }), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# ==================================================================
# NEW ROUTES — Government Schemes
# ==================================================================

# Public: Get all active schemes
@app.route('/api/schemes', methods=['GET'])
def get_schemes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM schemes WHERE is_active=1 ORDER BY created_at DESC"
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Public: Get latest 3 schemes for homepage
@app.route('/api/schemes/latest', methods=['GET'])
def get_latest_schemes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, description, benefits, scheme_date FROM schemes "
            "WHERE is_active=1 ORDER BY created_at DESC LIMIT 3"
        )
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: Add new scheme (supports poster image upload)
@app.route('/api/admin/schemes', methods=['POST'])
def admin_add_scheme():
    title       = request.form.get('title')
    description = request.form.get('description')
    eligibility = request.form.get('eligibility')
    benefits    = request.form.get('benefits')
    scheme_date = request.form.get('scheme_date') or None
    last_date   = request.form.get('last_date') or None
    source_url  = request.form.get('source_url')

    # Handle poster upload
    poster_path = None
    if 'poster' in request.files:
        f = request.files['poster']
        if f and f.filename:
            fname = secure_filename(f.filename)
            poster_filename = f"scheme_{fname}"
            f.save(os.path.join(UPLOAD_FOLDER, poster_filename))
            poster_path = poster_filename

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schemes
                (title, description, eligibility, benefits, scheme_date, last_date, source_url, poster_path, added_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'admin')
        """, (title, description, eligibility, benefits, scheme_date, last_date, source_url, poster_path))
        conn.commit()
        return jsonify({'message': 'Scheme added successfully'}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# Admin: Delete scheme
@app.route('/api/admin/schemes/<int:scheme_id>', methods=['DELETE'])
def admin_delete_scheme(scheme_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE schemes SET is_active=0 WHERE id=%s", (scheme_id,))
        conn.commit()
        return jsonify({'message': 'Scheme removed'}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# ==================================================================
# MAIN
# ==================================================================
if __name__ == '__main__':
    print("=" * 55)
    print("  Digital Gram Panchayat — UPGRADED Server")
    print("=" * 55)
    print("  URL:    http://localhost:5000")
    print("  Health: http://localhost:5000/api/health")
    print("=" * 55)
    app.run(debug=True, port=5000)
