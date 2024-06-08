import string
import discord
from typing import Optional
from discord import Embed, Member, channel, Invite, Role, Guild, VoiceChannel
from discord import Interaction, SelectOption, File, Button
from discord.ext import commands
from discord.ext.commands import errors

import data_service.config_service as S
from data_service.config_service import RECORDS_DB
from data_service.config_service import delete_command_user_invoke, database_fail
from data_service.database_service import delete_from_db, id_lookup, insert_db, read_db 
from data_service.database_service import update_db, add_id, read_id
from log_service.setup import setup_logging

from barmaid import CLIENT, DATABASE
log = setup_logging()

@commands.hybrid_group(with_app_command=True, name="h")
@commands.guild_only()      
async def helpme(ctx:commands.Context):
    """Gets help for a specified command.

    Args:
        ctx (commands.Context): Context of invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.invoked_subcommand:
        if not ctx.interaction:
            await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        await ctx.send("Please specify command you want help for.", 
                       delete_after=S.DELETE_COMMAND_INVOKE)

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
@commands.has_guild_permissions(manage_messages=True)
async def clear(ctx:commands.Context, amount:int=1):
    """Removes any number of messages in chat history.

    Args:
        ctx: Current context of the message that invoked the command.
        amount (optional): Number of messages to delete.
    """
    # If invoked via slash commands, no need to purge invoke itself.
    await ctx.defer(ephemeral=True)    
    if not ctx.interaction:
        amount += 1
    
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
    # Bot missing permissions
    await ctx.defer(ephemeral=True)
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
    """Sends you your user discord identificator number.
    
    Args:
    ctx: Current context of the message that invoked the command.
    """
    await ctx.defer(ephemeral=True)
    id = ctx.message.author.id
    
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
async def echo(ctx:commands.Context, *, message:str):
    """Echoes the message.

    Args:
        ctx: Context of the invoked command.
        message: Message to be repeated.
    """
    
    await ctx.defer(ephemeral=True)
    if not message:
        raise commands.CommandError(f"Argument `message` cannot be empty.")
    
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
@commands.has_guild_permissions(administrator=True)
async def guid(ctx:commands.Context):
    """Sends you your discord server identification number.

    Args:
        ctx: Context deducted from invocation.
    """
    await ctx.defer(ephemeral=True)
    guild_id = ctx.guild.id
    if not ctx.interaction:
        await ctx.message.author.send(f"{guild_id = }")
        await ctx.message.delete()
        return
    await ctx.send(f"{guild_id = }")
    
@guid.error
async def guid_error(ctx:commands.Context, error:errors): 
    await ctx.defer(ephemeral=True)   
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(error,
                       delete_after=S.DELETE_COMMAND_ERROR)
  
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

def _check_valid_prefix(prefix:str):
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
    """Shows prefix used on a server.

    Args:
        ctx (commands.Context): Context of command invocation
    """
    await ctx.defer(ephemeral=True)
    
    prefix = await read_db(DATABASE, ctx.guild.id, "prefix")
    if not prefix:
        await database_fail(ctx)
        return
    
    await ctx.send(f"Current bot prefix is set to `{prefix}` symbol.", 
                   delete_after=S.DELETE_COMMAND_INVOKE)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

@prefix.error
async def prefix_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    await ctx.send(error,
                   delete_after=S.DELETE_COMMAND_ERROR)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)

@commands.hybrid_command(name="set-prefix", with_app_command=True)
@commands.guild_only()
async def prefixset(ctx:commands.Context, new_prefix:str):
    """Sets a new prefix on a server.

    Args:
        ctx (commands.Context): Context of command invocation
        new_prefix (str, optional): Symbol to be the new prefix.
    """
    await ctx.defer(ephemeral=True)
    
    if not new_prefix:
        await ctx.send(f"Argument `new_prefix` cannot be empty.", delete_after=S.DELETE_COMMAND_ERROR)
        return
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
        
    SYMBOLS = string.punctuation
    
    if not _check_valid_prefix(new_prefix):
        await ctx.send("Prefix cannot have more than one special symbol. " \
            f"Allowed symbols are:\n > {SYMBOLS}", delete_after=S.DELETE_COMMAND_ERROR)
        return

    changed = await update_db(DATABASE, ctx.guild.id, 'prefix', new_prefix)
    # changed = await read_db(DATABASE, ctx.guild.id, 'prefix')
    if not changed:
        await database_fail(ctx)
    else:
        await ctx.send(f"Prefix was set to `{new_prefix}` successfully.", 
                    delete_after=S.DELETE_COMMAND_INVOKE)
        
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

# @prefixset.error
# async def prefixset_error(ctx:commands.Context, error:errors):
#     await ctx.defer(ephemeral=True)
    
#     if not ctx.interaction:
#         await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR) 
        
#     if isinstance(error, commands.CommandError):
#         await ctx.send(error,
#                        delete_after=S.DELETE_COMMAND_ERROR)
#         return
        
        
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
@commands.bot_has_guild_permissions(administrator=True)
@commands.has_guild_permissions(kick_members=True)
async def kick(ctx:commands.Context,
                   members:commands.Greedy[Member], *,
                   reason:str="No reason provided"):
    """Kicks multiple user(s) from server.

    Args:
        ctx (commands.Context): Context of command invocation
        members (commands.Greedy[Member], optional): Multiple mentioned members.
        reason (str, optional): Anything they did wrong.
    """
    await ctx.defer(ephemeral=True)
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
    await ctx.defer(ephemeral=True)
    if isinstance(error, commands.MissingPermissions):
        owner = ctx.guild.owner
        direct_message = await owner.create_dm()
        await direct_message.send(f"{ctx.message.author} performed " \
            "kick operation, but misses permission Kick Members.")
        await ctx.send(error)
        if not ctx.interaction:
            await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
        return

    await ctx.send(error,
                delete_after=S.DELETE_COMMAND_ERROR)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
    return

async def add_to_naughty_list(member:int, guild:Guild, reason:str):
    """Adds banned member to global bot naughty list, anyone can see on
    different servers how naughty the member is.

    Args:
        member (int): Naughty members
        guild (Guild): Guild banned from
        reason (str): Guild reason banned for
    """    
    exists = await id_lookup(RECORDS_DB, member)
    if not exists:
        await add_id(RECORDS_DB, member)
        
    info_about_ban = {
        "guild_name": guild.name,
        "reason": reason
    }
    if not await insert_db(RECORDS_DB, member, guild.id, info_about_ban):
        await update_db(RECORDS_DB, member, guild.id, info_about_ban)
      
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
@commands.bot_has_guild_permissions(administrator = True)
@commands.has_guild_permissions(ban_members=True)
async def ban(ctx:commands.Context, members:commands.Greedy[Member], *,
              reason:str ="No reason provided", del_msg_in_days:int = 1):
    """Bans the user(s) from the server.

    Args:
        ctx (discord.Context): Context of the invoked command.
        members (discord.Member): Mentioned discord members.
        reason (str, optional): Reason why user(s) were banned from server.
        del_msg_in_days (int): Deletes messages banned user(s) wrote in past days.
        Defaults to "No reason provided".
    """
    await ctx.defer(ephemeral=True)
    
    if not members:
        raise commands.CommandError("No people to perform kick operation.")
    
    names = [mem.name for mem in members]
    names_str = ", ".join(names) if len(names) > 1 else names[0]
    
    # Server-side      
    ban = Embed(title=f"Banned {names_str}!", description=f"Reason: {reason}")
    ban.set_footer(text=f"By: {ctx.author}")
    await ctx.channel.send(embed=ban,
                   delete_after=S.DELETE_DAY)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    # Member-side
    for member in members:
        ban = Embed(title=f"You were banned from {ctx.guild.name}",
                     description=f"Reason: {reason}")
        ban.set_footer(text=f"By: {ctx.author}")
        # Send can fail, because member can block DM's from server members.
        try:
            await member.send(embed=ban)
        except discord.Forbidden:
            # We still want to kick that member
            await member.ban(reason=reason, delete_message_days=del_msg_in_days)
            continue
        await member.ban(reason=reason, delete_message_days=del_msg_in_days)
        await add_to_naughty_list(member.id, ctx.guild, reason)
    # App response

    await ctx.send("Success!", 
                   delete_after=S.DELETE_COMMAND_INVOKE)

@ban.error
async def ban_error(ctx:commands.Context, error:errors):
    """Informs server owner deducted from context about who tried
    to perform an ban operation without permissions.

    Args:
        error (discord.errors): Error raised.
        ctx (commands.Context): Context of the invoked command.
    """
    await ctx.defer(ephemeral=True)
    if isinstance(error, commands.MissingPermissions):
        owner = ctx.guild.owner
        direct_message = await owner.create_dm()
        await direct_message.send(f"{ctx.message.author} performed " \
            "ban operation, but misses permission Ban Members.")
        await ctx.send(error)
        if not ctx.interaction:
            await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
        return

    await ctx.send(error,
                delete_after=S.DELETE_COMMAND_ERROR)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
    return

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def records(ctx:commands.Context, member:Member):
    """Retrives naughty records for specified member.

    Args:
        ctx (commands.Context): Context of invoke
        member (Member): Member to determine if its naughty.
    """
    await ctx.defer(ephemeral=True)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
        
    exists = await id_lookup(RECORDS_DB, member.id)
    if not exists:
        await ctx.send(f"Discord User: {member} has no records.",
                 delete_after=S.DELETE_COMMAND_INVOKE)
        return
    
    data = await read_id(RECORDS_DB, member.id)
    data_items = data.items()
    message = f"User {member} has  `{len(data_items)}` records:\n>>> "
    for _, server_info in data_items:
        gn = server_info["guild_name"]
        r = server_info["reason"]
        message += f"{gn} — {r}"
        
    await ctx.send(message, delete_after=S.DELETE_COMMAND_INVOKE)
    
@records.error
async def records_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR) 
        
    if isinstance(error, commands.CommandError):
        await ctx.send(error,
                       delete_after=S.DELETE_COMMAND_ERROR)
        
        
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
@commands.has_guild_permissions(move_members=True)
async def move(ctx:commands.Context, destination:VoiceChannel,
               members:commands.Greedy[Member], *, reason:str=None):
    """Moves user(s) into targeted voice channel.

    Args:
        ctx (commands.Context): Context of command invoke
        destination (VoiceChannel, optional): Where to move them.
        members (Member, optional): Members to move.
        reason (str, optional): Why move was performed. Defaults to None.
    """
    await ctx.defer(ephemeral=True)
    if not members:
        raise commands.CommandError("No people to perform move operation on.")
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

    reason = "" if reason is None else reason
    for member in members:
        await member.move_to(channel=destination,
                                reason=reason+f", by {ctx.author}")
        
    await ctx.send("Success!", delete_after=S.DELETE_COMMAND_INVOKE)
        
@move.error
async def move_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
        
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author.mention} missing permissions Move Members",
                 delete_after=S.DELETE_COMMAND_ERROR)
        return
    elif isinstance(error, commands.CommandError):
        await ctx.send(error, delete_after=S.DELETE_COMMAND_ERROR)
        return
    raise error

@helpme.command(name="move")
async def move_help(ctx:commands.Context):
    """Shows help with move command.

    Args:
        ctx (commands.Context): Context of invoke
    """
    await ctx.defer(ephemeral=True)
    emb = Embed(title="Help: move",
                description="<prefix>move @mention1 .. @mentionN destination reason",
                color=S.EMBED_HELP_COMMAND_COLOR)
    
    emb.set_footer(text="DISCLAIMER! If you are not using slash command: " \
        "Discord doesn't support tagging voice channels like text channels." \
        " To tag voice channel you have to visit Settings->Advanced->Developer Mode->On, and Right Click desired voice channel" \
        " Copy ID, then write <#> for each destination or source argument to the command." \
        " Paste what you've copied after # symbol.")
    
    await ctx.send(embed=emb, delete_after=S.DELETE_EMBED_HELP)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
                
@commands.hybrid_group(with_app_command=True, name="admin")
@commands.guild_only()
async def massdm(ctx:commands.Context):
    """Server owner can message all of it's members into DM.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    pass

@massdm.command()
async def message(ctx:commands.Context, *, message:str):
    """Sends message to all server members. *SERVER-OWNER ONLY*

    Args:
        ctx (commands.Context): Context of command invoke
        message (str, optional): Message to send.
    """
    await ctx.defer(ephemeral=True)
    if not message:
        raise commands.CommandError("Argument message cannot be empty")
    owner:Member = ctx.guild.owner
    if not ctx.interaction:
        await ctx.message.delete()
        
    if ctx.author == owner:
        server:Guild = ctx.guild

        if server.member_count <= S.MASSDM_EXPLOIT_LIMIT: 
            for mem in server.members:
                if mem == owner:
                    await mem.send(f"**{ctx.guild.name}** what was sent to others:\n>>> " +
                                message)
                    continue
                if mem.bot == True:
                    continue
                await mem.send(f"**{ctx.guild.name}** server sents a message:\n" + message)
            await ctx.send("Success!", delete_after=S.DELETE_COMMAND_INVOKE)
            return
        
        await ctx.send(f"**{ctx.guild.name}** Cannot sent because server member count" +
            f" exceeded limit of {S.MASSDM_EXPLOIT_LIMIT}",
            delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"You're not the owner of this server, sorry.", 
                   delete_after=S.DELETE_COMMAND_ERROR)

