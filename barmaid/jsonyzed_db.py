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
        (any | False): Corresponding value to the key, or False if wasn't found any. 
    """
    guid_str = str(guid)
    
    try:
        with open(DATABASE_NAME, READ_FLAG) as f:
            json_obj = json.load(f)
            try:
                value_by_key = json_obj[guid_str][key]
                # can return None which was converted from json's null
                return value_by_key
            except KeyError as e:
                return False
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
        (str | None): Returns the updated database as string, or None
        if key failed.
    """
    guid_str = str(guid)
    
    try:
        with open(DATABASE_NAME, READ_FLAG) as f:
            db_in_json = json.load(f)
    # for now
    except OSError as e:
        raise OSError(e)
    
    try:
        # If key isn't present in database
        if not read_db(guid, key):
            return None
        db_in_json[guid_str][key] = new_value
    except KeyError:
        return None
    result = json.dumps(db_in_json, indent=2)
    
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
        (str | None): Returns updated database as string or None, 
        if you key already existed.
    """
    guid_str = str(guid)
    
    # If key is already present in database
    if read_db(guid, key):
        return None
    
    try:
        with open(DATABASE_NAME, READ_FLAG) as f:
            db_in_json = json.load(f)
    except OSError:
        return None
    
    db_in_json[guid_str][key] = value
    to_save = json.dumps(db_in_json, indent=2)
    
    try:
        with open(DATABASE_NAME, WRITE_FLAG) as f:
            f.write(to_save)
            return db_in_json
    except OSError:
        return None
    
if __name__ == "__main__":
    print(read_db(907946271946440745, "prefix"))
    print(insert_db(907946271946440745, "auto-role", "<@&1005976398420267008>"))
    
    d = {"pes": 1}
    a = frozenset(d)
    try:
        a["kocka"] = 2
    except:
        pass
    print(a)
    