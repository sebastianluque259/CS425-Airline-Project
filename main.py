import os
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
from prettytable import PrettyTable
import getpass

from customer_payments import (
    register_customer,
    get_customer,
    add_payment_address,
    list_payment_addresses,
    update_payment_address,
    delete_payment_address,
    add_credit_card,
    list_credit_cards,
    update_credit_card_address,
    delete_credit_card,
)


# Step 2: Load environment variables
load_dotenv()

print("Database Configuration:")
print(f"Database: {os.environ.get('PGDATABASE')}")
print(f"Host: {os.environ.get('PGHOST')}")
print(f"Port: {os.environ.get('PGPORT')}")
print(f"User: {os.environ.get('PGUSER')}")

print(
    f"Password: "
    f"{'Set' if os.environ.get('PGPASSWORD') else 'Not set'}"
)


# Step 3: Build connection parameters
conn_params = {
    "dbname": os.environ.get("PGDATABASE"),
    "user": os.environ.get("PGUSER"),
    "password": os.environ.get("PGPASSWORD"),
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432")
}


# Check required credentials
required_vars = ["dbname", "user", "password"]

missing = [
    var for var in required_vars
    if not conn_params.get(var)
]

if missing:
    print(f"Missing credentials: {missing}")
    exit()
else:
    print("All required credentials are present")


# Step 4: Connect to PostgreSQL
conn = None

try:
    conn = psycopg2.connect(**conn_params)
    print("\nConnection successful!")

except OperationalError as e:
    print(f"Connection failed: {e}")
    exit()


