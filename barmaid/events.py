import asyncio
from datetime import datetime, timedelta
import uuid

from jsonified_database import insert_db, read_db, update_db
import utilities as S
from utilities import DATABASE, delete_command_user_invoke
from EventView import EventView
from scheduled_events import ScheduledEvents

from discord import Embed, Member, channel, Invite
from discord import Role, Guild, VoiceChannel, Reaction, User, Object

from discord.message import Message

from discord.ext import commands
from discord.ext.commands import Context

"""
Client instance loaded after barmaid.load_extensions() passes its instance into
events.setup().

Disclaimer: from barmaid import client, as it is module global variable doesn't
work for example at events.usr_input(ctx, client).
"""
CLIENT:commands.Bot = None

# to be del
async def ask_for(ctx:Context, requested_input:str)->str:
    # Asks in chat for for requested input
    await ctx.send(f"{requested_input}", delete_after=S.DELETE_MINUTE)   
    # Gets in chat asnwer for the input
    answer = await usr_input(ctx, CLIENT)
    # If was valid message, sets it to be cleared later
    await answer.delete(delay=S.DELETE_MINUTE) if answer is not None else None
    # If was invalid message or timeouted
    if is_timedout_or_cancelled(answer):
        return
    # Parse the answer 
    answer = None if answer.content == "skip" else answer.content
    return answer

# to be del             
def is_timedout_or_cancelled(msg:Message):
    """Determines if message user responded was timeouted or command cancel
    message.

    Args:
        msg (Message): Message we determine

    Returns:
        bool: True if timeouted or content of message was cancel.
    """
    try:
        if (msg.content == "cancel"):
            return True
    except AttributeError:
        if msg == None:
            return True
        return False

# to be del
async def usr_input(ctx:Context, bot:commands.Bot, timeout:int=60) -> Message:
    """Waits for input from user in a form of next message.

    Args:
        ctx (Context): Context where we expect the message
        bot (commands.Bot): Bot which listens to message
        timeout (int, optional): Timeout the user has to respond. Defaults to 60.

    Returns:
        Message: Instance of message bot got in responde, None if user runs out
        of time.
    """
    try:
        msg:Message = await bot.wait_for("message",
                                 timeout=timeout,
                                 check=lambda message: message.author == ctx.author)
    except asyncio.TimeoutError:
        await ctx.send("Took you too long to respond!",
                       delete_after=S.DELETE_MINUTE)
        return
    return msg   

async def format_time(in_str:str) -> str:
    """Formats string from %Y-%m-%d %H:%M:%S into ISO8601 format.

    Args:
        in_str (str): String to format

    Returns:
        str: %Y-%m-%dT%H:%M:%S string format
    """
    FORMAT_FROM = "%Y-%m-%d %H:%M:%S"
    FORMAT_TO = "%Y-%m-%dT%H:%M:%S"
    
    return datetime.strptime(in_str, FORMAT_FROM).strftime(FORMAT_TO)

@commands.hybrid_group(with_app_command=True)
@commands.guild_only()
@commands.has_permissions(manage_messages=True)
async def events(ctx:commands.Context):
    pass

