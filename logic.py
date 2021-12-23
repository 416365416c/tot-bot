import random
import asyncio
import discord
from datetime import datetime, timedelta

import datastore

POLL_INTERVAL=300 # Seconds between checks for scheduled activity
SUPER_MINUTES=10

# ALL TIMES IN UTC

helpTxt = """I support the following commands:
help - this message
timeoff <days> - register time off for a specific number of days
return - register a return from time off
when <user name> - query when user X should be back
soon - returns a list of users expected back within the next week
"""
helpAdminTxt = """For esteemed admins, I support the following commands:
help admin - this message
list <role name> - list members with role R who are away and when they'll be back.
empower <role name> - toggles admin powers for role R
bind <server id> - binds this bot instance to a server by id; resets admin roles.
super OTT - Enter superadmin mode; requires OTT from server logs.
Usually you'll use superadmin mode once to call bind and then empower with an initial admin role.
"""
# clear <user name> - clear the record for named user
# refresh - Updates user/server/role names in the database using the discord ids saved alongside.
unknownTxt = "Sorry, I don't understand. Try 'help' for more details."
unimplementedTxt = unknownTxt
permissionTxt = "Sorry, this command is only available to admins."
unconfiguredTxt = "Please contact my administrator, for I am not yet configured for use."
backTxt = "Welcome back!"

def xy_str(dt):
    """ Returns a Xth of Y style string """
    if type(dt) == str:
        dt = datetime.fromisoformat(dt)
    dayStr = str(dt.day)
    dayVal = dt.day % 10
    if (dt.day > 10 and dt.day < 20):
        dayStr += "th"
    elif dayVal == 1:
        dayStr += "st"
    elif dayVal == 2:
        dayStr += "nd"
    elif dayVal == 3:
        dayStr += "rd"
    else:
        dayStr += "th" # 0 case, and catch-all
    return f"{dayStr} of {dt.strftime('%B')}"

def check_for_admin(ds_con, lad, user_id, user_roles):
    superadmins = datastore.get_super_logins(ds_con)
    for s in superadmins:
        if s[0] == user_id and s[1] + timedelta(minutes=SUPER_MINUTES) > datetime.utcnow():
            return "super"
    admin_roles = datastore.get_roles(ds_con)
    if len(list(set(user_roles) &  set(admin_roles))) > 0:
        return "admin"
    return None

def respond_to(ds_con, lad, user_id, user_name, message):
    admin_mode = check_for_admin(ds_con, lad, user_id, lad.get_user_roles(user_id))
    # Returns string response. Message should be a sequence of space separated words, with the first one lower cased already
    if message.startswith("help"):
        # help - prints help text
        if message == "help admin":
            return f"Current Guild: {lad.guild_name()}\n" + helpAdminTxt
        return helpTxt
    elif message.startswith("super"):
        # ex. super RandomPassword - Enter superadmin mode for ten minutes, wherein the current user can call admin/superadmin commands.
        if admin_mode == "super":
            return "You already have a super admin session"
        lockouts = datastore.get_super_lockouts(ds_con)
        for l in lockouts:
            if l[0] == user_id and l[1] + timedelta(minutes=SUPER_MINUTES) > datetime.utcnow():
                return f"You must wait {SUPER_MINUTES} before attempting to enter super admin mode again"

        # Requires an OTT from the server logs.
        password = message[6:] # Drop 'super ', rest is password
        if password and datastore.check_master_password(ds_con, password):
            print(f"super attempt succeeded: {user_name} {user_id}")
            datastore.push_super_login(ds_con, user_id)
            new_pass = datastore.reset_master_password(ds_con)
            print(f"New OTT: {new_pass}")
            return f"Welcome administrator. Your session will expire in {SUPER_MINUTES} minutes."
        else:
            print(f"super attempt failed: {password}")
            datastore.push_super_lockout(ds_con, user_id)
            return f"Incorrect password. Please try again in {SUPER_MINUTES} minutes."
    elif lad.guild_name() == None and admin_mode == None: # commands above skip config check, so that you can enter admin mode
        return unconfiguredTxt
    elif message.startswith("timeoff"):
        # ex. timeoff 7 - sets user to be back after a period of time specified (back time = now + period)
        #     Supported times are: X U, where U is days/hours/minutes/months/years. Default days.
        #     If timeoff is used with an unrecognized unit, an error is printed
        #     If timeoff is used with something than X U, we assume it's a joke (e.g. "until they fix it") and a random 1-1000 day time is chosen.
        message_split = message.split(" ")
        if len(message_split) == 1:
            return "Usage: timeoff number [unit]"

        time_delta = None
        time = None

        try:
            time = int(message_split[1])
        except ValueError:
            try:
                time = float(message_split[1])
                # It's a float, but not an int...
                return "Sorry, I don't do fractions."
            except ValueError:
                # Not a number. Probably just a joke
                time = random.randint(1,1000)
                message_split = [] # Don't try to load a unit
        except TypeError:
            pass # Leave time as None

        if time == None:
            print(f"Bad time: {message}")
            return unknownTxt

        unit = "day(s)"
        if len(message_split) > 2: 
            unit = message_split[2].lower()
        
        if unit == "day" or unit == "days" or unit == "day(s)": # (s) only in our default case
            time_delta = timedelta(days=time)
        elif unit == "hour" or unit == "hours":
            time_delta = timedelta(hours=time)
        elif unit == "week" or unit == "weeks":
            time_delta = timedelta(weeks=time)
        elif unit == "month" or unit == "months":
            time_delta = timedelta(days=time*30) # Not perfect, but close enough
        elif unit == "year" or unit == "years":
            time_delta = timedelta(days=time*365) # Ditto
        elif unit == "minute" or unit == "minutes" or unit.endswith("second") or unit.endswith("seconds"):
            return "Sorry, I don't keep track of times that short."
        
        if time_delta == None:
            print(f"Bad unit: {message}")
            return unknownTxt
            
        datastore.upsert_user(ds_con, user_name, user_id, datetime.utcnow() + time_delta)
        return f"See you in {time} {unit}." #TODO: Wave emoji
    elif message.startswith("when"):
        # ex. when jimmy - Checks to see if a user is in the database and if so returns when they are expected back
        query_name = message[5:] # Drop 'when ', rest is name
        results = datastore.query_by_name(ds_con, query_name)
        for r in results:
            t_back = datetime.fromisoformat(r[2])
            t_now = datetime.utcnow()
            if t_back > t_now:
                return f"{r[0]} is expected to return on the {xy_str(r[2])}."
        return f"I have no intel on {query_name} or their whereabouts."
    elif message.startswith("return"):
        # return - sets user to be back immediately, without acknowledgement or further prompting
        datastore.upsert_user(ds_con, user_name.lower(), user_id, datetime.utcnow())
        datastore.ack_event(ds_con, user_id)
        return backTxt
    elif message.startswith("soon"):
        # soon - Returns who will be coming back "soon" (need to define soon)
        results = datastore.get_backs(ds_con)
        ret = ""
        for r in results:
            t_back = datetime.fromisoformat(r[2])
            t_now = datetime.utcnow()
            if t_back > t_now and t_back - timedelta(weeks=1) <= t_now:
                ret += f"{r[0]} is expected to return on the {xy_str(r[2])}.\n"
        if ret == "":
            return "Nobody is coming back soon."
        return ret
    elif message.startswith("list"):
        # ex. list admins - ADMIN REQUIRED Returns a list of who is coming back, optionally filtered by role
        if admin_mode == None:
            return permissionTxt

        role_name = None
        if (len(message) > 5):
            role_name = message[5:] # Drop 'list ', rest is role name
        backs = datastore.get_backs(ds_con)
        users = []
        role_id = lad.get_role_name_or_id(role_name=role_name)
        for b in backs:
            if role_name == None or role_id in lad.get_user_roles(b[1]):
                users.append((b[0], b[1], b[2]))

        if len(users) == 0:
            return "No users found"
            
        if role_name == None:
            role_name = "User"
        retStr = f"Returning {role_name}s: \n"
        for u in users:
            retStr += f"{u[0]} expects to be back on the {xy_str(u[2])}\n"
        return retStr 
    elif message.startswith("clear"):
        # TODO: ex. clear jimmy - ADMIN REQUIRED Removes a user's timeoff record, without their involvement, so that they no longer show up 
        return unimplementedTxt 
    elif message.startswith("refresh"):
        # TODO: refresh - ADMIN REQUIRED Goes through the user/role/server names in the db and refetches them from the ids
        return unimplementedTxt 
    elif message.startswith("empower"):
        # ex. empower admins - ADMIN REQUIRED Toggles the admin flag for the named role. With no argument, prints list of currently empowered roles.
        if admin_mode == None:
            return permissionTxt

        role_name = None
        if (len(message) > 8):
            role_name = message[8:] # Drop 'empower ', rest is role name
        if role_name:
            role_id = lad.get_role_name_or_id(role_name=role_name)
            if role_id == None:
                return f"Cannot find role {role_name}!"
            datastore.toggle_role(ds_con, role_id, user_id)

        roles = datastore.get_roles(ds_con)
        if (len(roles) == 0):
            return "No admin roles set."

        retStr = "Admin roles are now: "
        for r in roles:
            role_name = lad.get_role_name_or_id(role_id=r)
            if role_name:
                retStr += f"{role_name}, "
        return retStr[:-2]
    elif message.startswith("bind"):
        # ex. bind someId - SUPERADMIN REQUIRED Binds this bot instance to the current server.
        if admin_mode != "super":
            return permissionTxt

        guild_id = message[5:] # Drop 'bind ', rest is guild id
        lad.set_guild(guild_id)
        guild_name = lad.guild_name()
        if guild_name:
            datastore.set_guild(ds_con, guild_id)
        else:
            return f"I cannot bind to {guild_id} as I cannot access it."
        return f"tot-bot instance now bound to {guild_name}."
    else:
        return unknownTxt

def check_backs(ds_con, lad):
    """ Send DM reminders to those back within the next day """
    if lad.guild_name() == None:
        return
    backs = datastore.get_backs(ds_con)
    for b in backs:
        if b[3]: #Already ack'd
            continue
        if len(lad.get_user_roles(b[1])) == 0:
            # No roles, must have left the guild. Ignore them
            datastore.ack_event(ds_con, b[1])
            continue
        t_back = datetime.fromisoformat(b[2])
        t_now = datetime.utcnow()
        if t_back > t_now and t_back - timedelta(days=1) <= t_now:
            lad.dm(b[1], f"Looking forward to seeing you back in {lad.guild_name()} on the {xy_str(b[2])}!")
            datastore.ack_event(ds_con, b[1])

def poll(ds_con, lad):
    """ Called regularly to react to DB state """
    check_backs(ds_con, lad)
    # Schedule the next call
    asyncio.get_running_loop().call_later(POLL_INTERVAL, poll, ds_con, lad)
