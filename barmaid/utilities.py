import discord
import json

def create_embed(title:str, description:str) -> discord.Embed:
        return discord.Embed(title=title, description=description)

class Settings:
        """Bot class containing settings loaded from configuration file.
        """
        # PREFIX
        DEFAULT_PREFIX = ".."
        
        # MESSAGES
        with open("config.json", "r") as f:
                serialized = json.load(f)
        msg_stngs = serialized['DeleteMessages']
           
        DELETE_ORDINARY_MESSAGE = msg_stngs['DELETE_HOUR']
        DELETE_COMMAND_ERROR = msg_stngs['DELETE_ORDINARY_MESSAGE']  
        DELETE_HOUR = msg_stngs['DELETE_COMMAND_ERROR'] 
        DELETE_EMBED_ORDINARY = msg_stngs['DELETE_EMBED_ORDINARY'] 
        DELETE_EMBED_SYSTEM = msg_stngs['DELETE_EMBED_SYSTEM']
        
        # ACTIVITY
        act_stngs = serialized['Activity']
        
        CLIENT_ACTIVITY = act_stngs['CLIENT_ACTIVITY']  
        

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass