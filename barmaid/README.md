# Barmaid Bot

The default prefix is `..`

To invoke commands you do such as:
```
..ping
>>> Pong!
```

## module `admin_tools.py`
List of all commands in this module:


- `ping` - Outputs the ping between the client and the server.
```
<prefix>ping
>>> Pong! Latency: 1 miliseconds!
```

- `clear` - Clears the number of messages in the channel.

- `kick` - Kicks the user from the server.
```
<prefix>kick @user
>>> Kicked @user!

Reason: No reason provided 

By: @user
```

---
List of non-listed commands in this module:


- `_echo` - Echoes the message.
```
<prefix>_echo This is a test message.
>>> This is a test message.
```

- `_invoker_id` - Sends the id discord representation of message author into his DMs.
```
<prefix>_invoker_id
>>>DM<<< <your_discord_user_id>
```

- `_dmall` - Secret. Not implemented.


## module `minigames.py`
List of all commands in this module:

- `deathroll` - Outputs a random deathrolled number by given range, or tells if you lost.
```
<prefix>deathroll
>>> @user deathrolled x. Range[1 - 1,000]
```

```
<prefix> deathroll 5
>>> @user deathrolled 1 and LOST! Range[1 - 5]
```

- `deathroll rules` - Subcommand for deathroll, informs about the game rules.
```
<prefix>deathroll rules
>>> Two players sets a bet typically for money. They use that amount of money and multiply it by 10, 100 or 1000 to make the starting rolling number higher so the game doesn't end too quick. Any player can decide to start and rolls that result number from multiplication. The randomly rolled number must the other player use as the new rolling upperbounds. First player whom reaches number 1 loses.

```

- `git` - Pseudo-git messaging game.
```
<prefix>git
>>> Invalid git command passed...
```

- `git push` - Subcommand of git for pushing the data to git servers.
```
<prefix>git push
>>> Invalid push arguments passed...
```

```
<prefix>git push origin master
>>> Pushing to origin master
```
