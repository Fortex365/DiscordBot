import discord
from discord.ext import commands


client = None


@commands.command(description="Latency between the bot and discord servers.",
                  aliases=["pong","ping!","pong!","latency"])
async def ping(ctx):
    """Outputs the ping between the client and the sever.

    Args:
        ctx: Current context of the message that invoked the command.
    """
    if ctx.message.guild: 
      await ctx.message.delete()
      await ctx.send(f"Pong! Latency: {round(client.latency*1000)} miliseconds.",
                     tts=True, delete_after=10)


@commands.command(description="Deletes the given number of messages in the channel where was invoked",
                  aliases=["clr","delmsgs","delmsg"])
async def clear(ctx, amount = 1):
    """Clears the number of messages in the channel where it was invoked.

    Args:
        ctx: Current context of the message that invoked the command.
        amount (int, optional): Number of messages to be deleted to, excluding the invoked command itself. Defaults to 1.
    """
    await ctx.channel.purge(limit=amount+1)


def setup(client_bot):
    """Setup function which allows this module to be an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself, passed in from barmaid.load_extention("admin_tools").
    """
    global client
    client = client_bot
    
    client_bot.add_command(ping)
    client_bot.add_command(clear)