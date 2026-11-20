"""Customer registration and payment-address/card operations for phaseii.sql.

Pass an already-open psycopg2 connection to each function. The caller is
responsible for closing it. Each write function commits on success and rolls
back automatically on error via the psycopg2 connection context manager.
"""


def register_customer(conn, email_address, name):
    """Create a customer. home_airport remains NULL until set later."""
    email_address = email_address.strip()
    name = name.strip()
    if not email_address or not name:
        raise ValueError("Email address and name are required.")

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO Customer (email_address, name)
                   VALUES (%s, %s)
                   RETURNING email_address;""",
                (email_address, name),
            )
            return cur.fetchone()[0]


def get_customer(conn, email_address):
    """Return (email_address, name, home_airport), or None."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT email_address, name, home_airport
                   FROM Customer WHERE email_address = %s;""",
                (email_address,),
            )
            return cur.fetchone()


def update_customer_name(conn, email_address, new_name):
    """Update a customer's name."""
    new_name = new_name.strip()

    if not new_name:
        raise ValueError("Name cannot be empty.")

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE Customer
                   SET name = %s
                   WHERE email_address = %s
                   RETURNING name;""",
                (new_name, email_address)
            )

            if cur.fetchone() is None:
                raise ValueError("Customer not found.")


def update_customer_home_airport(conn, email_address, new_airport):
    """Update a customer's home airport."""
    new_airport = new_airport.strip().upper() if new_airport else None

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE Customer
                   SET home_airport = %s
                   WHERE email_address = %s
                   RETURNING home_airport;""",
                (new_airport, email_address)
            )

            if cur.fetchone() is None:
                raise ValueError("Customer not found.")


def update_customer_email(conn, old_email, new_email):
    """Change a customer's email while preserving cards, addresses and bookings."""
    new_email = new_email.strip()

    if not new_email:
        raise ValueError("Email cannot be empty.")

    if old_email == new_email:
        return new_email

    with conn:
        with conn.cursor() as cur:

            # Get existing customer
            cur.execute(
                """SELECT name, home_airport
                   FROM Customer
                   WHERE email_address = %s
                   FOR UPDATE;""",
                (old_email,)
            )

            customer = cur.fetchone()

            if customer is None:
                raise ValueError("Customer not found.")

            name, home_airport = customer

            # Create customer with new email
            cur.execute(
                """INSERT INTO Customer
                   (email_address, name, home_airport)
                   VALUES (%s, %s, %s);""",
                (new_email, name, home_airport)
            )

            # Copy payment addresses
            cur.execute(
                """INSERT INTO Customer_Payment_Address
                   (email_address, payment_address)
                   SELECT %s, payment_address
                   FROM Customer_Payment_Address
                   WHERE email_address = %s;""",
                (new_email, old_email)
            )

            # Reassign credit cards
            cur.execute(
                """UPDATE Credit_Card
                   SET email_address = %s
                   WHERE email_address = %s;""",
                (new_email, old_email)
            )

            # Reassign bookings
            cur.execute(
                """UPDATE Booking
                   SET email_address = %s
                   WHERE email_address = %s;""",
                (new_email, old_email)
            )

            # Remove old payment addresses
            cur.execute(
                """DELETE FROM Customer_Payment_Address
                   WHERE email_address = %s;""",
                (old_email,)
            )

            # Remove original customer record
            cur.execute(
                """DELETE FROM Customer
                   WHERE email_address = %s;""",
                (old_email,)
            )

    return new_email


def add_payment_address(conn, email_address, payment_address):
    """Add one address for a registered customer."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO Customer_Payment_Address
                   (email_address, payment_address)
                   VALUES (%s, %s);""",
                (email_address, payment_address),
            )


def list_payment_addresses(conn, email_address):
    """Return a list of strings containing this customer's addresses."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT payment_address
                   FROM Customer_Payment_Address
                   WHERE email_address = %s
                   ORDER BY payment_address;""",
                (email_address,),
            )
            return [row[0] for row in cur.fetchall()]


def update_payment_address(conn, email_address, old_address, new_address):
    """Rename an address, updating any cards that use it, atomically.

    The existing schema's FK has no ON UPDATE CASCADE; inserting the new
    address, repointing cards, then deleting the old one works without altering
    the schema. A duplicate new address will raise a UNIQUE violation.
    """
    if old_address == new_address:
        return "New address must be different from the old address."
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT 1 FROM Customer_Payment_Address
                   WHERE email_address = %s AND payment_address = %s
                   FOR UPDATE;""",
                (email_address, old_address),
            )
            if cur.fetchone() is None:
                raise ValueError("The original address was not found.")
            cur.execute(
                """INSERT INTO Customer_Payment_Address
                   (email_address, payment_address) VALUES (%s, %s);""",
                (email_address, new_address),
            )
            cur.execute(
                """UPDATE Credit_Card
                   SET payment_address = %s
                   WHERE email_address = %s AND payment_address = %s;""",
                (new_address, email_address, old_address),
            )
            cur.execute(
                """DELETE FROM Customer_Payment_Address
                   WHERE email_address = %s AND payment_address = %s;""",
                (email_address, old_address),
            )


def delete_payment_address(conn, email_address, payment_address):
    """Delete an address only if no credit card still references it."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM Customer_Payment_Address
                   WHERE email_address = %s AND payment_address = %s
                   RETURNING payment_address;""",
                (email_address, payment_address),
            )
            if cur.fetchone() is None:
                raise ValueError("Address not found.")


def add_credit_card(conn, email_address, payment_address):
    """Create a card record linked to an existing address; return its ID."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO Credit_Card (email_address, payment_address)
                   VALUES (%s, %s) RETURNING card_id;""",
                (email_address, payment_address),
            )
            return cur.fetchone()[0]


def list_credit_cards(conn, email_address):
    """Return (card_id, payment_address) tuples for this customer."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT card_id, payment_address
                   FROM Credit_Card
                   WHERE email_address = %s
                   ORDER BY card_id;""",
                (email_address,),
            )
            return cur.fetchall()


def update_credit_card_address(conn, email_address, card_id, payment_address):
    """Set a card's payment address, restricted to its owner's addresses."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE Credit_Card
                   SET payment_address = %s
                   WHERE card_id = %s AND email_address = %s
                   RETURNING card_id;""",
                (payment_address, card_id, email_address),
            )
            if cur.fetchone() is None:
                raise ValueError("Card not found for this customer.")


def delete_credit_card(conn, email_address, card_id):
    """Delete an unused card; FK to BookingFlight may prevent deletion."""
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM Credit_Card
                   WHERE card_id = %s AND email_address = %s
                   RETURNING card_id;""",
                (card_id, email_address),
            )
            if cur.fetchone() is None:
                raise ValueError("Card not found for this customer.")

#IMPORTANT: deleting a card already used in BookingFlight will be blocked by the existing foreign key. We can decide later whether to preserve historical cards through an inactive status instead.
