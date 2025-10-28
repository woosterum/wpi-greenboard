-- ---
-- Schema Definition
-- ---
-- Drop existing tables in reverse order of dependency
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS packages;
DROP TABLE IF EXISTS persons;
DROP TABLE IF EXISTS emissions;
DROP TABLE IF EXISTS carriers;
DROP TYPE IF EXISTS transaction_types;

-- Create the carriers table
CREATE TABLE carriers (
    carrier_id SERIAL PRIMARY KEY,
    carrier_name VARCHAR(20) NOT NULL
);

-- Insert the default 'Other' carrier as per the prompt's instructions
INSERT INTO carriers (carrier_name) VALUES ('Other');

-- Create the emissions lookup table
CREATE TABLE emissions (
    service_type VARCHAR(50) PRIMARY KEY,
    emission_factor FLOAT
);

-- Create the persons table (students, faculty, and workers)
-- wpi_id is CHAR(9) to store 9-digit numbers as strings
CREATE TABLE persons (
    wpi_id CHAR(9) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_student BOOLEAN,
    is_mailroom_worker BOOLEAN,
    box_number VARCHAR(5),
    class_year INT, -- If > 4 => Graduate Student
    supervisor_id CHAR(9) NULL,
    CONSTRAINT supervisor_fk
        FOREIGN KEY (supervisor_id)
        REFERENCES persons(wpi_id)
        ON DELETE SET NULL  -- if supervisor is deleted, set supervisor_id to null
        ON UPDATE CASCADE
);

-- Create the departments table (links person to one or more departments)
CREATE TABLE departments (
    person_id CHAR(9) NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (person_id, department_name),
    CONSTRAINT departments_fk
        FOREIGN KEY (person_id)
        REFERENCES persons(wpi_id)
        ON DELETE CASCADE  -- delete departments when person is deleted
        ON UPDATE CASCADE
);

-- Create the packages table
CREATE TABLE packages (
    package_id SERIAL PRIMARY KEY,
    carrier_id INT NULL,
    recipient_id CHAR(9) NULL,
    tracking_number VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NULL,
    date_shipped TIMESTAMP,
    total_emissions_kg FLOAT,
    distance_traveled FLOAT,
    CONSTRAINT packages_recipient_fk
        FOREIGN KEY (recipient_id)
        REFERENCES persons(wpi_id)
        ON DELETE SET NULL  -- keep package if an recipient row is deleted
        ON UPDATE CASCADE,
    CONSTRAINT carrier_id_fk
        FOREIGN KEY (carrier_id)
        REFERENCES carriers(carrier_id)
        ON DELETE RESTRICT  -- cannot delete carrier if package references it
        ON UPDATE CASCADE,
    CONSTRAINT service_type_fk
        FOREIGN KEY (service_type)
        REFERENCES emissions(service_type)
        ON DELETE SET NULL  -- keep package if an emissions row is deleted
        ON UPDATE CASCADE
);

-- Create the ENUM type for transactions
CREATE TYPE transaction_types AS ENUM ('delivered', 'stored', 'routed');

-- Create the transactions table (logs all package events)
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    transaction_type TRANSACTION_TYPES,
    locker VARCHAR(20),
    location VARCHAR(20),
    package_id INT NOT NULL,
    worker_id CHAR(9) NULL,
    CONSTRAINT transactions_package_fk
        FOREIGN KEY (package_id)
        REFERENCES packages(package_id)
        ON DELETE RESTRICT  -- block deleting a package if transactions exist
        ON UPDATE CASCADE,
    CONSTRAINT transactions_worker_fk
        FOREIGN KEY (worker_id)
        REFERENCES persons(wpi_id)
        ON DELETE SET NULL  -- keep transaction if worker is deleted
        ON UPDATE CASCADE
);

-- ---
-- Sample Data Population
-- ---

-- Clear existing data.
TRUNCATE TABLE transactions, departments, packages, persons, emissions, carriers RESTART IDENTITY CASCADE;

