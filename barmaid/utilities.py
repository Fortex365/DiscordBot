import json
from discord import Embed, Colour


"""Bot class containing settings loaded from configuration file.
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
DELETE_COMMAND_INVOKE = msg_stngs['DELETE_ORDINARY_MESSAGE']
DELETE_COMMAND_ERROR = msg_stngs['DELETE_COMMAND_ERROR']  
DELETE_EMBED_ORDINARY = msg_stngs['DELETE_EMBED_ORDINARY'] 
DELETE_EMBED_SYSTEM = msg_stngs['DELETE_EMBED_SYSTEM']
EMBED_HELP_COMMAND_COLOR = Colour.blue()

# ACTIVITY
act_stngs = serialized['Activity']

CLIENT_ACTIVITY = act_stngs['CLIENT_ACTIVITY']  

MASSDM_EXPLOIT_LIMIT = 200

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass