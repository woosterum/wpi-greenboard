CREATE DATABASE greenboard;

CREATE TABLE carriers (
    carrier_id SERIAL PRIMARY KEY,
    carrier_name VARCHAR(20) UNIQUE NOT NULL
);

INSERT INTO carriers (carrier_name) VALUES ('Other');

CREATE TABLE emmissions (
    service_type VARCHAR(50) PRIMARY KEY,
    emission_factor FLOAT
);

CREATE TABLE persons (
    wpi_id CHAR(9) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_student BOOLEAN,
    is_mailroom_worker BOOLEAN,
    box_number VARCHAR(255),
    class_year INT, -- If > 4 => Graduate Student
    supervisor_id CHAR(9) NULL REFERENCES persons(wpi_id)
);


CREATE TABLE packages (
    package_id SERIAL PRIMARY KEY,
    carrier_id INT REFERENCES carriers(carrier_id),
    tracking_number VARCHAR(255) NOT NULL,
    recipient_id CHAR(9) NOT NULL REFERENCES persons(wpi_id),
    service_type VARCHAR(50) REFERENCES emmissions(service_type),
    date_shipped TIMESTAMP,
    total_emissions_kg FLOAT,
    distance_traveled FLOAT
);

-- Indicates department or major affiliation
CREATE TABLE departments (
    person_id CHAR(9) REFERENCES persons(wpi_id),
    department_name VARCHAR(100),
    PRIMARY KEY (person_id, department_name)
);

CREATE TYPE transaction_types AS ENUM ('delivered', 'stored', 'routed');

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    transaction_type TRANSACTION_TYPES,
    locker VARCHAR(255),
    location VARCHAR(255),
    package_id INT NOT NULL REFERENCES packages(package_id),
    worker_id CHAR(9) NOT NULL REFERENCES persons(wpi_id)
);

