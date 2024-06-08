import asyncio
from datetime import datetime, timedelta
import uuid

from data_service.database_service import insert_db, read_db, update_db
import data_service.config_service as S
from data_service.config_service import DATABASE, delete_command_user_invoke
from event_service.EventView import EventView
from event_service.scheduled_events import ScheduledEvents

from discord import Embed, Member, channel, Invite
from discord import Role, Guild, VoiceChannel, Reaction, User, Object

from discord.message import Message

from discord.ext import commands
from discord.ext.commands import Context
from log_service.setup import setup_logging
from event_service.EventView import embed_hash

"""
Client instance loaded after barmaid.load_extensions() passes its instance into
events.setup().

Disclaimer: from barmaid import client, as it is module global variable doesn't
work for example at events.usr_input(ctx, client).
"""
CLIENT:commands.Bot = None
log = setup_logging()

async def format_time(in_str:str) -> str:
    """Formats string from %Y-%m-%d %H:%M:%S into ISO8601 format.

    Args:
        in_str (str): String to format

    Returns:
        str: %Y-%m-%dT%H:%M:%S string format
    """
    FORMAT_FROM = "%Y-%m-%d %H:%M:%S"
    FORMAT_TO = "%Y-%m-%dT%H:%M:%S"
    try:
        return datetime.strptime(in_str, FORMAT_FROM).strftime(FORMAT_TO)
    except Exception as e:
        raise ValueError(f"Invalid string input: {in_str}")

@commands.hybrid_group(with_app_command=True)
@commands.guild_only()
async def events(ctx:commands.Context):
    pass

