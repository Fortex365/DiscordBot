import asyncio
import discord
from discord.ext import commands, tasks
from utilities import Settings as S, create_embed
from json_db import read_db, update_db

client = None
MICROSECONDS_TO_MILISECONDS = 1000

@commands.command(aliases=["pong","ping!","pong!","latency"])
@commands.guild_only()
async def ping(ctx:commands.Context):
    """Outputs the ping between the client and the server.

    Args:
        ctx: Current context of the message that invoked the command.
    """
    if ctx.message.guild: 
      await ctx.message.delete()
      await ctx.send(
          f"Pong! Latency: {round(client.latency*MICROSECONDS_TO_MILISECONDS)} miliseconds.",
          tts=True, delete_after=S.DELETE_ORDINARY_MESSAGE)
      
@commands.command(aliases=["clr","delmsgs","delmsg"])
@commands.guild_only()
async def clear(ctx:commands.Context, amount:int = 1):
    """Clears the number of messages in the channel where it was invoked.

    Args:
        ctx: Current context of the message that invoked the command.
        
        amount (int, optional): Number of messages to be deleted to,
        excluding the invoked command itself. Defaults to 1.
    """
    if amount > 0:
        await ctx.channel.purge(limit=amount+1)
    else:
        await ctx.send(f"Error! Amount of messages to be deleted has to be positive number.", 
                       delete_after=S.DELETE_COMMAND_ERROR)
               