try:

    # ==========================================
    # Step 5: Test the connection
    # Slide 13
    # ==========================================

    with conn.cursor() as cursor:

        cursor.execute("SELECT version();")

        print(
            f"\nPostgreSQL version: "
            f"{cursor.fetchone()[0][:50]}..."
        )

        cursor.execute("""
            SELECT current_database() AS db,
                   current_user AS user,
                   inet_server_addr() AS server;
        """)

        db_info = cursor.fetchone()

        print(f"Database: {db_info[0]}")
        print(f"User: {db_info[1]}")
        print(f"Server: {db_info[2]}")

        # Retrieve all tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()

        print(f"\nTables: {len(tables)} found")

        for table in tables:
            print(table[0])


    # Step 6: SELECT with a cursor


    print("\n--- AIRPORT INFORMATION ---")

    select_sql = """
        SELECT iata_id, name, country, state
        FROM Airport;
    """

    with conn.cursor() as cursor:

        cursor.execute(select_sql)

        airports = cursor.fetchall()

        for row in airports:

            print(
                f"ID: {row[0]}, "
                f"Airport: {row[1]}, "
                f"Country: {row[2]}, "
                f"State: {row[3]}"
            )


    # ==========================================
    # Step 7: Formatted flight report
    # Slide 17
    # ==========================================

    print("\n--- FLIGHT PRICE REPORT ---")

    select_sql = """
        SELECT airline_code,
               flight_number,
               departure_airport,
               destination_airport,
               economy_price,
               first_price
        FROM Flight
        ORDER BY economy_price DESC;
    """

    with conn.cursor() as cursor:

        cursor.execute(select_sql)

        print("-" * 85)

        print(
            f"{'Airline':<10} "
            f"{'Flight':<10} "
            f"{'Departure':<12} "
            f"{'Destination':<15} "
            f"{'Economy':>15} "
            f"{'First':>15}"
        )

        print("-" * 85)

        for row in cursor.fetchall():

            airline_code, flight_number, departure, destination, economy, first = row

            formatted_economy = "${:,.2f}".format(economy)

            formatted_first = "${:,.2f}".format(first)

            print(
                f"{airline_code:<10} "
                f"{flight_number:<10} "
                f"{departure:<12} "
                f"{destination:<15} "
                f"{formatted_economy:>15} "
                f"{formatted_first:>15}"
            )

        print("-" * 85)


    # ==========================================
    # Step 8: Parameterized SELECT
    # Slides 18-19
    # ==========================================

    print("\n--- FLIGHTS DEPARTING FROM ORD ---")

    select_sql = """
        SELECT airline_code,
               flight_number,
               departure_airport,
               destination_airport,
               flight_date
        FROM Flight
        WHERE departure_airport = %s;
    """

    with conn.cursor() as cursor:

        cursor.execute(select_sql, ("ORD",))

        flights = cursor.fetchall()

        if flights:

            for row in flights:

                print(
                    f"Airline: {row[0]}, "
                    f"Flight: {row[1]}, "
                    f"From: {row[2]}, "
                    f"To: {row[3]}, "
                    f"Date: {row[4]}"
                )

        else:
            print("No flights found.")


    # ==========================================
    # Step 9: Parameterized SELECT with user input
    # Slide 20
    # ==========================================

    print("\n--- SEARCH FOR FLIGHTS ---")

    departure = input(
        "Enter departure airport: "
    ).strip().upper()

    destination = input(
        "Enter destination airport: "
    ).strip().upper()

    select_sql = """
        SELECT airline_code,
               flight_number,
               departure_airport,
               destination_airport,
               flight_date,
               economy_price,
               first_price
        FROM Flight
        WHERE departure_airport = %s
          AND destination_airport = %s;
    """

    with conn.cursor() as cursor:

        cursor.execute(
            select_sql,
            (departure, destination)
        )

        flights = cursor.fetchall()

        if flights:

            for row in flights:

                print(
                    f"Airline: {row[0]}, "
                    f"Flight: {row[1]}, "
                    f"From: {row[2]}, "
                    f"To: {row[3]}, "
                    f"Date: {row[4]}, "
                    f"Economy: ${row[5]}, "
                    f"First: ${row[6]}"
                )

        else:
            print("No flights found.")


    # ==========================================
    # Step 10: Display flights with PrettyTable
    # Slide 21
    # ==========================================

    print("\n--- ALL FLIGHTS ---")

    with conn.cursor() as cursor:

        cursor.execute("""
            SELECT airline_code,
                   flight_number,
                   departure_airport,
                   destination_airport,
                   flight_date,
                   economy_price,
                   first_price
            FROM Flight
            ORDER BY flight_date;
        """)

        flights = cursor.fetchall()

        table = PrettyTable()

        table.field_names = [
            "Airline",
            "Flight Number",
            "Departure",
            "Destination",
            "Flight Date",
            "Economy Price",
            "First Price"
        ]

        for row in flights:

            table.add_row(row)

        print(table)


    # ==========================================
    # Step 11: Display customers with PrettyTable
    # ==========================================

    print("\n--- ALL CUSTOMERS ---")

    with conn.cursor() as cursor:

        cursor.execute("""
            SELECT email_address,
                   name,
                   home_airport
            FROM Customer;
        """)

        customers = cursor.fetchall()

        table = PrettyTable()

        table.field_names = [
            "Email Address",
            "Customer Name",
            "Home Airport"
        ]

        for row in customers:

            table.add_row(row)

        print(table)


    # ==========================================
    # Step 12: Display airlines with PrettyTable
    # ==========================================

    print("\n--- ALL AIRLINES ---")

    with conn.cursor() as cursor:

        cursor.execute("""
            SELECT airline_code,
                   name,
                   country_origin
            FROM Airline;
        """)

        airlines = cursor.fetchall()

        table = PrettyTable()

        table.field_names = [
            "Airline Code",
            "Airline Name",
            "Country of Origin"
        ]

        for row in airlines:

            table.add_row(row)

        print(table)


# Handle database errors
except Exception as e:

    print("An error occurred:", e)

    conn.rollback()


# Close the database connection
finally:

    if conn is not None and not conn.closed:

        conn.close()

        print("\nConnection closed.")