@massdm.error
async def massdm_error(error:errors, ctx:commands.Context):
    await ctx.defer(ephemeral=True)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_ERROR)
    
    elif isinstance(error, commands.CommandError):
        await ctx.send(error, delete_after=S.DELETE_COMMAND_ERROR)
        return
    raise error

@massdm.command()
async def embedded(ctx:commands.Context, message:str, footer:str, 
                  color:str="0x00fefe"):
    """Sends embedded message to all server members. *SERVER-OWNER ONLY*

    Args:
        ctx (commands.Context): Context of command invocation
        message (str, optional): Message to be sent.
        color (str, optional): Color in hex value for embed. Defaults to "0x00fefe". *ADVANCED*
        footer (str, optional): Bottom information of embed.
    """
    await ctx.defer(ephemeral=True)
    if not message:
        raise commands.CommandError("Argument message cannot be empty")

    if not ctx.interaction:
        await ctx.message.delete()
        
    emb = Embed(title=f"{ctx.guild.name} server sents a message:",
                description=message, color=int(color, 0))
    emb.set_footer(text=footer)

    owner:Member = ctx.guild.owner
    if ctx.author == owner:
        server:Guild = ctx.guild

        if server.member_count <= S.MASSDM_EXPLOIT_LIMIT: 
            for mem in server.members:
                if mem == owner:
                    await mem.send(f"**{ctx.guild.name}** what was sent to others:",
                                embed=emb)
                    continue
                if mem.bot == True:
                    continue
                await mem.send(embed=emb)

            await ctx.send("Success!", delete_after=S.DELETE_COMMAND_INVOKE)
            return

        await ctx.send(f"**{ctx.guild.name}** Cannot sent because server member count" +
            f" exceeded limit of {S.MASSDM_EXPLOIT_LIMIT}",
            delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"You're not the owner of this server, sorry.", 
                   delete_after=S.DELETE_COMMAND_ERROR)

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def rules(ctx:commands.Context):
    """Shows rules on a server.

    Args:
        ctx (commands.Context): Context of command invocation
    """
    await ctx.defer(ephemeral=True)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    guild_rules:dict = await read_db(DATABASE, ctx.guild.id,
                                     "guild-rules")
    if guild_rules:
        result:list = []      
        for idx, rule in guild_rules.items():
            result.append(f"{int(idx)+1}. " + rule)
        formated_output = "\n".join(result)
        await ctx.send(formated_output, delete_after=S.DELETE_MINUTE)
        return
    await ctx.send("No rules have been set yet.",
                   delete_after=S.DELETE_COMMAND_INVOKE)
        
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def addrule(ctx:commands.Context, *, new_rule:str):
    """Allows to append new rules. They're sent to new users on server.

    Args:
        ctx (commands.Context): Context of command invoke
        rules (str, optional): New rule to apply.
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Missing `administrator` permission",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
    exists = await read_db(DATABASE, ctx.guild.id, "guild-rules")
    if not exists:
        rules:dict = {}
    else:
        rules = exists
    rules[f"{len(rules)}"] = new_rule
    
    ok_update = await update_db(DATABASE, ctx.guild.id, "guild-rules", rules)
    if ok_update:
        await ctx.send("New rule applied.")
        return
    await database_fail(ctx)

@commands.hybrid_command(with_app_command=True, name="reset-rules", 
                         aliases=["rules_reset", "reset_rules"])
@commands.guild_only()
async def rules_reset(ctx:commands.Context):
    """Resets all rules on server back to zero.

    Args:
        ctx (commands.Context): Context of invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Missing `administrator` permission",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
    successful_remove = await delete_from_db(DATABASE, ctx.guild.id, "guild-rules")
    if successful_remove:
        await ctx.send("Rules no longer apply.", 
                        delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await database_fail(ctx)

@addrule.error
async def setrules_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    raise error

@rules_reset.error
async def rules_reset_error(ctx:commands.Context, error:errors):    
    await ctx.defer(ephemeral=True)

    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

    raise error

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def delrule(ctx:commands.Context, index:int):
    """Removes rule at index position.

    Args:
        ctx (commands.Context): Context of invoke
        index (int): Index number of rule to delete.
    """ 
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Missing `administrator` permission",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
       
    guild_rules:dict = await read_db(DATABASE, ctx.guild.id, "guild-rules")
    if not guild_rules:
        await ctx.send("There are no rules therefore nothing to delete.")
        return
    del guild_rules[str(index-1)]
    idx = 0
    new_dict = {}
    for _, value in guild_rules.items():
        new_dict[str(idx)] = value
        idx += 1

    ok_update = await update_db(DATABASE, ctx.guild.id, "guild-rules", new_dict)
    if ok_update:
        await ctx.send(f"Rule {index} deleted.")
        return
    await database_fail(ctx)

@delrule.error
async def delrule_error(ctx:commands.Context, error:errors):
    await ctx.defer(ephemeral=True)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    raise error
    
@commands.hybrid_command(with_app_command=True, name="bot",
                         aliases=["invitebot", "botinvite", "boturl", "urlbot"])
async def binvite(ctx:commands.Context):
    """Invitation link to add bot somewhere else.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    await ctx.defer(ephemeral=True)
    msg = Embed(title="Invitation link [Bot]", description=S.BOT_INVITE_URL)
    await ctx.send(embed=msg,
                   delete_after=S.DELETE_MINUTE)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
@commands.guild_only()
@commands.hybrid_command(with_app_command=True, name="invite",
                aliases=["invitef", "invitefriend", "finv", "invf"])
async def finvite(ctx:commands.Context, kick_after_dc:bool=False,
                  age:int=0, use:int=0):
    """Generates server invite for your friends.

    Args:
        ctx (commands.Context): Context of command invoke
        temp (bool, optional): True if new invited members should get kick after disconnect.
        Defaults to False.
        age (int, optional): Time before invitation expires. Default infinite.
        use (int, optional): Uses before invitation expires. Default infinite.
    """
    await ctx.defer(ephemeral=True)
    ch:channel.TextChannel = ctx.channel
    invite:Invite = await ch.create_invite(temporary=kick_after_dc, max_uses=use,
                                max_age=age)
    embd = Embed(title="Invitation link [Server]", description=invite.url)
    await ctx.send(embed=embd, delete_after=S.DELETE_MINUTE)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

@helpme.command(name="finvite")
async def finvite_help(ctx:commands.Context):
    """Show help with finvite command.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    await ctx.defer(ephemeral=True)
    embd = Embed(title="Help: finvite", 
                 description="Args: kick_after_dc[True/False] max_age[seconds]"\
                     " max_uses[number]",
                 color=S.EMBED_HELP_COMMAND_COLOR)
    await ctx.send(embed=embd,
                   delete_after=S.DELETE_HOUR)

@commands.hybrid_group(with_app_command=True,
                         aliases=["asignrole","roleasign"])
@commands.guild_only()
async def autorole(ctx:commands.Context):
    """Shows current role set for auto-giving for newly server joins.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    pass

@autorole.command()
async def show(ctx:commands.Context):
    """Shows current role set for auto-giving for newly server joins.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE) 
    response = await read_db(DATABASE,ctx.guild.id, "auto-role")
    if response:
        await ctx.send(f"Role to give when someone joins this server is: " \
            f"{ctx.guild.get_role(response).mention}",
            delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Looks like no roles are set.",
                    delete_after=S.DELETE_COMMAND_INVOKE)

