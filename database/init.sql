CREATE DATABASE greenboard;

CREATE TABLE carriers (
    carrier_id SERIAL PRIMARY KEY,
    carrier_name VARCHAR(20) NOT NULL
);

CREATE TYPE transport_modes AS ENUM ('air', 'ground', 'sea');

CREATE TABLE packages (
    package_id SERIAL PRIMARY KEY,
    tracking_number VARCHAR(255) NOT NULL,
    package_carrier INT NOT NULL REFERENCES carriers(carrier_id),
    service_type VARCHAR(50),
    date_shipped TIMESTAMP,
    transportation_method TRANSPORT_MODES,
    total_emissions_kg FLOAT,
    distance_traveled_mi FLOAT
);

CREATE TABLE persons (
    wpi_id CHAR(9) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_student BOOLEAN,
    is_mailroom_worker BOOLEAN,
    is_faculty BOOLEAN,
    box_number VARCHAR(5),
    class_year INT, -- If > 4 => Graduate Student
    supervisor_id CHAR(9) NULL REFERENCES persons(wpi_id)
);

-- Indicates department or major affiliation
CREATE TABLE departments (
    person_id CHAR(9) PRIMARY KEY REFERENCES persons(wpi_id),
    department_name VARCHAR(100) PRIMARY KEY
);

CREATE TYPE transaction_types AS ENUM ('delivered', 'stored', 'routed');

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    transaction_type TRANSACTION_TYPES,
    locker VARCHAR(20),
    location VARCHAR(20),
    package_id INT NOT NULL REFERENCES packages(package_id),
    worker_id CHAR(9) NOT NULL REFERENCES persons(wpi_id)
);

