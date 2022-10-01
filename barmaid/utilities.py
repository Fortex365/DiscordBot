import json
from discord import Colour
from discord.ext import commands

HOURS_TO_DAY=24
CONFIG_FILE_NAME = "config.json"
READ_MODE = "r"

"""
Server default prefix symbol
"""
DEFAULT_SERVER_PREFIX = ".."

"""
Message settings
"""
try:
    with open(CONFIG_FILE_NAME, READ_MODE) as f:
        settings = json.load(f)
except OSError:
        pass

msg_stngs = settings['DeleteMessages']      
DELETE_HOUR = 3600 
DELETE_MINUTE = 60
DELETE_DAY = DELETE_HOUR*HOURS_TO_DAY 
DELETE_COMMAND_INVOKE = msg_stngs['DELETE_COMMAND_INVOKE']
DELETE_COMMAND_ERROR = msg_stngs['DELETE_COMMAND_ERROR']  
DELETE_EMBED_POST = msg_stngs['DELETE_EMBED_POST'] 
DELETE_EMBED_HELP = msg_stngs['DELETE_EMBED_HELP']
EMBED_HELP_COMMAND_COLOR = Colour.blue()

"""
Filenames
"""
DATABASE = settings["DATABASE_FILE_NAME"]
NAUGHTY = settings["GLOBAL_NAUGHTY_LIST"]

"""
Activity settings
"""
act_stngs = settings['Activity']
CLIENT_ACTIVITY = act_stngs['CLIENT_ACTIVITY']  

"""
Security settings
"""
MASSDM_EXPLOIT_LIMIT = 200

"""
Bot related stuff
"""
BOT_INVITE_URL = "https://discord.com/api/oauth2/authorize?client_id=" \
    "821538075078557707&permissions=8&scope=bot%20applications.commands"

"""
Utility functions
"""
async def delete_command_user_invoke(ctx:commands.Context, time:int):
    """Some time after command invocation has passed, the invoker's command message will be deleted.

    Args:
        ctx (commands.Context): Context to delete the message from.
        time (int): Time to pass before delete happens.
    """
    await ctx.message.delete(delay=time+1)

async def database_fail(ctx:commands.Context):
    """Informs the user that something unexpected went wrong.

    Args:
        ctx (commands.Context): Context to send message to.
    """
    await ctx.send("An error occured. Try again.",
                   delete_after=DELETE_COMMAND_ERROR)

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass