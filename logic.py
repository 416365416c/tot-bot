import random
from datetime import datetime, timedelta

import datastore

# Command Examples
#
# help - prints help
# timeoff 7 - sets user to be back after a period of time specified (back time = now + period)
#     Supported times are: X U, where U is days/hours/minutes/months/years. Default days.
#     If timeoff is used with an unrecognized unit, an error is printed
#     If timeoff is used with no numbers, we assume it's a joke (e.g. "until they fix it") and a random 1-1000 day time is chosen.
#     TODO: Around when a user is expected to be back, a message with their name will be sent to the channel. Use discord.utils.sleep_until(datetime)
# TODO: soon - Returns who will be coming back "soon" (need to define soon)
# when jimmy - Checks to see if a user is in the database and if so returns when they are expected back TODO: Should use ack to see if they're really away
# return - sets user to be back immediately, without acknowledgement
# unrecognized commands suggest help

# ALL TIMES IN UTC

helpTxt = """I support the following commands:
help - this message
timeoff X - register time off for a specific number of days
return - register a return from time off
when X - query when user X should be back
"""
unknownTxt = "Sorry, I don't understand. Try 'help' for more details."
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

def respond_to(ds_con, user_id, user_name, message):
    # Returns string response. Message should be all lowercase and a sequence of space separated words
    if message.startswith("help"):
        return helpTxt
    elif message.startswith("timeoff"):
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
            unit = message_split[2]
        
        if unit == "day" or unit == "days" or unit == "day(s)": # (s) only in our default case
            time_delta = timedelta(days=time)
        elif unit == "hour" or unit == "hours":
            time_delta = timedelta(hours=time)
        elif unit == "week" or unit == "weeks":
            time_delta = timedelta(weeks=time)
        elif unit == "month" or unit == "months":
            time_delta = timedelta(days=time*30) # Not perfect, but close enough
        elif unit == "year" or unit == "years":
            time_delta = timedelta(days=time*30) # Ditto
        elif unit == "minute" or unit == "minutes" or unit.endswith("second") or unit.endswith("seconds"):
            return "Sorry, I don't keep track of times that short."
        
        if time_delta == None:
            print(f"Bad unit: {message}")
            return unknownTxt
            
        datastore.upsert_user(ds_con, user_name.lower(), user_id, datetime.utcnow() + time_delta)
        return f"See you in {time} {unit}." #TODO: Wave emoji
    elif message.startswith("when"):
        query_name = message[5:] # Drop 'when ', rest is name
        results = datastore.query_by_name(ds_con, query_name)
        if len(results) == 0:
            return f"I have no intel on {query_name} or their whereabouts."
        for r in results:
            return f"{query_name} is expected to return on the {xy_str(r[2])}."
    elif message.startswith("return"):
        datastore.upsert_user(ds_con, user_name.lower(), user_id, datetime.utcnow())
        datastore.ack_event(ds_con, user_id)
        return backTxt
    else:
        return unknownTxt