-- 1. Populate 'carriers'
-- ('Other' will be ID 1, 'UPS' ID 2, etc.)
INSERT INTO carriers (carrier_name) VALUES
('Other'),
('UPS'),
('FedEx'),
('USPS'),
('DHL');

-- 2. Populate 'emissions'
INSERT INTO emissions (service_type, emission_factor) VALUES
('UPS Ground', 0.52),
('UPS Next Day Air', 1.15),
('FedEx Ground', 0.49),
('FedEx Express', 1.08),
('USPS Priority', 0.61),
('DHL Express', 0.95),
('Other', 0.75); -- A generic factor for 'Other'

-- 3. Populate 'persons'
-- (Supervisors first, using 9-digit numeric strings for wpi_id)
INSERT INTO persons (wpi_id, first_name, last_name, is_student, is_mailroom_worker, box_number, class_year, supervisor_id)
VALUES
-- Mailroom Staff (Start with 9s)
('900000001', 'Maria', 'Supervisor', FALSE, TRUE, NULL, NULL, NULL),
('900000002', 'Bob', 'Builder', FALSE, TRUE, NULL, NULL, '900000001'),
('900000003', 'Wendy', 'Worker', FALSE, TRUE, NULL, NULL, '900000001'),
-- Students (Start with 1s)
('100000001', 'Alice', 'Anderson', TRUE, FALSE, '1001', 2025, NULL),
('100000002', 'Charlie', 'Chaplin', TRUE, FALSE, '1002', 2027, NULL), -- Grad student
('100000004', 'Frank', 'Farmer', TRUE, FALSE, '1004', 2026, NULL),
('100000005', 'Grace', 'Hopper', TRUE, FALSE, '1005', 2025, NULL),
('100000006', 'Henry', 'Hudson', TRUE, FALSE, '1006', 2028, NULL),
-- Faculty (Start with 8s)
('800000001', 'David', 'Davidson', FALSE, FALSE, '9001', NULL, NULL), -- Dept. box
-- Student Worker (Student ID, but mailroom worker)
('100000003', 'Eve', 'Employee', TRUE, TRUE, '1003', 2026, '900000002'); -- Supervised by Bob

-- 4. Populate 'departments'
INSERT INTO departments (person_id, department_name) VALUES
('900000001', 'Mailroom'),
('900000002', 'Mailroom'),
('900000003', 'Mailroom'),
('100000001', 'Computer Science'),
('100000002', 'Robotics Engineering'),
('100000004', 'Biology'),
('100000005', 'Computer Science'),
('100000006', 'Civil Engineering'),
('800000001', 'Computer Science'),
('100000003', 'Mechanical Engineering'),
('100000003', 'Mailroom'); -- Student worker belongs to two departments

-- 5. Populate 'packages'
-- (IDs 1-10)
INSERT INTO packages (carrier_id, tracking_number, recipient_id, service_type, date_shipped, total_emissions_kg, distance_traveled)
VALUES
(
    2, -- UPS
    '1Z12345E0100000001',
    '100000001', -- Alice
    'UPS Ground',
    '2025-10-25 10:00:00',
    130.0,
    250.0
),
(
    3, -- FedEx
    '987654321098',
    '800000001', -- David
    'FedEx Express',
    '2025-10-26 15:00:00',
    540.0,
    500.0
),
(
    4, -- USPS
    '9400100000000000000012',
    '100000002', -- Charlie
    'USPS Priority',
    '2025-10-27 08:00:00',
    91.5,
    150.0
),
(
    2, -- UPS
    '1Z_AUTO_LOCKER_PKG',
    '100000003', -- Eve
    'UPS Next Day Air',
    '2025-10-27 12:00:00',
    230.0,
    200.0
),
(
    5, -- DHL
    '4444555566',
    '100000001', -- Alice (second package)
    'DHL Express',
    '2025-09-15 12:00:00',
    1900.0,
    2000.0
),
-- New Packages
(
    4, -- USPS
    '9400100000000000000020',
    '100000004', -- Frank
    'USPS Priority',
    '2025-10-20 16:00:00',
    61.0,
    100.0
),
(
    3, -- FedEx
    '787878787878',
    '100000005', -- Grace
    'FedEx Ground',
    '2025-10-21 11:30:00',
    367.5,
    750.0
),
(
    2, -- UPS
    '1Z9876543210000001',
    '100000006', -- Henry
    'UPS Ground',
    '2025-10-26 17:00:00',
    26.0,
    50.0
),
(
    1, -- Other
    'AMZN_L_123456789',
    '100000004', -- Frank (second package)
    'Other',
    '2025-10-26 10:00:00',
    150.0,
    200.0
),
(
    2, -- UPS
    '1Z1111111111111111',
    '100000005', -- Grace (second package)
    'UPS Next Day Air',
    '2025-10-27 14:00:00',
    1150.0,
    1000.0
);


