#!/usr/bin/env python3
import discord
import sqlite3 as sl
import logging
import os
import asyncio

import datastore
import logic
import lad

logger = logging.getLogger('discord')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#TODO: Use logging for app logs as well, and redirect to a file
sldb = sl.connect('tot.db')
datastore.init_db(sldb)
# Reset OTT every restart and use, maybe add periodically just for lolz?
new_pass = datastore.reset_master_password(sldb)
print(f"First OTT: {new_pass}")
intents = discord.Intents.default()
intents.members = True # Non-standard but necessary for the server bind approach
client = discord.Client(intents=intents)
lad = lad.Lad(client)

init_flag = False

@client.event
async def on_ready():
    global init_flag
    print(f"Started {client.user} - {client.user.id}")
    if not init_flag:
        init_flag = True
        guild_id = datastore.get_guild(sldb)
        if guild_id:
            lad.set_guild(guild_id)
        await logic.poll_forever(sldb, lad) # Never returns, but does sleep


@client.event
async def on_message(message):
    if message.author == client.user:
        return # Ignore own messages, just in case
    if any([mention for mention in message.mentions if mention.id == client.user.id]):
        # respond only if mentioned

        # For crude parsing, strip a bunch of formatting and then only take words which aren't "special"
        message_words = discord.utils.remove_markdown(message.clean_content).split(' ')
        message_content = ""
        first_word = True
        for word in message_words:
            if len(word) >= 1 and word[0] not in "!@#$":
                if first_word:
                    message_content += f"{word.lower()} " # Lower-case command only for easy parsing
                    first_word = False
                else:
                    message_content += f"{word} " # Trailing space is okay as we'll rstrip
        message_content = message_content.rstrip()
        user_name = message.author.nick
        if user_name == None:
            user_name= message.author.name
        response = logic.respond_to(sldb, lad, message.author.id, user_name, message_content)
        await message.channel.send(response, reference=message.to_reference())

client.run(os.environ["DISCORD_BOT_TOKEN"])
