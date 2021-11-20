#!/usr/bin/env python3
import discord
import sqlite3 as sl
import logging
import os

import datastore
import logic

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

sldb = sl.connect('tot.db')
datastore.init_db(sldb)
client = discord.Client()

@client.event
async def on_ready():
    global myId
    print(f"Started {client.user} - {client.user.id}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return # Ignore own messages, just in case
    if any([mention for mention in message.mentions if mention.id == client.user.id]):
        # respond only if mentioned

        # For crude parsing, strip a bunch of formatting and then only take words which aren't "special"
        message_words = discord.utils.remove_markdown(message.clean_content).split(' ')
        message_content = ""
        for word in message_words:
            if len(word) >= 1 and word[0] not in "!@#$":
                message_content += f"{word} " # Trailing space is okay
        message_content = message_content.rstrip().lower()
        user_name = message.author.nick
        if user_name == None:
            user_name= message.author.name
        response = logic.respond_to(sldb, message.author.id, user_name, message_content)
        await message.channel.send(response, reference=message.to_reference())

client.run(os.environ["TEST_TOKEN"])
