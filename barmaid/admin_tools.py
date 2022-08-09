import asyncio
import utilities as S
import string
from discord import Embed, Member, errors, channel, Invite, Role, Guild, Message
from discord.ext import commands
from jsonyzed_db import insert_db, read_db, update_db

client:commands.Bot = None
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
          tts=True, delete_after=S.DELETE_COMMAND_INVOKE)
      
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
@commands.guild_only()
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
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def guid(ctx:commands.Context):
    """Sends the guild id from context to the invoker into DMs.

    Args:
        ctx (commands.Context): Context deducted from invocation.
    """
    guid = ctx.guild.id
    await ctx.message.author.send(f"{guid = }")

@commands.command(invoke_without_subcommand=True)
@commands.guild_only()
async def prefix(ctx:commands.Context):
    prefix = read_db(ctx.guild.id, "prefix")
    if not prefix:
        await ctx.send(f"Oops. Something internally went wrong with receiving the data.", 
                       delete_after=S.DELETE_COMMAND_ERROR)
    
    if ctx.invoked_subcommand:
        return
    await ctx.send(f"Current bot prefix is set to `{prefix}` symbol.", 
                   delete_after=S.DELETE_COMMAND_INVOKE)
    await delete_invoke_itself(ctx, S.DELETE_COMMAND_INVOKE)