@events.command()
async def idelete(ctx:commands.Context, search_by_name:str):
    """Deletes internal discord event by it's name.

    Args:
        ctx (commands.Context): Invoke context
        search_by_name (str): Title of the event to search for.
    """
    await ctx.defer(ephemeral=True)
    
    try:
        event_id = await ScheduledEvents.find_guild_event(search_by_name, ctx.guild.id)
    except:
        await ctx.send(f"Existing event with name `{search_by_name}` not found.",
                        delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    resp = await ScheduledEvents.delete_guild_event(ctx.guild.id, event_id)
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if resp.status == 204:
        await ctx.send(f"Deleted event `{search_by_name}`", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Event delete has failed. Try again later.", 
                   delete_after=S.DELETE_COMMAND_ERROR)

@events.command()
async def edit_voice(ctx:commands.Context, search_by_name:str, new_title:str, new_description:str, new_start_time:str, new_voice:VoiceChannel, new_end_time:str=None):
    """Edits internal discord event.

    Args:
        ctx (commands.Context): Context of invoke
        search_by_name (str): Title of the event to search for.
        new_title (str): Title of event
        new_description (str): Description of event
        new_start_time (str): Use "yy-mm-dd hh:mm" format
        new_voice (VoiceChannel): Voice channel id
        new_end_time (str, optional): Use "yy-mm-dd hh:mm" format. Optional.
    """
    await ctx.defer(ephemeral=True)
    
    MILENIUM = "20"
    new_start_time += ":00"
    if new_end_time:
        new_end_time = new_end_time + ":00"
    try:
        start = await format_time(MILENIUM+new_start_time)
        end = await format_time(MILENIUM+new_end_time) if new_end_time is not None else None
    except:
        if not new_end_time:
            await ctx.send(f"Invalid time format. start:`{new_start_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        else:
            await ctx.send(f"Invalid time format. start:`{new_start_time[:-3]}` \t end:`{new_end_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        return

    try:
        event_id = await ScheduledEvents.find_guild_event(search_by_name, ctx.guild.id)
    except:
        await ctx.send(f"Existing event with name `{search_by_name}` not found.",
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    
    resp = await ScheduledEvents.modify_guild_event(
        event_id,
        ctx.guild.id,
        new_title,
        new_description,
        start,
        end,
        None,
        new_voice.id
    )
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if resp.status == 200:
        await ctx.send(f"Old event `{search_by_name}` has new title `{new_title}` with date `{new_start_time}`", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Event edit has failed. Try again later.", 
                   delete_after=S.DELETE_COMMAND_ERROR)
    
@events.command()
async def edit_location(ctx:commands.Context, search_by_name:str, new_title:str, new_description:str, new_start_time:str, new_end_time:str, new_location:str):
    """Edits internal discord event.

    Args:
        ctx (commands.Context): Context of invoke
        search_by_name (str): Title of the event to search for.
        new_title (str): Title of event
        new_description (str): Description of event
        new_start_time (str): Use "yy-mm-dd hh:mm" format. REQUIRED.
        new_end_time (str): Use "yy-mm-dd hh:mm" format. REQUIRED.
        new_location (str): Your location name
    """
    await ctx.defer(ephemeral=True)
    
    MILENIUM = "20"
    new_start_time += ":00"
    metadata = {"location": new_location}
    if new_end_time:
        new_end_time = new_end_time + ":00"
    try:
        start = await format_time(MILENIUM+new_start_time)
        end = await format_time(MILENIUM+new_end_time) if new_end_time is not None else None
    except:
        if not new_end_time:
            await ctx.send(f"Invalid time format. start:`{new_start_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        else:
            await ctx.send(f"Invalid time format. start:`{new_start_time[:-3]}` \t end:`{new_end_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        return

    try:
        event_id = await ScheduledEvents.find_guild_event(search_by_name, ctx.guild.id)
    except:
        await ctx.send(f"Existing event with name `{search_by_name}` not found.",
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    
    resp = await ScheduledEvents.modify_guild_event(
        event_id,
        ctx.guild.id,
        new_title,
        new_description,
        start,
        end,
        metadata,
    )
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if resp.status == 200:
        await ctx.send(f"Old event `{search_by_name}` has new title `{new_title}` with date `{new_start_time}`", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Event edit has failed. Try again later.", 
                   delete_after=S.DELETE_COMMAND_ERROR)
  
@events.command()
async def ivoice(ctx:commands.Context, title:str, description:str, start_time:str, voice_ch:VoiceChannel, end_time:str=None):
    """Creates event as internal discord feature, with voice channel.

    Args:
        ctx (commands.Context): Context of invoke
        title (str): Title of event
        description (str): Description of event
        start_time (str): Use "yy-mm-dd hh:mm" format
        voice_ch (VoiceChannel): Voice channel id
        end_time (str, optional): Use "yy-mm-dd hh:mm" format. Optional.
    """    
    await ctx.defer(ephemeral=True)
    
    MILENIUM = "20"
    start_time += ":00"
    if end_time:
        end_time = end_time + ":00"
    try:
        start = await format_time(MILENIUM+start_time)
        end = await format_time(MILENIUM+end_time) if end_time is not None else None
    except:
        if not end_time:
            await ctx.send(f"Invalid time format. start:`{start_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        else:
            await ctx.send(f"Invalid time format. start:`{start_time[:-3]}` \t end:`{end_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        return

    resp = await ScheduledEvents.create_guild_event(
        ctx.guild.id,
        title,
        description,
        start,
        end,
        None,
        voice_ch.id
    )
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if resp.status == 200:
        await ctx.send(f"Created event `{title}` on `{start_time}`", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Event creation has failed. Try again later.", 
                   delete_after=S.DELETE_COMMAND_ERROR)

@events.command()
async def ilocation(ctx:commands.Context, title:str, description:str, start_time:str, end_time:str, location:str):
    """Creates event as internal discord feature, with custom location.

    Args:
        ctx (commands.Context): Context of invoke
        title (str): Title of event
        description (str): Description of event
        start_time (str): Use "yy-mm-dd hh:mm" format. REQUIRED.
        end_time (str): Use "yy-mm-dd hh:mm" format. REQUIRED.
        location (str): Your location name
    """
    await ctx.defer(ephemeral=True)
    start_time += ":00"
    end_time += ":00"
    metadata = {"location": location}
    
    MILENIUM = "20"
    try:
        start = await format_time(MILENIUM+start_time)
        end = await format_time(MILENIUM+end_time) if end_time is not None else None
    except:
        if not end_time:
            await ctx.send(f"Invalid time format. start:`{start_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        else:
            await ctx.send(f"Invalid time format. start:`{start_time[:-3]}` \t end:`{end_time[:-3]}`", 
                        delete_after=S.DELETE_COMMAND_ERROR)
        return

    
    resp = await ScheduledEvents.create_guild_event(
        ctx.guild.id,
        title,
        description,
        start,
        end,
        metadata,
    )
    
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
    if resp.status == 200:
        await ctx.send(f"Created event `{title}`  on `{start_time}`", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Event creation has failed. Try again later.", 
                   delete_after=S.DELETE_COMMAND_ERROR)

@events.command()
async def echat(ctx:commands.Context, include_names:bool, title:str,
                description:str, start_time:str, voice:VoiceChannel,
                limit:int=0):
    """External chat-based interactive event via buttons.

    Args:
        ctx (commands.Context): Context of invoke
        include_names (bool): Include names in event category lists.
        title (str): Title of event
        description (str): Description of event
        start_time (str): Start time of event. Use yy-mm-dd hh:mm to enable notifications.
        voice (VoiceChannel): Voice channel
    """
    # Will be long interaction
    await ctx.defer()
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.defer(ephemeral=True)
        await ctx.send("You are missing Manage Messages permission(s) to run this command.",
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    if "cancelled" in title:
        await ctx.send("Title cannot include word `cancelled` in it.",
                       delete_after=S.DELETE_MINUTE, ephemeral=True)
        return
    orignal_time = start_time
    # Get rid of prefixed message in chat that invoked it
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    # Quality of life for the input
    MILENIUM = "20"
    start_time += ":00"
    start_time = MILENIUM + start_time
    # New hash for event
    hash:str = uuid.uuid4().hex
    hash = hash[:10] # first 10 of the hash to not make it long
    # New event with buttons
    buttons = EventView()
    default_unknown_value = "N/A" if include_names else "0"
    sign_up_string = f"Sign-ups✅ 0/{limit}" if limit > 0 and include_names else "Sign-ups✅"
    sign_up_string = f"Sign-ups✅ (limited {limit})" if limit > 0 and not include_names else sign_up_string
    lim = True if limit > 0 else False
    
    emb = Embed(color=int("0x2f3136", 0))
    emb.set_author(name=f"by: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    emb.add_field(name="Name", value=title, inline=True)
    emb.add_field(name="Date", value=orignal_time, inline=True)
    emb.add_field(name="Description", value=description, inline=True)
    emb.add_field(name="Voice", value=f"<#{voice.id}>", inline=False)
    emb.add_field(name=sign_up_string, value=default_unknown_value, inline=True)
    emb.add_field(name="Declined❌", value=default_unknown_value, inline=True)
    emb.add_field(name="Tentative❔", value=default_unknown_value, inline=True)
    include_names = "names" if include_names else "no_names"
    lim = "limit" if lim else "no_limit"
    emb.set_footer(text=f"{hash} • {include_names} • {lim}")
    
    ok = await insert_db(DATABASE, ctx.guild.id, hash, {"author": ctx.author.id})
    if not ok:
        await ctx.send("Something has failed. Try again later.", 
                       delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
        return
    event_message = await ctx.send(embed=emb, view=buttons)
    try:
        await setup_notification(ctx, emb, event_message.id, start_time)
        log.info(f"Notification set: {ctx.guild.name} at {start_time}")
    except ValueError:
        error_message = f"❗Date not recognized❗\n" \
            f"Notifications not applied.\nstart_time:`{orignal_time}`"
        await ctx.send(content=error_message,
                 delete_after=S.DELETE_COMMAND_ERROR, ephemeral=True)
      
async def setup_notification(ctx:Context, emb:Embed, message_id:int, time:str):
    """Set's a timed notification for event start 15 minutes ahead.

    Args:
        ctx (Context): Context of invoke
        emb (Embed): Original embed of event
        time (str): Start time of event

    Raises:
        ValueError: If time format wasn't recognized and notification could not
        be set.
    """
    NAME_FIELD_POSITION = 0
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
    
    # Determine time to wait before notification
    try:
        iso_time_format = await format_time(time)
    except ValueError:
        raise ValueError("Format could have not been recognized.")
    event_name = emb.fields[NAME_FIELD_POSITION].value
    original_time = datetime.strptime(iso_time_format, ISO_FORMAT)
    fifteen_mins_before = original_time - timedelta(minutes=15)
    time_now = datetime.utcnow() + timedelta(hours=2) # CZ
    to_wait = fifteen_mins_before - time_now
    if time_now > fifteen_mins_before:
        return
    await ctx.send(f"Notifications was set 15 minutes ahead successfully!",
                    delete_after=S.DELETE_COMMAND_INVOKE)
    
    # wait the desired time
    await asyncio.sleep(to_wait.seconds)
    
    # only notify if the event wasnt cancelled
    new_updated_message = await ctx.fetch_message(message_id)
    new_updated_embed = new_updated_message.embeds[0]
    event_name = new_updated_embed.fields[0]
    if not "Cancelled: " in event_name.value:
    
        # Notify in the channel
        await ctx.send(f"@here Event `{event_name.value}` starting soon!",
                    delete_after=S.DELETE_COMMAND_INVOKE)
                
        # Notify the signed up members
        name_field = new_updated_embed.fields[4]
        mentions = name_field.value
        trick_to_get_mentions_in_list = await ctx.send(content=mentions)
        await trick_to_get_mentions_in_list.delete()
        user_mentions = trick_to_get_mentions_in_list.mentions
        for u in user_mentions:
            await u.send(f"Event `{event_name.value}` on `{ctx.guild.name}` is starting soon!")
        log.info(f"Notification runned: {ctx.guild.name} on embed {embed_hash(emb)}")
                  
async def setup(target: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global CLIENT
    
    COMMANDS = [events]
    
    for c in COMMANDS:
        target.add_command(c)
        
    CLIENT = target

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass