import json

DATABASE_NAME = "data.json"
READ_FLAG = "r"
WRITE_FLAG = "w"
READ_WRITE_FLAG = "rw"

def read_db(guid:int, key:str):
    """Reads the value corresponding by key in the database by given
    guild id (guid) searched by.

    Args:
        guid (int): Guild id searched by.
        key (str): Any key value we search for.

    Raises:
        OSError: If something failed reading the file.

    Returns:
        (any, None): Corresponding value to the key, or None if wasn't found any. 
    """
    guid_str = str(guid)
    
    try:
        with open(DATABASE_NAME, READ_FLAG) as f:
            json_obj = json.load(f)
            try:
                guild_data = json_obj[guid_str]
                value_by_key = guild_data[key]
                return value_by_key
            except KeyError as e:
                return None
    # for now
    except OSError as e:
        raise OSError(e)

def update_db(guid:int, key:str, new_value):
    """Updates existing key-pair in the database stored by guild id (guid).
    If no such key exists, you cannot update it, and returns None.

    Args:
        guid (int): Guild id in the database.
        key (str): Key which we update.
        new_value (any): New value to the key.
        
    Raises:
        OSError: If something failed reading/writing the file.

    Returns:
        (dict, None): Returns the updated database as python dictionary, or None
        if key failed.
    """
    guid_str = str(guid)
    
    try:
        with open(DATABASE_NAME, READ_FLAG) as f:
            old_obj = json.load(f)
    # for now
    except OSError as e:
        raise OSError(e)
    
    new_obj = old_obj
    try:
        guild_data = new_obj[guid_str]
        # If key isn't present in database
        if not read_db(guid, key):
            return None
        guild_data[key] = new_value
        new_obj[guid_str] = guild_data
    except KeyError:
        return None
    result = json.dumps(new_obj, indent=2)
    
    try:
        with open(DATABASE_NAME, WRITE_FLAG) as f:
            f.write(result)
        return result
    # for now
    except OSError as e:
        raise OSError(e)
    
def insert_db(guid:int, key:str, value):
    """Inserts new key into the database with its value.
    If key already exists, returns None.
    
    Args:
        guid (int): Guild id in the database
        key (str): New key we add value to
        value (any): Value to the key

    Raises:
        OSError: If something failed reading/writing the file.
        
    Returns:
        (dict, None): Returns updated database as python dictionary or None, 
        if you key already existed.
    """
    guid_str = str(guid)
    
    # If key is already present in database
    if read_db(guid, key):
        return None
    
    try:
        with open(DATABASE_NAME, READ_FLAG) as f:
            old_obj = json.load(f)
    except OSError:
        return None
    
    new_obj = old_obj
    key_value_data = {
        key: value
    }
    new_obj[guid_str] = key_value_data
    to_save = json.dumps(new_obj, indent=2)
    
    try:
        with open(DATABASE_NAME, WRITE_FLAG) as f:
            f.write(to_save)
            return new_obj
    except OSError:
        return None
    