-- ====================================================================
-- ViziCheck - Production-Grade Testing Database Seed Script (MySQL)
-- Safe cleanup + dependency-ordered seed data for Postman API Testing
-- ====================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Truncate testing tables safely
TRUNCATE TABLE checkins;
TRUNCATE TABLE scan_logs;
TRUNCATE TABLE gate_event_history;
TRUNCATE TABLE qr_tokens;
TRUNCATE TABLE pass_status_history;
TRUNCATE TABLE visitor_passes;
TRUNCATE TABLE visit_requests;
TRUNCATE TABLE visitors;
TRUNCATE TABLE audit_logs;

SET FOREIGN_KEY_CHECKS = 1;

-- 2. Seed Base System Roles if missing
INSERT IGNORE INTO roles (id, name, description, created_at) VALUES 
(1, 'SUPER_ADMIN', 'Platform Administrator with unrestricted privileges', NOW()),
(2, 'TENANT_ADMIN', 'Tenant Administrator for tenant-wide operations', NOW()),
(3, 'SECURITY_OFFICER', 'Security Guard handling gate check-in/out', NOW()),
(4, 'VISITOR', 'External Visitor account', NOW());

-- 3. Seed Testing Tenants
INSERT IGNORE INTO tenants (id, code, name, slug, contact_person, contact_email, contact_phone, description, status, created_at) VALUES
(101, 'TEN-CAPNIS01', 'Capnis Infotech Pvt Ltd', 'capnis-infotech', 'Rajesh Sharma', 'contact@capnis.com', '+918041234567', 'Building 4, Electronic City Phase 1, Bengaluru, Karnataka 560100', 'ACTIVE', NOW()),
(102, 'TEN-TCS02', 'Tata Consultancy Services', 'tata-consultancy', 'Ananya Verma', 'contact@tcs.com', '+912267778888', 'TCS House, Raveline Street, Fort, Mumbai, Maharashtra 400001', 'ACTIVE', NOW());

-- 4. Seed Test Users (Password: TestPassword123!)
-- Argon2id/bcrypt password hash for 'TestPassword123!'
SET @TEST_PWD = '$2b$12$K8Z0bM73wU.bTpx94k.NceG2JvK7M8B9aW0cE1dF2gH3iJ4k5l6m6';

INSERT IGNORE INTO users (id, role_id, tenant_id, first_name, last_name, email, phone, password_hash, is_active, created_at) VALUES
(1, 1, NULL, 'Super', 'Admin', 'admin@vizicheck.com', '+919876543210', @TEST_PWD, 1, NOW()),
(2, 2, 101, 'Admin', 'Kumar', 'admin.capnis-infotech@vizicheck.com', '+91981010001', @TEST_PWD, 1, NOW()),
(3, 1, 101, 'Vikram', 'Singh', 'vikram.singh@capnis-infotech.com', '+91981010002', @TEST_PWD, 1, NOW()),
(4, 3, 101, 'Guard', 'Kumar', 'security.capnis-infotech@vizicheck.com', '+91981010003', @TEST_PWD, 1, NOW()),
(5, 2, 102, 'Admin', 'Sharma', 'admin.tata-consultancy@vizicheck.com', '+91981020001', @TEST_PWD, 1, NOW()),
(6, 1, 102, 'Priya', 'Nair', 'priya.nair@tata-consultancy.com', '+91981020002', @TEST_PWD, 1, NOW()),
(7, 3, 102, 'Security', 'Officer', 'security.tata-consultancy@vizicheck.com', '+91981020003', @TEST_PWD, 1, NOW());

