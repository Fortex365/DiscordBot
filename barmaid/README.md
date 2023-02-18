# Discord Bot whose name is `Barmaid`
Do you like inn enviroment with barmans or barmaids serving you drinks all night long? :beer:
Are you looking into discord bot with any soul for your discord server? :ghost:

Barmaid has one! Barmaid Bot will roleplay her role on your server. Kind of.
Also if you hate how command invocation messages and some responses are left in the text channel, don't worry -- Barmaid has got you covered.

[:envelope: Invitation](https://discord.com/oauth2/authorize?client_id=821538075078557707&permissions=8&scope=bot%20applications.commands)

## Code asignment [CZ]:
```
Student napíše Bota pro komunikační platformu Discord, v programovacím jazyce Python.
Student zároveň s tím vyřeší požadavek na hosting Bota pro jej nepřetržitý provoz.
Bot by měl sloužit k obecným potřebám různorodých komunit využívající tuto platformu, 
např. Bot bude zprostředkovávat vytváření a plánování eventů pro uživatele komunity a jejich účasti 
na daném eventu. Dále bude Bot sloužit jako administrátorský nástroj pro administrátora komunity např. 
hromadné mazání a posílání zpráv, hromadné přesouvání uživatelů, a samotné zprostředkování pravidel pro komunitu.
V neposlední řadě bude Bot moci streamovat v tzv. Voice Channels hudbu zadanou odkazem např. ze Spotify, Youtube.
```

## Code asignment [EN]:
```
Student will code a bot for Discord platform in Python language. Student will also resolve it's own hosting.
Bot should be used as a general purpose tool for the variety communities using Discord nowadays.
Should be able to create a event on server and manage it for the server. (Sign in/Sign out of event, logging their attendance).
Next, it should be a tool of some kind for administators on the server, which they can use to mass message everyone on the server, mass member movement, and last but not least - manage the rules for the server.
Lastly, what bot could do is to stream music via Voice Channels on server passed by URL eg. Spotify, Youtube.
```

# To host bot on your own
Make sure your machine's running `Python 3.9+`, you can download it [here](https://www.python.org/).


Installing Python for Linux:
```
sudo apt install python3-pip
```
To quickly check whether you've Python installed:
```
python --version
```
To install any requirements needed:
```
 pip install -r requirements.txt
```

Make sure you have `FFmpeg` installed and added to the PATH enviroment variables. You can download it [here](https://www.ffmpeg.org/).

For Linux its:
```
sudo apt install ffmpeg
```

Visit [Discord Developer Portal](https://discord.com/developers/applications) and create new application there and save it's  `token`. KEEP IT SECRET!

For Mac/Linux:
```
export DISCORD_BOT_TOKEN=your_token_here
```
For Windows [little more for that here](https://phoenixnap.com/kb/windows-set-environment-variable):
```
setx DISCORD_BOT_TOKEN="your_token_here"
```
Once again from [Discord Developer Portal](https://discord.com/developers/applications) create an invitation link to add your bot to discord servers. Give it `administrator` and select scope to `application.commands.` Copy generated invite link and fill accordingly to config.

Open `config.json` and edit the following `BOT_URL_AUTH_HEADER, BOT_INVITE_URL, BOT_ID`:
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
  },
  "DATABASE_FILE_NAME": "data.json",
  "GLOBAL_NAUGHTY_LIST": "naughty_list.json",
  "BOT_URL_AUTH_HEADER": "https://discord.com/oauth2/authorize?client_id=821538075078557707",
  "BOT_INVITE_URL": "https://discord.com/api/oauth2/authorize?client_id=821538075078557707&permissions=8&scope=bot%20applications.commands",
  "BOT_ID": 821538075078557707
}
```
After you're done editting, it's time to run it!
```
python .\barmaid
```
For running script on Linux server I suggest you to use `screen` first to make the script running even after your session from server is abandoned. Then you can `Ctrl + A + D` to detach from session before you close [PuTTY](https://www.putty.org/).
```
> screen
> python barmaid.py
```
For next resuming the previous session after connecting again to server use:
```
screen -r
```

# The default prefix bot reacts on server is `..`
:heavy_exclamation_mark::heavy_exclamation_mark::heavy_exclamation_mark:It's suggested to use in-app slash commands.:heavy_exclamation_mark::heavy_exclamation_mark::heavy_exclamation_mark:

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
    "CLIENT_ACTIVITY": ["Your Barmaid!",
     "Serving drinks!",
      "Local Pub."]
  }
}
```
You can modify this data to your own liking:
- "DELETE_COMMAND_INVOKE" - Regular message (respond to command) until its deletion. *Number: time in seconds.*
- "DELETE_COMMAND_ERROR" - Regular error message (respond to command) until its deletion. *Number: time in seconds.*
- "DELETE_EMBED_POST" - Important message (respond to command, announce etc.) until its deletion. *Number: time in seconds.*
- "DELETE_EMBED_HELP" - Command help message until its deletion. *Number: time in seconds.*
- "CLIENT_ACTIVITY" - Activity bot is showing up as "Playing now". (Cannot be per server.) *List: containing several strings".*

# Overview of commands:

- rules, addrule, delrule, reset-rules

- autorole [show, remove, set]

- play, play-playlist, pause, stop, resume, volume, queue

- admin [message, embedded]

- ban, kick, naughty

- invite, bot

- events [ivoice, ilocation, echat]

- filter [show, remove, add]

- moderation [show, add, reset]

- move

- ping, id, guid, echo

- prefix, setprefix

