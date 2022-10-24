from typing import Union
from jsonified_database import insert_db, read_db, update_db

import utilities as S
from utilities import DATABASE

from discord import Embed, Member
from discord import User

from discord import Interaction, ButtonStyle
from discord.ui import Button, View, button

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

def does_embed_have_sign_limit(emb:Embed) -> bool:
    """Gets atribute of embed whether use limit to sign ups in events.

    Args:
        emb (Embed): Embed to determine

    Returns:
        bool: True if limit, False otherwise
    """
    footer:str = emb.footer.text
    limit:str = footer.split(",")
    return eval(limit[2])

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
    async def do_action(new_emb:Embed, old_emb:Embed,
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
        new_emb = EventView.del_name_occurance(old_emb, clicked_by)
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
    
    @staticmethod
    async def do_action_no_names(type:str, origin_embed:Embed, interaction:Interaction, clicked_by:Union[User, Member]):
        # check iput
        accepted_input = ["sign", "tentative", "decline"]
        if not type in accepted_input:
            raise ValueError(f"Value {type} is not accepted by this method.")
        
        # determine type of action
        if type == "sign":
            POSITION = EventView.SIGN_IN_FIELD_POSITION
        elif type == "decline":
            POSITION = EventView.DECLINED_FIELD_POSITION
        else:
            POSITION = EventView.TENTATIVE_FIELD_POSITION
            
        # remove my vote from any field im in
        changed = await EventView.del_my_one_count(origin_embed, clicked_by,
                                        interaction.guild_id, type)
        votes:dict = await read_db(DATABASE, interaction.guild_id,
                                    embed_hash(origin_embed))
        if votes:
            # update my vote as signed/decline/tentative
            votes[str(clicked_by.id)] = type
            await update_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                        votes)
        else:
            # my first vote is signed/decline/tentative
            await insert_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
                            {str(clicked_by.id): type})
        fields = changed.fields
        action = fields[POSITION]
        new_name = action.name
        new_value = int(action.value)+1
        """
        JE POTŘEBA UDĚLAT POČET HLASŮ DLE POČTU V DATABÁZI JINAK JEDEN UŽIVATEL 
        JE SCHOPNÝ ODEČÍST DALŠÍHO
        """
        if type == "sign":
            text = new_name.split(" ")
            limit = text[2]
            limit_value = int(limit.removesuffix(")"))
            new_value = limit_value if new_value > limit_value else new_value
        new_inline = action.inline
        changed.set_field_at(POSITION,
                                value=str(new_value), name=new_name,
                                inline=new_inline)
        await interaction.edit_original_response(embed=changed)  
        
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
        
        v:str = v.removeprefix("N/A") if "N/A" in v else v
    
        
        if does_embed_include_names(origin_embed):
            new_emb = EventView.del_name_occurance(origin_embed, clicked_by)
            # special threatment to names with limit
            if does_embed_have_sign_limit(origin_embed):
                text = n.split(" ")
                limit = text[1]
                limit_values = limit.split("/")
                add_my_count = int(limit_values[0])+1
                add_my_count = limit_values[1] if add_my_count > int(limit_values[1]) else add_my_count
                n = "Sign-ups✅ " + str(add_my_count) + "/" + limit_values[1]
                
            await EventView.do_action(new_emb,
                                            origin_embed, interaction,
                                            EventView.SIGN_IN_FIELD_POSITION,
                                            clicked_by, n, v, i)
            return
        else:
            await EventView.do_action_no_names("sign", origin_embed, interaction, clicked_by)
            #changed = await del_my_one_count(origin_embed, clicked_by,
            #                                interaction.guild_id, "sign")
            #votes:dict = await read_db(DATABASE, interaction.guild_id,
            #                            embed_hash(origin_embed))
            #if votes:
            #    # update my vote as signed
            #    votes[str(clicked_by.id)] = "sign"
            #    await update_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
            #                votes)
            #else:
            #    # my first vote is signed
            #    await insert_db(DATABASE, interaction.guild_id, embed_hash(origin_embed),
            #                    {str(clicked_by.id): "sign"})
            #fields = changed.fields
            #sign = fields[EventView.SIGN_IN_FIELD_POSITION]
            #new_value = int(sign.value)+1
            #new_name = sign.name
            #new_inline = sign.inline
            #changed.set_field_at(EventView.SIGN_IN_FIELD_POSITION,
            #                     value=str(new_value), name=new_name,
            #                     inline=new_inline)
            #await interaction.edit_original_response(embed=changed)
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
        
        v:str = v.removeprefix("N/A") if "N/A" in v else v
        
        if does_embed_include_names(origin_embed):
            new_emb = EventView.del_name_occurance(origin_embed, clicked_by)
            await EventView.do_action(new_emb,
                                            origin_embed, interaction,
                                            EventView.DECLINED_FIELD_POSITION,
                                            clicked_by, n, v, i)
            return
        else:
            changed = await EventView.del_my_one_count(origin_embed, clicked_by,
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
        
        v:str = v.removeprefix("N/A") if "N/A" in v else v
        
        if does_embed_include_names(origin_embed):
            new_emb = EventView.del_name_occurance(origin_embed, clicked_by)
            await EventView.do_action(new_emb,
                                            origin_embed, interaction,
                                            EventView.TENTATIVE_FIELD_POSITION,
                                            clicked_by, n, v, i)
            return
        else:
            changed = await EventView.del_my_one_count(origin_embed, clicked_by,
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
    
    @staticmethod
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
            if does_embed_have_sign_limit(emb) and pos == EventView.SIGN_IN_FIELD_POSITION:
                text = new_name.split(" ")
                limit = text[1]
                limit_values = limit.split("/")
                delete_my_count = int(limit_values[0])-1
                delete_my_count = 0 if delete_my_count < 0 else delete_my_count
                new_name = "Sign-ups✅ " + str(delete_my_count) + "/" + limit_values[1]
            new_inline = field.inline
            
            if usr.mention in new_value:
                new_value = new_value.replace(usr.mention, "", 1)
                new_value = "N/A" if new_value == "" else new_value
                emb.set_field_at(pos, name=new_name, value=new_value, inline=new_inline)
        return emb

    @staticmethod
    async def del_my_one_count(emb:Embed, usr:User, guild_id:int) -> Embed:
        """Delete's user count in any of the category in chat-posted scheduled event.

        Args:
            emb (Embed): Current state of embed
            usr (User): User's vote to remove
            guild_id (int): Guild id of the message

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