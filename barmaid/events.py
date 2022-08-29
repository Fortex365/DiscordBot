import asyncio
import utilities as S
from datetime import datetime
from utilities import delete_command_user_invoke
from scheduled_events import ScheduledEvents
from hashlib import blake2b
from typing import Union
from discord import Embed, Member, channel, Invite
from discord import Role, Guild, VoiceChannel, Reaction, User
from discord.ext import commands
from discord.message import Message
from discord.ext.commands import errors, Context

"""
Client instance loaded after barmaid.load_extensions() passes its instance into
events.setup().

Disclaimer: from barmaid import client, as it is module global variable doesn't
work for example at events.usr_input(ctx, client).
"""
CLIENT:commands.Bot = None

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

@commands.group(invoke_without_command=True)
@commands.guild_only()
@commands.has_permissions(manage_messages=True)
async def event(ctx:Context):
    if not ctx.invoked_subcommand:
        SKIP_OR_CANCEL_STRING = "\n> Type `skip` (to skip this" \
        " argument) or `cancel` (to cancel command)."
        TIMESTAMP_FORMAT = "\n> Note: valid date is in this format " \
            "`2000-1-31 00:00:00`. Cannot make event in past datetime."
        YES_OR_NO = "\n> Please type either `yes` or `no` to this question."
        GET_VOICE_ID = "\n> To get voice channel id, visit discord settings and" \
            " toggle developer as \"On\" then right-click desired voice-channel and copy its id."
        FORMAT_FROM = "%Y-%m-%d %H:%M:%S"
        FORMAT_TO = "%Y-%m-%dT%H:%M:%S"
        
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        
        # Get name of scheduled event
        name = await ask_for(ctx, f"**What the title should be?**"+SKIP_OR_CANCEL_STRING)
        # Get desc of sch. event
        desc = await ask_for(ctx, f"**What the description is?**"+SKIP_OR_CANCEL_STRING)
        # Get start timestamp
        start = await ask_for(ctx, f"**When the event should start?**"+TIMESTAMP_FORMAT)
        start = datetime.strptime(start, FORMAT_FROM).strftime(FORMAT_TO)
        # Get end ts.
        end = await ask_for(ctx, f"**When the event ends?**"+TIMESTAMP_FORMAT)
        end = datetime.strptime(end, FORMAT_FROM).strftime(FORMAT_TO)
        # Decide location
        is_voice = await ask_for(ctx, f"**Do you wish the event to take place in voice-room?**"+YES_OR_NO)
        
        if is_voice.lower() == "yes":
            # Get channel id
            channel = await ask_for(ctx, f"**Whats the channel id then?**"+GET_VOICE_ID)
            is_valid = ctx.guild.get_channel(int(channel))
            if not is_valid:
                await ctx.send(f"Thats not valid voice-channel id in current guild!",
                         delete_after=S.DELETE_COMMAND_ERROR)
                return
            
            await ScheduledEvents.create_guild_event(
                ctx.guild.id,
                name,
                desc,
                start,
                end,
                None,
                channel
            )
            await ctx.send(f"{ctx.author.mention} **created `{name}` event!**" \
                "\nFor more info visit server events in the top left corner.",
                           delete_after=S.DELETE_DAY)
        else:
            # Get location name
            tmp_location = await ask_for(ctx, f"**Whats the location?**")
            location = {"location": tmp_location}
        
            await ScheduledEvents.create_guild_event(
                ctx.guild.id,
                name,
                desc,
                start,
                end,
                location
            )
            await ctx.send(f"{ctx.author.mention} **created `{name}` event!**" \
                "\nFor more info visit server events in the top left corner.",
                           delete_after=S.DELETE_DAY)

@event.command()
async def simple(ctx:Context, count_people:bool=False, calendar:bool=False):
    SKIP_OR_CANCEL_STRING = "\nType `skip` (to skip this" \
        " argument) or `cancel` (to cancel command)."

    if not ctx.invoked_subcommand:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
        # Title of event
        await ctx.send(f"What the title should be?"+SKIP_OR_CANCEL_STRING,
                       delete_after=S.DELETE_MINUTE)
        title = await usr_input(ctx, CLIENT)
        await title.delete(delay=S.DELETE_MINUTE) if title is not None else None
        if is_timedout_or_cancelled(title):
            return
        title = None if title.content == "skip" else title.content

        # Description of event
        await ctx.send(f"What the description is?"+SKIP_OR_CANCEL_STRING,
                       delete_after=S.DELETE_MINUTE)
        desc = await usr_input(ctx, CLIENT)
        await desc.delete(delay=S.DELETE_MINUTE) if desc is not None else None
        if is_timedout_or_cancelled(desc):
            return
        desc = None if desc.content == "skip" else desc.content
        
        # Date of event
        await ctx.send(f"When the event is?"+SKIP_OR_CANCEL_STRING,
                       delete_after=S.DELETE_MINUTE)
        date = await usr_input(ctx, CLIENT)
        await date.delete(delay=S.DELETE_MINUTE) if date is not None else None
        if is_timedout_or_cancelled(date):
            return
        date = None if date.content == "skip" else date.content
        
        # Embed creation of event
        emb = Embed()
        event_hash = blake2b(digest_size=10).hexdigest()
        
        emb.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        emb.add_field(name="Name", value=title, inline=True) if title else None
        emb.add_field(name="Date", value=date, inline=True) if date else None
        emb.add_field(name="Description", value=desc, inline=False) if desc else None
        emb.add_field(name="Sign-ups", value="N/A", inline=True)
        emb.add_field(name="Calendar", value="N/A", inline=True)
        emb.set_footer(text=event_hash)
        
        sent_emb:Message = await ctx.send(embed=emb)
        # Add reactions
        await sent_emb.add_reaction("📝") 
        await sent_emb.add_reaction("❌") 
        await sent_emb.add_reaction("🤷‍♀️") 
              
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
    
async def setup(target: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global CLIENT
    
    COMMANDS = [event]
    
    for c in COMMANDS:
        target.add_command(c)
        
    CLIENT = target

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass

"""
TO DO:
make sign-ups sign-outs for events (toggle with number or list of @mentions, or autoswitch)
implement add to calendar for events
implement notifications for events (to remind event is starting soon)
add place to event

implement fully custom embed user can make field by field
"""