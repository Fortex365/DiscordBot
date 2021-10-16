import discord
from discord.ext import commands


client = None


@commands.command(aliases=["pong","ping!","pong!","latency"])
async def ping(ctx):
    """Outputs the ping between the client and the sever.

    Args:
        ctx: Current context of the message that invoked the command.
    """
    if ctx.message.guild: 
      await ctx.message.delete()
      await ctx.send(f"Pong! Latency: {round(client.latency*1000)} miliseconds.",
                     tts=True, delete_after=10)


@commands.command(aliases=["clr","delmsgs","delmsg"])
async def clear(ctx, amount = 1):
    """Clears the number of messages in the channel where it was invoked.

    Args:
        ctx: Current context of the message that invoked the command.
        amount (int, optional): Number of messages to be deleted to, excluding the invoked command itself. Defaults to 1.
    """
    await ctx.channel.purge(limit=amount+1)


@commands.command()
async def _dmall(ctx, msg):
    """Sends DMs to all members of all servers the bot is on.
    Bot owner only. Since its bannable for scam exploiting.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    await ctx.message.delete()
    if str(ctx.message.author.id) == "320281775249162240":
        pass    
        
        
@commands.command()
async def _invoker_id(ctx):
    """Sends the id discord reprezentation of message author into his DMs.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    await ctx.message.delete()
    id = ctx.message.author.id
    print(ctx.message.author)
    await ctx.message.author.send(id)
        
        
def setup(client_bot):
    """Setup function which allows this module to be an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself, passed in from barmaid.load_extention("admin_tools").
    """
    global client
    client = client_bot
    
    client_bot.add_command(ping)
    client_bot.add_command(clear)
    client_bot.add_command(_invoker_id)
    client_bot.add_command(_dmall)