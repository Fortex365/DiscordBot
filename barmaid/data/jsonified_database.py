import asyncio
import json
import aiofiles
from collections import OrderedDict
from functools import wraps
from log.error_log import setup_logging

log = setup_logging()

READ_FLAG = "r"
WRITE_FLAG = "w"
READ_WRITE_FLAG = "rw"

def async_cache(func):
    cache = {}
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        
        if key not in cache:
            cache[key] = await func(*args, **kwargs)
        return cache[key]
    return wrapper

def async_lru_cache(maxsize=8):
    cache = OrderedDict()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            
            if key in cache:
                value = cache.pop(key)
                cache[key] = value
            else:
                if len(cache) >= maxsize:
                    cache.popitem(last=False)
                value = await func(*args, **kwargs)
                cache[key] = value
            return value
        return wrapper
    return decorator

async def open_file(file_name:str) -> dict:
    """Opens json file and returns it as dict object.

    Raises:
        OSError: File open can fail

    Returns:
        dict: Dict made out of json file
    """
    try:
        async with aiofiles.open(file_name, READ_FLAG) as f:
            contents = await f.read()
            json_as_dict = json.loads(contents)
    except OSError as e:
        log.critical(f"Opening file failed: {file_name} due {e}")
        raise OSError(e)
    return json_as_dict

async def flush_file(file_name:str, data:dict) -> str:
    """Flushes dict obj into json file

    Args:
        data (dict): Dictionary to flush

    Raises:
        OSError: Write operation can fail

    Returns:
        str: String that was flushed
    """
    try:
        async with aiofiles.open(file_name, WRITE_FLAG) as f:
            await f.write(data)
            return data
    except OSError as e:
        log.critical(f"Writing to file failed: {file_name} due {e}")
        raise OSError(e)

async def read_db(file_name:str, id:int, key:str):
    """Reads the value corresponding by key in the database by given
     id (guild | member) searched by.

    Args:
        id (int): Guild or member id searched by.
        key (str): Any key value we search for.

    Returns:
        (any | None): Corresponding value to the key, or None if wasn't found any. 
    """   
    id_str = str(id)
    
    data = await open_file(file_name)
    try:
        value_by_key = data[id_str][key]
        return value_by_key
    except KeyError as e:
        return None

async def read_id(file_name:str, id:int):
    """Reads all corresponding data to id in specified database

    Args:
        file_name (str): Json file
        id (int): Id of guild or member

    Returns:
        any | None: Data found (can can list, dict, int etc.) or None if doesnt
        exists.
    """
    id_str = str(id)
    
    data = await open_file(file_name)
    try:
        value_by_key = data[id_str]
        return value_by_key
    except KeyError as e:
        return None

async def update_db(file_name:str, id:int, key:str, new_value):
    """Updates existing key-pair in the database stored by id (guild | member).
    If no such key exists, the key is added and asigned with new_value.

    Args:
        id (int): Guild or member id in the database.
        key (str): Key which we update.
        new_value (any): New value to the key.
        
    Raises:
        OSError: If something failed reading/writing the file.

    Returns:
        (str | None): Returns the updated database as string, or None
        if key failed.
    """
    id_str = str(id)
    
    data = await open_file(file_name)
    try:
        data[id_str][key] = new_value
    except KeyError:
        return None
    
    new_data = json.dumps(data, indent=2)
    
    result = await flush_file(file_name, new_data)
    return result

async def insert_db(file_name:str, id:int, key:str, value) -> str:
    """Inserts new key into the database with its value.
    If key already exists, returns None.
    
    Args:
        guid (int): Guild id in the database
        key (str): New key we add value to
        value (any): Value to the key
        
    Returns:
        (str | None): Returns updated database as string or None, 
        if your key already existed.
    """
    id_str = str(id)
    
    if await read_db(file_name, id, key):
        return None
    
    data = await open_file(file_name)
    data[id_str][key] = value
    to_save = json.dumps(data, indent=2)
    
    result = await flush_file(file_name, to_save)
    return result

async def delete_from_db(file_name:str, id:int, key:str) -> str:
    """Deletes existing key-pair in json file. When nothing to delete, 
    returns None.

    Args:
        id (int): Guild or member id that dict belongs to.
        key (str): Key to delete with its value.

    Returns:
       str: data.json or naughty_list.json (as str) after deletion.
    """
    id_str = str(id)
    skip_del = False
    
    if not await read_db(file_name, id, key):
        skip_del = True
    
    data = await open_file(file_name)
    if not skip_del:
        del data[id_str][key]
    to_save = json.dumps(data, indent=2)
    if skip_del:
        return to_save
    result = await flush_file(file_name, to_save)
    return result

async def add_id(file_name:str, id:int) -> str:
    """Adds new id into database.

    Args:
        id (int): Guild or member id to add.

    Returns:
        str: New json database
    """
    id_str = str(id)
    
    data = await open_file(file_name)
    data[id_str] = {}
    to_save = json.dumps(data, indent=2)
    
    result = await flush_file(file_name, to_save)
    return result

async def id_lookup(file_name:str, id:int) -> int:
    """Looks up for id in the specified json.

    Args:
        file_name (str): Json file
        id (int): Id to search for

    Returns:
        int: If id was found, else None
    """
    id_str = str(id)
    
    data = await open_file(file_name)
    try:
        result = data[id_str]
    except KeyError as e:
        return None
    return id

if __name__ == "__main__":
    pass