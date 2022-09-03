from typing import Optional
from discord.ext import commands

from barmaid import CLIENT

@commands.hybrid_command(name="test", with_app_command=True)
async def test(ctx:commands.Context, *, name:Optional[str]):
    await ctx.send(f"hi {name}")

async def setup(target: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global CLIENT
    
    COMMANDS = [
        test
    ]
    
    for c in COMMANDS:
        target.add_command(c)
    CLIENT = target

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass