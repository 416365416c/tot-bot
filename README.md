# tot-bot
Discord Bot for tracking time off on a single server. Binds to one server so that it can interact with users based on their roles with that server.

Mostly a simple toy project for playing with a discord bot. Note that my quick exploration of the subject suggests that message bots like this are an older style, and modern "interaction" based applications are preferred by discord. However, the python package doesn't seem to support them.

Uses the discord python package, see below. Code is structured in a mostly functional way, with the bulk of the code being functional and unit tested. Until it starts actually interfacing with Discord, of course.

See logic.py for commands and their explanation in the comments. There is room for more commands and dockerization.

It requires the members intent so that it can get members and roles from the guild as part of the guild binding feature. It should not require the new message intent because it only responds if mentioned (or in a DM).

# USAGE

## Discord setup
1. Login to your [https://discord.com/developers/applications][discount developer account].
2. Create a new application.
3. In the application configuration, add a bot user.
4. Copy the bot token and provide it to the app via the `TEST_TOKEN` environment variable.

See https://discordpy.readthedocs.io/en/stable/discord.html#discord-intro for better generic docs.

## Running
Requires python3.8 or later.

`pip install -r requirements.txt`
`python3 tot.py`

By default it will store state in a sqlite3 database ile in the current working directory.

Use the OAuth2 URL Generator on Discord to create an invite link for your bot. A server admin who clicks the link will have the option to add the bot to their server. After the bot is added to a server, you need to bind it to the server using the following sequence of commands:

1. `super <OTT>` using the OTT from the command line output, this gives your user super admin mode temporarily.
2. `bind <server-id>` to bind it to your server. This must be done after you add the bot to your server. This instance of the running bot will not be able to be used on other servers (though it can still be added to them with limited functionality).
3. `empower <role-name>` to empower a role on your server to have admin powers. This is optional, but prevents you from needing to enter super admin mode again.

