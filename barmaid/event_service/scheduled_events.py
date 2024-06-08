import json
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from data_service.config_service import BOT_AUTH_HEADER
from log_service.setup import setup_logging

log = setup_logging()

class ScheduledEvents:
    """Class to interact with Discord's scheduled events API."""

    GUILD_ONLY = 2
    STAGE_INSTANCE = 1
    VOICE = 2
    EXTERNAL = 3

    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    API_URL = "https://discord.com/api/v10"

    AUTH_HEADERS = {
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": f"DiscordBot ({BOT_AUTH_HEADER}) Python/3.9 aiohttp/3.7.4",
        "Content-Type": "application/json"
    }

    @staticmethod
    async def _fetch(session, url, method='GET', data=None):
        """Helper method to handle HTTP requests."""
        try:
            async with session.request(method, url, data=data) as response:
                response.raise_for_status()
                log.info(f"{method} success: to {url}")
                return await response.json() if response.status != 204 else None
        except Exception as e:
            log.warning(f"{method} error: to {url} as {e}")

    @classmethod
    async def list_guild_events(cls, guild_id):
        """Returns a list of upcoming events for the specified guild ID."""
        url = f"{cls.API_URL}/guilds/{guild_id}/scheduled-events"
        async with aiohttp.ClientSession(headers=cls.AUTH_HEADERS) as session:
            return await cls._fetch(session, url)

    @classmethod
    async def find_guild_event(cls, target_name, guild_id):
        """Finds an event by name and returns its ID."""
        events = await cls.list_guild_events(guild_id)
        for event in events:
            if target_name in event["name"]:
                return event["id"]
        raise ValueError(f"Event with target_name='{target_name}' cannot be found in guild_id={guild_id}")

    @classmethod
    async def create_guild_event(cls, guild_id, event_name, event_description, event_start_time, event_end_time, event_metadata, channel_id=None):
        """Creates a guild event."""
        if channel_id and event_metadata:
            raise ValueError("If event_metadata is set, channel_id must be None, and vice versa.")
        
        url = f"{cls.API_URL}/guilds/{guild_id}/scheduled-events"
        entity_type = cls.EXTERNAL if channel_id is None else cls.VOICE
        
        event_data = json.dumps({
            "name": event_name,
            "privacy_level": cls.GUILD_ONLY,
            "scheduled_start_time": event_start_time,
            "scheduled_end_time": event_end_time,
            "description": event_description,
            "channel_id": channel_id,
            "entity_metadata": event_metadata,
            "entity_type": entity_type
        })
        
        async with aiohttp.ClientSession(headers=cls.AUTH_HEADERS) as session:
            return await cls._fetch(session, url, method='POST', data=event_data)

    @classmethod
    async def modify_guild_event(cls, event_id, guild_id, event_name, event_description, event_start_time, event_end_time, event_metadata, channel_id=None):
        """Modifies an existing guild event."""
        if channel_id and event_metadata:
            raise ValueError("If event_metadata is set, channel_id must be None, and vice versa.")
        
        url = f"{cls.API_URL}/guilds/{guild_id}/scheduled-events/{event_id}"
        entity_type = cls.EXTERNAL if channel_id is None else cls.VOICE
        
        event_data = json.dumps({
            "name": event_name,
            "privacy_level": cls.GUILD_ONLY,
            "scheduled_start_time": event_start_time,
            "scheduled_end_time": event_end_time,
            "description": event_description,
            "channel_id": channel_id,
            "entity_metadata": event_metadata,
            "entity_type": entity_type
        })
        
        async with aiohttp.ClientSession(headers=cls.AUTH_HEADERS) as session:
            return await cls._fetch(session, url, method='PATCH', data=event_data)

    @classmethod
    async def delete_guild_event(cls, guild_id, event_id):
        """Deletes a guild event."""
        url = f"{cls.API_URL}/guilds/{guild_id}/scheduled-events/{event_id}"
        async with aiohttp.ClientSession(headers=cls.AUTH_HEADERS) as session:
            return await cls._fetch(session, url, method='DELETE')

if __name__ == "__main__":
    """Main module should not execute any action."""
    pass
