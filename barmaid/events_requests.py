import json
import os
import asyncio
import aiohttp

class DiscordEvents:
    """Class to create and list Discord events utilizing their API"""
    def __init__(self) -> None:
        TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
        BOT = "https://discord.com/oauth2/authorize?client_id=821538075078557707&permissions=8&scope=bot%20applications.commands"
        self.base_api_url = 'https://discord.com/api/v8'

        
        self.auth_headers = {
            "Authorization":f"Bot {TOKEN}",
            "User-Agent":f"DiscordBot ({BOT}) Python/3.9 aiohttp/3.8.1",
            "Content-Type":"application/json"
        }

    async def list_guild_events(self, guild_id: int) -> list:
        """Returns a list of upcoming events for the supplied guild ID
        Format of return is a list of one dictionary per event containing information.
        """
        
        event_retrieve_url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"
        
        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            try:
                async with session.get(event_retrieve_url) as response:
                    response.raise_for_status()
                    assert response.status == 200
                    response_list = json.loads(await response.read())
            except Exception as e:
                print(f"EXCEPTION: {e}")
            finally:
                await session.close()
        return response_list

    async def create_guild_event(self, guild_id: int,event_name: str,
        event_description: str,  event_start_time: str, event_end_time: str,
        event_metadata: dict, event_privacy_level=2, channel_id=None) -> None:
        """Creates a guild event using the supplied arguments
        The expected event_metadata format is event_metadata={"location": "YOUR_LOCATION_NAME"}
        The required time format is %Y-%m-%dT%H:%M:%S
        """
        
        event_create_url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"
        
        event_data = json.dumps({
            "name": event_name,
            "privacy_level": event_privacy_level,
            "scheduled_start_time": event_start_time,
            "scheduled_end_time": event_end_time,
            "description": event_description,
            "channel_id": channel_id,
            "entity_metadata": event_metadata,
            "entity_type": 3
        })

        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            try:
                async with session.post(event_create_url, data=event_data) as response:
                    response.raise_for_status()
                    assert response.status == 200
            except Exception as e:
                print(f"EXCEPTION: {e}")
            finally:
                await session.close()
                
async def test():
    foo = DiscordEvents()
    abc = await foo.list_guild_events(907946271946440745)
    e = await foo.create_guild_event(907946271946440745,"This title", "This desc", "2022-08-26T17:45:00","2022-08-26T17:55:00",{"location":"U tebe doma"},2, None)
    
    
if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    