@autorole.error
async def autorole_error(error:errors, ctx:commands.Context):
    await ctx.defer(ephemeral=True)

    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if isinstance(error, commands.CommandError):
        await ctx.send(error, delete_after=S.DELETE_COMMAND_ERROR)
        return
    elif isinstance(error, commands.BadArgument):
        await ctx.send(error, 
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    raise error
           
@autorole.command()
async def set(ctx:commands.Context, role:Role):
    """Sets role to auto-asign for those who join server.

    Args:
        ctx (commands.Context): Context of command invoke
        role (Role, optional): Role to give. MAKE SURE THE ROLE IS BELOW BOTS ROLE IN HIERARCHY!
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not role:
        await ctx.send("No role has been specified.", 
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    guid = ctx.guild.id
    valid_role = ctx.guild.get_role(role.id)
    
    if not valid_role:
        await ctx.send("Role does not exist.", delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
     
    response = await insert_db(DATABASE, guid, "auto-role", role.id)
    if response:
        await ctx.send(f"New role set.", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    response = await update_db(DATABASE, guid, "auto-role", role.id)
    if response:
        await ctx.send(f"Auto-role was updated.", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await database_fail(ctx)

@autorole.command()
async def remove(ctx:commands.Context):
    """Removes role for auto-asign on server joins.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                        delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    guid = ctx.guild.id
    
    success = await delete_from_db(DATABASE, guid, "auto-role")
    if success:
        await ctx.send("Auto-role removed.", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await database_fail(ctx)
    
@helpme.command(name="autorole")
async def autorole_help(ctx:commands.Context):
    """Show help with autorole command.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    emb = Embed(title="Help: autorole",
                description="<prefix>autorole set @role_mention\n" \
                    "<prefix>autorole show\n" \
                    "<prefix>autorole remove\n" \
                    "MAKE SURE THE ROLE BOT WILL GIVE IS UNDER BOTS ROLE IN HIERARCHY!",
                    color=S.EMBED_HELP_COMMAND_COLOR)    
    await ctx.send(embed=emb, delete_after=S.DELETE_EMBED_HELP)
 
@commands.hybrid_group(with_app_command=True)
@commands.guild_only()
async def filter(ctx:commands.Context):
    """Filter group command.

    Args:
        ctx (commands.Context): Context of invoke
    """
    pass

@filter.command()
async def show(ctx:commands.Context):
    """Shows all blacklisted words.

    Args:
        ctx (commands.Context): Context of invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("You are missing Manage Messages permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    blacklist:list = await read_db(DATABASE, ctx.guild.id, "blacklist")

    if not blacklist:
        await ctx.send(f"None are set.", delete_after=S.DELETE_COMMAND_ERROR)
        return

    blacklist_str = "\n".join(blacklist)
    await ctx.send(f"Blacklisted entries are:\n >>> {blacklist_str}", 
                    delete_after=S.DELETE_COMMAND_INVOKE)
  
@filter.command()
async def add(ctx:commands.Context, entry:str):
    """Adds new word to blacklist. Or whole phrase if inside double quotes.

    Args:
        ctx (commands.Context): Context of invoke
        entry (str): Banned word or phrase (must be in quotes).
    """
    await ctx.defer(ephemeral=True)
    
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("You are missing Manage Messages permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    exists = await read_db(DATABASE, ctx.guild.id, "guild-rules")
    if not exists:
        blacklist:list = []
    else:
        blacklist = [exists]

    is_ok = await insert_db(DATABASE, ctx.guild.id, "blacklist", blacklist)
    if not is_ok:
        is_updated = await update_db(DATABASE, ctx.guild.id, "blacklist", blacklist)
        if not is_updated:
            await database_fail(ctx)
            return
    await ctx.send(f"New words have been added to the blacklist.",
                   delete_after=S.DELETE_COMMAND_INVOKE)

@filter.command()
async def remove(ctx:commands.Context, entry:str):
    """Removes specified word (phrase) from blacklist.

    Args:
        ctx (commands.Context): Context of invoke
        entry (str): Word to be revoked from blacklist. Phrase
        must be in quotes.
    """ 
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("You are missing Manage Messages permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)

    current_bl:list = await read_db(DATABASE,ctx.guild.id, "blacklist")
    if not current_bl:
        await ctx.send(f"Looks like none were ever set.", 
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    for _ in current_bl:
        if entry == _:
            try:
                current_bl.remove(entry)
            except ValueError as e:
                continue
                
    is_updated = await update_db(DATABASE, ctx.guild.id, "blacklist", current_bl)
    if not is_updated:
        await database_fail(ctx)
        return
    await ctx.send(f"`{entry}` has been removed from blacklist.",
                   delete_after=S.DELETE_COMMAND_INVOKE)
     
@helpme.command(name="filter")
async def filter_help(ctx:commands.Context):
    """Shows help for filter command.

    Args:
        ctx (commands.Context): Context of command invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    emb = Embed(title="Help: filter",
                description="<prefix>filter add entry\n" \
                    "<prefix>filter remove entry",
                    color=S.EMBED_HELP_COMMAND_COLOR)    
    await ctx.send(embed=emb, delete_after=S.DELETE_EMBED_HELP)

@commands.hybrid_group(with_app_command=True, name="moderation")
@commands.guild_only()
async def mods_to_notify(ctx:commands.Context):
    pass

@mods_to_notify.command()
async def show(ctx:commands.Context):
    """Shows which members bot treats as guild moderators.

    Args:
        ctx (commands.Context): Context of invoke
    """ 
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    mods_id:list = await read_db(DATABASE, ctx.guild.id, "mods_to_notify")
    if not mods_id:
        await ctx.send("None set yet!")
        return
    mods:Member = [ctx.guild.get_member(int(m)) for m in mods_id]
    msg = "Guild mods:\n>>> "
    for m in mods:
        msg+= f"{m.mention}\n"
    await ctx.send(msg)
    
@mods_to_notify.command()
async def add(ctx:commands.Context, member:Member):
    """Adds member to be treated as guild moderator.

    Args:
        ctx (commands.Context): Context of invoke
        member (Member): User to treat as guild mod
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    
    mods_now:list = await read_db(DATABASE, ctx.guild.id, "mods_to_notify")   
    ok = await insert_db(DATABASE, ctx.guild.id, "mods_to_notify", [member.id])
    if not ok:
        mods_now.append(member.id)
        # remove dups
        mods_now = _remove_list_duplicates(mods_now)
        await update_db(DATABASE, ctx.guild.id, "mods_to_notify", mods_now)
    await ctx.send(f"{member} added!", delete_after=S.DELETE_COMMAND_INVOKE)

@mods_to_notify.command()
async def reset(ctx:commands.Context):
    """Resets moderators back to zero.

    Args:
        ctx (commands.Context): Context of invoke
    """
    await ctx.defer(ephemeral=True)
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You are missing Administrator permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    await delete_from_db(DATABASE, ctx.guild.id, "mods_to_notify")
    
    await ctx.send("Reset successful.", delete_after=S.DELETE_COMMAND_INVOKE)

def _remove_list_duplicates(l:list):
    """Removes any dups in a list.

    Args:
        l (list): List to iterate

    Returns:
        list: New list without dup values
    """
    return list(dict.fromkeys(l))   
 
async def setup(target: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global CLIENT
        
    COMMANDS_TO_ADD = [
                ping, clear, id,
                prefix, prefixset, ban,
                kick, echo, guid,
                binvite, finvite, autorole, 
                massdm, rules, addrule, 
                filter, helpme, move, 
                rules_reset, delrule, records,
                mods_to_notify
    ]
    
    for c in COMMANDS_TO_ADD:
        target.add_command(c)
    CLIENT = target

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass
