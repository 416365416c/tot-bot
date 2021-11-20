import unittest
import sqlite3
from datetime import datetime

import datastore

class TestDataStore(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        datastore.init_db(self.con)

    def tearDown(self):
        self.con.close()

    def testInit(self):
        datastore.init_db(self.con) # Already done in setUp, this tests it can be called twice without harm
        found = False
        with self.con as con:
            results = con.execute("SELECT name from sqlite_master WHERE type = 'table';")
            for r in results:
                if r[0] == "users":
                    found = True
        self.assertTrue(found)

    def testPopulate(self):
        with self.con as con:
            datastore.upsert_user(con, "Test A", "1", datetime(2021, 2, 21, 18))
            datastore.upsert_user(con, "Test B", 2, datetime(2021, 2, 21, 19))
            datastore.upsert_user(con, "Test C", 3, datetime(2021, 2, 21, 20))
            datastore.upsert_user(con, "Test A", "1", datetime(2021, 2, 21, 21))

        expected = [
                ('Test A', '1', '2021-02-21 21:00:00', 0),
                ('Test B', '2', '2021-02-21 19:00:00', 0),
                ('Test C', '3', '2021-02-21 20:00:00', 0)
        ]

        with self.con as con:
            results = con.execute("SELECT * from users;")
            i = 0
            for r in results:
                self.assertEqual(r, expected[i])
                i += 1
            self.assertEqual(i, len(expected))

    def testAcks(self):
        expected = [
                ('Test B', '2', '2021-02-21 18:00:00'),
                ('Test A', '1', '2021-02-21 19:00:00'),
        ]
        with self.con as con:
            datastore.upsert_user(con, "Test A", 1, datetime(2021, 2, 21, 19))
            datastore.upsert_user(con, "Test B", 2, datetime(2021, 2, 21, 18))
            results = datastore.get_latest(con)
            self.assertEqual(results, expected)

        with self.con as con:
            datastore.ack_event(con, 1)
            results = datastore.get_latest(con)
            i = 0
            for r in results:
                self.assertEqual(r, expected[i])
                i += 1
            self.assertEqual(i, 1)

    def testQuery(self):
        with self.con as con:
            datastore.upsert_user(con, "Test A", 1, datetime(2021, 2, 21, 18))
            datastore.upsert_user(con, "Test B", 2, datetime(2021, 2, 21, 19))

        with self.con as con:
            results = datastore.query_by_name(con, "Test B")
            self.assertEqual(results, [('Test B', '2', '2021-02-21 19:00:00', 0)])

        with self.con as con:
            datastore.ack_event(con, "2")
            results = datastore.query_by_name(con, "Test B")
            self.assertEqual(results, []) # Ack'd users do not show in queries

        with self.con as con:
            datastore.upsert_user(con, "Test B", 2, datetime(2021, 2, 21, 21))
            results = datastore.query_by_name(con, "Test B")
            self.assertEqual(results, [('Test B', '2', '2021-02-21 21:00:00', 0)])

if __name__ == '__main__':
    unittest.main()