@events.command()
async def ivoice(ctx:commands.Context, title:str, description:str, start_time:str, voice_ch:VoiceChannel, end_time:str=None):
    """Creates event as internal discord feature, with voice channel.

    Args:
        ctx (commands.Context): Context of invoke
        title (str): Title of event
        description (str): Description of event
        start_time (str): Use "yy-mm-dd hh:mm:ss" format
        voice_ch (VoiceChannel): Voice channel id
        end_time (str, optional): Use "yy-mm-dd hh:mm:ss" format. Optional.
    """    
    await ctx.defer(ephemeral=True)
    
    MILENIUM = "20"
    start = await format_time(MILENIUM+start_time)
    end = await format_time(MILENIUM+end_time) if end_time is not None else None

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
        await ctx.send(f"Created event `{title}`", delete_after=S.DELETE_COMMAND_INVOKE)
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
        start_time (str): Use "yy-mm-dd hh:mm:ss" format
        voice_ch (VoiceChannel): Voice channel id
        end_time (str): Use "yy-mm-dd hh:mm:ss" format. REQUIRED.
    """
    await ctx.defer(ephemeral=True)
    
    metadata = {"location": location}
    
    MILENIUM = "20"
    start = await format_time(MILENIUM+start_time)
    end = await format_time(MILENIUM+end_time)

    
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
        await ctx.send(f"Created event `{title}`", delete_after=S.DELETE_COMMAND_INVOKE)
        return
    await ctx.send(f"Event creation has failed. Try again later.", 
                   delete_after=S.DELETE_COMMAND_ERROR)

@events.command()
async def echat(ctx:commands.Context, include_names:bool, title:str, description:str, start_time:str, voice:VoiceChannel, limit:int=0):
    """External chat-based interactive event via buttons.

    Args:
        ctx (commands.Context): Context of invoke
        include_names (bool): Include names in event category lists.
        title (str): Title of event
        description (str): Description of event
        start_time (str): Start time of event. Use yyyy-mm-dd hh:mm:ss to enable notifications.
        voice (VoiceChannel): Voice channel
    """
    # will be long interaction
    await ctx.defer()
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    hash = uuid.uuid4().hex
    v = EventView()
    default_unknown_value = "N/A" if include_names else "0"
    sign_up_string = f"Sign-ups✅ 0/{limit}" if limit > 0 and include_names else "Sign-ups✅"
    sign_up_string = f"Sign-ups✅ (limited {limit})" if limit > 0 and not include_names else sign_up_string
    lim = True if limit > 0 else False
    
    emb = Embed()
    emb.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    emb.add_field(name="Name", value=title, inline=True)
    emb.add_field(name="Date", value=start_time, inline=True)
    emb.add_field(name="Description", value=description, inline=True)
    emb.add_field(name="Voice", value=f"<#{voice.id}>", inline=False)
    emb.add_field(name=sign_up_string, value=default_unknown_value, inline=True)
    emb.add_field(name="Declined❌", value=default_unknown_value, inline=True)
    emb.add_field(name="Tentative❔", value=default_unknown_value, inline=True)
    emb.add_field(name="Calendar", value="N/A", inline=False)
    emb.set_footer(text=f"{hash}, {include_names}, {lim}")
    
    ok = await insert_db(DATABASE, ctx.guild.id, hash, {})
    if not ok:
        await ctx.send("Something has failed. Try again later.", 
                       delete_after=S.DELETE_COMMAND_ERROR)
        return
    event_message = await ctx.send(embed=emb, view=v)
    try:
        await setup_notification(ctx, emb, event_message.id, start_time)
    except ValueError:
        await ctx.send("Event start time notification could not recognize date." / 
                 "Notification for event won't be applied.",
                 delete_after=S.DELETE_COMMAND_ERROR)
      
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
    time_now = datetime.utcnow() + timedelta(hours=2)
    to_wait = fifteen_mins_before - time_now
    if time_now > fifteen_mins_before:
        return
    await ctx.send(f"Notifications was set 15 minutes ahead successfully!",
                    delete_after=S.DELETE_COMMAND_INVOKE)
    
    # Notify in the channel
    await asyncio.sleep(to_wait.seconds)
    await ctx.send(f"@here Event `{event_name}` starting soon!",
                delete_after=S.DELETE_COMMAND_INVOKE)
    
    # Notify the signed up members
    new_updated_message = await ctx.fetch_message(message_id)
    new_updated_embed = new_updated_message.embeds[0]
    sign_field = new_updated_embed.fields[4]
    mentions = sign_field.value
    trick_to_get_mentions_in_list = await ctx.send(content=mentions)
    await trick_to_get_mentions_in_list.delete()
    user_mentions = trick_to_get_mentions_in_list.mentions
    for u in user_mentions:
        await u.send(f"Event `{event_name}` on `{ctx.guild.name}` is starting soon!")
                  
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

"""
TO DO:
implement add to calendar for events
"""