from datetime import datetime
import secrets
from passlib.hash import argon2

# NB Make sure host uses UTC TZ for CURRENT_TIMESTAMP to work right

config_oid = None

# Maintain transparent in-memory cache because this is used every call for admin checks
roles_cache = None

# In-memory values still managed by datastore
superadmins = [] #Array of id/time tuple.
superfails = [] #Same, but for lockouts.
def get_super_logins(_con):
    return superadmins
def get_super_lockouts(_con):
    return superfails
def push_super_login(_con, user_id):
    superadmins.append((user_id, datetime.utcnow()))
def push_super_lockout(_con, user_id):
    superfails.append((user_id, datetime.utcnow()))

def _reset_globals():
    global config_oid
    global roles_cache
    global superadmins
    global superfails
    config_oid = None
    roles_cache = None
    superadmins = []
    superfails = []

def init_db(con):
    global config_oid
    _reset_globals()
    with con:
        con.execute(""" CREATE TABLE IF NOT EXISTS users
        (
            discord_name VARCHAR(255),
            discord_id VARCHAR(255) UNIQUE,
            last_back DATETIME,
            ack_flag BOOLEAN DEFAULT FALSE
        );
        """);
        con.execute(""" CREATE TABLE IF NOT EXISTS config
        (
            bound_guild_id VARCHAR(255),
            master_password VARCHAR(255)
        );
        """);

        # Always one config record for persistent config
        config = con.execute("SELECT oid FROM config;").fetchone()
        if config == None:
            config2 = con.execute("INSERT INTO config (bound_guild_id, master_password) VALUES (NULL, NULL);")
            config_oid = con.execute("SELECT oid FROM config;").fetchone()[0]
        else:
            config_oid = config[0]

        con.execute(""" CREATE TABLE IF NOT EXISTS admin_roles
        (
            role_id VARCHAR(255) UNIQUE,
            set_by VARCHAR(255),
            set_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """);

        #con.execute(""" CREATE TABLE IF NOT EXISTS command_log 
        #(
        #    user_id VARCHAR(255) FOREIGN KEY REFERENCES users(discord_id),
        #    command_type VARCHAR(255),
        #    command_string TEXT NOT NULL,
        #    command_at DATETIME DEFAULT NOW()
        #);
        #""");

def get_backs(con):
    """Returns all back events in the future, oldest first"""
    ret = []
    nowstr = str(datetime.utcnow())
    with con:
        results = con.execute("SELECT discord_name as user_name, discord_id as user_id, last_back, ack_flag FROM users WHERE last_back > ? ORDER BY last_back;", (nowstr,))
        for res in results:
            ret.append(res)
    return ret

def ack_event(con, user_id):
    """Sets the ack flag for the specified user record"""
    with con:
        con.execute("UPDATE users SET ack_flag = true WHERE discord_id = ?;", (user_id,))

def query_by_name(con, user_name):
    """Returns when the user(s) named will be back (If we know)"""
    # In theory this can return multiple users with the same nick. To solve for
    # this case, always use the discord_id for mentions when resolving, and
    # there may be multiple users returned.
    ret = []
    with con:
        results = con.execute("SELECT * FROM users WHERE discord_name LIKE ?;", (user_name,))
        for res in results:
            ret.append(res)
    return ret

def upsert_user(con, user_name, user_id, date=None):
    """Sets the user's back time to date, or to immediately back if date not set"""
    if date == None:
        date = datetime.utcnow()
    with con:
        users = con.execute("SELECT oid FROM users WHERE discord_id = ?;", (user_id,))
        user = users.fetchone()
        if (user is None):
            con.execute("INSERT INTO users (discord_name, discord_id, last_back) VALUES (?, ?, ?);", (user_name, user_id, date))
        else:
            con.execute("UPDATE users SET last_back = ?, discord_name = ?, ack_flag = false WHERE oid = ?;", (date, user_name, user[0]))

def reset_master_password(con):
    """Sets the one time master password to something new and returns it"""
    new_password = secrets.token_urlsafe(16)
    new_hash = argon2.hash(new_password)
    with con:
        con.execute("UPDATE config SET master_password = ? WHERE oid = ?", (new_hash, config_oid))
        return new_password
    return None

def check_master_password(con, password):
    """Returns True iff passed password hash matches one in the database"""
    with con:
        config = con.execute("SELECT master_password FROM config WHERE oid = ?;", (config_oid,)).fetchone()
        if config and config[0] and argon2.verify(password, config[0]):
            return True
    return False

def set_guild(con, guild_id):
    """Sets bound guild in config"""
    global roles_cache
    with con:
        con.execute("UPDATE config SET bound_guild_id = ? WHERE oid = ?", (guild_id, config_oid))
        # Wipe admin roles for new server
        con.execute("DELETE FROM admin_roles")
        roles_cache = None

def get_guild(con):
    """Gets bound guild in config"""
    with con:
        res = con.execute("SELECT bound_guild_id FROM config").fetchone()
        if res:
            return res[0]
    return None

def toggle_role(con, role_id, user_id):
    """Toggles the existence of a role in admin_roles"""
    global roles_cache
    with con:
        roles = con.execute("SELECT oid FROM admin_roles WHERE role_id = ?;", (role_id,))
        db_id = None
        for r in roles:
            db_id = r[0]

        if (db_id is None):
            con.execute("INSERT INTO admin_roles (role_id, set_by) VALUES (?, ?);", (role_id, user_id))
        else:
            con.execute("DELETE FROM admin_roles WHERE oid = ?;", (db_id,)) 
        roles_cache = None

def get_roles(con):
    """Returns the admin roles as a list"""
    global roles_cache
    if roles_cache:
        return roles_cache

    with con:
        ret = []
        roles = con.execute("SELECT role_id FROM admin_roles;");
        for r in roles:
            ret.append(r[0])
        roles_cache = ret
        return roles_cache
    return []
