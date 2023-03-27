import os
import logging
import asyncio
from dotenv import load_dotenv

from datetime import datetime
from typing import Union
from discord import Member, Intents, Game, Status, Reaction
from discord import Role, Guild, Embed, Colour, User
from discord.message import Message
from discord.ext import commands, tasks
from discord.ext.commands import Context

import data.configuration as S
from data.configuration import DATABASE, RECORDS_DB, CLIENT_ACTIVITY
from data.jsonified_database import id_lookup, insert_db, read_db, add_id, read_id
from events.EventView import EventView
from log.error_log import setup_logging
from re import search

# Intents manages some level of permissions bot can do
INTENTS = Intents.default()
INTENTS.members, INTENTS.presences = True, True
INTENTS.message_content, INTENTS.reactions = True, True

# Listed modules to be loaded into client
EXTENSIONS = [
    "admin_tool",
    "events.event",
    "music",
]

async def get_prefix(client:commands.Bot, message:Message):
    """Retrieves the prefix corresponding to a server if set,
    otherwise returns default one.

    Args:
        client (commands.Bot): Bot instance
        message (Message): Any message that can contain prefix

    Returns:
        list: list of prefixes outputed via commands.when_mentioned_or()
    """
    if not message.guild:
        return commands.when_mentioned_or(S.DEFAULT_SERVER_PREFIX)(client, message)
    
    prefix = await read_db(DATABASE, message.guild.id, 'prefix')
    if not prefix:
        is_okay = await insert_db(DATABASE, message.guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX)
        if not is_okay:
            return
        prefix = S.DEFAULT_SERVER_PREFIX
    return commands.when_mentioned_or(prefix)(client, message)

# Client has to be top level variable because of @ decorator for events
CLIENT = commands.Bot(command_prefix=get_prefix, intents=INTENTS)

# Create of log handle
log_handle:logging.Logger = setup_logging()

@CLIENT.event
async def on_ready():
    """Initialization function to set some bot states, after it's bootup.
    """    
    await CLIENT.change_presence(status=Status.dnd,
        activity=Game(name="Booting..", start=datetime.now()))
    print("Online.")
    await asyncio.sleep(5)
    change_status.start()

@tasks.loop(seconds=10)
async def change_status():
    status = next(CLIENT_ACTIVITY)
    await CLIENT.change_presence(
        activity=Game(status)
    )

@CLIENT.event
async def on_guild_join(guild:Guild):
    """If bots joins new server it adds its guid to a database

    Args:
        guild (Guild): Guild bot joined in
    """
    id = await add_id(DATABASE, guild.id)
    prefix = await insert_db(DATABASE, guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX)
    while not id or not prefix:
        id = await add_id(DATABASE, guild.id)
        prefix = await insert_db(DATABASE, guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX)

@CLIENT.event
async def on_member_join(member:Member):
    """Event triggered when member joins a server and asigns server's chosen
    role for that member.

    Args:
        member (Member): Member who joined server
    """
    # Auto-asign role given by guild
    role_asigned_by_guild:int = await read_db(DATABASE, member.guild.id, "auto-role")
    member_guild:Guild = member.guild
    if role_asigned_by_guild:
        role_to_give:Role = member_guild.get_role(role_asigned_by_guild)
        await member.add_roles(role_to_give)
    
    # Auto-rules given by guild
    await send_guild_rules(member, member_guild)
    # Aware moderators of naughty member join
    if await check_records(member):
        await aware_of_records(member, member_guild)
    
async def aware_of_records(member:Member, guild:Guild):
    mods_id = await read_db(DATABASE, guild.id, "mods_to_notify")
    mods = [guild.get_member(id) for id in mods_id]
    naughty = await read_id(RECORDS_DB, member.id)
    naugty_items = naughty.items()
    
    for m in mods:
        await m.send(f"{member} joined {guild.name} with `{len(naugty_items)}` " +
               "naughty records.\nUse `/naughty @mention` on your server " +
               "to see more information.")
    