-- 6. Populate 'transactions'
INSERT INTO transactions (date, transaction_type, locker, location, package_id, worker_id)
VALUES
-- Package 1 (Alice): Stored, then Delivered
(
    '2025-10-27 09:15:00',
    'stored',
    'CC-Lobby A101',
    '1001',
    1, -- Package 1
    '900000002' -- Bob
),
(
    '2025-10-27 14:30:00',
    'delivered',
    'CC-Lobby A101',
    '1001',
    1, -- Package 1
    '100000003' -- Eve (student worker)
),

-- Package 2 (David): Routed to department
(
    '2025-10-28 10:00:00',
    'routed',
    NULL, -- No locker
    '9001', -- Dept. box location
    2, -- Package 2
    '900000003' -- Wendy
),

-- Package 3 (Charlie): Stored, not yet picked up
(
    '2025-10-28 11:00:00',
    'stored',
    'Gateway-01 B05',
    '1002',
    3, -- Package 3
    '900000002' -- Bob
),

-- Package 4 (Eve): Stored by automated system (NULL worker_id)
(
    '2025-10-28 11:15:00',
    'stored',
    'AUTO-LKR-01',
    '1003',
    4, -- Package 4
    NULL -- Automated system
),
(
    '2025-10-28 11:16:00', -- Eve picked it up a minute later
    'delivered',
    'AUTO-LKR-01',
    '1003',
    4, -- Package 4
    NULL -- Automated system
),

-- Package 5 (Alice's 2nd): Stored and Delivered by Supervisor
(
    '2025-09-18 10:20:00',
    'stored',
    'CC-Lobby C212',
    '1001',
    5, -- Package 5
    '900000001' -- Maria
),
(
    '2025-09-18 17:00:00',
    'delivered',
    'CC-Lobby C212',
    '1001',
    5, -- Package 5
    '900000001' -- Maria
),

-- Package 6 (Frank): Stored and Delivered
(
    '2025-10-22 13:00:00',
    'stored',
    'Gateway-01 C10',
    '1004',
    6, -- Package 6
    '900000003' -- Wendy
),
(
    '2025-10-23 09:30:00',
    'delivered',
    'Gateway-01 C10',
    '1004',
    6, -- Package 6
    '900000003' -- Wendy
),

-- Package 7 (Grace): Stored, not yet picked up
(
    '2025-10-23 14:00:00',
    'stored',
    'CC-Lobby D01',
    '1005',
    7, -- Package 7
    '900000002' -- Bob
),

-- Package 8 (Henry): Stored, not yet picked up
(
    '2025-10-28 10:30:00',
    'stored',
    'CC-Lobby D02',
    '1006',
    8, -- Package 8
    '100000003' -- Eve
),

-- Package 9 (Frank's 2nd): Stored, not yet picked up
(
    '2025-10-28 11:10:00',
    'stored',
    'Gateway-01 C11',
    '1004',
    9, -- Package 9
    '900000003' -- Wendy
),

-- Package 10 (Grace's 2nd): Stored, not yet picked up
(
    '2025-10-28 11:18:00',
    'stored',
    'CC-Lobby D03',
    '1005',
    10, -- Package 10
    '100000003' -- Eve
);
