import os
import discord
from discord.ext import commands

client = commands.Bot(command_prefix= "..")


def install_extensions(client):
    """Install all the extentions in the other files to the client.

    Args:
        client: The bot instance itself.
    """
    client.load_extension("admin_tools")    
            
            
@client.event
async def on_ready():
    """Method which sets some defaults when the client finally boots up.
    """
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Game(name="Your local e-Barmaid"))
    
    
CONNECTION_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
install_extensions(client)
client.run(CONNECTION_TOKEN)