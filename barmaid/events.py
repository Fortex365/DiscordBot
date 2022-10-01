import asyncio
from datetime import datetime
from hashlib import blake2b
import uuid
from typing import Union
from jsonified_database import insert_db, read_db, update_db

import utilities as S
from utilities import DATABASE, delete_command_user_invoke
from scheduled_events import ScheduledEvents

from discord import Embed, Member, channel, Invite
from discord import Role, Guild, VoiceChannel, Reaction, User

from discord import app_commands, Interaction, ButtonStyle, InteractionMessage
from discord.ui import Button, View, button
from discord.app_commands import Choice

from discord.message import Message

from discord.ext import commands
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

def embed_hash(emb:Embed) -> str:
    """Gets hash of the embed.

    Args:
        emb (Embed): Embed to get its hash

    Returns:
        str: Hash
    """
    footer:str = emb.footer.text
    hash = footer.split(",")
    return hash[0]

def does_embed_include_names(emb:Embed) -> bool:
    """Gets atribute of embed whether use count people or include names.

    Args:
        emb (Embed): Embed to determine

    Returns:
        bool: True if names, False for counting
    """
    footer:str = emb.footer.text
    include_names:str = footer.split(",")
    return eval(include_names[1])

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
async def new_events(ctx:commands.Context):
    pass

@new_events.command()
async def internal_voice(ctx:commands.Context, title:str, description:str, start_time:str, voice_ch:VoiceChannel, end_time:str=None):
    """Creates event as internal discord feature. [VOICECHANNEL LOCATION]

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

@new_events.command()
async def internal_location(ctx:commands.Context, title:str, description:str, start_time:str, end_time:str, location:str):
    """Creates event as internal discord feature. [EXTERNAL LOCATION]

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

@new_events.command()
async def chat_post(ctx:commands.Context, include_names:bool, title:str, description:str, start_time:str, voice:VoiceChannel):
    """Posts an event into chat. Users can interact with it via buttons.

    Args:
        ctx (commands.Context): Context of invoke
        include_names (bool): Whether use count or list user names
        title (str): Title of event
        description (str): Description of event
        start_time (str): Start time of event
        voice (VoiceChannel): Voice channel
    """
    # will be long interaction
    await ctx.defer()
    if not ctx.interaction:
        await delete_command_user_invoke(ctx, S.DELETE_COMMAND_INVOKE)
    #hash = blake2b(digest_size=10).hexdigest()
    hash = uuid.uuid4().hex
    v = EventView()
    default_unknown_value = "N/A" if include_names else "0"
    
    emb = Embed()
    emb.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    emb.add_field(name="Name", value=title, inline=True)
    emb.add_field(name="Date", value=start_time, inline=True)
    emb.add_field(name="Description", value=description, inline=True)
    emb.add_field(name="Voice", value=f"<#{voice.id}>", inline=False)
    emb.add_field(name="Sign-ups✅", value=default_unknown_value, inline=True)
    emb.add_field(name="Declined❌", value=default_unknown_value, inline=True)
    emb.add_field(name="Tentative❔", value=default_unknown_value, inline=True)
    emb.add_field(name="Calendar", value="N/A", inline=False)
    emb.set_footer(text=f"{hash}, {include_names}")
    
    ok = await insert_db(DATABASE, ctx.guild.id, hash, {})
    if not ok:
        await ctx.send("Something has failed. Try again later.")
        return
    await ctx.send(embed=emb, view=v)

