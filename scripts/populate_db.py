import os
import csv
import psycopg2
import time


def populate_db():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host="db"
            )
            break
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(5)
    else:
        raise Exception("Could not connect to the database")

    cur = conn.cursor()

    # Clear existing data
    cur.execute("TRUNCATE TABLE transactions, packages, persons, departments RESTART IDENTITY CASCADE")

    with open('report.csv', 'r') as f:
        reader = csv.DictReader(f)

        carriers = {}
        persons = {}

        for row in reader:
            # Insert carrier if it doesn't exist
            carrier_name = row['Item']
            if carrier_name not in carriers:
                cur.execute(
                    "INSERT INTO carriers (carrier_name) VALUES (%s) ON CONFLICT (carrier_name) DO NOTHING RETURNING carrier_id",
                    (carrier_name,))
                result = cur.fetchone()
                if result:
                    carriers[carrier_name] = result[0]
                else:
                    cur.execute("SELECT carrier_id FROM carriers WHERE carrier_name = %s", (carrier_name,))
                    carriers[carrier_name] = cur.fetchone()[0]

            # Create placeholder persons
            person_hashes = {
                'Delivered To': row.get('Delivered To'),
                'Routed To': row.get('Routed To'),
                'Stored To': osw.get('Stored To'),
                'Delivered By': row.get('Delivered By'),
                'Routed By': row.get('Routed By'),
                'Stored By': row.get('Stored By'),
            }

            for key, person_hash in person_hashes.items():
                if person_hash and person_hash not in persons:
                    # Generate a unique wpi_id. Using the hash should be fine for now.
                    # Making sure it is 9 chars long
                    wpi_id = person_hash[:9]
                    is_mailroom_worker = "By" in key
                    cur.execute(
                        "INSERT INTO persons (wpi_id, box_number, is_mailroom_worker) VALUES (%s, %s, %s) ON CONFLICT (wpi_id) DO NOTHING RETURNING wpi_id",
                        (wpi_id, person_hash, is_mailroom_worker)
                    )
                    result = cur.fetchone()
                    if result:
                        persons[person_hash] = result[0]
                    else:
                        cur.execute("SELECT wpi_id FROM persons WHERE box_number = %s", (person_hash,))
                        persons[person_hash] = cur.fetchone()[0]

            # Insert package
            cur.execute(
                "INSERT INTO packages (carrier_id, tracking_number) VALUES (%s, %s) RETURNING package_id",
                (carriers[carrier_name], row['Tracking Number'])
            )
            package_id = cur.fetchone()[0]

            # Insert transactions
            if row.get('Date Stored'):
                cur.execute(
                    "INSERT INTO transactions (date, transaction_type, locker, location, package_id, worker_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (row['Date Stored'], 'stored', f"{row['Locker Bank Name']} {row['Locker Number']}",
                     row['stored Location1'], package_id, persons[row['Stored By']])
                )
            if row.get('Date Routed'):
                cur.execute(
                    "INSERT INTO transactions (date, transaction_type, location, package_id, worker_id) VALUES (%s, %s, %s, %s, %s)",
                    (row['Date Routed'], 'routed', row['Routed Location1'], package_id, persons[row['Routed By']])
                )
            if row.get('Date Delivered'):
                cur.execute(
                    "INSERT INTO transactions (date, transaction_type, locker, location, package_id, worker_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (row['Date Delivered'], 'delivered', f"{row['Locker Bank Name']} {row['Locker Number']}",
                     row['Delivered Location1'], package_id, persons[row['Delivered By']])
                )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    populate_db()
