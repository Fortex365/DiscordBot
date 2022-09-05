import re
import string
import discord
from typing import Optional
from discord import Embed, Member, channel, Invite, Role, Guild, VoiceChannel
from discord import Interaction, SelectOption, File, Button
from discord.ext import commands
from discord.ext.commands import errors

import utilities as S
from utilities import delete_command_user_invoke, database_fail
from jsonified_database import delete_from_db, insert_db, read_db, update_db

from barmaid import CLIENT

@commands.hybrid_command(name="ping",
                         aliases=["pong","ping!","pong!","latency"],
                         with_app_command=True)
@commands.guild_only()
async def ping(ctx:commands.Context):
    """Latency between bot and discord.

    Args:
        ctx: Current context of the message that invoked the command.
    """
    MICROSECONDS_TO_MILISECONDS = 1000

    await ctx.defer(ephemeral=True)
    
    await ctx.send(
          "Pong! Latency: " \
              f"{round(CLIENT.latency*MICROSECONDS_TO_MILISECONDS)} " \
                  "miliseconds",
          delete_after=S.DELETE_COMMAND_INVOKE)
    
    if not ctx.interaction: 
      await ctx.message.delete()
      
@commands.hybrid_command(name="clear",
                         aliases=["clr","delmsgs","delmsg"],
                         with_app_command=True)
@commands.guild_only()
@commands.has_permissions(manage_messages=True)
async def clear(ctx:commands.Context, amount:int=1):
    """Removes any number of messages in chat history.

    Args:
        ctx: Current context of the message that invoked the command.
        amount (optional): Number of messages to delete.
    """
    # If invoked via slash commands, no need to purge invoke itself.
    if not ctx.interaction:
        amount += 1
    
    await ctx.defer(ephemeral=True)    
    if amount > 0:
        await ctx.channel.purge(limit=amount)
        amount = amount - 1 if not ctx.interaction else amount
        await ctx.send(content=f"Cleared `{amount}` message(s)",
                       delete_after=S.DELETE_COMMAND_INVOKE)
    else:
        await ctx.send(f"Amount of messages to be deleted has" \
            " to be a positive number",
            delete_after=S.DELETE_COMMAND_ERROR)
        
@clear.error
async def clear_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)    

    # Bot missing permissions
    if isinstance(error, discord.Forbidden):
        await ctx.send(f"{CLIENT} missing permissions `Manage Messages`",
                        delete_after=S.DELETE_COMMAND_ERROR)
    # User missing permission
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(error, delete_after=S.DELETE_COMMAND_ERROR)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
    
@commands.hybrid_command(name="id",
                         with_app_command=True)
async def id(ctx:commands.Context):
    """Sends your discord identificator number.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    id = ctx.message.author.id
    await ctx.defer(ephemeral=True)
    
    if not ctx.interaction:
        if ctx.message.guild:
            await ctx.message.delete()
        await ctx.message.author.send(id)
        return
    await ctx.send(id)

@id.error
async def invoker_id_error(ctx:commands.Context, error:errors,):
    await ctx.defer(ephemeral=True)
    
    await ctx.send(error,
                   delete_after=S.DELETE_COMMAND_ERROR)
        
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

@commands.hybrid_command(name="echo",
                         aliases=["repeat"],
                         with_app_command=True)
async def echo(ctx:commands.Context, *, message:str=None):
    """Echoes the message the command is invoked with.

    Args:
        ctx: Context of the invoked command.
        message: Message to be repeated.
    """
    
    if not message:
        raise commands.CommandError(f"Argument message cannot be empty. Was `{message}`")
    
    await ctx.defer(ephemeral=True)
    if ctx.guild and not ctx.interaction:
        await ctx.message.delete()
    await ctx.send(message,
                   delete_after=S.DELETE_COMMAND_INVOKE)

@echo.error
async def echo_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    
    if isinstance(error, commands.CommandError):
        await ctx.send(error,
                       delete_after=S.DELETE_COMMAND_ERROR)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
    
@commands.hybrid_command(name="guid",
                         aliases=["guildid", "gid"],
                         with_app_command=True)
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def guid(ctx:commands.Context):
    """Sends your discord server id identificator number.

    Args:
        ctx: Context deducted from invocation.
    """
    server_id = ctx.guild.id
    await ctx.defer(ephemeral=True)
    if not ctx.interaction:
        await ctx.message.author.send(f"{server_id = }")
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"{server_id = }")
    
@guid.error
async def guid_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(error,
                       delete_after=S.DELETE_COMMAND_ERROR)
  
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

def _check_prefix(prefix:str):
    """Checks if input string is valid prefix.

    Args:
        prefix (str): Prefix to check

    Raises:
        ValueError: If prefix is not valid

    Returns:
        str: Valid prefix
    """
    SYMBOLS = string.punctuation
    
    if prefix == S.DEFAULT_SERVER_PREFIX:
        return prefix
    
    if (len(prefix) > 1) or (not prefix in SYMBOLS):
        return False
    return prefix

@commands.hybrid_command(name="prefix",
                         with_app_command=True)
@commands.guild_only()
async def prefix(ctx:commands.Context):
    """Prefix used in discord server.

    Args:
        ctx (commands.Context): Context of command invocation
    """
    await ctx.defer(ephemeral=True)
    
    prefix = await read_db(ctx.guild.id, "prefix")
    if not prefix:
        await database_fail(ctx)
        return
    
    await ctx.send(f"Current bot prefix is set to `{prefix}` symbol.", 
                   delete_after=S.DELETE_COMMAND_INVOKE)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

@prefix.error
async def prefix_error(ctx:commands.Context, error:errors):
    await ctx.send(error,
                   delete_after=S.DELETE_COMMAND_ERROR)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

@commands.hybrid_command(name="setprefix",
                         aliases=["prefixset"],
                         with_app_command=True)
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def setprefix(ctx:commands.Context, new_prefix:str=None):
    """Sets new prefix for discord server.

    Args:
        ctx (commands.Context): Context of command invocation
        new_prefix (str, optional): Symbol to be the new prefix.
    """
    SYMBOLS = string.punctuation
    
    if not new_prefix:
        raise commands.CommandError(f"Argument new_prefix cannot be empty. Was `{new_prefix}`")
    
    if not _check_prefix(new_prefix):
        raise commands.CommandError("Prefix cannot have more than one special symbol. " \
            f"Allowed symbols are:\n > {SYMBOLS}")

    await ctx.defer(ephemeral=True)
    if not await update_db(ctx.guild.id, 'prefix', new_prefix):
        await database_fail(ctx)
    else:
        await ctx.send(f"Prefix was set to `{new_prefix}` successfully.", 
                    delete_after=S.DELETE_COMMAND_INVOKE)
        
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

@setprefix.error
async def setprefix_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    
    if isinstance(error, commands.CommandError):
        await ctx.send(error,
                       delete_after=S.DELETE_COMMAND_ERROR)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(error,
                       delete_after=S.DELETE_COMMAND_ERROR)
        
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR) 
        
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
@commands.has_permissions(kick_members = True)
async def kick(ctx:commands.Context,
                   members:commands.Greedy[Member]=None, *,
                   reason:str="No reason provided"):
    """Kicks multiple users from discord server.

    Args:
        ctx (commands.Context): Context of command invocation
        members (commands.Greedy[Member], optional): Multiple mentioned members
        Defaults to None.
        reason (str, optional): Anything they did wrong
    """
    if not members:
        raise commands.CommandError("No people to perform kick operation.")

    names = [mem.name for mem in members]
    names_str = ", ".join(names) if len(names) > 1 else names[0]
    
    # Server-side      
    kick = Embed(title=f"Kicked {names_str}!", description=f"Reason: {reason}")
    kick.set_footer(text=f"By: {ctx.author}")
    await ctx.channel.send(embed=kick,
                   delete_after=S.DELETE_DAY)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    # Member-side
    for member in members:
        kick = Embed(title=f"You were kicked from {ctx.guild.name}",
                     description=f"Reason: {reason}")
        kick.set_footer(text=f"By: {ctx.author}")
        # Send can fail, because member can block DM's from server members.
        try:
            await member.send(embed=kick)
        except discord.Forbidden:
            # We still want to kick that member
            await member.kick(reason=reason)
            continue
        await member.kick(reason=reason)
    # App response
    await ctx.defer(ephemeral=True)
    await ctx.send("Success!", 
                   delete_after=S.DELETE_COMMAND_INVOKE)

@kick.error
async def kick_error(ctx:commands.Context, error:errors):
    """Informs server owner deducted from context about who tried
    to perform an kick operation without permissions.

    Args:
        error (discord.errors): Error raised.
        ctx (commands.Context): Context of the invoked command.
    """
    if isinstance(error, commands.MissingPermissions):
        owner = ctx.guild.owner
        direct_message = await owner.create_dm()
        await direct_message.send(f"{ctx.message.author} performed " \
            "kick operation, but misses permission Kick Members.")
        await ctx.defer(ephemeral=True)
        await ctx.send(error)
        if not ctx.interaction:
            await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
        return

    await ctx.defer(ephemeral=True)
    await ctx.send(error,
                delete_after=S.DELETE_COMMAND_ERROR)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
    return
      
@commands.group(invoke_without_command=True)
@commands.guild_only()
@commands.has_permissions(ban_members = True)
@commands.bot_has_permissions(administrator = True)
async def ban(ctx:commands.Context, user:Member, *,
              reason:str ="No reason provided", del_msg_in_days:int = 1):
    """Bans the user from the server deducted from the context.

    Args:
        ctx (discord.Context): Context of the invoked command.
        user (discord.Member): Mentioned discord member
        reason (str, optional): Reason why user was kicked from server.
        del_msg_in_days (int): Deletes msgs banned user wrote in past days
        Defaults to "No reason provided".
    """
    if not ctx.invoked_subcommand:
        
        # Member-side
        ban = Embed(title=f"Banned {user}!", description=f"Reason: {reason}")
        ban.set_footer(text=f"By: {ctx.author}")
        await user.ban(reason=reason, delete_message_days=del_msg_in_days)    
        await user.send(embed=ban)
        
        # Server-side
        await ctx.message.delete()
        ban = Embed(title=f"Banned {user}!", description=f"Reason: {reason}")
        ban.set_footer(text=f"By: {ctx.author}")
        await ctx.channel.send(embed=ban, delete_after=S.DELETE_DAY)

@ban.command()
async def more(ctx:commands.Context, members:commands.Greedy[Member]=None,
               days:int=1, *, reason:str="No reason provided"):
    """Subcommand of ban to allow multiple users to ban.

    Args:
        ctx (commands.Context): Context of command invocation
        members (commands.Greedy[Member], optional): Mention of members. Defaults to None.
        days (int, optional): Days to delete user's messages in history. Defaults to 1.
        reason (str, optional): Reason of punishment. Defaults to "No reason provided".
    """
    if not members:
        await ctx.send(f"Error! No people to ban",
                        delete_after=S.DELETE_COMMAND_ERROR)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    
    for member in members:
        # Member-side
        ban = Embed(title=f"Banned {member}!", description=f"Reason: {reason}")
        ban.set_footer(text=f"By: {ctx.author}")
        await member.ban(reason=reason, delete_message_days=days)
        await member.send(embed=ban)

    # Server-side
    await ctx.message.delete()
    ban = Embed(title=f"Banned {members}!", description=f"Reason: {reason}")
    ban.set_footer(text=f"By: {ctx.author}")
    await ctx.send(embed=ban, delete_after=S.DELETE_DAY)

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
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    raise error
  
@commands.group(invoke_without_command=True)
@commands.guild_only()
@commands.has_permissions(move_members=True)
async def move(ctx:commands.Context, destination:VoiceChannel=None,
               source:VoiceChannel=None, *, reason:str=None):
    """Provides control to move all members of one channel into other channel.

    Args:
        ctx (commands.Context): Context of command invoke
        destination (VoiceChannel, optional): Where to move them. Defaults to None.
        source (VoiceChannel, optional): From where. Defaults to None.
        reason (str, optional): Why to move them. Defaults to None.
    """
    if not ctx.invoked_subcommand:
        members:list[Member] = source.members
    
        for member in members:
            await member.move_to(channel=destination,
                                 reason=reason+f", by {ctx.author}")
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
@move.command()
async def users(ctx:commands.Context, members:commands.Greedy[Member],
                destination:VoiceChannel=None, *, reason:str=None):
    """Provides control to move named users into desired destination.

    Args:
        ctx (commands.Context): Context of command invoke
        users (commands.Greedy[Member]): List of mentioned members
        destination (VoiceChannel, optional): Where to move them. Defaults to None.
        reason (str, optional): Why to move them. Defaults to None.
    """
    for member in members:
        await member.move_to(channel=destination,
                                 reason=reason+f", by {ctx.author}")
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
@move.error
async def move_error(error:errors, ctx:commands.Context):
    if isinstance(error, commands.MissingPermissions):
        ctx.send(f"{ctx.author} missing permissions `move_members`",
                 delete_after=S.DELETE_COMMAND_ERROR)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    raise error
             
@move.command()
async def help(ctx:commands.Context):
    emb = Embed(title="Help: move",
                description="<prefix>move destination source reason\n" \
                    "<prefix>move @mention1 .. @mentionN destination reason",
                color=S.EMBED_HELP_COMMAND_COLOR)
    emb.set_footer(text="DISCLAIMER! Discord doesn't support tagging voice channels like text channels." \
        " To tag voice channel you have to visit Settings->Advanced->Developer Mode->On, and Right Click desired voice channel" \
        " Copy ID, then write <#> for each destination or source argument to the command." \
        " Paste what you've copied after # symbol.")
    await ctx.send(embed=emb, delete_after=S.DELETE_EMBED_HELP)
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
                
@commands.group(invoke_without_command=True, aliases=["dmall", "alldm"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def massdm(ctx:commands.Context, *, msg:str):
    """Allows owner of server to mass message privately all of its members.

    Args:
        ctx (commands.Context): Context of command invoke
        msg (str): Message to send everyone
    """
    if not ctx.invoked_subcommand:
        owner:Member = ctx.guild.owner
        
        await ctx.message.delete()
        if ctx.author == owner:
            if not msg:
                await owner.send(f"[DM-ALL] argument `message` was empty.")
                return
            server:Guild = ctx.guild

            if server.member_count <= S.MASSDM_EXPLOIT_LIMIT: 
                for mem in server.members:
                    if mem == owner:
                        await mem.send(f"[{ctx.guild.name}] what was sent to others:\n\n" +
                                    msg)
                        continue
                    if mem.bot == True:
                        continue
                    await mem.send(msg)
                return
            await owner.send("[{ctx.guild.name}] Cannot sent because server member count" +
                f" exceeded limit of {S.MASSDM_EXPLOIT_LIMIT}")

@massdm.error
async def massdm_error(error:errors, ctx:commands.Context):
    if isinstance(error, commands.MissingPermissions):
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    raise error

@massdm.command()
async def embed(ctx:commands.Context, msg:str=None, color:str="0x00fefe",
                footer:str=None):
    """Allows owner of server to send embed message to all server members in
    private chat.

    Args:
        ctx (commands.Context): Context of command invocation
        msg (str, optional): Message to be sent. Defaults to None.
        color (str, optional): Color of embed. Defaults to "0x00fefe".
        footer (str, optional): Bottom information of embed. Defaults to None.
    """
    emb = Embed(title=f"[{ctx.guild.name}] owner sends all this message:",
                description=msg, color=int(color, 0))
    if footer:
        emb.set_footer(text=footer)

    owner:Member = ctx.guild.owner
    await ctx.message.delete()
    if ctx.author == owner:
        if not msg:
            await owner.send(f"[DM-ALL] argument title+message was empty.")
            return
        server:Guild = ctx.guild

        if server.member_count <= S.MASSDM_EXPLOIT_LIMIT: 
            for mem in server.members:
                if mem == owner:
                    await mem.send(f"[DM-ALL] what was sent to others:",
                                embed=emb)
                    continue
                if mem.bot == True:
                    continue
                await mem.send(embed=emb)
            return
        await owner.send("[DM-ALL] Cannot sent because server member count" +
            f"exceeded limit of {S.MASSDM_EXPLOIT_LIMIT}")
    
@commands.command()
@commands.guild_only()
async def rules(ctx:commands.Context):
    """Responds with currently set rules on server.

    Args:
        ctx (commands.Context): Context of command invocation
    """
    guild_rules = await read_db(ctx.guild.id, "guild-rules")
    if guild_rules:
        await ctx.send(guild_rules, delete_after=S.DELETE_MINUTE)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send("No rules have been set yet.", delete_after=S.DELETE_COMMAND_ERROR)
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
@commands.command()
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def setrules(ctx:commands.Context, *, rules:str=None):
    """Allows to set rules for server which are sent to new joined members.

    Args:
        ctx (commands.Context): Context of command invoke
        rules (str, optional): Guild rules.. Defaults to None.
    """
    # No argument passed or disabling current guild rules.
    if not rules:
        rules_already_exist = await read_db(ctx.guild.id, "guild-rules")
        if rules_already_exist:
            successfull_remove = await delete_from_db(ctx.guild.id, "guild-rules")
            if successfull_remove:
                await ctx.send("Rules no longer apply.", delete_after=S.DELETE_COMMAND_INVOKE)
                await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
                return
            await database_fail(ctx)
            return
        await ctx.send("No guild rules were applied here before.", delete_after=S.DELETE_COMMAND_INVOKE)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
    rsp = await insert_db(ctx.guild.id, "guild-rules", rules)
    if not rsp:
        rsp = await update_db(ctx.guild.id, "guild-rules", rules)
        if not rsp:
            await database_fail(ctx)
            return
    await ctx.send("New guild rules have been applied.", delete_after=S.DELETE_COMMAND_INVOKE)
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

@setrules.error
async def setrules_error(error:errors, ctx:commands.Context):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"Only guild administrators can do that.",
                       delete_after=S.DELETE_COMMAND_ERROR)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    raise error

@commands.command(aliases=["invitebot", "botinvite", "boturl", "urlbot"])
async def invite(ctx:commands.Context):
    """Allows anyone to get bot invitation link to new server.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    INVITE_URL = "https://discord.com/api/oauth2/authorize?client_id=821538075078557707&permissions=8&scope=bot%20applications.commands"
    msg = Embed(title="Invitation link [Bot]", description=INVITE_URL)
    await ctx.send(embed=msg,
                   delete_after=S.DELETE_MINUTE)
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
@commands.guild_only()
@commands.group(invoke_without_command=True,
                aliases=["invitef", "invitefriend", "finv", "invf"])
async def finvite(ctx:commands.Context,
                  kick_after_dc:bool=False,
                  age:int=0,
                  use:int=0):
    """Generates new server invite for your friends.

    Args:
        ctx (commands.Context): Context of command invoke
        temp (bool, optional): True if new invited members should get kick after disconnect.
        Defaults to False.
        age (int, optional): Time before invitation expires. Defaults to 0.
        use (int, optional): Uses before invitation expires. Defaults to 0.
    """
    if not ctx.invoked_subcommand:
        ch:channel.TextChannel = ctx.channel
        invite:Invite = await ch.create_invite(temporary=kick_after_dc, max_uses=use,
                                    max_age=age)
        embd = Embed(title="Invitation link [Server]", description=invite.url)
        await ctx.send(embed=embd, delete_after=S.DELETE_MINUTE)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
@finvite.command()
async def help(ctx:commands.Context):
    """Provides help for command arguments.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    embd = Embed(title="Help: finvite", 
                 description="Args: kick_after_dc[True/False] max_age[seconds] max_uses[number]",
                 color=S.EMBED_HELP_COMMAND_COLOR)
    await ctx.send(embed=embd)

@commands.group(invoke_without_command=True, aliases=["asignrole","roleasign"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def autorole(ctx:commands.Context):
    """Provides auto role managing by bot for those who join server. Responds
    with set role

    Args:
        ctx (commands.Context): Context of command invoke
    """
    if not ctx.invoked_subcommand:
        response = await read_db(ctx.guild.id, "auto-role")
        if response:
            await ctx.send(f"Role to give when someone joins this server is: " \
                f"{ctx.guild.get_role(response).mention}",
                delete_after=S.DELETE_COMMAND_INVOKE)
            await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
            return
        await ctx.send(f"Looks like no roles are set.",
                       delete_after=S.DELETE_COMMAND_INVOKE)

@autorole.error
async def autorole_error(error:errors, ctx:commands.Context):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author} missing permission `administrator`",
                       delete_after=S.DELETE_COMMAND_ERROR)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    raise error
           
@autorole.command()
async def set(ctx:commands.Context, role:Role=None):
    """Sets mentioned role to auto-asignment for new joins on server.

    Args:
        ctx (commands.Context): Context of command invoke
        role (Role, optional): Role to give. Defaults to None.
    """
    if not role:
        await ctx.send("No role mentioned.", delete_after=S.DELETE_COMMAND_ERROR)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    
    guid = ctx.guild.id
    response = await insert_db(guid, "auto-role", role.id)
    if response:
        await ctx.send(f"New role set.", delete_after=S.DELETE_COMMAND_INVOKE)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    response = await update_db(guid, "auto-role", role.id)
    if response:
        await ctx.send(f"Auto-role was updated.", delete_after=S.DELETE_COMMAND_INVOKE)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    await database_fail(ctx)

@autorole.command() 
async def remove(ctx:commands.Context):
    """Removes role for auto-asign on server joins.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    guid = ctx.guild.id
    
    success = await delete_from_db(guid, "auto-role")
    if success:
        await ctx.send("Auto-role removed.", delete_after=S.DELETE_COMMAND_INVOKE)
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        return
    await database_fail(ctx)
    
@autorole.command()
async def help(ctx:commands.Context):
    """Provides help with command arguments.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    emb = Embed(title="Help: autorole",
                description="<prefix>autorole set @role_mention\n" \
                    "<prefix>autorole remove",
                    color=S.EMBED_HELP_COMMAND_COLOR)    
    await ctx.send(embed=emb, delete_after=S.DELETE_EMBED_HELP)
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
 
@commands.group(invoke_without_command=True)
@commands.guild_only()
@commands.has_permissions(manage_messages=True)
async def filter(ctx:commands.Context):
    
    if not ctx.invoked_subcommand:
        blacklist:list = await read_db(ctx.guild.id, "blacklist")
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

        if not blacklist:
            await ctx.send(f"None are set.", delete_after=S.DELETE_COMMAND_ERROR)
            return

        blacklist_str = "\n".join(blacklist)
        await ctx.send(f"Blacklisted words are:\n >>> {blacklist_str}", 
                        delete_after=S.DELETE_COMMAND_INVOKE)
  
@filter.command()
async def add(ctx:commands.Context, *, words:str):
    words_each:list = words.split()
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

    is_ok = await insert_db(ctx.guild.id, "blacklist", words_each)
    if not is_ok:
        is_updated = await update_db(ctx.guild.id, "blacklist", words_each)
        if not is_updated:
            await database_fail(ctx)
            return
    await ctx.send(f"New words have been added to the blacklist.",
                   delete_after=S.DELETE_COMMAND_INVOKE)

@filter.command()
async def remove(ctx:commands.Context, *, words_to_del:str):
    words:list = words_to_del.split()
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

    current_bl:list = await read_db(ctx.guild.id, "blacklist")
    if not current_bl:
        await ctx.send(f"Looks like none were ever set.", delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    for w in words:
        for _ in current_bl:
            if w == _:
                try:
                    current_bl.remove(w)
                except ValueError as e:
                    continue
                
    is_updated = await update_db(ctx.guild.id, "blacklist", current_bl)
    if not is_updated:
        await database_fail(ctx)
        return
    await ctx.send(f"`{words_to_del}` has been removed from blacklist.",
                   delete_after=S.DELETE_COMMAND_INVOKE)
     
@filter.command()
async def help(ctx:commands.Context):
    """Provides help with command arguments.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    emb = Embed(title="Help: filter",
                description="<prefix>filter add word1 word2 ... wordn\n" \
                    "<prefix>filter remove word1",
                    color=S.EMBED_HELP_COMMAND_COLOR)    
    await ctx.send(embed=emb, delete_after=S.DELETE_EMBED_HELP)
    await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
      
async def setup(target: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global CLIENT
    
    COMMANDS = [
                ping, clear, id,
                prefix, setprefix, ban,
                kick, echo, guid,
                invite, finvite, autorole, 
                massdm, rules, setrules,
                move, filter
    ]
    
    for c in COMMANDS:
        target.add_command(c)
    CLIENT = target

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass

"""
TO DO:
"""