class EventView(View):
    """Class reprezenting a view for chat based scheduled events.

    Args:
        View (discord.ui.View): View component
    """
    EMBED_CHATPOST_EVENT_POSITION = 0
    SIGN_IN_FIELD_POSITION = 4
    DECLINED_FIELD_POSITION = 5
    TENTATIVE_FIELD_POSITION = 6
    
    def __init__(self):
        super().__init__(timeout=None)

    @staticmethod
    async def do_update_embed(new_emb:Embed, old_emb:Embed,
                              interaction:Interaction, position:int,
                              clicked_by:User, name:str, value:str, 
                              inline:bool):
        """Removes clicked user from all types (Signin, Declined, Tentatives)
        and puts him into the new one clicked.

        Args:
            new_emb (Embed): Embed with user in new category
            old_emb (Embed): Embed with user in previous category
            interaction (Interaction): Interaction of buttons
            position (int): Position of embed field to update in new category
            clicked_by (User): User who clicked button
            name (str): Field name
            value (str): Field value
            inline (bool): Whether or not field is inline
        """
        new_emb = del_name_occurance(old_emb, clicked_by)
        if not clicked_by.mention in value:
            new_emb.set_field_at(position, name=name,
                                 value=value+"\n"+clicked_by.mention,
                                 inline=inline)
            
            await interaction.edit_original_response(embed=new_emb)
            return
    
    @staticmethod
    async def get_embed_name_value_inline(origin_embed:Embed, vote_category):
        """For embed returns it's tuple (value, name, inline) based on vote 
        category.

        Args:
            origin_embed (Embed): Embed from the message
            vote_category: Vote category

        Returns:
            tuple: Tuple of (value, name, inline)
        """
        emb_fields = origin_embed.fields
        
        signins_value = emb_fields[vote_category].value
        signins_name = emb_fields[vote_category].name
        signins_inline = emb_fields[vote_category].inline
        return (signins_name, signins_value, signins_inline)
     
    async def enable_all_buttons(self):
        """Enables all buttons.
        """
        self.sign_in.disabled = False
        self.decline.disabled = False
        self.tentative.disabled = False
        
    @button(label="Accept", style=ButtonStyle.green)
    async def sign_in(self, interaction: Interaction, button:Button):
        """Button for handling user input to sign into chat-posted scheduled
        event.

        Args:
            interaction (Interaction): Interaction of button
            button (Button): Button itself
        """
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        n, v, i = await EventView.get_embed_name_value_inline(origin_embed, EventView.SIGN_IN_FIELD_POSITION)
        
        v:str = v.removeprefix("N/A") if "N/A" in v else None
        
        if does_embed_include_names(origin_embed):
            new_emb = del_name_occurance(origin_embed, clicked_by)
            await EventView.do_update_embed(new_emb,
                                            origin_embed, interaction,
                                            EventView.SIGN_IN_FIELD_POSITION,
                                            clicked_by, n, v, i)
            return
        else:
            changed = await del_my_one_count(origin_embed, clicked_by,
                                            interaction.guild_id, "sign")
            votes:dict = await read_db(DATABASE, interaction.guild_id,
                                        embed_hash(origin_embed))
            if votes:
                # update my vote as signed
                votes[str(clicked_by.id)] = "sign"
                await update_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                            votes)
            else:
                # my first vote is signed
                await insert_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                                {str(clicked_by.id): "sign"})
            fields = changed.fields
            sign = fields[EventView.SIGN_IN_FIELD_POSITION]
            new_value = int(sign.value)+1
            new_name = sign.name
            new_inline = sign.inline
            changed.set_field_at(EventView.SIGN_IN_FIELD_POSITION,
                                 value=str(new_value), name=new_name,
                                 inline=new_inline)
            await interaction.edit_original_response(embed=changed)
            await self.enable_all_buttons()
            button.disabled = True
            
    @button(label="Decline", style=ButtonStyle.red)
    async def decline(self, interaction: Interaction, button:Button):
        """Button for handling user input to decline into chat-posted scheduled
        event.

        Args:
            interaction (Interaction): Interaction of button
            button (Button): Button itself
        """
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        n, v, i = await EventView.get_embed_name_value_inline(origin_embed, EventView.DECLINED_FIELD_POSITION)
        
        v:str = v.removeprefix("N/A") if "N/A" in v else None
        
        if does_embed_include_names(origin_embed):
            new_emb = del_name_occurance(origin_embed, clicked_by)
            await EventView.do_update_embed(new_emb,
                                            origin_embed, interaction,
                                            EventView.DECLINED_FIELD_POSITION,
                                            clicked_by, n, v, i)
            return
        else:
            changed = await del_my_one_count(origin_embed, clicked_by,
                                            interaction.guild_id, "decline")
            votes:dict = await read_db(DATABASE, interaction.guild_id,
                                        embed_hash(origin_embed))
            if votes:
                # update my vote as declined
                votes[str(clicked_by.id)] = "decline"
                await update_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                            votes)
            else:
                # my first vote is declined
                await insert_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                                {str(clicked_by.id): "decline"})
            fields = changed.fields
            decline = fields[EventView.DECLINED_FIELD_POSITION]
            new_value = int(decline.value)+1
            new_name = decline.name
            new_inline = decline.inline
            changed.set_field_at(EventView.DECLINED_FIELD_POSITION,
                                 value=str(new_value), name=new_name,
                                 inline=new_inline)
            await interaction.edit_original_response(embed=changed)
            await self.enable_all_buttons()
            button.disabled = True
    
    @button(label="Tentative", style=ButtonStyle.secondary)
    async def tentative(self, interaction: Interaction, button:Button):
        """Button for handling user input to tentative into chat-posted scheduled
        event.

        Args:
            interaction (Interaction): Interaction of button
            button (Button): Button itself
        """
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        n, v, i = await EventView.get_embed_name_value_inline(origin_embed, EventView.TENTATIVE_FIELD_POSITION)
        
        v:str = v.removeprefix("N/A") if "N/A" in v else None
        
        if does_embed_include_names(origin_embed):
            new_emb = del_name_occurance(origin_embed, clicked_by)
            await EventView.do_update_embed(new_emb,
                                            origin_embed, interaction,
                                            EventView.TENTATIVE_FIELD_POSITION,
                                            clicked_by, n, v, i)
            return
        else:
            changed = await del_my_one_count(origin_embed, clicked_by,
                                            interaction.guild_id, "tentative")
            votes:dict = await read_db(DATABASE, interaction.guild_id,
                                        embed_hash(origin_embed))
            if votes:
                # update my vote as tentative
                votes[str(clicked_by.id)] = "tentative"
                await update_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                            votes)
            else:
                # my first vote is tentative
                await insert_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                                {str(clicked_by.id): "tentative"})
            fields = changed.fields
            tentative = fields[EventView.TENTATIVE_FIELD_POSITION]
            new_value = int(tentative.value)+1
            new_name = tentative.name
            new_inline = tentative.inline
            changed.set_field_at(EventView.TENTATIVE_FIELD_POSITION,
                                 value=str(new_value), name=new_name,
                                 inline=new_inline)
            await interaction.edit_original_response(embed=changed)
            await self.enable_all_buttons()
            button.disabled = True
    
def del_name_occurance(emb:Embed, usr:User) -> Embed:
    """Removes user occurence in chat-posted scheduled event in one of its 
    category.

    Args:
        emb (Embed): Embed of the scheduled event
        usr (User): User to remove from its category

    Returns:
        Embed: New embed without user in any of the category
    """
    emb_fields = emb.fields[EventView.SIGN_IN_FIELD_POSITION:EventView.TENTATIVE_FIELD_POSITION+1]
    start_count = EventView.SIGN_IN_FIELD_POSITION
    emb_fields_with_position = []
    for f in emb_fields:
        emb_fields_with_position.append((f, start_count))
        start_count += 1
        
    for field, pos in emb_fields_with_position:
        new_value:str = field.value
        new_name = field.name
        new_inline = field.inline
        
        if usr.mention in new_value:
            new_value = new_value.replace(usr.mention, "", 1)
            new_value = "N/A" if new_value == "" else new_value
            emb.set_field_at(pos, name=new_name, value=new_value, inline=new_inline)
    return emb

async def del_my_one_count(emb:Embed, usr:User, guild_id:int, sent_by:str) -> Embed:
    """Delete's user count in any of the category in chat-posted scheduled event.

    Args:
        emb (Embed): Current state of embed
        usr (User): User's vote to remove
        guild_id (int): Guild id of the message
        sent_by (str): Values "sign" "decline" "tentative" sent by buttons

    Raises:
        ValueError: When user's vote doesnt match acceptable value

    Returns:
        Embed: New embed without user's vote
    """
    votes = await read_db(DATABASE, guild_id, embed_hash(emb))
    emb_fields = emb.fields
    try:
        user_vote = votes[str(usr.id)]
    except KeyError:
        return emb
    if user_vote == "sign":
        sign = emb_fields[EventView.SIGN_IN_FIELD_POSITION]
        new_value = sign.value
        name = sign.name
        inline = sign.inline
        # we subtract our vote
        new_value = int(new_value)-1
        # if undershoot
        if new_value <= 0:
            new_value = "0"
        # modify the embed and return it
        emb.set_field_at(EventView.SIGN_IN_FIELD_POSITION,
                         name=name,
                         value=str(new_value),
                         inline=inline)
        return emb
    elif user_vote == "decline":
        decline = emb_fields[EventView.DECLINED_FIELD_POSITION]
        new_value = decline.value
        name = decline.name
        inline = decline.inline
        new_value = int(new_value)-1
        if new_value <= 0:
            new_value = "0"
        emb.set_field_at(EventView.DECLINED_FIELD_POSITION,
                         name=name,
                         value=str(new_value),
                         inline=inline)
        return emb
    elif user_vote == "tentative":
        tentative = emb_fields[EventView.TENTATIVE_FIELD_POSITION]
        new_value = tentative.value
        name = tentative.name
        inline = tentative.inline
        new_value = int(new_value)-1
        if new_value <= 0:
            new_value = "0"
        emb.set_field_at(EventView.TENTATIVE_FIELD_POSITION,
                         name=name,
                         value=str(new_value),
                         inline=inline)
        return emb
    raise ValueError("Bad argument value of user event vote.")
            
async def setup(target: commands.Bot):
    """Setup function which allows this module to be
    an extension loaded into the main file.

    Args:
        client_bot: The bot instance itself,
        passed in from barmaid.load_extention("admin_tools").
    """
    global CLIENT
    
    COMMANDS = [new_events]
    
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