"""Offline checks: SQL calls and return handling only; no PostgreSQL required."""
import unittest
from unittest.mock import MagicMock
import customer_payments as api


class CustomerPaymentsOfflineTests(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cur = self.conn.cursor.return_value.__enter__.return_value

    def test_register_uses_parameters(self):
        self.cur.fetchone.return_value = ("x@example.com",)
        result = api.register_customer(self.conn, "x@example.com", "X")
        self.assertEqual(result, "x@example.com")
        sql, args = self.cur.execute.call_args.args
        self.assertIn("INSERT INTO Customer", sql)
        self.assertEqual(args, ("x@example.com", "X"))

    def test_register_requires_name(self):
        with self.assertRaises(ValueError):
            api.register_customer(self.conn, "x@example.com", " ")

    def test_add_address_uses_owner(self):
        api.add_payment_address(self.conn, "x@example.com", "Main St")
        sql, args = self.cur.execute.call_args.args
        self.assertIn("Customer_Payment_Address", sql)
        self.assertEqual(args, ("x@example.com", "Main St"))

    def test_add_card_returns_generated_id(self):
        self.cur.fetchone.return_value = (42,)
        self.assertEqual(api.add_credit_card(self.conn, "x@example.com", "Main St"), 42)
        self.assertIn("RETURNING card_id", self.cur.execute.call_args.args[0])

    def test_update_address_moves_linked_cards_before_delete(self):
        self.cur.fetchone.return_value = (1,)
        api.update_payment_address(self.conn, "x@example.com", "Old", "New")
        sql_calls = [c.args[0] for c in self.cur.execute.call_args_list]
        self.assertEqual(len(sql_calls), 4)
        self.assertIn("INSERT INTO Customer_Payment_Address", sql_calls[1])
        self.assertIn("UPDATE Credit_Card", sql_calls[2])
        self.assertIn("DELETE FROM Customer_Payment_Address", sql_calls[3])

    def test_delete_card_checks_owner(self):
        self.cur.fetchone.return_value = (17,)
        api.delete_credit_card(self.conn, "x@example.com", 17)
        _, args = self.cur.execute.call_args.args
        self.assertEqual(args, (17, "x@example.com"))


if __name__ == "__main__":
    unittest.main()
