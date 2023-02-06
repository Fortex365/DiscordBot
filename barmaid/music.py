import utilities as S
import discord
import asyncio
import requests
import random
import youtube_dl
from discord.ext import commands

"""
Client instance loaded after barmaid.load_extensions() passes its instance into
music.setup().
"""
CLIENT:commands.Bot = None
_voice_clients = {}
_queues = {}
_yt_dl_options = {'format': 'bestaudio/best'}
_ytdl = youtube_dl.YoutubeDL(_yt_dl_options)
_ffmpeg_options = {"options": "-vn"}
_JUKEBOX_ERROR = "Sorry, something unexpected sent wrong with jukebox." \
    " Please try again later."

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def play(ctx:commands.Context, url:str):
    """Adds the song to play in jukeboox.

    Args:
        ctx (commands.Context): Invoke context
        url (str): Music url. YouTube only.
    """
    await ctx.defer(ephemeral=True)
    # connect to voice channel if not already connected
    voice_client = _voice_clients.get(ctx.guild.id)
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()
        _voice_clients[ctx.guild.id] = voice_client

    # add the new URL to the queue
    queue = _queues.get(ctx.guild.id)
    if not queue:
        queue = asyncio.Queue()
        _queues[ctx.guild.id] = queue
    await queue.put(url)

    # start playing the next song if not already playing
    if not voice_client.is_playing():
        await play_next(ctx)
        await ctx.send("Jukebox started!",
                        ephemeral=True, delete_after=S.DELETE_EPHEMERAL)
    await ctx.send("Added to queue!", ephemeral=True, 
                   delete_after=S.DELETE_EPHEMERAL)

async def play_next(ctx:commands.Context):
    """Helper function that provides playing music in the right voice client 
    from its queue and handles callback for playing the next in queue.

    Args:
        ctx (commands.Context): _description_
    """
    queue = _queues[ctx.guild.id]
    url = await queue.get()

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: _ytdl.extract_info(url, download=False)) # meanwhile v loopu může běžet něco jiného než se extract dokončí
    music = data["url"]
    player = discord.FFmpegPCMAudio(music, **_ffmpeg_options)
    if not player.is_opus():
        player = discord.PCMVolumeTransformer(player, volume=1.0)
        
    voice_client = _voice_clients[ctx.guild.id]
    voice_client.play(player, after=lambda e:
        asyncio.run_coroutine_threadsafe(play_next(ctx), loop=loop))
    voice_client.player = player

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def play_playlist(ctx:commands.Context, playlist_url: str, shuffle=False):
    """Plays playlist.

    Args:
        ctx (commands.Context): Invoke context
        playlist_url (str): URL containing a playlist
        shuffle (bool, optional): Whether shuffle or not. Defaults to False.
    """
    await ctx.defer(ephemeral=True)
    await ctx.send(f"May take some time if playlist is huge. " + 
                   "Will start playing as soon as it's ready!")
    # retrieve the list of URLs in the playlist

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda:
        _ytdl.extract_info(playlist_url, download=False))
    urls = [entry["url"] for entry in data["entries"]]

    # shuffle the list of URLs if shuffle is True
    if shuffle:
        random.shuffle(urls)

    # add the first x songs to the queue for the current guild and start playing
    queue = _queues.get(ctx.guild.id)
    if not queue:
        queue = asyncio.Queue()
        _queues[ctx.guild.id] = queue
    for url in urls:
        await queue.put(url)

    voice_client = _voice_clients.get(ctx.guild.id)
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()
        _voice_clients[ctx.guild.id] = voice_client
    if not voice_client.is_playing():
        await play_next(ctx)
        await ctx.interaction.followup.send("Playlist started!",
                                            ephemeral=True,
                                            delete_after=S.DELETE_EPHEMERAL)
            
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def stop(ctx:commands.Context):
    """Stops the jukebox and disconnects the bot from voice.

    Args:
        ctx (commands.Context): Invoke context.
    """
    await ctx.defer(ephemeral=True)
    try:
        _voice_clients[ctx.guild.id].stop()
        await _voice_clients[ctx.guild.id].disconnect()
    except:
        await ctx.send(_JUKEBOX_ERROR,
                       ephemeral=True, delete_after=S.DELETE_EPHEMERAL)

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def pause(ctx:commands.Context):
    """Pauses the jukebox.

    Args:
        ctx (commands.Context): Invoke context.
    """
    await ctx.defer(ephemeral=True)
    try:
        _voice_clients[ctx.guild.id].pause()
    except:
        await ctx.send(_JUKEBOX_ERROR,
                       ephemeral=True, delete_after=S.DELETE_EPHEMERAL)

@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def resume(ctx:commands.Context):
    """Resumes the jukebox.

    Args:
        ctx (commands.Context): Invoke context.
    """
    await ctx.defer(ephemeral=True)
    try:
        _voice_clients[ctx.guild.id].resume()
    except:
        await ctx.send(_JUKEBOX_ERROR,
                       ephemeral=True, delete_after=S.DELETE_EPHEMERAL)  

@commands.command(with_app_command=True)
@commands.guild_only()
async def skip(ctx: commands.Context):
    """Skips the current playing song.
    
    Args:
        ctx (commands.Context): Invoke context
    """
    await ctx.defer(ephemeral=True)
    voice_client:discord.VoiceClient = _voice_clients.get(ctx.guild.id)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await play_next(ctx)
        await ctx.send("Song skipped!",
                       ephemeral=True, delete_after=S.DELETE_EPHEMERAL)
    else:
        await ctx.send("Nothing is currently playing.")
              
@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def volume(ctx:commands.Context, volume:int):
    """Sets the volume of the bot in voice channel.

    Args:
        ctx (commands.Context): Invoke context
        volume (int, optional): New % volume value. Defaults to 100.
    """
    await ctx.defer(ephemeral=True)
    try:
        vc:discord.VoiceClient = _voice_clients[ctx.guild.id]
    except KeyError:
        await ctx.send("Not playing!", delete_after=S.DELETE_EPHEMERAL)
        return
    if vc.is_playing() or vc.is_paused():
        if volume > 0 and volume < 101:
            try:
                vc.player.volume = volume / 100
            except:
                await ctx.send(_JUKEBOX_ERROR, ephemeral=True,
                   delete_after=S.DELETE_EPHEMERAL)
                return
            await ctx.send("Success!", ephemeral=True,
                           delete_after=S.DELETE_EPHEMERAL)
                   
async def setup(bot:commands.Bot):
    """Setup function which allows this module to be an extension
    loaded into the main file.

    Args:
        bot: The bot instance itself, passed in
        from barmaid.load_extention("minihames").
    """
    global CLIENT
    
    bot.add_command(play)
    bot.add_command(play_playlist)
    bot.add_command(stop)
    bot.add_command(pause)
    bot.add_command(resume)
    bot.add_command(volume)

    CLIENT = bot

if __name__ == "__main__":
    """In case of trying to execute this module, nothing should happen.
    """
    pass