import asyncio
import json
import aiofiles

DATABASE_NAME = "data.json"
READ_FLAG = "r"
WRITE_FLAG = "w"
READ_WRITE_FLAG = "rw"

async def open_file() -> dict:
    """Opens json file and returns it as dict object.

    Raises:
        OSError: File open can fail

    Returns:
        dict: Dict made out of json file
    """
    try:
        async with aiofiles.open(DATABASE_NAME, READ_FLAG) as f:
            contents = await f.read()
            json_as_dict = json.loads(contents)
    except OSError as e:
        raise OSError(e)
    return json_as_dict

async def flush_file(data:dict) -> str:
    """Flushes dict obj into json file

    Args:
        data (dict): Dictionary to flush

    Raises:
        OSError: Write operation can fail

    Returns:
        str: String that was flushed
    """
    try:
        async with aiofiles.open(DATABASE_NAME, WRITE_FLAG) as f:
            await f.write(data)
            return data
    except OSError as e:
        raise OSError(e)

async def read_db(guid:int, key:str):
    """Reads the value corresponding by key in the database by given
    guild id (guid) searched by.

    Args:
        guid (int): Guild id searched by.
        key (str): Any key value we search for.

    Returns:
        (any | False): Corresponding value to the key, or False if wasn't found any. 
    """   
    guild_str = str(guid)
    
    data = await open_file()
    try:
        value_by_key = data[guild_str][key]
        return value_by_key
    except KeyError as e:
        return False

async def update_db(guid:int, key:str, new_value):
    """Updates existing key-pair in the database stored by guild id (guid).
    If no such key exists, you cannot update it, and returns None.

    Args:
        guid (int): Guild id in the database.
        key (str): Key which we update.
        new_value (any): New value to the key.
        
    Raises:
        OSError: If something failed reading/writing the file.

    Returns:
        (str | None): Returns the updated database as string, or None
        if key failed.
    """
    guid_str = str(guid)
    
    data = await open_file()
    try:
        if not await read_db(guid, key):
            return None
        data[guid_str][key] = new_value
    except KeyError:
        return None
    
    new_data = json.dumps(data, indent=2)
    
    result = await flush_file(new_data)
    return result
    
async def insert_db(guid:int, key:str, value) -> str:
    """Inserts new key into the database with its value.
    If key already exists, returns None.
    
    Args:
        guid (int): Guild id in the database
        key (str): New key we add value to
        value (any): Value to the key
        
    Returns:
        (str | None): Returns updated database as string or None, 
        if you key already existed.
    """
    guid_str = str(guid)
    
    if await read_db(guid, key):
        return None
    
    data = await open_file()
    data[guid_str][key] = value
    to_save = json.dumps(data, indent=2)
    
    result = await flush_file(to_save)
    return result

async def delete_from_db(guid:int, key:str) -> str:
    """Deletes existing key-pair in server's dictionary.

    Args:
        guid (int): Guild id that dict belongs to.
        key (str): Key to delete with its value.

    Returns:
       str: Guild dict (as str) after deletion.
    """
    guid_str = str(guid)
    
    if not await read_db(guid, key):
        return None
    
    data = await open_file()
    del data[guid_str][key]
    to_save = json.dumps(data, indent=2)
    
    result = await flush_file(to_save)
    return result  

async def add_guild(guid:int) -> str:
    """Adds new guild into database.

    Args:
        guid (int): Guild id to add.

    Returns:
        str: New json database
    """
    guid_str = str(guid)
    
    data = await open_file()
    data[guid_str] = {}
    to_save = json.dumps(data, indent=2)
    
    result = await flush_file(to_save)
    return result

async def test():
    a = await open_file()
    print(a)
       
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())

"""
TO-DO
rewrite basic blocking i/o files as nonblocking asynchronous i/o
with aiofiles https://pypi.org/project/aiofiles/
"""    