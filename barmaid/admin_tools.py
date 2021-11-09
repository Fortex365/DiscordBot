import discord
from discord.errors import Forbidden, HTTPException
from discord.ext import commands
import asyncio
from utils import create_embed


client = None

DELETE_HOUR = 3600
DELETE_REGULAR_MESSAGE = 15
DELETE_EMBED_REGULAR = 300
DELETE_SYSTEM_EMBED = 3600


@commands.command(aliases=["pong","ping!","pong!","latency"])
async def ping(ctx):
    """Outputs the ping between the client and the server.

    Args:
        ctx: Current context of the message that invoked the command.
    """
    if ctx.message.guild: 
      await ctx.message.delete()
      await ctx.send(f"Pong! Latency: {round(client.latency*1000)} miliseconds.",
                     tts=True, delete_after=DELETE_REGULAR_MESSAGE)


@commands.guild_only()
@commands.command(aliases=["clr","delmsgs","delmsg"])
async def clear(ctx, amount = 1):
    """Clears the number of messages in the channel where it was invoked.

    Args:
        ctx: Current context of the message that invoked the command.
        
        amount (int, optional): Number of messages to be deleted to,
        excluding the invoked command itself. Defaults to 1.
    """
    await ctx.channel.purge(limit=amount+1)


@commands.guild_only()
@commands.command()
@commands.has_permissions(administrator=True)
async def _dmall(ctx, msg):
    """Sends DMs to all members of all servers the bot is on.
    Bot owner only. Since its bannable for scam exploiting.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    await ctx.message.delete()
    if str(ctx.message.author.id) == "320281775249162240":
        await ctx.message.author.send("Not yet implemented command!")    

        
@commands.guild_only()        
@commands.command()
@commands.has_permissions(administrator=True)
async def _invoker_id(ctx):
    """Sends the id discord representation of message author into his DMs.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    await ctx.message.delete()
    id = ctx.message.author.id
    print(ctx.message.author)
    await ctx.message.author.send(id)


@commands.guild_only()
@commands.command()
@commands.has_permissions(kick_members = True)
@commands.bot_has_permissions(administrator = True)
async def kick(ctx, user: discord.Member, *,
               reason="No reason provided"):
    """Kicks the user from the server deducted from the context.

    Args:
        ctx (discord.Context): Context of the invoked command.
        user (discord.Member): Tagged discord member
        reason (str, optional): Reason why user was kicked from server. Defaults to "No reason provided".
    """
    await ctx.message.delete()
    await user.kick(reason=reason)    
    
    kick = create_embed(
        f"Kicked {str(user)}!", f"Reason: {reason}\nBy: {ctx.author.mention}")
    await ctx.channel.send(embed=kick, delete_after=DELETE_SYSTEM_EMBED)
    
    kick = create_embed(
        f"Kicked {str(user)}!", f"Reason: {reason}\nBy: {ctx.author}")
    await user.send(embed=kick)


@kick.error
async def kick_error(ctx, error):
    """Informs server owner deducted from context about who tried
    to perform an kick operation without permissions.

    Args:
        ctx (discord.Context): Context of the invoked command.
    """
    #if isinstance(error, Forbidden):
    owner = ctx.guild.owner
    direct_message = await owner.create_dm()
    
    await direct_message.send(
        f"Missing permissions (kick): {ctx.message.author}")
    
    
@commands.guild_only()
@commands.command()
@commands.has_permissions(ban_members = True)
@commands.bot_has_permissions(administrator = True)
async def ban(ctx, user: discord.Member, *, 
              reason="No reason provided",
              delete_message_days=1):
    """Bans the user from the server deducted from the context.

    Args:
        ctx (discord.Context): Context of the invoked command.
        user (discord.Member): Tagged discord member
        reason (str, optional): Reason why user was kicked from server. Defaults to "No reason provided".
    """
    await ctx.message.delete()
    await user.ban(reason=reason, delete_message_days=delete_message_days)    
    
    kick = create_embed(
        f"Banned {str(user)}!", f"Reason: {reason}\nBy: {ctx.author.mention}")
    await ctx.channel.send(embed=kick, delete_after=DELETE_SYSTEM_EMBED)
    
    kick = create_embed(
        f"Banned {str(user)}!", f"Reason: {reason}\nBy: {ctx.author}")
    await user.send(embed=kick)


@ban.error
async def ban_error(ctx, error):
    """Informs server owner deducted from context about who tried
    to perform an ban operation without permissions.

    Args:
        ctx (discord.Context): Context of the invoked command.
    """
    if isinstance(error, Forbidden):
        owner = ctx.guild.owner
        direct_message = await owner.create_dm()
        
        await direct_message.send(
            f"Missing permissions (ban): {ctx.message.author}")

     
@commands.command()
async def _echo(ctx, *, message: str = None):
    """Echoes the message the command is invoked with.

    Args:
        ctx (discord.Context): Context of the invoked command.
        message (str): Message to be repeated.
    """
    if message == None:
        await ctx.send("Empty args!", delete_after=DELETE_REGULAR_MESSAGE)
        await asyncio.sleep(DELETE_REGULAR_MESSAGE)
        await ctx.message.delete()
        return
    await ctx.send(message, delete_after=DELETE_REGULAR_MESSAGE)
    await asyncio.sleep(DELETE_REGULAR_MESSAGE)
    await ctx.message.delete()
           
        
def setup(client_bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global client
    client = client_bot
    
    client_bot.add_command(ping)
    client_bot.add_command(clear)
    client_bot.add_command(kick)
    client_bot.add_command(ban)
    
    client_bot.add_command(_invoker_id)
    client_bot.add_command(_dmall)
    client_bot.add_command(_echo)