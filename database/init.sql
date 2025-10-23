CREATE DATABASE greenboard;

CREATE TABLE carriers (
    carrier_id SERIAL PRIMARY KEY,
    carrier_name VARCHAR(20) NOT NULL
);

INSERT INTO carriers (carrier_name) VALUES ('Other');

CREATE TABLE emissions (
    service_type VARCHAR(50) PRIMARY KEY,
    emission_factor FLOAT
);

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

-- Indicates department or major affiliation
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

CREATE TYPE transaction_types AS ENUM ('delivered', 'stored', 'routed');

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
