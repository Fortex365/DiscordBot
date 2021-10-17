import discord
from discord.ext import commands
import random

client = None


@commands.command(aliases=["roll","rolldice","diceroll"])
async def deathroll(ctx, range=1000):
    """Outputs a random deathrolled number by given range,
    or tells if you lost.

    Args:
        ctx: Current context of the message that invoked the command.
        
        range (int, optional): Upper range for random generated number.
        Defaults to 1000.
    """
    num_int = int(range)
    res = random.randint(1,num_int)
    
    if res > 1:
        await ctx.send(
            f"{ctx.message.author.mention} deathrolled {res:,}. Range[1 - {range:,}]")
    else:
        await ctx.send(
            f"{ctx.message.author.mention} deathrolled {res:,} and LOST! Range[1 - {range:,}]")
  
    
def setup(client_bot):
    """Setup function which allows this module to be an extension
    loaded into the main file.

    Args:
        client_bot: The bot instance itself, passed in
        from barmaid.load_extention("minihames").
    """
    global client
    client = client_bot
    
    client_bot.add_command(deathroll)
