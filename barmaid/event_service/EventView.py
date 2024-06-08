from typing import Union
from functools import lru_cache
from discord import Embed, Member, User, Interaction, ButtonStyle
from discord.ui import Button, View, button
from data_service.database_service import insert_new_key_by_guild_id, read_key_by_guild_id, update_key_by_guild_id
import data_service.config_service as S
from data_service.config_service import DATABASE
from log_service.setup import setup_logging

log = setup_logging()

def embed_hash(emb: Embed) -> str:
    """Gets hash of the embed."""
    footer = emb.footer.text
    return footer.split("•")[0].strip()[:10]

def does_embed_include_names(emb: Embed) -> bool:
    """Checks if the embed includes names instead of counts."""
    footer = emb.footer.text
    return "no_names" not in footer.split("•")[1]

def does_embed_have_sign_limit(emb: Embed) -> bool:
    """Checks if the embed has a sign-up limit."""
    footer = emb.footer.text
    return "no_limit" not in footer.split("•")[2]

class EventView(View):
    """Class representing a view for chat-based scheduled events."""
    EMBED_CHATPOST_EVENT_POSITION = 0
    SIGN_IN_FIELD_POSITION = 4
    DECLINED_FIELD_POSITION = 5
    TENTATIVE_FIELD_POSITION = 6
    
    def __init__(self):
        super().__init__(timeout=None)

    @staticmethod
    async def do_action(new_emb: Embed, old_emb: Embed,
                        interaction: Interaction, position: int,
                        clicked_by: User, name: str, value: str, 
                        inline: bool):
        """Handles user actions for signing in, declining, and tentative."""
        new_emb = EventView.del_name_occurance(old_emb, clicked_by)
        if clicked_by.mention not in value:
            new_emb.set_field_at(position, name=name, value=f"{value}\n{clicked_by.mention}", inline=inline)
            await interaction.edit_original_response(embed=new_emb)

    @staticmethod
    async def get_embed_name_value_inline(origin_embed: Embed, vote_category: int):
        """Returns the value, name, and inline attributes of the embed field."""
        field = origin_embed.fields[vote_category]
        return field.name, field.value, field.inline
     
    async def enable_all_buttons(self):
        """Enables all buttons."""
        self.sign_in.disabled = False
        self.decline.disabled = False
        self.tentative.disabled = False
    
    @staticmethod
    def is_cancelled(embed: Embed) -> bool:
        """Checks if the event is cancelled."""
        return "Cancelled: " in embed.fields[0].value
        
    @staticmethod
    async def do_action_no_names(type: str, origin_embed: Embed, interaction: Interaction, clicked_by: Union[User, Member]):
        """Handles actions when names are not included in the embed."""
        if type not in ["sign", "tentative", "decline"]:
            raise ValueError(f"Value {type} is not accepted by this method.")
        
        position = {
            "sign": EventView.SIGN_IN_FIELD_POSITION,
            "decline": EventView.DECLINED_FIELD_POSITION,
            "tentative": EventView.TENTATIVE_FIELD_POSITION
        }[type]
        
        changed = await EventView.del_no_name_occurance(origin_embed, clicked_by, interaction.guild_id, type)
        votes = await read_key_by_guild_id(DATABASE, interaction.guild_id, embed_hash(origin_embed)) or {}
        votes[str(clicked_by.id)] = type
        
        fields = changed.fields
        action = fields[position]
        new_name = action.name
        new_value = int(action.value)
        
        if type == "sign":
            limit = int(new_name.split(" ")[2].replace(")", "")) if " " in new_name else 999999
            if new_value < limit:
                new_value += 1
                await update_key_by_guild_id(DATABASE, interaction.guild_id, embed_hash(origin_embed), votes)
            else:
                await interaction.followup.send("I'm sorry, but the event exceeded its sign-ups.", ephemeral=True)
                return
        else:
            new_value += 1
            await update_key_by_guild_id(DATABASE, interaction.guild_id, embed_hash(origin_embed), votes)
        
        changed.set_field_at(position, name=new_name, value=str(new_value), inline=action.inline)
        await interaction.edit_original_response(embed=changed)
        
    @button(label="Accept", style=ButtonStyle.gray, emoji="✔", custom_id="persistent:sign")
    async def sign_in(self, interaction: Interaction, button: Button):
        """Button for handling user input to sign into chat-posted scheduled event."""
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        n, v, i = await EventView.get_embed_name_value_inline(origin_embed, EventView.SIGN_IN_FIELD_POSITION)
        
        if EventView.is_cancelled(origin_embed):
            return
        
        v = v if "N/A" not in v else ""
        
        if does_embed_include_names(origin_embed):
            new_emb = EventView.del_name_occurance(origin_embed, clicked_by)
            if does_embed_have_sign_limit(origin_embed):
                text = n.split(" ")
                limit_values = text[1].split("/")
                add_my_count = int(limit_values[0]) + 1
                if add_my_count > int(limit_values[1]):
                    return
                n = f"Sign-ups✅ {add_my_count}/{limit_values[1]}"
            await EventView.do_action(new_emb, origin_embed, interaction, EventView.SIGN_IN_FIELD_POSITION, clicked_by, n, v, i)
        else:
            await EventView.do_action_no_names("sign", origin_embed, interaction, clicked_by)
            
    @button(label="Decline", style=ButtonStyle.gray, emoji="✖", custom_id="persistent:decline")
    async def decline(self, interaction: Interaction, button: Button):
        """Button for handling user input to decline chat-posted scheduled event."""
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        n, v, i = await EventView.get_embed_name_value_inline(origin_embed, EventView.DECLINED_FIELD_POSITION)
        
        if EventView.is_cancelled(origin_embed):
            return
        
        v = v if "N/A" not in v else ""
        
        if does_embed_include_names(origin_embed):
            new_emb = EventView.del_name_occurance(origin_embed, clicked_by)
            await EventView.do_action(new_emb, origin_embed, interaction, EventView.DECLINED_FIELD_POSITION, clicked_by, n, v, i)
        else:
            await EventView.do_action_no_names("decline", origin_embed, interaction, clicked_by)
    
    @button(label="Tentative", style=ButtonStyle.gray, emoji="➖", custom_id="persistent:tentative")
    async def tentative(self, interaction: Interaction, button: Button):
        """Button for handling user input to tentative chat-posted scheduled event."""
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        n, v, i = await EventView.get_embed_name_value_inline(origin_embed, EventView.TENTATIVE_FIELD_POSITION)
        
        if EventView.is_cancelled(origin_embed):
            return
        
        v = v if "N/A" not in v else ""
        
        if does_embed_include_names(origin_embed):
            new_emb = EventView.del_name_occurance(origin_embed, clicked_by)
            await EventView.do_action(new_emb, origin_embed, interaction, EventView.TENTATIVE_FIELD_POSITION, clicked_by, n, v, i)
        else:
            await EventView.do_action_no_names("tentative", origin_embed, interaction, clicked_by)
            
    @button(label="Cancel", style=ButtonStyle.gray, emoji="⚙", custom_id="persistent:cancel")
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        clicked_by = interaction.user
        
        origin = await interaction.original_response()
        origin_embed = origin.embeds[EventView.EMBED_CHATPOST_EVENT_POSITION]
        hash = embed_hash(origin_embed)
        event = await read_key_by_guild_id(DATABASE, interaction.guild_id, hash)
        author_id = event["author"]
        
        if author_id == clicked_by.id:
            embed_fields = origin_embed.fields
            name_field = embed_fields[0]
            if "Cancelled: " in name_field.value:
                return
            cancelled_name = "Cancelled: " + name_field.value
            time_field = embed_fields[1]
            cancelled_time = "~~" + time_field.value + "~~"
            origin_embed.set_field_at(0, name=name_field.name, value=cancelled_name, inline=name_field.inline)
            origin_embed.set_field_at(1, name=time_field.name, value=cancelled_time, inline=time_field.inline)
            await interaction.edit_original_response(embed=origin_embed)
            await interaction.channel.send(f"Event `{name_field.value}` at `{time_field.value}` was cancelled by author. Buttons disabled.")
        else:
            await interaction.followup.send("Sorry, only the author of the event can cancel it.", ephemeral=True)
          
    @staticmethod
    def del_name_occurance(emb: Embed, usr: User) -> Embed:
        """Removes user occurrence from all categories in the embed."""
        for pos in range(EventView.SIGN_IN_FIELD_POSITION, EventView.TENTATIVE_FIELD_POSITION + 1):
            field = emb.fields[pos]
            if usr.mention in field.value:
                new_value = field.value.replace(usr.mention, "").strip()
                new_value = "N/A" if not new_value else new_value
                if pos == EventView.SIGN_IN_FIELD_POSITION and does_embed_have_sign_limit(emb):
                    text = field.name.split(" ")
                    limit_values = text[1].split("/")
                    limit_values[0] = str(int(limit_values[0]) - 1)
                    new_name = f"Sign-ups✅ {limit_values[0]}/{limit_values[1]}"
                    emb.set_field_at(pos, name=new_name, value=new_value, inline=field.inline)
                else:
                    emb.set_field_at(pos, name=field.name, value=new_value, inline=field.inline)
        return emb

    @staticmethod
    async def del_no_name_occurance(emb: Embed, usr: User, guild_id: int, type: str) -> Embed:
        """Deletes user's vote from the embed fields."""
        votes = await read_key_by_guild_id(DATABASE, guild_id, embed_hash(emb))
        if str(usr.id) not in votes:
            return emb
        
        vote_type = votes[str(usr.id)]
        position = {
            "sign": EventView.SIGN_IN_FIELD_POSITION,
            "decline": EventView.DECLINED_FIELD_POSITION,
            "tentative": EventView.TENTATIVE_FIELD_POSITION
        }[vote_type]
        
        return await EventView._del_no_name_occurance(emb, position, votes, guild_id, usr)
    
    @staticmethod
    async def _del_no_name_occurance(embed: Embed, position: int, votes: dict, guild_id: int, user: User) -> Embed:
        """Helper method to delete user's vote occurrence."""
        field = embed.fields[position]
        new_value = int(field.value) - 1 if str(user.id) in votes else int(field.value)
        new_value = max(new_value, 0)
        embed.set_field_at(position, name=field.name, value=str(new_value), inline=field.inline)
        votes.pop(str(user.id), None)
        await update_key_by_guild_id(DATABASE, guild_id, embed_hash(embed), votes)
        return embed
    
if __name__ == "__main__":
    pass
