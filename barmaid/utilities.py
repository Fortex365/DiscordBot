import discord

def create_embed(title:str, description:str) -> discord.Embed:
        return discord.Embed(title=title, description=description)

class BarmaidSettings:
        # Time in seconds
        DELETE_HOUR = 3600
        DELETE_ORDINARY_MESSAGE = 15
        DELETE_COMMAND_ERROR = 15
        DELETE_EMBED_ORDINARY = 300
        DELETE_EMBED_SYSTEM = 3600
        # Prefix for invoking commands, has to be some string symbol
        CLIENT_PREFIX = ".."
        # Presence activity to show up
        CLIENT_ACTIVITY = "Your local e-Barmaid"

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass