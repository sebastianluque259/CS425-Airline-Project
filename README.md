# CS425-Airline-Project

SQL-Based Airline Application

## Customer Registration & Account Management

This module implements customer registration, profile management, payment-address management, and basic credit-card management for the CS425 Airline Flight Booking Application.

The application uses **Python**, **PostgreSQL**, and **psycopg2**, with a preliminary console interface for testing.

### 1. Implemented Features

#### Customer Registration and Profile Management

| Feature             | Description                                                                                  |
| ------------------- | -------------------------------------------------------------------------------------------- |
| Register Customer   | Create a new account with an email address and name.                                         |
| View Profile        | Retrieve a customer's email, name, and home airport.                                         |
| Update Name         | Modify a customer's name.                                                                    |
| Update Email        | Change a customer's email while preserving associated addresses, credit cards, and bookings. |
| Update Home Airport | Assign, change, or clear a customer's home airport.                                          |

Each customer is uniquely identified by their email address, which serves as the primary key in the `Customer` table.

#### Payment Address Management

| Feature        | Description                                                              |
| -------------- | ------------------------------------------------------------------------ |
| Add Address    | Register a new payment address for a customer.                           |
| View Addresses | List all addresses associated with a customer.                           |
| Update Address | Modify an existing address and automatically update linked credit cards. |
| Delete Address | Remove an address if no credit card currently references it.             |

Addresses are stored in the `Customer_Payment_Address` table.

The composite primary key `(email_address, payment_address)` prevents duplicate addresses for the same customer.

#### Credit Card Management

| Feature                | Description                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------- |
| Add Credit Card        | Create a credit-card record associated with a customer's existing payment address. |
| View Credit Cards      | Retrieve all credit-card records belonging to a customer.                          |
| Update Payment Address | Change the billing address associated with a credit card.                          |
| Delete Credit Card     | Remove a credit-card record if no existing booking references it.                  |

Each credit card is uniquely identified by a PostgreSQL-generated `card_id`.

**Current limitation:** The database currently stores only the card ID, customer email, and payment address. Actual card details such as expiration dates or card numbers are not yet implemented.

### 2. Project Structure

The current implementation uses the following files:

```text
project/
├── main.py
├── main_menu.py
├── customer_payments.py
├── test_customer_payments.py
├── phaseii.sql
├── requirements.txt
├── .env
└── .gitignore
```

**File descriptions:**

- `main.py` — Original PostgreSQL connection and database-query demonstration script.
- `main_menu.py` — Preliminary console interface for customer and payment management.
- `customer_payments.py` — Reusable Python functions implementing customer and payment operations.
- `test_customer_payments.py` — Offline unit tests for database operations.
- `phaseii.sql` — PostgreSQL relational schema from Phase II.
- `requirements.txt` — Required Python dependencies.
- `.env` — Local database connection credentials (not committed to GitHub).

### 3. Setup Instructions

#### Step 1 — Create a virtual environment

From the project root directory:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

#### Step 2 — Install dependencies

```bash
python -m pip install -r requirements.txt
```

The required packages are:

| Package           | Purpose                      |
| ----------------- | ---------------------------- |
| `psycopg2-binary` | PostgreSQL connectivity      |
| `python-dotenv`   | Loading database credentials |
| `prettytable`     | Formatting SQL query results |

#### Step 3 — Configure PostgreSQL

The application requires access to a PostgreSQL database containing the tables defined in `phaseii.sql`.

Create a `.env` file in the project root directory:

```dotenv
PGDATABASE=your_database_name
PGUSER=your_postgres_username
PGPASSWORD=your_postgres_password
PGHOST=localhost
PGPORT=5432
```

Replace the placeholder values with the correct database credentials.

If connecting to a remote PostgreSQL server, replace `localhost` with the appropriate server hostname. Configure SSL as required by the server; the console also supports an optional `PGSSLMODE` environment variable.

**Important:** Never commit `.env` or database passwords to GitHub.

Include these entries in `.gitignore`:

```gitignore
.venv/
.env
__pycache__/
```

#### Step 4 — Run the application

Start the console interface:

```bash
python main_menu.py
```

The program automatically attempts to connect to PostgreSQL using the provided environment variables.

### 4. Console Interface

The current application uses a text-based interface rather than a graphical interface.

#### Main Menu

```text
===========================================
MAIN MENU — CS425 AIRLINE BOOKING (TEST)
===========================================
1. Create account
2. Select existing account (TEST MODE)
0. Exit
```

Users can create a new account or select an existing customer to test account-management operations.

**Note:** Account selection is currently for testing purposes only. It does not perform password authentication or verify user identity.

#### Account Menu

```text
===========================================
ACCOUNT MENU
===========================================
 1. View profile
 2. Change name
 3. Change email address
 4. Change home airport
 5. View payment addresses
 6. Add payment address
 7. Edit payment address
 8. Delete payment address
 9. View credit cards
10. Add credit-card record
11. Change credit-card payment address
12. Delete credit-card record
 0. Log out
```

Each option calls the corresponding function in `customer_payments.py`.

The interface includes input handling, error messages, and confirmation prompts for destructive operations.

### 5. Database Integration

The application uses `psycopg2` to execute SQL queries against PostgreSQL.

Functions receive an existing database connection as their first argument.

Example:

```python
register_customer(
    conn,
    "alice@example.com",
    "Alice Chen"
)

add_payment_address(
    conn,
    "alice@example.com",
    "123 Main Street, Chicago"
)

card_id = add_credit_card(
    conn,
    "alice@example.com",
    "123 Main Street, Chicago"
)
```

Database operations use parameterized SQL queries to avoid directly inserting user input into SQL strings.

Write operations use transactions:

- Successful operations are committed.
- Failed operations are rolled back.
- PostgreSQL primary-key and foreign-key constraints protect data integrity.

The application also checks customer ownership when modifying or deleting credit-card records.

### 6. Testing

Offline unit tests are provided in `test_customer_payments.py`.

Run the tests using:

```bash
python -m unittest -v test_customer_payments.py
```

The current tests cover:

- Parameterized customer registration.
- Validation of required registration fields.
- Address ownership in SQL operations.
- Automatically generated credit-card IDs.
- Address updates involving linked credit cards.
- Credit-card deletion restricted by customer ownership.

The initial six offline tests passed.

**Testing limitation:** These tests use mocked database connections. Integration testing against the actual PostgreSQL database is still required.

### 7. Known Limitations and Pending Features

The current implementation is a preliminary functional module, not the complete airline booking application.

**Not yet implemented:**

- Secure account authentication or login.
- Storage and modification of actual credit-card details.
- Flight searching with dates and connecting flights.
- Seat availability checks.
- Flight booking and payment confirmation.
- Viewing and cancelling existing bookings.
- Complete integration of all modules into the final application.

Additionally, credit cards referenced by existing bookings cannot currently be deleted due to database foreign-key constraints.

### 8. Next Development Steps

1. Test all customer and payment operations against the shared PostgreSQL database.
2. Resolve any integration or database-constraint errors.
3. Implement the remaining flight-searching functionality.
4. Implement flight booking and cancellation operations.
5. Integrate the modules into the final console application.

---

**Current Development Status:** Customer registration, profile editing, payment-address management, and basic credit-card record management have been implemented. The preliminary console interface is available for testing, but full PostgreSQL integration testing and the remaining airline booking functionality are pending.
