"""Preliminary CS425 console menu for phaseii.sql.

Run on the machine that can reach the PostgreSQL server:
    python main_menu.py

Requires a .env file with PGDATABASE, PGUSER, PGPASSWORD, PGHOST, PGPORT.
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

from customer_payments import (
    register_customer,
    get_customer,
    update_customer_name,
    update_customer_home_airport,
    update_customer_email,
    add_payment_address,
    list_payment_addresses,
    update_payment_address,
    delete_payment_address,
    add_credit_card,
    list_credit_cards,
    update_credit_card_address,
    delete_credit_card,
)


def heading(text):
    print("\n" + "=" * 43)
    print(text)
    print("=" * 43)


def ask(label, required=True):
    while True:
        answer = input(f"{label}: ").strip()
        if answer or not required:
            return answer
        print("This value cannot be empty.")


def ask_card_id():
    while True:
        value = ask("Enter card ID")
        if value.isdecimal() and int(value) > 0:
            return int(value)
        print("Card ID must be a positive integer.")


def confirm(message):
    return input(f"{message} (y/N): ").strip().lower() == "y"


def call_db(conn, function, *args):
    """Call a reusable function and show predictable errors without crashing."""
    try:
        return True, function(conn, *args)
    except ValueError as error:
        print(f"Error: {error}")
    except psycopg2.IntegrityError as error:
        conn.rollback()
        code = error.pgcode
        if code == "23505":
            print("Error: That record already exists (duplicate key).")
        elif code == "23503":
            print("Error: This operation violates a foreign-key relationship. ")
            print("Check that the referenced customer/airport/address exists, ")
            print("or remove dependent records before deleting.")
        elif code == "23514":
            print("Error: A database CHECK constraint was violated.")
        else:
            print(f"Database constraint error: {error.diag.message_primary or str(error)}")
    except psycopg2.Error as error:
        conn.rollback()
        print(f"Database error: {error.diag.message_primary or str(error)}")
    return False, None


def show_addresses(conn, email):
    ok, addresses = call_db(conn, list_payment_addresses, email)
    if not ok:
        return None
    if not addresses:
        print("No payment addresses saved.")
        return []
    print("\nSaved payment addresses:")
    for i, address in enumerate(addresses, start=1):
        print(f"  {i}. {address}")
    return addresses


def choose_address(conn, email):
    addresses = show_addresses(conn, email)
    if not addresses:
        return None
    while True:
        value = ask("Choose address number (0 to cancel)")
        if value.isdecimal():
            number = int(value)
            if number == 0:
                return None
            if 1 <= number <= len(addresses):
                return addresses[number - 1]
        print("Please choose one of the displayed numbers.")


def show_cards(conn, email):
    ok, cards = call_db(conn, list_credit_cards, email)
    if not ok:
        return None
    if not cards:
        print("No credit-card records saved.")
        return []
    print("\nSaved credit-card records:")
    for card_id, payment_address in cards:
        print(f"  ID {card_id}: payment address = {payment_address}")
    return cards


def select_card(conn, email):
    cards = show_cards(conn, email)
    if not cards:
        return None
    selected_id = ask_card_id()
    if selected_id not in {card_id for card_id, _ in cards}:
        print("This card ID is not associated with the selected customer.")
        return None
    return selected_id


def account_menu(conn, email):
    """Run account menu until user logs out. Return current email afterward."""
    while True:
        heading(f"ACCOUNT MENU — {email}")
        print(" 1. View profile")
        print(" 2. Change name")
        print(" 3. Change email address")
        print(" 4. Change home airport")
        print(" 5. View payment addresses")
        print(" 6. Add payment address")
        print(" 7. Edit payment address")
        print(" 8. Delete payment address")
        print(" 9. View credit cards")
        print("10. Add credit-card record")
        print("11. Change credit-card payment address")
        print("12. Delete credit-card record")
        print(" 0. Log out")
        choice = ask("Choose an option")

        if choice == "0":
            print("Account deselected.")
            return
        elif choice == "1":
            ok, customer = call_db(conn, get_customer, email)
            if ok and customer:
                email_value, name, airport = customer
                print(f"\nEmail: {email_value}\nName: {name}\nHome airport: {airport or '(not set)'}")
            elif ok:
                print("Customer not found; returning to main menu.")
                return
        elif choice == "2":
            name = ask("New name")
            ok, _ = call_db(conn, update_customer_name, email, name)
            if ok:
                print("Name updated.")
        elif choice == "3":
            new_email = ask("New email address")
            if confirm(f"Change email from {email} to {new_email}?"):
                ok, updated = call_db(conn, update_customer_email, email, new_email)
                if ok:
                    email = updated  # Update active account identity after PK change.
                    print(f"Email updated to {email}.")
        elif choice == "4":
            airport = ask("New three-letter IATA code (blank to clear)", required=False)
            ok, _ = call_db(conn, update_customer_home_airport, email, airport or None)
            if ok:
                print("Home airport updated.")
        elif choice == "5":
            show_addresses(conn, email)
        elif choice == "6":
            address = ask("Payment address")
            ok, _ = call_db(conn, add_payment_address, email, address)
            if ok:
                print("Payment address added.")
        elif choice == "7":
            old_address = choose_address(conn, email)
            if old_address is not None:
                new_address = ask("New payment address")
                ok, _ = call_db(conn, update_payment_address, email, old_address, new_address)
                if ok:
                    print("Address updated (linked cards updated, too).")
        elif choice == "8":
            address = choose_address(conn, email)
            if address is not None and confirm(f"Delete '{address}'?"):
                ok, _ = call_db(conn, delete_payment_address, email, address)
                if ok:
                    print("Address deleted.")
        elif choice == "9":
            show_cards(conn, email)
        elif choice == "10":
            address = choose_address(conn, email)
            if address is not None:
                ok, card_id = call_db(conn, add_credit_card, email, address)
                if ok:
                    print(f"Credit-card record created, ID: {card_id}.")
                    print("Note: The current schema stores no actual card number/expiry.")
        elif choice == "11":
            card_id = select_card(conn, email)
            if card_id is not None:
                address = choose_address(conn, email)
                if address is not None:
                    ok, _ = call_db(conn, update_credit_card_address, email, card_id, address)
                    if ok:
                        print("Credit-card payment address updated.")
        elif choice == "12":
            card_id = select_card(conn, email)
            if card_id is not None and confirm(f"Delete card record {card_id}?"):
                ok, _ = call_db(conn, delete_credit_card, email, card_id)
                if ok:
                    print("Credit-card record deleted.")
        else:
            print("Invalid option. Try again.")


def main_menu(conn):
    while True:
        heading("MAIN MENU — CS425 AIRLINE BOOKING (TEST)")
        print("1. Create account")
        print("2. Select existing account (TEST MODE — no authentication)")
        print("0. Exit")
        choice = ask("Choose an option")

        if choice == "0":
            print("Goodbye!")
            return
        elif choice == "1":
            email = ask("Email address")
            name = ask("Name")
            ok, registered_email = call_db(conn, register_customer, email, name)
            if ok:
                print("Customer registered successfully.")
                account_menu(conn, registered_email)
        elif choice == "2":
            print("WARNING: Test mode only. Email lookup is NOT a secure sign-in.")
            email = ask("Existing customer email")
            ok, customer = call_db(conn, get_customer, email)
            if ok and customer:
                account_menu(conn, customer[0])
            elif ok:
                print("No customer found with that email address.")
        else:
            print("Invalid option. Try again.")


def connect():
    load_dotenv()
    parameters = {
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
    }
    if os.getenv("PGSSLMODE"):
        parameters["sslmode"] = os.environ["PGSSLMODE"]
    missing = [k for k in ("dbname", "user", "password") if not parameters[k]]
    if missing:
        raise ValueError("Missing .env values for: " + ", ".join(missing))
    return psycopg2.connect(**parameters)


def main():
    try:
        conn = connect()
    except (ValueError, psycopg2.OperationalError) as error:
        print(f"Could not connect to PostgreSQL: {error}")
        return 1
    try:
        main_menu(conn)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting menu.")
    finally:
        conn.close()
        print("Database connection closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
