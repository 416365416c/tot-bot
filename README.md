# tot-bot
Discord Bot for tracking time off on a single server.

Uses the discord python package. See below.

Also a simple toy project for playing with a discord bot. Note that my quick exploration of the subject suggests that message bots like this are an older style, and modern "interaction" based applications are preferred by discord. However, the python package doesn't seem to support them.

See logic.py for commands and their explanation. There is room for more commands and dockerization.

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

Use the OAuth2 URL Generator on Discord to create an invite link for your bot. A server admin who clicks the link will have the option to add the bot to their server.

It requires the Members intent so tha it can get members and roles from the guild as part of the guild binding. It does not require message intents because it only responds if mentioned (or in a DM).
