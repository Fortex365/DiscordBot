from jsonyzed_db import read_db, insert_db, update_db

print(read_db(907946271946440745, "prefix"))
print(insert_db(907946271946440745, "auto-role", "<@&1005976398420267008>"))
print(update_db(907946271946440745, "auto-role", "test"))