-- 5. Seed Test Visitors for Capnis Infotech (Tenant 101)
INSERT INTO visitors (id, tenant_id, visitor_code, first_name, last_name, email, phone, company, government_id_type, government_id_number, status, created_at) VALUES
(1001, 101, 'VIS-TEN-CAPNIS01-0001', 'Rohan', 'Patel', 'rohan.patel@infosys.com', '+91971010001', 'Infosys Ltd', 'AADHAAR', '7890-1234-1001', 'ACTIVE', NOW()),
(1002, 101, 'VIS-TEN-CAPNIS01-0002', 'Sunita', 'Mukherjee', 'sunita.m@wipro.com', '+91971010002', 'Wipro Digital', 'PAN', '7890-1234-1002', 'ACTIVE', NOW()),
(1003, 101, 'VIS-TEN-CAPNIS01-0003', 'Amitabh', 'Roy', 'amitabh.roy@jio.com', '+91971010003', 'Reliance Jio', 'PASSPORT', '7890-1234-1003', 'BLACKLISTED', NOW());

-- 6. Seed Visit Requests
INSERT INTO visit_requests (id, tenant_id, request_code, visitor_id, host_id, purpose, department, scheduled_start_time, scheduled_end_time, status, created_by, approved_by, approved_at, created_at) VALUES
(2001, 101, 'REQ-TEN-CAPNIS01-0001', 1001, 3, 'Product Demonstration & Architecture Sync', 'Engineering', NOW() - INTERVAL 1 HOUR, NOW() + INTERVAL 7 HOUR, 'APPROVED', 3, 3, NOW() - INTERVAL 1 HOUR, NOW()),
(2002, 101, 'REQ-TEN-CAPNIS01-0002', 1002, 3, 'Annual Vendor Compliance Audit', 'Human Resources', NOW() + INTERVAL 2 HOUR, NOW() + INTERVAL 10 HOUR, 'PENDING', 3, NULL, NULL, NOW());

-- 7. Seed Visitor Pass
INSERT INTO visitor_passes (id, uuid, tenant_id, pass_code, visit_request_id, visitor_id, host_id, valid_from, valid_until, status, latest_qr_version, created_at) VALUES
(3001, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 101, 'VP-2026-TEN-CAPNIS01-0001', 2001, 1001, 3, NOW() - INTERVAL 1 HOUR, NOW() + INTERVAL 7 HOUR, 'ACTIVE', 1, NOW());

-- 8. Seed Active QR Token
INSERT INTO qr_tokens (id, tenant_id, pass_id, version, token, is_active, expires_at, created_at) VALUES
(4001, 101, 3001, 1, 'VIZICHECK:PASS:a1b2c3d4-e5f6-7890-abcd-ef1234567890:V1:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhMWIyYzNkNC1lNWY2LTc4OTAtYWJjZC1lZjEyMzQ1Njc4OTAiLCJ0ZW5hbnRfaWQiOjEwMSwidmlzaXRvcl9pZCI6MTAwMSwidmlzaXRfcmVxdWVzdF9pZCI6MjAwMSwidmVyc2lvbiI6MSwidG9rZW5fdHlwZSI6IlZJU0lUT1JfUEFTUyIsImlzcyI6IlZpemlDaGVjayIsImF1ZCI6IkdhdGVTY2FubmVyIiwiaWF0IjoxNzg1NDI2NTMxLCJleHAiOjE3ODU0NDA5MzF9.mockSignatureHashString', 1, NOW() + INTERVAL 7 HOUR, NOW());

-- 9. Seed Active Check-In
INSERT INTO checkins (id, uuid, tenant_id, pass_id, visit_request_id, visitor_id, host_id, checkin_time, status, gate_device_id, scanner_name, scanner_ip, scanner_location, scanner_version, gate_name, gate_number, verification_method, checked_in_by, created_at) VALUES
(5001, UUID(), 101, 3001, 2001, 1001, 3, NOW() - INTERVAL 30 MINUTE, 'CHECKED_IN', 'DEV-GATE-CAPNIS-01', 'North Gate Scanner', '192.168.1.101', 'North Lobby Entrance', 'v1.2.0', 'North Gate', 'Gate 1', 'QR_SCAN', 4, NOW());

-- ====================================================================
-- SEED COMPLETE
-- ====================================================================