async def send_guild_rules(member:Member, guild_joined:Guild):
    """For newly joined member on a server, bot sends this user server specified
    rules.

    Args:
        member (Member): Member who joined
        guild_joined (Guild): Guild which member joined
    """
    guild_rules:dict = await read_db(DATABASE, guild_joined.id, "guild-rules")
    if guild_rules:
        result:list = []      
        for idx, rule in guild_rules.items():
            result.append(f"{int(idx)+1}. " + rule)
        formated_output = "\n".join(result)
        emb = Embed(title=f"[{guild_joined.name}] server's rules:",
                    description=formated_output,
                    color=Colour.red())
        emb.set_footer(text="Being part of that server means you do respect these rules.")
        await member.send(embed=emb)

@CLIENT.event    
async def on_message(msg:Message):
    """Event triggered when bot sees a message in guild or in his direct
    messages. Used to further process message for commands in guild
    or talk back in direct messages.

    Args:
        msg (Message): Message that triggered the event
    """
    if msg.author == CLIENT.user:
        return
    if msg.guild:
        await check_blacklist(msg.guild, msg)
        await CLIENT.process_commands(msg)
        return
    await msg.channel.send("I don't serve any drinks here.")

@CLIENT.event
async def on_message_edit(before:Message, after:Message):
    if after.author == CLIENT.user:
        return
    if after.guild:
        await check_blacklist(after.guild, after)

async def check_blacklist(guild:Guild, msg:Message):
    """Checks if guild's blacklisted words are contained in message.
    Deletes the message if it contains blacklisted content and warns its author.

    Args:
        guild (Guild): Guild's blacklist to check
        msg (Message): Message to check
    """
    if await is_blacklist_exception(msg):
        return
    
    bl = await read_db(DATABASE, guild.id, "blacklist")
    if not bl:
        return
    
    msg_content = msg.content
    
    for w in bl:
        if w in msg_content:
            await msg.delete()
            await msg.author.send(f"Word \"{w}\" is restricted to use in `{guild.name}`")

async def check_records(member:Member)->bool:
    """Checks whether or not the member has any records.

    Args:
        member (Member): Member to check

    Returns:
        bool: True if naughty, False if not
    """
    recorded = await id_lookup(RECORDS_DB, member.id)
    if recorded:
        return True
    return False

async def is_blacklist_exception(msg:Message)->bool:
    FILTER_REMOVE_COMMAND_EXCEPTION = "filter remove"
    msg_content = msg.content[:13]
    msg_content.lower()
    
    if search(FILTER_REMOVE_COMMAND_EXCEPTION, msg_content):
        return True
    return False
      
@CLIENT.event
async def on_command_error(ctx:Context, error:commands.CommandError):
    """Event triggered when command module raises an exception.
    Used to handle the raised exceptions

    Args:
        ctx (Context): Context passed by command that raised exception
        error (CommandError): Error instance
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(error, ephemeral=True)
        return
    # if isinstance(error, commands.MissingPermissions):
    #     await ctx.send(error,
    #                    delete_after=S.DELETE_COMMAND_ERROR)
    # if isinstance(error, commands.HybridCommandError):
    #     await ctx.send("No permissions to do that.",
    #                    delete_after=S.DELETE_COMMAND_ERROR)

@CLIENT.event        
async def on_message_error(ctx:Context, error):
    pass

@CLIENT.event
async def setup_hook():
    """Syncs slash commands in all connected guilds and makes buttons
    restart persistent.
    """
    synced_commands =  await CLIENT.tree.sync()
    print(f"In-app commands have been synchronized.")
    synced_commands = [sc.name for sc in synced_commands]
    print(f"Following were affected: {synced_commands}")
    CLIENT.add_view(EventView())

async def install_extensions(target:commands.Bot):
    """Installs all the extentions in the other files to the client.

    Args:
        client (commands.Bot): Instance of the bot itself.
    """
    for ext in EXTENSIONS:
        await target.load_extension(ext)
        
if __name__ == "__main__":
    """This is main module and only one to be executed."""
    # Loads .env file
    load_dotenv()
    CONNECTION_TOKEN = os.getenv("TOKEN")
    
    # Gets the event loop
    loop = asyncio.new_event_loop()
    
    # Puts the load of dependency files into loop
    loop.run_until_complete(install_extensions(CLIENT))
    # Starts the bot client
    CLIENT.run(CONNECTION_TOKEN)
