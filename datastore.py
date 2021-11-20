def init_db(con):
    with con:
        con.execute(""" CREATE TABLE IF NOT EXISTS users
        (
            discord_name VARCHAR(255),
            discord_id VARCHAR(255),
            last_back DATETIME,
            ack_flag BOOLEAN DEFAULT FALSE
        );
        """);
        #con.execute(""" CREATE TABLE IF NOT EXISTS command_log 
        #(
        #    user_id VARCHAR(255) FOREIGN KEY REFERENCES users(id),
        #    command_type VARCHAR(255),
        #    command_string TEXT NOT NULL,
        #    command_at DATETIME DEFAULT NOW()
        #);
        #""");

def get_latest(con):
    """Returns all back events which haven't been ack'd, oldest first"""
    ret = []
    with con:
        results = con.execute("SELECT discord_name as user_name, discord_id as user_id, last_back FROM users WHERE ack_flag = false ORDER BY last_back;")
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
        results = con.execute("SELECT * FROM users WHERE discord_name = ? AND ack_flag = false;", (user_name,))
        for res in results:
            ret.append(res)
    return ret

def upsert_user(con, user_name, user_id, date):
    """Sets the user's back time to date, or to immediately back if date not set"""
    with con:
        users = con.execute("SELECT oid FROM users WHERE discord_id = ?;", (user_id,))
        db_id = None
        for u in users:
            if db_id != None:
                print(f"ERROR: Multiple rows for user {user_id}")
            else:
                db_id = u[0]

        if (db_id is None):
            con.execute("INSERT INTO users (discord_name, discord_id, last_back) VALUES (?, ?, ?);", (user_name, user_id, date))
        else:
            con.execute("UPDATE users SET last_back = ?, discord_name = ?, ack_flag = false WHERE oid = ?;", (date, user_name, db_id))
