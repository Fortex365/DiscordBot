import os
import discord
from discord.ext import commands
from utilities import BarmaidSettings as BS

# Intents manages some level of permissions
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.presences = True

# Client has to be top level variable because of @ decorator 
client = commands.Bot(command_prefix=BS.CLIENT_PREFIX, intents=INTENTS)

# Code files to be loaded into client
# utilities.py not meant to be extension to be loaded into client
EXTENSIONS = ["admin_tools", "minigames"]

@client.event
async def on_ready():
    """Method which sets some inicialization when
    the client finally boots up.
    """
    await client.change_presence(status=discord.Status.idle,
        activity=discord.Game(name=BS.CLIENT_ACTIVITY))

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