import json
import os
import asyncio
import aiohttp

class ScheduledEvents:
    """Class connected to discord endpoint via http to communicate with it.
    """
    
    GUILD_ONLY = 2
    STAGE_INSTANCE = 1
    VOICE = 2
    EXTERNAL = 3
    
    TOKEN:str = os.environ.get('DISCORD_BOT_TOKEN')
    BOT:str = "https://discord.com/oauth2/authorize?client_id=821538075078557707"
    API_URL:str = "https://discord.com/api/v8"
    
    AUTH_HEADERS:dict = {
        "Authorization":f"Bot {TOKEN}",
        "User-Agent":f"DiscordBot ({BOT}) Python/3.9 aiohttp/3.8.1",
        "Content-Type":"application/json"
    }
    
    @staticmethod
    async def list_guild_events(guild_id:int)->list:
        """Returns a list of upcoming events for the supplied guild ID
        Format of return is a list of one dictionary per event containing information.

        Args:
            guild_id (int): Guild id in the endpoint

        Returns:
            list: Events as objects
        """
        
        ENDPOINT_URL = f"{ScheduledEvents.API_URL}/guilds/{guild_id}/scheduled-events"
        
        async with aiohttp.ClientSession(headers=ScheduledEvents.AUTH_HEADERS) as session:
            try:
                async with session.get(ENDPOINT_URL) as response:
                    response.raise_for_status()
                    assert response.status == 200
                    response_list = json.loads(await response.read())
            except Exception as e:
                print(f"EXCEPTION: {e}")
            finally:
                await session.close()
        return response_list
    
    @staticmethod
    async def create_guild_event(guild_id: int, event_name: str, 
        event_description: str,  event_start_time: str, event_end_time: str,
        event_metadata: dict, channel_id:int=None):
        """Creates a guild event using the supplied arguments.
        The expected event_metadata format is event_metadata={"location": "YOUR_LOCATION_NAME"}
        The required time format is %Y-%m-%dT%H:%M:%S aka ISO8601

        Args:
            guild_id (str): Guild id in endpoint
            event_name (str): Name of event
            event_description (str): Description of event
            event_start_time (str): Start timestamp
            event_end_time (str): End timestamp 
            event_metadata (dict): External location data
            channel_id (int, optional): Id of voice channel. Defaults to None.
        Raises:
            ValueError: Cannot have both (event_metadata) and (channel_id) 
            at the same time.
        """
        if channel_id and event_metadata:
            raise ValueError(f"If event_metadata is set, channel_id must be set to None. And vice versa.")
        
        ENDPOINT_URL = f"{ScheduledEvents.API_URL}/guilds/{guild_id}/scheduled-events"
        entity_type = ScheduledEvents.EXTERNAL if channel_id is None else ScheduledEvents.VOICE
        
        event_data = json.dumps({
            "name": event_name,
            "privacy_level": ScheduledEvents.GUILD_ONLY,
            "scheduled_start_time": event_start_time,
            "scheduled_end_time": event_end_time,
            "description": event_description,
            "channel_id": channel_id,
            "entity_metadata": event_metadata,
            "entity_type": entity_type
        })
        
        async with aiohttp.ClientSession(headers=ScheduledEvents.AUTH_HEADERS) as session:
            try:
                async with session.post(ENDPOINT_URL, data=event_data) as response:
                    response.raise_for_status()
                    assert response.status == 200
            except Exception as e:
                print(f"EXCEPTION: {e}")
            finally:
                await session.close()
                
                
async def test():
    abc = await ScheduledEvents.list_guild_events(907946271946440745)
    abc = json.dumps(abc, indent=2)
    print(abc)
    # Timestamps must be ahead of time
    #e = await ScheduledEvents.create_guild_event(907946271946440745,"This title", "This desc", "2022-08-28T23:45:00","2022-08-28T23:55:00",{"location":"doma"}, None)
    
    
if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    
""" 
todo:
maybe http patch (edit events)
maybe del event by name
"""