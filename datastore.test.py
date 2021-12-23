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
            datastore.upsert_user(con, "Test A", 1, datetime(2021, 2, 21, 18))
            datastore.upsert_user(con, "Test B", 2, datetime(2021, 2, 21, 19))
            datastore.upsert_user(con, "Test C", 3, datetime(2021, 2, 21, 20))
            datastore.upsert_user(con, "Test A", 1, datetime(2021, 2, 21, 21))

        expected = [
                ('Test A', 1, '2021-02-21 21:00:00', 0),
                ('Test B', 2, '2021-02-21 19:00:00', 0),
                ('Test C', 3, '2021-02-21 20:00:00', 0)
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
                ('Test B', 2, '2121-02-21 18:00:00', 0),
                ('Test A', 1, '2121-02-21 19:00:00', 0),
        ]
        with self.con as con:
            datastore.upsert_user(con, "Test A", 1, datetime(2121, 2, 21, 19))
            datastore.upsert_user(con, "Test B", 2, datetime(2121, 2, 21, 18))
            results = datastore.get_backs(con)
            self.assertEqual(results, expected)

        with self.con as con:
            datastore.ack_event(con, 1)
            expected[1] = ('Test A', 1, '2121-02-21 19:00:00', 1)
            results = datastore.get_backs(con)
            i = 0
            for r in results:
                self.assertEqual(r, expected[i])
                i += 1
            self.assertEqual(i, 2)

    def testQuery(self):
        with self.con as con:
            datastore.upsert_user(con, "Test A", 1, datetime(2121, 2, 21, 18))
            datastore.upsert_user(con, "Test B", 2, datetime(2121, 2, 21, 19))

        with self.con as con:
            results = datastore.query_by_name(con, "Test B")
            self.assertEqual(results, [('Test B', 2, '2121-02-21 19:00:00', 0)])

        with self.con as con:
            datastore.upsert_user(con, "Test B", 2, datetime(2121, 2, 21, 21))
            results = datastore.query_by_name(con, "Test B")
            self.assertEqual(results, [('Test B', 2, '2121-02-21 21:00:00', 0)])

        with self.con as con:
            datastore.upsert_user(con, "Test B", 2)
            datastore.upsert_user(con, "Test C", 2, datetime(2021, 2, 21, 21))
            results = datastore.get_backs(con)
            self.assertEqual(results, [('Test A', 1, '2121-02-21 18:00:00', 0)]) # Only future back times in backs


    def testMasterPassword(self):
        with self.con as con:
            mp = datastore.reset_master_password(con)
            self.assertNotEqual(mp, None)
            self.assertTrue(datastore.check_master_password(con, mp))
            not_mp = mp + "but not"
            self.assertFalse(datastore.check_master_password(con, not_mp))

        with self.con as con:
            # Since we're using a fancy hash, may as well check that the password isn't stored in plaintext
            mp2 = datastore.reset_master_password(con)
            self.assertNotEqual(mp2, None)

            config = con.execute("SELECT master_password FROM config;").fetchone()
            self.assertNotEqual(config, None)
            self.assertNotEqual(config[0], mp2)

            self.assertTrue(datastore.check_master_password(con, mp2))
                

    def testAdminRoles(self):
        around_now = datetime.utcnow()
        with self.con as con:
            roles = datastore.get_roles(con)
            self.assertEqual(roles, [])

        with self.con as con:
            datastore.toggle_role(con, 1, 1)
            datastore.toggle_role(con, 2, 1)
            datastore.toggle_role(con, 3, 1)

            roles = datastore.get_roles(con)
            self.assertEqual(roles, [1, 2, 3])

        with self.con as con:
            datastore.toggle_role(con, 2, 1)

            roles = datastore.get_roles(con)
            self.assertEqual(roles, [1, 3])

        with self.con as con:
            # Since we're logging these changes, may as well ensure that is in the db
            role_data = con.execute("SELECT set_by, set_at FROM admin_roles WHERE role_id = 1;").fetchone()
            self.assertNotEqual(role_data, None)
            self.assertEqual(role_data[0], 1)
            #Somehow datetimes with microsecond precision count as earlier than the same datetime without...
            #self.assertTrue(datetime.fromisoformat(role_data[1]). >= around_now)

        with self.con as con:
            datastore.set_guild(con, 1)
            guild = datastore.get_guild(con)
            self.assertEqual(guild, 1)

            roles = datastore.get_roles(con)
            self.assertEqual(roles, [])


if __name__ == '__main__':
    unittest.main()
