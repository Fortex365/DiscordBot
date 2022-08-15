import json
from discord import Colour
from discord.ext import commands
import asyncio

"""
Bot instance containing settings loaded from configuration file.
"""
# PREFIX
DEFAULT_SERVER_PREFIX = ".."

# MESSAGES
try:
        with open("config.json", "r") as f:
                serialized = json.load(f)
except OSError:
        pass
msg_stngs = serialized['DeleteMessages']      
DELETE_HOUR = 3600 
DELETE_MINUTE = 60
DELETE_DAY = 3600*24 
DELETE_COMMAND_INVOKE = msg_stngs['DELETE_COMMAND_INVOKE']
DELETE_COMMAND_ERROR = msg_stngs['DELETE_COMMAND_ERROR']  
DELETE_EMBED_POST = msg_stngs['DELETE_EMBED_POST'] 
DELETE_EMBED_HELP = msg_stngs['DELETE_EMBED_HELP']
EMBED_HELP_COMMAND_COLOR = Colour.blue()

# ACTIVITY
act_stngs = serialized['Activity']
CLIENT_ACTIVITY = act_stngs['CLIENT_ACTIVITY']  

# Exploit prevention
MASSDM_EXPLOIT_LIMIT = 200

async def delete_command_user_invoke(ctx:commands.Context, time:int):
    """Some time after command invocation has passed, the invoker's command message will be deleted.

    Args:
        ctx (commands.Context): Context to delete the message from.
        time (int): Time to pass before delete happens.
    """
    await asyncio.sleep(time+1)
    await ctx.message.delete()

async def database_fail(ctx:commands.Context):
    """Informs the user that something unexpected went wrong.

    Args:
        ctx (commands.Context): Context to send message to.
    """
    await ctx.send("Oops. Something's wrong.", delete_after=DELETE_COMMAND_ERROR)

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass