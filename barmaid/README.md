# Discord Bot whose name is `Barmaid`
Do you like inn enviroment with barmans or barmaids serving you drinks all night long? :beer:
Are you looking into discord bot with any soul for your discord server? :ghost:

Barmaid has one! Barmaid Bot will roleplay her role on your server. Kind of.


## Code asignment [CZ]:
```Student napíše Bota pro komunikační platformu Discord, v programovacím jazyce Python.
Student zároveň s tím vyřeší požadavek na hosting Bota pro jej nepřetržitý provoz.
Bot by měl sloužit k obecným potřebám různorodých komunit využívající tuto platformu, 
např. Bot bude zprostředkovávat vytváření a plánování eventů pro uživatele komunity a jejich účasti 
na daném eventu. Dále bude Bot sloužit jako administrátorský nástroj pro administrátora komunity např. 
hromadné mazání a posílání zpráv, hromadné přesouvání uživatelů, a samotné zprostředkování pravidel pro komunitu.
V neposlední řadě bude Bot moci streamovat v tzv. Voice Channels hudbou zadanou odkazem např. ze Spotify, Youtube.
```

## Code asignment [EN]:
```
Student will code a bot for Discord platform in Python language. Student will also resolve it's own hosting.
Bot should be used as a general purpose tool for the variety communities using Discord nowadays.
Should be able to create a event on server and manage it for the server. (Sign in/Sign out of event, logging their attendance).
Next, it should be a tool of some kind for administators on the server, which they can use to mass message everyone on the server, mass member movement, and last but not least - manage the rules for the server.
Lastly, what bot could do is to stream music via Voice Channels on server passed by URL eg. Spotify, Youtube.
```
# The default prefix bot reacts on server is `..`

Example:
```
..ping
>>> Pong! Latency is 0ms.
```
# Main module `barmaid.py`
Brief overview what the module does:
- Sets up the client permissions
- Sets up client extensions
- Sets up client itself

# Module `admin_tools.py`
List of all commands in this module:

- `ping` - Outputs the ping between the client and the server.
- `clear` - Clears the number of messages in the channel. *Permission required.*
- `invoker_id` Sends the discord member number identificator to direct message. *Permission required.*
- `guid` - Sends guild identification number to direct message. *Permission required.*
- `prefix` - Responds with the current prefix is set on the server.
    - `prefix set` - Sets the new prefix for the server. *Permission required.*
- `kick` - Kicks the user from the server. *Permission required.*

Example:
```
<prefix>kick @user
>>> Kicked @user! Reason: No reason provided 

By: @user
```
- `ban` - Bans the user from the server. *Permission required.*
- `echo` - Echoes the message.

## Module `minigames.py`
List of all commands in this module:

- `deathroll` - Play a deathroll game.
    - `deathroll rules` - Show the rules for the game


- `git` - Play the pseudo-git game. *Does nothing interesting.*
    - `git push` - Explore yourself.
