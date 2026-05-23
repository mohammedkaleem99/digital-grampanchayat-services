-- ============================================================
-- Digital Gram Panchayat - UPGRADED Database Schema
-- Run this file in phpMyAdmin or MySQL Workbench
-- ============================================================

CREATE DATABASE IF NOT EXISTS gram_panchayat;
USE gram_panchayat;

-- ============================================================
-- TABLE 1: users (unchanged - keeps existing login/register)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: services (unchanged)
-- ============================================================
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'fa-file-alt'
);

-- ============================================================
-- TABLE 3: applications (unchanged)
-- ============================================================
CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- ============================================================
-- TABLE 4: complaints (unchanged)
-- ============================================================
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    status ENUM('Pending', 'In Progress', 'Resolved') DEFAULT 'Pending',
    urgency_level ENUM('normal', 'urgent') DEFAULT 'normal',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- TABLE 5: NEW - service_applications_details
-- Stores detailed form data for each service application
-- ============================================================
CREATE TABLE IF NOT EXISTS service_applications_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    user_id INT NOT NULL,
    service_id INT NOT NULL,

    full_name VARCHAR(150) NOT NULL,
    father_name VARCHAR(150),
    mother_name VARCHAR(150),
    date_of_birth DATE,
    gender ENUM('Male', 'Female', 'Other'),
    address TEXT,
    village VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    mobile VARCHAR(15),
    aadhar_number VARCHAR(20),

    -- For Income Certificate
    annual_income DECIMAL(12, 2),
    occupation VARCHAR(100),

    -- For Death Certificate
    deceased_name VARCHAR(150),
    date_of_death DATE,
    cause_of_death VARCHAR(255),

    -- For Water / Electricity Request
    request_details TEXT,

    -- File Upload paths
    photo_path VARCHAR(255),
    aadhar_path VARCHAR(255),
    ration_card_path VARCHAR(255),
    other_doc_path VARCHAR(255),

    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- ============================================================
-- TABLE 6: NEW - certificates
-- ============================================================
CREATE TABLE IF NOT EXISTS certificates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    certificate_number VARCHAR(50) UNIQUE NOT NULL,
    file_path VARCHAR(255),
    issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- ============================================================
-- TABLE 7: NEW - schemes
-- ============================================================
CREATE TABLE IF NOT EXISTS schemes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    eligibility TEXT,
    benefits TEXT,
    scheme_date DATE,
    last_date DATE,
    source_url VARCHAR(500),
    poster_path VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    added_by ENUM('admin', 'auto') DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SEED DATA
-- ============================================================
INSERT IGNORE INTO users (id, name, email, password, role) VALUES 
(1, 'Admin User', 'admin@grampanchayat.gov', 'admin123', 'admin');

INSERT IGNORE INTO services (id, service_name, description, icon) VALUES
(1, 'Birth Certificate', 'Apply for an official Birth Certificate from Gram Panchayat', 'fa-baby'),
(2, 'Death Certificate', 'Apply for an official Death Certificate', 'fa-scroll'),
(3, 'Income Certificate', 'Get a certified Income Certificate for your household', 'fa-rupee-sign'),
(4, 'Water Connection', 'Request a new water connection or resolve water supply issues', 'fa-tint'),
(5, 'Electricity Request', 'Request a new power connection or report electrical issues', 'fa-bolt'),
(6, 'Residence Certificate', 'Get official proof of residence from Gram Panchayat', 'fa-home'),
(7, 'Caste Certificate', 'Apply for an OBC/SC/ST Caste Certificate', 'fa-id-card');

INSERT IGNORE INTO schemes (title, description, eligibility, benefits, scheme_date, source_url, added_by) VALUES
('PM Kisan Samman Nidhi', 
 'Financial benefit of Rs.6000 per year is transferred in three equal installments of Rs.2000 each every four months to farmer families.',
 'All land-holding farmer families with cultivable land',
 'Rs. 6000 per year direct bank transfer',
 '2019-02-01', 'https://pmkisan.gov.in', 'admin'),

('Pradhan Mantri Awas Yojana (Gramin)', 
 'PMAY-G aims to provide pucca houses with basic amenities to all homeless householders and those living in kutcha or dilapidated houses.',
 'BPL families, SC/ST households, widows, ex-servicemen in rural areas',
 'Rs. 1.20 lakh financial assistance for plain areas, Rs. 1.30 lakh for hilly areas',
 '2016-11-20', 'https://pmayg.nic.in', 'admin'),

('Mahatma Gandhi NREGA',
 'MGNREGS guarantees 100 days of wage employment in a financial year to rural households whose adult members do unskilled manual work.',
 'Adult members of rural households willing to do unskilled manual work',
 '100 days guaranteed wage employment at minimum wage rate',
 '2005-09-05', 'https://nrega.nic.in', 'admin'),

('PM Jan Arogya Yojana (Ayushman Bharat)',
 'Provides health cover of Rs. 5 lakh per family per year for secondary and tertiary care hospitalization to poor and vulnerable families.',
 'Families identified as per SECC 2011 data',
 'Health coverage up to Rs. 5 lakh per year per family',
 '2018-09-23', 'https://pmjay.gov.in', 'admin'),

('PM Ujjwala Yojana',
 'Provides free LPG connections to women from Below Poverty Line households to protect health of rural women.',
 'Women from BPL households, SC/ST households, PMAY beneficiaries',
 'Free LPG connection with financial assistance for first refill',
 '2016-05-01', 'https://pmuy.gov.in', 'admin');
