import os

import asyncio
import logging
from datetime import datetime
from typing import Union
from discord import Member, Intents, Game, Status, Reaction
from discord import Role, Guild, Embed, Colour, User, Object
from discord.message import Message
from discord.ext import commands
from discord.ext.commands import Context

import utilities as S
import slash_commands
from jsonified_database import insert_db, read_db, add_guild
from error_log import setup_logging

# Intents manages some level of permissions bot can do
INTENTS = Intents.default()
INTENTS.members, INTENTS.presences = True, True
INTENTS.message_content, INTENTS.reactions = True, True

# Modules to be loaded into client
EXTENSIONS = [
    "admin_tools",
    "minigames",
    "events",
    "slash_commands"
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
    
    prefix = await read_db(message.guild.id, 'prefix')
    if not prefix:
        is_okay = await insert_db(message.guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX)
        if not is_okay:
            return
        prefix = S.DEFAULT_SERVER_PREFIX
    return commands.when_mentioned_or(prefix)(client, message)

# Client has to be top level variable because of @ decorator 
CLIENT = commands.Bot(command_prefix=get_prefix, intents=INTENTS)

# Log handler
log_handle:logging.Logger = setup_logging()

@CLIENT.event
async def on_reaction_add(reaction:Reaction, who_clicked:Union[Member, User]):
    """WIP THIS IS JUST A TEST 
    """    
    msg:Message = reaction.message
    
    if msg.guild:
        if who_clicked.bot:
            return
        if reaction.emoji in ["📝","❌", "🤷‍♀️"]:
            await msg.channel.send(f"{who_clicked.name} reacted {reaction.emoji}")

@CLIENT.event
async def on_ready():
    """Initialization function to set some bot states, after it's bootup.
    """    
    await CLIENT.change_presence(status=Status.idle,
        activity=Game(name=S.CLIENT_ACTIVITY, start=datetime.now()))
    print("Online.")

@CLIENT.event
async def on_guild_join(guild:Guild):
    """If bots joins new server it adds its guid to a database

    Args:
        guild (Guild): Guild bot joined in
    """
    success = await add_guild(guild.id)
    while not success:
        success = await add_guild(guild.id)

@CLIENT.event
async def on_member_join(member:Member):
    """Event triggered when member joins a server and asigns server's chosen
    role for that member.

    Args:
        member (Member): Member who joined server
    """
    # Auto-asign role given by guild
    role_asigned_by_guild:int = await read_db(member.guild.id, "auto-role")
    member_guild:Guild = member.guild
    if role_asigned_by_guild:
        role_to_give:Role = member_guild.get_role(role_id=role_asigned_by_guild)
        await member.add_roles(role_to_give)
    
    # Auto-rules given by guild
    await send_guild_rules(member, member_guild)
    
async def send_guild_rules(member:Member, guild_joined:Guild):
    """For newly joined member on a server, bot sends this user server specified
    rules.

    Args:
        member (Member): Member who joined
        guild_joined (Guild): Guild which member joined
    """
    guild_rules = await read_db(guild_joined.id, "guild-rules")
    if guild_rules:
        emb = Embed(title=f"[{guild_joined.name}] server's rules:",
                    description=guild_rules,
                    color=Colour.red())
        emb.set_footer(text="Using features on that server means you do respect these rules.")
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
    
    bl = await read_db(guild.id, "blacklist")
    if not bl:
        return
    
    msg_content = msg.content
    
    for w in bl:
        if w in msg_content:
            await msg.delete()
            await msg.author.send(f"Word \"{w}\" is restricted to use in `{guild.name}`")

async def is_blacklist_exception(msg:Message)->bool:
    FILTER_REMOVE_COMMAND_EXCEPTION = "filter remove"
    msg_content = msg.content
    msg_content.lower()
    
    if FILTER_REMOVE_COMMAND_EXCEPTION in msg_content:
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
        await ctx.send(f"{error}", delete_after=S.DELETE_COMMAND_ERROR,
                       ephemeral=True)
        await ctx.message.delete()
        return
    elif isinstance(error, commands.CommandInvokeError):
        raise error
        #return
    raise error
    
@CLIENT.event
async def on_message_error(ctx:Context, error):
    raise error

@CLIENT.event
async def setup_hook():
    await CLIENT.tree.sync()
    print(f"hybrid commands synced")

async def install_extensions(target:commands.Bot):
    """Install all the extentions in the other files to the client.

    Args:
        client (commands.Bot): Instance of the bot itself.
    """
    for ext in EXTENSIONS:
        await target.load_extension(ext)
        
    
if __name__ == "__main__":
    """This is main module and only one to be executed."""
    
    CONNECTION_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    loop = asyncio.get_event_loop()
    
    # Boots up the client
    loop.run_until_complete(install_extensions(CLIENT))
    CLIENT.run(CONNECTION_TOKEN)
