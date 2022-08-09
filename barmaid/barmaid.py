import os
import logging
import utilities as S
from datetime import datetime
from discord import Member, Intents, Game, Status, utils, Role, Guild
from discord.message import Message
from discord.ext import commands
from discord.ext.commands import Context
from jsonyzed_db import insert_db, read_db
from error_log import setup_logging

# Intents manages some level of permissions
INTENTS = Intents.default()
INTENTS.members, INTENTS.presences = True, True


# Code files to be loaded into client
# utilities.py not meant to be extension to be loaded into client
EXTENSIONS = ["admin_tools", "minigames"]

async def get_prefix(client:commands.Bot, message:Message):
    """Retrieves the prefix corresponding to a server if set,
    otherwise returns default one.

    Args:
        client (commands.Bot): Bot instance
        message (Message): Any message that can contain prefix

    Returns:
        list: list of prefixes outputed via commands.when_mentioned_or
    """
    if not message.guild:
        return commands.when_mentioned_or(S.DEFAULT_SERVER_PREFIX)(client, message)
    
    prefix = read_db(message.guild.id, 'prefix')
    if not prefix:
        is_okay = insert_db(message.guild.id, 'prefix', S.DEFAULT_SERVER_PREFIX)
        if not is_okay:
            return
        prefix = S.DEFAULT_SERVER_PREFIX
    return commands.when_mentioned_or(prefix)(client, message)

# Client has to be top level variable because of @ decorator 
client = commands.Bot(command_prefix=get_prefix, intents=INTENTS)

# Log handler
log_handle:logging.Logger = setup_logging()

@client.event
async def on_ready():
    """Initialization function to set some bot states, after it's bootup.
    """
    await client.change_presence(status=Status.idle,
        activity=Game(name=S.CLIENT_ACTIVITY, start=datetime.now()))

@client.event
async def on_member_join(member:Member):
    """Event triggered when member joins a server and asigns server's chosen
    role for that member.

    Args:
        member (Member): Member who joined server
    """
    role_asigned_by_guild:int = read_db(member.guild.id, "auto-role")
    member_guild:Guild = member.guild
    role_to_give:Role = member_guild.get_role(role_id=role_asigned_by_guild)
    await member.add_roles(role_to_give)

@client.event    
async def on_message(msg:Message):
    """Event triggered when bot sees a message in guild or in his direct
    messages. Used to further process message for commands in guild
    or talk back in direct messages.

    Args:
        msg (Message): Message that triggered the event
    """
    if msg.author == client.user:
        return
    if msg.guild:
        await client.process_commands(msg)
        return
    await msg.channel.send("Nothing precoded answer here.")
    
@client.event
async def on_command_error(ctx:Context, error:commands.CommandError):
    """Event triggered when command module raises an exception.
    Used to handle the raised exceptions

    Args:
        ctx (Context): Context passed by command that raised exception
        error (CommandError): Error instance
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{error}", delete_after=S.DELETE_COMMAND_ERROR)
        return
    raise error
    
@client.event
async def on_message_error(ctx:Context, error):
    raise error

def get_client() -> commands.Bot:
    """Kinda redundant cause client is top level variable
    accessible everywhere in this module.
    May delete this function later.

    Returns:
        client (commands.Bot): instance of client
    """
    return client

def install_extensions(target:commands.Bot):
    """Install all the extentions in the other files to the client.

    Args:
        client (commands.Bot): Instance of the bot itself.
    """
    for ext in EXTENSIONS:
        target.load_extension(ext) 
                 
def run(client:commands.Bot):
    """Method serves as a main function which is run when this module is run. 
    Meant to be the only module from this package that can be executed.
    
    Args:
        client (commands.Bot): Instance of the bot itself.
    """   
    CONNECTION_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    install_extensions(client)
    client.run(CONNECTION_TOKEN)
    
if __name__ == "__main__":
    """This is main module and only one to be executed."""
    
    # Boots up the client
    run(client)