@commands.command()
@commands.has_permissions(administrator=True)
async def invoker_id(ctx:commands.Context):
    """Sends the id discord representation of message author into his DMs.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    id = ctx.message.author.id
    if ctx.message.guild:
        await ctx.message.delete()
    await ctx.message.author.send(id)
    
@commands.command()
@commands.has_permissions(administrator=True)
async def guid(ctx:commands.Context):
    """Sends the guild id from context to the invoker into DMs.

    Args:
        ctx (commands.Context): Context deducted from invocation.
    """
    guid = ctx.guild.id
    await ctx.message.author.send(f"{guid = }")

def update_client_prefix(client:commands.Bot, new_prefix:str):
    """Changes the prefix the client listens to.
    Function used in prefix subcommand set.

    Args:
        new_prefix (str): New prefix to set to.
    """
    client_old = client
    client_new = client_old
    client_new.command_prefix = new_prefix
    return client_new

@commands.group(invoke_without_subcommand=True)
#@commands.has_permissions(administrator=True)
async def prefix(ctx:commands.Context):
    prefix = read_db(ctx.guild.id, "prefix")
    if not prefix:
        await ctx.send(f"Oops. Something internally went wrong with receiving the data.", 
                       delete_after=S.DELETE_ORDINARY_MESSAGE)
    
    if ctx.invoked_subcommand:
        return
    await ctx.send(f"Current bot prefix is set to `{prefix}` symbol.", 
                   delete_after=S.DELETE_ORDINARY_MESSAGE)
    await delete_invoke_itself(ctx, S.DELETE_ORDINARY_MESSAGE)

# SET PREFIX HAS TO BE COMMAND ON ITS OWN CUZ YOU CANNOT CHECK PERMISSIONS ON SUBCOMMANDS (PREFIX FOR EVERYONE, SET PREFIX FOR ADMINS ONLY) 
@prefix.command()
async def set(ctx:commands.Context, new_prefix:str=None):
    global client
    
    if not new_prefix:
        await ctx.send(f"Error! Prefix cannot be empty.", 
                       delete_after=S.DELETE_ORDINARY_MESSAGE)
        await delete_invoke_itself(ctx, S.DELETE_ORDINARY_MESSAGE)
        return

    if not update_db(ctx.guild.id, 'prefix', new_prefix):
        await ctx.send(f"Oops. Something internally went wrong with sending the data.",
                       delete_after=S.DELETE_ORDINARY_MESSAGE)
        return
    await ctx.send(f"Prefix was set to `{new_prefix}` succesfully.", 
                   delete_after=S.DELETE_ORDINARY_MESSAGE)
    await delete_invoke_itself(ctx, S.DELETE_ORDINARY_MESSAGE)
      
@commands.command()
@commands.guild_only()
@commands.has_permissions(kick_members = True)
@commands.bot_has_permissions(administrator = True)
async def kick(ctx:commands.Context, user: discord.Member, *,
               reason="No reason provided"):
    """Kicks the user from the server deducted from the context.

    Args:
        ctx (discord.Context): Context of the invoked command.
        user (discord.Member): Tagged discord member
        reason (str, optional): Reason why user was kicked from server.
        Defaults to "No reason provided".
    """
    await ctx.message.delete()
    await user.kick(reason=reason)    
    
    kick = create_embed(
        f"Kicked {str(user)}!", f"Reason: {reason}\nBy: {ctx.author.mention}")
    await ctx.channel.send(embed=kick, delete_after=S.DELETE_EMBED_SYSTEM)
    
    kick = create_embed(
        f"Kicked {str(user)}!", f"Reason: {reason}\nBy: {ctx.author}")
    await user.send(embed=kick)

@kick.error
async def kick_error(error:discord.errors, ctx:commands.Context):
    """Informs server owner deducted from context about who tried
    to perform an kick operation without permissions.

    Args:
        error (discord.errors): Error raised.
        ctx (commands.Context): Context of the invoked command.
    """
    if isinstance(error, commands.MissingPermissions):
        owner = ctx.guild.owner
        direct_message = await owner.create_dm()
    
        await direct_message.send(
            f"Missing permissions (kick_members): {ctx.message.author}")
      
@commands.command()
@commands.guild_only()
@commands.has_permissions(ban_members = True)
@commands.bot_has_permissions(administrator = True)
async def ban(ctx:commands.Context, user: discord.Member, *,
              reason: str ="No reason provided", del_msg_in_days: int = 1):
    """Bans the user from the server deducted from the context.

    Args:
        ctx (discord.Context): Context of the invoked command.
        user (discord.Member): Tagged discord member
        reason (str, optional): Reason why user was kicked from server.
        Defaults to "No reason provided".
    """
    await ctx.message.delete()
    await user.ban(reason=reason, delete_message_days=del_msg_in_days)    
    
    kick = create_embed(
        f"Banned {str(user)}!", f"Reason: {reason}\nBy: {ctx.author.mention}")
    await ctx.channel.send(embed=kick, delete_after=S.DELETE_EMBED_SYSTEM)
    
    kick = create_embed(
        f"Banned {str(user)}!", f"Reason: {reason}\nBy: {ctx.author}")
    await user.send(embed=kick)

@ban.error
async def ban_error(error:discord.errors, ctx:commands.Context):
    """Informs server owner deducted from context about who tried
    to perform an ban operation without permissions.

    Args:
        error (discord.errors): Error raised.
        ctx (commands.Context): Context of the invoked command.
    """
    if isinstance(error, commands.MissingPermissions):
        owner = ctx.guild.owner
        direct_message = await owner.create_dm()
        
        await direct_message.send(
            f"Missing permissions (ban_members): {ctx.message.author}")
  
@commands.command()
async def echo(ctx:commands.Context, *, message: str = None):
    """Echoes the message the command is invoked with.

    Args:
        ctx (discord.Context): Context of the invoked command.
        message (str): Message to be repeated.
    """
    if message == None:
        await ctx.send(f"Error! Argument {message=}",
                       delete_after=S.DELETE_ORDINARY_MESSAGE)
        await delete_invoke_itself(ctx, S.DELETE_ORDINARY_MESSAGE)
        return
    await ctx.message.delete()
    await ctx.send(message, delete_after=S.DELETE_ORDINARY_MESSAGE)
    
async def delete_invoke_itself(ctx:commands.Context, time:S):
    """Some time after command invocation has passed, the invoker's command message will be deleted.

    Args:
        ctx (commands.Context): Context to delete the message from.
        time (utilities.BarmaidSettings): Time to pass before delete happens.
    """
    await asyncio.sleep(time+1)
    await ctx.message.delete()
    
# to do:
# - auto-asign role for newbies
                  
def setup(client_bot: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global client
    client = client_bot
    
    client.add_command(ping)
    client.add_command(clear)
    client.add_command(invoker_id)
    client.add_command(prefix)
    client.add_command(ban) 
    client.add_command(kick)
    client.add_command(echo)
    client.add_command(guid)
    
if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass