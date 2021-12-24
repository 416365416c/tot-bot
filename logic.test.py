import unittest
import sqlite3
from datetime import datetime, timedelta

import datastore
import lad
import logic

class TestLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Logic depends on datastore
        self.con = sqlite3.connect(":memory:")
        datastore.init_db(self.con)
        # Logic depends on LAD
        self.lad = lad.FakeLad()

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
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "help")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "help admin")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "unknown")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "supercalifragilisticexpialidocious")
        self.assertTrue(len(ret) > 5)

    def testTimeOff(self):
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff")
        self.assertTrue(ret.startswith("Usage:"))
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 0") # Valid, mostly used for testing
        self.assertEqual(ret, "See you in 0 day(s).")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1")
        self.assertEqual(ret, "See you in 1 day(s).")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1 day")
        self.assertEqual(ret, "See you in 1 day.")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 2 days")
        self.assertEqual(ret, "See you in 2 days.")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1 week")
        self.assertEqual(ret, "See you in 1 week.")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1 month")
        self.assertEqual(ret, "See you in 1 month.")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1 year")
        self.assertEqual(ret, "See you in 1 year.")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1 second")
        self.assertTrue(ret.startswith("Sorry"))
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1 parsec") # Prints to console
        self.assertTrue(ret.startswith("Sorry"))
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 0.2 days")
        self.assertTrue(ret.startswith("Sorry"))
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff until the cows come home")
        self.assertTrue(ret.startswith("See you in")) # Number is random

    def testWhen(self):
        logic.respond_to(self.con, self.lad, 9, "Mr Test", "timeoff 1")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "when mr test")
        # Response depends on current date
        self.assertTrue("Mr Test" in ret) # Positive case finds proper name
        # Negative case
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "when mr pest")
        self.assertTrue("mr pest" in ret) # Negatie case spits out input (lower cased)

        logic.respond_to(self.con, self.lad, 10, "Mr Long", "timeoff 1000")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "soon")
        self.assertTrue("Mr Test" in ret)
        self.assertFalse("Mr Long" in ret)

        # These require admin, available though super admin in tests
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "list")
        self.assertTrue(ret.startswith("Sorry"))

        otp = datastore.reset_master_password(self.con)
        logic.respond_to(self.con, self.lad, 1, "Ace", "super " + otp)

        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "list")
        self.assertTrue("Mr Test" in ret)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "list Fake Role")
        self.assertTrue("Mr Test" in ret)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "list Role that doesn't exist")
        self.assertFalse("Mr Test" in ret)


    def testReturn(self):
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 1")
        back_time = logic.xy_str(datetime.utcnow() + timedelta(days=1))
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "when ace")
        self.assertTrue(back_time in ret)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "return")
        self.assertTrue(len(ret) > 5)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "when ace")
        self.assertFalse(back_time in ret)

    def testPermissions(self):
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "empower Testers")
        self.assertTrue(ret.startswith("Sorry"))

        # These require admin, available though super admin in tests
        otp = datastore.reset_master_password(self.con)
        logic.respond_to(self.con, self.lad, 1, "Ace", "super " + otp)

        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "empower")
        self.assertFalse("Fake Role" in ret)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "empower Fake Role") #Note name -> id -> name happens in FakeLad
        self.assertTrue("Fake Role" in ret)
        self.assertFalse("Role1" in ret)
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "empower")
        self.assertTrue("Fake Role" in ret)

        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "empower the nonexistent")
        self.assertTrue("Cannot find role" in ret)

        # bind should reset roles, but not super
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "bind 0")
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "empower")
        self.assertFalse("Sorry" in ret)
        self.assertFalse("Fake Role" in ret)

        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "super already")
        self.assertTrue(ret.startswith("You already"))

    def testLockout(self):
        # Separate test because needs a clean state
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "super wrong")
        self.assertTrue(ret.startswith("Incorrect"))
        ret = logic.respond_to(self.con, self.lad, 1, "Ace", "super wrong")
        self.assertTrue(ret.startswith("You must wait"))

    async def testMessages(self):
        logic.respond_to(self.con, self.lad, 1, "Ace", "timeoff 4 hours")
        back_time = logic.xy_str(datetime.utcnow() + timedelta(hours=4))
        await logic.check_backs(self.con, self.lad)
        ret = self.lad.pop_last_dm()
        self.assertTrue(ret.startswith("Ace:"))
        self.assertTrue("Fake Guild" in ret)
        self.assertTrue(back_time in ret)

        # Pop works
        ret = self.lad.pop_last_dm()
        self.assertTrue(ret == None)

        # No new msg due to ack flag
        await logic.check_backs(self.con, self.lad)
        ret = self.lad.pop_last_dm()
        self.assertTrue(ret == None)

if __name__ == '__main__':
    unittest.main()
