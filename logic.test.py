import unittest
import sqlite3
from datetime import datetime

import datastore
import logic

class TestLogic(unittest.TestCase):
    def setUp(self):
        # Logic depends on datastore
        self.con = sqlite3.connect(":memory:")
        datastore.init_db(self.con)

    def tearDown(self):
        self.con.close()

    def testXYStr(self):
        a = logic.xy_str(datetime(2021, 11, 13))
        b = logic.xy_str(str(datetime(2021, 11, 13)))

        self.assertEqual(a,b)
        self.assertEqual(a, "13th of November")

        self.assertEqual(logic.xy_str(datetime(2021,1,1)), "1st of January")
        self.assertEqual(logic.xy_str(datetime(2021,1,2)), "2nd of January")
        self.assertEqual(logic.xy_str(datetime(2021,1,3)), "3rd of January")
        self.assertEqual(logic.xy_str(datetime(2021,1,4)), "4th of January")

    def testMisc(self):
        # These don't do anything but should respond fixed strings and not crash
        ret = logic.respond_to(self.con, 1, "Ace", "help")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, 1, "Ace", "unknown")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, 1, "Ace", "supercalifragilisticexpialidocious")
        self.assertTrue(len(ret) > 5)

    def testTimeOff(self):
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff")
        self.assertTrue(ret.startswith("Usage:"))
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 0") # Valid, mostly used for testing
        self.assertEqual(ret, "See you in 0 day(s).")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1")
        self.assertEqual(ret, "See you in 1 day(s).")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1 day")
        self.assertEqual(ret, "See you in 1 day.")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 2 days")
        self.assertEqual(ret, "See you in 2 days.")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1 week")
        self.assertEqual(ret, "See you in 1 week.")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1 month")
        self.assertEqual(ret, "See you in 1 month.")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1 year")
        self.assertEqual(ret, "See you in 1 year.")
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1 second")
        self.assertTrue(ret.startswith("Sorry"))
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 1 lightyear") # Prints to console
        self.assertTrue(ret.startswith("Sorry"))
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 0.2 days")
        self.assertTrue(ret.startswith("Sorry"))
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff until the cows come home")
        self.assertTrue(ret.startswith("See you in")) # Number is random

    def testWhen(self):
        logic.respond_to(self.con, 1, "Mr Test", "timeoff 1")
        ret = logic.respond_to(self.con, 1, "Ace", "when mr test")
        # Response depends on current date
        self.assertTrue("mr test" in ret)
        # Negative case
        ret = logic.respond_to(self.con, 1, "Ace", "when mr pest")
        self.assertTrue("mr pest" in ret)

    def testReturn(self):
        ret = logic.respond_to(self.con, 1, "Ace", "timeoff 0")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, 1, "Ace", "when ace")
        self.assertTrue(logic.xy_str(datetime.utcnow()) in ret)
        ret = logic.respond_to(self.con, 1, "Ace", "return")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, 1, "Ace", "when ace")
        self.assertFalse(logic.xy_str(datetime.utcnow()) in ret)

if __name__ == '__main__':
    unittest.main()
