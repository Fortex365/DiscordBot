msg = {
    "DELETE_HOUR": 3600,
    "DELETE_ORDINARY_MESSAGE": 15,
    "DELETE_COMMAND_ERROR": 15,
    "DELETE_EMBED_ORDINARY": 300,
    "DELETE_EMBED_SYSTEM": 3600
}

act = {
    "CLIENT_ACTIVITY": "Your local e-Barmaid"
}

d = {
    "DeleteMessages": msg,
    "Activity": act
}

#import json
#
#jobj = json.dumps(d, indent=2)
#with open("config.json", "w") as f:
#    f.write(jobj)
#
#with open("config.json", "r") as a:
#    data = json.load(a)
#    print(data)

dict = {
    "data": 1
}

from json_db import read_db, update_db, insert_db

print(read_db(907946271946440745, "ahoj"))
print(update_db(1, "ahoj", 5))