import discord
from discord.ext import commands
import random
from utilities import create_embed
from utilities import Settings as S

# Will be assigned by installing extensions from the main module
client:commands.Bot = None
       
@commands.guild_only()        
@commands.group(invoke_without_command=True,
                aliases=["roll","rolldice","diceroll"])
async def deathroll(ctx, range: int = 1000):
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
    """Subcommand for deathroll, informs the caller about the game rules.

    Args:
        ctx: Current context of the message that invoked the command.
    """
    game_rules = "Two players sets a bet typically for money. " \
    "They use that amount of money and multiply it by 10, 100 or 1000 to " \
    "make the starting rolling number higher so the game doesn't end too " \
    "quick. Any player can decide to start and rolls that result number " \
    "from multiplication. The randomly rolled number must the other player " \
    "use as the new rolling upperbound. First player whom reaches number " \
    "1 loses."
    embed = create_embed("Deathroll rules:", game_rules)
    await ctx.send(embed=embed,
                   delete_after=S.DELETE_EMBED_ORDINARY)
 
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
              
def setup(bot:commands.Bot):
    """Setup function which allows this module to be an extension
    loaded into the main file.

    Args:
        bot: The bot instance itself, passed in
        from barmaid.load_extention("minihames").
    """
    global client
    client = bot
    client.add_command(deathroll)
    client.add_command(git)

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass