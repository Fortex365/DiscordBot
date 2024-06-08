#region Module Imports
import os
import logging
import asyncio
from dotenv import load_dotenv

from datetime import datetime
from typing import Union
from discord import Member, Intents, Game, Status, Reaction, Role, Guild, Embed, Colour, User
from discord.message import Message
from discord.ext import commands, tasks
from discord.ext.commands import Context

import data_service.config_service as S
from data_service.config_service import DATABASE, RECORDS_DB, CLIENT_ACTIVITY
from data_service.database_service import guild_id_exists, insert_new_key_by_guild_id, read_key_by_guild_id, add_new_guild_id_with_empty_dataset, read_data_by_guild_id
from event_service.EventView import EventView
from log_service.setup import setup_logging
from re import search
from audio_service.audio import check_inactivity
#endregion 

#region Default App Settings

# Intents manages some level of permissions bot can do
INTENTS = Intents.default()
INTENTS.members, INTENTS.presences = True, True
INTENTS.message_content, INTENTS.reactions = True, True

# Listed modules to be loaded into client
EXTENSIONS = [
    # "commands.tools",
    "event_service.event",
    "audio_service.audio",
]

async def get_prefix(client: commands.Bot, message: Message):
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
    
    exists = await guild_id_exists(DATABASE, message.guild.id)
    if not exists:
        await add_new_guild_id_with_empty_dataset(DATABASE, message.guild.id)
    
    prefix = await read_key_by_guild_id(DATABASE, message.guild.id, 'prefix')
    if not prefix:
        is_okay = await insert_new_key_by_guild_id(DATABASE, message.guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX)
        if not is_okay:
            return
        prefix = S.DEFAULT_SERVER_PREFIX
    return commands.when_mentioned_or(prefix)(client, message)

# Client has to be top level variable because of @ decorator for events
CLIENT = commands.Bot(command_prefix=get_prefix, intents=INTENTS)

# Create of log handle
log_handle: logging.Logger = setup_logging()

#endregion

#region Events
@CLIENT.event
async def on_ready():
    """Initialization function to set some bot states, after it's bootup.
    """    
    await CLIENT.change_presence(status=Status.dnd, activity=Game(name="Booting..", start=datetime.now()))
    print("Online.")
    await asyncio.sleep(2)
    check_inactivity.start()
    change_status.start()

@CLIENT.event
async def on_guild_join(guild: Guild):
    """If bot joins new server it adds its guid to a database

    Args:
        guild (Guild): Guild bot joined in
    """
    while not await add_new_guild_id_with_empty_dataset(DATABASE, guild.id) or not await insert_new_key_by_guild_id(DATABASE, guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX):
        pass
        
    default_channel = guild.system_channel
    if default_channel:
        welcome_message = "Hello, everyone! I am your new bot. Use commands by pre-typing `/` to open context menu."
        try:
            await default_channel.send(welcome_message, delete_after=S.DELETE_HOUR)
        except Exception:
            pass

@CLIENT.event
async def on_member_join(member: Member):
    """Event triggered when member joins a server and assigns server's chosen
    role for that member.

    Args:
        member (Member): Member who joined server
    """
    role_id = await read_key_by_guild_id(DATABASE, member.guild.id, "auto-role")
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)
    
    await send_guild_rules(member, member.guild)
    if await check_records(member):
        await notify_mods_of_records(member, member.guild)

@CLIENT.event    
async def on_message(msg: Message):
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
    else:
        await msg.channel.send("I don't serve any drinks here.")

@CLIENT.event
async def on_message_edit(before: Message, after: Message):
    if after.author == CLIENT.user:
        return
    if after.guild:
        await check_blacklist(after.guild, after)

@CLIENT.event
async def on_command_error(ctx: Context, error: commands.CommandError):
    """Event triggered when command module raises an exception.
    Used to handle the raised exceptions

    Args:
        ctx (Context): Context passed by command that raised exception
        error (CommandError): Error instance
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(error, ephemeral=True)
        return

@CLIENT.event        
async def on_message_error(ctx: Context, error):
    pass

@CLIENT.event
async def setup_hook():
    """Syncs slash commands in all connected guilds and makes buttons
    restart persistent.
    """
    synced_commands = await CLIENT.tree.sync()
    print(f"In-app commands have been synchronized: {[sc.name for sc in synced_commands]}")
    CLIENT.add_view(EventView())

#endregion

#region Tasks
@tasks.loop(seconds=5)
async def change_status():
    status = next(CLIENT_ACTIVITY)
    await CLIENT.change_presence(activity=Game(status))
#endregion

#region Helper Functions
async def notify_mods_of_records(member: Member, guild: Guild):
    mods_id = await read_key_by_guild_id(DATABASE, guild.id, "mods_to_notify")
    mods = [guild.get_member(id) for id in mods_id if guild.get_member(id)]
    naughty_records = await read_data_by_guild_id(RECORDS_DB, member.id)
    
    for mod in mods:
        await mod.send(f"{member} joined {guild.name} with `{len(naughty_records)}` naughty records.\nUse `/records @mention` on your server to see more information.")

async def send_guild_rules(member: Member, guild: Guild):
    """For newly joined member on a server, bot sends this user server specified rules."""
    guild_rules = await read_key_by_guild_id(DATABASE, guild.id, "guild-rules")
    if guild_rules:
        rules = "\n".join([f"{idx + 1}. {rule}" for idx, rule in enumerate(guild_rules.values())])
        embed = Embed(title=f"[{guild.name}] server rules:", description=rules, color=Colour.red())
        embed.set_footer(text="Being a member of that server means you respect these rules.")
        await member.send(embed=embed)

async def check_blacklist(guild: Guild, msg: Message):
    """Checks if guild's blacklisted words are contained in message. Deletes the message if it contains blacklisted content and warns its author."""
    if await is_blacklist_exception(msg):
        return
    
    blacklist = await read_key_by_guild_id(DATABASE, guild.id, "blacklist")
    if not blacklist:
        return
    
    for word in blacklist:
        if word in msg.content:
            await msg.delete()
            await msg.author.send(f"Word \"{word}\" is restricted to use in `{guild.name}`")

async def check_records(member: Member) -> bool:
    """Checks whether or not the member has any records."""
    return bool(await guild_id_exists(RECORDS_DB, member.id))

async def is_blacklist_exception(msg: Message) -> bool:
    return search("filter remove", msg.content[:13].lower()) is not None

async def install_extensions(target: commands.Bot):
    """Installs all the extensions in the other files to the client."""
    for ext in EXTENSIONS:
        await target.load_extension(ext)

#endregion
       
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
