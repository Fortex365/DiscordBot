# Discord Bot whose name is `Barmaid`
Do you like inn enviroment with barmans or barmaids serving you drinks all night long? :beer:
Are you looking into discord bot with any soul for your discord server? :ghost:

Barmaid has one! Barmaid Bot will roleplay her role on your server. Kind of.
Also if you hate how command invocation messages and some responses are left in the text channel, don't worry -- Barmaid has got you covered.

[:envelope: Invitation](https://discord.com/oauth2/authorize?client_id=821538075078557707&permissions=8&scope=bot%20applications.commands)

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

# Configuration file `config.json`
Can look something like this:
```json
{
  "DeleteMessages": {
    "DELETE_COMMAND_INVOKE": 15,
    "DELETE_COMMAND_ERROR": 25,
    "DELETE_EMBED_POST": 300,
    "DELETE_EMBED_HELP": 120
  },
  "Activity": {
    "CLIENT_ACTIVITY": "Your local e-Barmaid"
  }
}
```
You can modify this data to your own liking:
- "DELETE_COMMAND_INVOKE" - Regular message (respond to command) until its deletion. *Number: time in seconds.*
- "DELETE_COMMAND_ERROR" - Regular error message (respond to command) until its deletion. *Number: time in seconds.*
- "DELETE_EMBED_POST" - Important message (respond to command, announce etc.) until its deletion. *Number: time in seconds.*
- "DELETE_EMBED_HELP" - Command help message until its deletion. *Number: time in seconds.*
- "CLIENT_ACTIVITY" - Activity bot is showing up as "Playing now". (Cannot be per server.) *String: a sequance beginning and ending with ".*

# Module `events.py`

List of all commands in the module:

- `event` - create event into discord intergrated events
  - `event simple` - create not integrated dc events, but embed message type

# Module `admin_tools.py`
List of all commands in this module:

- `ping` - Outputs the ping between the client and the server.
- `clear` - Clears the number of messages in the channel. *Permission required.*
- `invoker_id` Sends the discord member number identificator to direct message. *Permission required.*
- `echo` - Echoes the message.
- `guid` - Sends guild identification number to direct message. *Permission required.*
- `prefix` - Responds with the current prefix is set on the server.

  - `setprefix` - Sets the new prefix for the server. *Permission required.*
- `kick` - Kicks the user from the server. *Permission required.*

  Example:
  ```
  <prefix>kick @user
  >>> Kicked @user! Reason: No reason provided 

  By: @user
  ```
  - `kick more` - mentions multiple users to kick
- `ban` - Bans the user from the server. *Permission required.*
  - `ban more` - Bans multiple users
- `move` - Moves all connected members from channel1 to channel2. *Permission required.*
  - `move users` - move multiple mentioned people
  - `move help` - Gives you help for the command.
- `massdm` - Sends direct message to all server members. *Disclaimer: owner only, small servers only.* Otherwise it would be against Discord ToS (spam, phishing).
  - `massdm embed` - allows to send embed message
- `rules` - Shows the server enforced rules. Rules are sent for each member who joins the server.
  - `rules set` - Set the new rules. *Permissions required.*
- `invite` - Allows you share bot with your friends.
- `finvite` - Allows you easily to invite friends to your server.
  - `finvite help` - Help for command usage.
- `autorole` - Set the role to auto-asign when new member joins server.
  - `autorole help` - Help for command usage.
  - `autorole set` - Set the role to asign.
  - `autorole remove` - Remove role to asign.
- `filter` - Gets blacklisted words on a server
  - `filter add` - adds new words to blacklist
  - `filter remove` - removes word from blacklist




## Module `minigames.py`
List of all commands in this module:

- `deathroll` - Play a deathroll game.
    - `deathroll rules` - Show the rules for the game


- `git` - Play the pseudo-git game. *Does nothing interesting.*
    - `git push` - Explore yourself.
