import os
import discord
from discord.ext import commands
from utilities import Settings as S
from json_db import insert_db, read_db

# Intents manages some level of permissions
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.presences = True


# Code files to be loaded into client
# utilities.py not meant to be extension to be loaded into client
EXTENSIONS = ["admin_tools", "minigames"]

async def get_prefix(client:commands.Bot, message):
    if not message.guild:
        return commands.when_mentioned_or(S.DEFAULT_PREFIX)(client, message)
    
    prefix = read_db(message.guild.id, 'prefix')
    if not prefix:
        is_okay = insert_db(message.guild.id, 'prefix', S.DEFAULT_PREFIX)
        if not is_okay:
            #await ctx.send(f"Oops...", delete_after=S.DELETE_ORDINARY_MESSAGE)
            return
        prefix = S.DEFAULT_PREFIX
    return commands.when_mentioned_or(prefix)(client, message)

# Client has to be top level variable because of @ decorator 
client = commands.Bot(command_prefix=get_prefix, intents=INTENTS)

@client.event
async def on_ready():
    """Method which sets some inicialization when
    the client finally boots up.
    """
    await client.change_presence(status=discord.Status.idle,
        activity=discord.Game(name=S.CLIENT_ACTIVITY))

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
    # This is main module and only one to be executed.
    run(client)