"""SET PREFIX HAS TO BE COMMAND ON ITS OWN
CUZ YOU CANNOT CHECK PERMISSIONS ON SUBCOMMANDS
(PREFIX FOR EVERYONE, SET PREFIX FOR ADMINS ONLY)""" 
@commands.command(aliases=["prefixset"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def setprefix(ctx:commands.Context, new_prefix:str=None):
    global client
    SYMBOLS = string.punctuation
    
    if not new_prefix:
        await ctx.send(f"Error! Prefix cannot be empty.", 
                       delete_after=S.DELETE_COMMAND_ERROR)
        await delete_invoke_itself(ctx, S.DELETE_COMMAND_INVOKE)
        return

    try:
        _check_prefix(new_prefix)
    except ValueError:
        await ctx.send(f"Oops. Prefix can only be one of special characters " +
                       f"like {SYMBOLS}", delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    if not update_db(ctx.guild.id, 'prefix', new_prefix):
        await ctx.send(f"Oops. Something internally went wrong with sending the data.",
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    await ctx.send(f"Prefix was set to `{new_prefix}` successfully.", 
                   delete_after=S.DELETE_COMMAND_INVOKE)
    await delete_invoke_itself(ctx, S.DELETE_COMMAND_INVOKE)
    
def _check_prefix(prefix:str):
    SYMBOLS = string.punctuation
    
    if prefix == S.DEFAULT_SERVER_PREFIX:
        return prefix
    if (len(prefix) > 1) or (not prefix in SYMBOLS):
        raise ValueError(f"Prefix cannot have more than one special symbol {prefix=}")
    return prefix
      
@commands.command()
@commands.guild_only()
@commands.has_permissions(kick_members = True)
@commands.bot_has_permissions(administrator = True)
async def kick(ctx:commands.Context, user: Member, *,
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
    
    kick = Embed(f"Kicked {str(user)}!", f"Reason: {reason}\nBy: {ctx.author.mention}")
    await ctx.channel.send(embed=kick, delete_after=S.DELETE_EMBED_SYSTEM)
    
    kick = Embed(f"Kicked {str(user)}!", f"Reason: {reason}\nBy: {ctx.author}")
    await user.send(embed=kick)

@kick.error
async def kick_error(error:errors, ctx:commands.Context):
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
async def ban(ctx:commands.Context, user: Member, *,
              reason: str ="No reason provided", del_msg_in_days: int = 1):
    """Bans the user from the server deducted from the context.

    Args:
        ctx (discord.Context): Context of the invoked command.
        user (discord.Member): Tagged discord member
        reason (str, optional): Reason why user was kicked from server.
        del_msg_in_days (int): Deletes msgs banned user wrote in past days
        Defaults to "No reason provided".
    """
    await ctx.message.delete()
    await user.ban(reason=reason, delete_message_days=del_msg_in_days)    
    
    ban = Embed(f"Banned {str(user)}!", f"Reason: {reason}\nBy: {ctx.author.mention}")
    await ctx.channel.send(embed=ban, delete_after=S.DELETE_EMBED_SYSTEM)
    
    ban = Embed(f"Banned {str(user)}!", f"Reason: {reason}\nBy: {ctx.author}")
    await user.send(embed=ban)

@ban.error
async def ban_error(error:errors, ctx:commands.Context):
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
                       delete_after=S.DELETE_COMMAND_ERROR)
        await delete_invoke_itself(ctx, S.DELETE_COMMAND_INVOKE)
        return
    if ctx.guild:
        await ctx.message.delete()
    await ctx.send(message, delete_after=S.DELETE_COMMAND_INVOKE)
    
async def delete_invoke_itself(ctx:commands.Context, time:S):
    """Some time after command invocation has passed, the invoker's command message will be deleted.

    Args:
        ctx (commands.Context): Context to delete the message from.
        time (utilities.BarmaidSettings): Time to pass before delete happens.
    """
    await asyncio.sleep(time+1)
    await ctx.message.delete()
    
# to do:
# - mass channel users move
# - pravidla

@commands.command(alias=["dmall", "alldm"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def massdm(ctx:commands.Context, *, msg:str):
    owner:Member = ctx.guild.owner
    
    await ctx.message.delete()
    if ctx.author == owner:
        if not msg:
            await owner.send(f"DM-ALL argument message was empty.")
            return
        server:Guild = ctx.guild

        if server.member_count <= S.MASSDM_EXPLOIT_LIMIT: 
            for mem in server.members:
                if mem == owner:
                    await mem.send(f"[DM-ALL] what was sent to others:\n\n" +
                                   msg)
                    continue
                if mem.bot == True:
                    continue
                await mem.send(msg)
            return
        await owner.send("[DM-ALL] Cannot sent because server member count" +
            f"exceeded limit of {S.MASSDM_EXPLOIT_LIMIT}")
        

@commands.command(aliases=["invitebot", "botinvite", "boturl", "urlbot"])
async def invite(ctx:commands.Context):
    INVITE_URL = "https://discord.com/oauth2/authorize?client_id=821538075078557707&permissions=8&scope=bot%20applications.commands"
    msg = Embed(title="Invitation link [Bot]", description=INVITE_URL)
    await ctx.send(embed=msg,
                   delete_after=S.DELETE_MINUTE)
    await delete_invoke_itself(ctx, S.DELETE_COMMAND_INVOKE)
    
@commands.guild_only()
@commands.group(invoke_without_command=True,
                aliases=["invitef", "invitefriend", "finv", "invf"])
async def finvite(ctx:commands.Context, temp:bool=False, age:int=0,
                  use:int=0):
    if not ctx.invoked_subcommand:
        ch:channel.TextChannel = ctx.channel
        invite:Invite = await ch.create_invite(temporary=temp, max_use=use,
                                    max_age=age)
        embd = Embed(title="Invitation link [Server]", description=invite.url)
        await ctx.send(embed=embd, delete_after=S.DELETE_MINUTE)
        await delete_invoke_itself(ctx, S.DELETE_COMMAND_INVOKE)

    
@finvite.command()
async def help(ctx:commands.Context):
    embd = Embed(title="Help: finvite", 
                 description="Args: temp[True/False] max_age[seconds] max_uses[number]",
                 color=S.EMBED_HELP_COMMAND_COLOR)
    await ctx.send(embed=embd)

@commands.group(invoke_without_command=True, aliases=["asignrole","roleasign"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def autorole(ctx:commands.Context):
    if not ctx.invoked_subcommand:
        response = read_db(ctx.guild.id, "auto-role")
        if response:
            await ctx.send(f"{response}")
            return
        await ctx.send(f"Failed.", delete_after=S.DELETE_COMMAND_ERROR)
            
@autorole.command()
async def set(ctx:commands.Context, role:Role):
    guid = ctx.guild.id
    response = insert_db(guid, "auto-role", role.id)
    if response:
        await ctx.send(f"New prefix set.", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    response = update_db(guid, "auto-role", role.id)
    if response:
        await ctx.send(f"Prefix was updated.", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Failed.", delete_after=S.DELETE_COMMAND_ERROR)
         
def setup(client_bot: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global client
    client = client_bot
    
    COMMANDS = [ping, clear, invoker_id, prefix, setprefix, ban, kick, echo, 
                guid, invite, finvite, autorole, massdm]
    
    for c in COMMANDS:
        client.add_command(c)

    
if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass