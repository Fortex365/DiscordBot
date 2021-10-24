import discord
from discord.ext import commands
import random
from utils import create_embed

client = None

DELETE_HOUR = 3600
DELETE_REGULAR_MESSAGE = 15
DELETE_EMBED_REGULAR = 300
DELETE_SYSTEM_EMBED = 3600
 
       
@commands.guild_only()        
@commands.group(invoke_without_command=True, aliases=["roll","rolldice","diceroll"])
async def deathroll(ctx, range=1000):
    """Outputs a random deathrolled number by given range,
    or tells if you lost.

    Args:
        ctx: Current context of the message that invoked the command.
        
        range (int, optional): Upper range for random generated number.
        Defaults to 1000.
    """
    if ctx.invoked_subcommand != None:
        return
    
    num_int = int(range)
    res = random.randint(1,num_int)

    if res > 1:
        await ctx.send(
            f"{ctx.message.author.mention} deathrolled {res:,}. Range[1 - {range:,}]")
    else:
        await ctx.send(
            f"{ctx.message.author.mention} deathrolled {res:,} and LOST! Range[1 - {range:,}]")
        
            
@deathroll.command()       
async def rules(ctx):
    """Subcommand for deathroll, informs the caller about the game rules."""
    rules_ = """Two players sets a bet typically for money. They use that amount of money and multiply it by 10, 100 or 1000 to make the starting rolling number higher so the game doesn't end too quick. Any player can decide to start and rolls that result number from multiplication. The randomly rolled number must the other player use as the new rolling upperbounds. First player whom reaches number 1 loses."""
    embed = create_embed("Deathroll rules:", rules_)
    await ctx.send(embed=embed, delete_after=DELETE_EMBED_REGULAR)

    
@commands.guild_only()
@commands.group()
async def git(ctx):
    """Pseudo-git game message.

    Args:
        ctx (discord.Context): Context of invoked command.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid git command passed.")


@git.command()
async def push(ctx, remote:str=None, branch:str=None):
    """Subcommand of git for pushing the data to git servers. 
    Messaging game.

    Args:
        ctx (discord.Context): Context of the invoked command.
        remote (str, optional): Remote to perform push on. Defaults to None.
        branch (str, optional): Branch to perform push on. Defaults to None.
    """
    if not remote or not branch:
        await ctx.send("Invalid push arguments passed.")
    else:
        await ctx.send(f"Pushing to {remote} {branch}")
    
            
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
    client_bot.add_command(git)
