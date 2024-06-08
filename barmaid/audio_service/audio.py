import data_service.config_service as S
import discord
import asyncio
import random
import yt_dlp
from log_service.setup import setup_logging
from discord.ext import commands, tasks

log = setup_logging()
CLIENT: commands.Bot = None
_voice_clients = {}
_queues = {}
_list_names = {}
_volumes = {}
_yt_dl_options = {
    'format': 'bestaudio/best',
    'ignoreerrors': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '96',
    }],
}
_ytdl = yt_dlp.YoutubeDL(_yt_dl_options)
_ffmpeg_options = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}
_JUKEBOX_ERROR = "Sorry, something unexpected went wrong with jukebox. Please try again later."
TIMEOUT_SECONDS = 600
_last_active_time = {}


async def connect_to_voice_channel(ctx):
    """Connects to the voice channel of the command's author if not already connected."""
    if not ctx.author.voice:
        await ctx.send("You're not connected to voice.", delete_after=S.DELETE_COMMAND_ERROR)
        return None

    voice_client = _voice_clients.get(ctx.guild.id)
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect(timeout=30, reconnect=True)
        _voice_clients[ctx.guild.id] = voice_client
        log.info(f"Connecting success: to {ctx.author.voice.channel.name} in {ctx.guild.name}")
    return voice_client


async def add_to_queue(ctx, url):
    """Adds the given URL to the guild's music queue."""
    queue = _queues.get(ctx.guild.id)
    if not queue:
        queue = asyncio.Queue()
        _queues[ctx.guild.id] = queue
    await queue.put(url)


async def fetch_song_info(url):
    """Fetches song information from YouTube."""
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: _ytdl.extract_info(url, download=False, process=False))
        return data
    except yt_dlp.DownloadError as download_error:
        return f"Download error: {str(download_error)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


async def play_next(ctx):
    """Plays the next song in the queue."""
    global _last_active_time
    queue = _queues.get(ctx.guild.id)
    if queue is None or queue.empty():
        return

    try:
        url = await queue.get()
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: _ytdl.extract_info(url, download=False))
        
        if not data:
            await ctx.send("Could not retrieve song data. Skipping...", delete_after=S.DELETE_EPHEMERAL)
            return

        music_url = data.get("url")
        if not music_url:
            await ctx.send("Could not extract music URL. Skipping...", delete_after=S.DELETE_EPHEMERAL)
            return

        player = discord.FFmpegPCMAudio(music_url, **_ffmpeg_options)
        if not player.is_opus():
            player = discord.PCMVolumeTransformer(player, volume=_volumes.get(ctx.guild.id, 1.0))

        voice_client = _voice_clients.get(ctx.guild.id)
        if not voice_client:
            await ctx.send("Voice client not found. Skipping...", delete_after=S.DELETE_EPHEMERAL)
            return

        # Define the after callback correctly
        def after_callback(error):
            if error:
                log.error(f"Error in after callback: {error}")
            future = asyncio.run_coroutine_threadsafe(play_next(ctx), loop)
            try:
                future.result()  # Block until the coroutine is done
            except Exception as e:
                log.error(f"Error running play_next: {e}")

        voice_client.play(player, after=after_callback)
        voice_client.player = player
        voice_client.now_playing = data.get("title", "Unknown Title")
        _last_active_time[ctx.guild.id] = asyncio.get_event_loop().time()
        log.info(f"Playing success: {voice_client.now_playing}, at {ctx.guild.name}")

    except Exception as e:
        log.error(f"Error in play_next: {e}")
        await ctx.send(_JUKEBOX_ERROR, delete_after=S.DELETE_COMMAND_ERROR)


async def play_music(ctx, url):
    """Handles playing music by adding to queue and starting playback if necessary."""
    voice_client = await connect_to_voice_channel(ctx)
    if not voice_client:
        return

    await add_to_queue(ctx, url)
    song_info = await fetch_song_info(url)
    if isinstance(song_info, str):
        await ctx.send(song_info, delete_after=S.DELETE_COMMAND_ERROR)
        return

    song_name = song_info["title"]
    _list_names.setdefault(ctx.guild.id, []).append(song_name)
    _last_active_time[ctx.guild.id] = asyncio.get_event_loop().time()

    if not voice_client.is_playing():
        await play_next(ctx)
        await ctx.send("Jukebox started!", delete_after=S.DELETE_EPHEMERAL)
    else:
        await ctx.send("Added to queue!", delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def play(ctx: commands.Context, url: str):
    await ctx.defer(ephemeral=True)
    await play_music(ctx, url)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def play_playlist(ctx: commands.Context, playlist_url: str, shuffle=False):
    await ctx.defer(ephemeral=True)
    voice_client = await connect_to_voice_channel(ctx)
    if not voice_client:
        return

    await ctx.send("May take some time if playlist is huge. Will start playing as soon as it's ready!", delete_after=S.DELETE_MINUTE)
    data = await fetch_song_info(playlist_url)
    if isinstance(data, str):
        await ctx.send(data, delete_after=S.DELETE_COMMAND_ERROR)
        return

    urls = [entry["url"] for entry in data.get("entries", []) if entry]
    song_names = [entry["title"] for entry in data.get("entries", []) if entry]
    if shuffle:
        random.shuffle(urls)

    _list_names.setdefault(ctx.guild.id, []).extend(song_names)
    for url in urls:
        await add_to_queue(ctx, url)

    _last_active_time[ctx.guild.id] = asyncio.get_event_loop().time()
    if not voice_client.is_playing():
        await play_next(ctx)
        await ctx.interaction.followup.send("Playlist started!", ephemeral=True, delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def stop(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    try:
        voice_client = _voice_clients.pop(ctx.guild.id, None)
        if voice_client:
            voice_client.stop()
            await voice_client.disconnect()
        _last_active_time.pop(ctx.guild.id, None)
        await ctx.send("Jukebox ended.", delete_after=S.DELETE_EPHEMERAL)
    except Exception:
        await ctx.send(_JUKEBOX_ERROR, ephemeral=True, delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def pause(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    try:
        _voice_clients[ctx.guild.id].pause()
        await ctx.send("Jukebox paused!", delete_after=S.DELETE_EPHEMERAL)
    except Exception:
        await ctx.send(_JUKEBOX_ERROR, ephemeral=True, delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def resume(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    try:
        _voice_clients[ctx.guild.id].resume()
        _last_active_time[ctx.guild.id] = asyncio.get_event_loop().time()
        await ctx.send("Jukebox resumed!", delete_after=S.DELETE_EPHEMERAL)
    except Exception:
        await ctx.send(_JUKEBOX_ERROR, ephemeral=True, delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def next(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    voice_client = _voice_clients.get(ctx.guild.id)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        _last_active_time[ctx.guild.id] = asyncio.get_event_loop().time()
        await play_next(ctx)
        await ctx.send("Song skipped!", delete_after=S.DELETE_EPHEMERAL)
    else:
        await ctx.send("Nothing is currently playing.", delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def volume(ctx: commands.Context, volume: int):
    await ctx.defer(ephemeral=True)
    try:
        voice_client = _voice_clients[ctx.guild.id]
        if voice_client.is_playing() or voice_client.is_paused():
            if 0 < volume < 101:
                voice_client.player.volume = volume / 100
                await ctx.send("Success!", ephemeral=True, delete_after=S.DELETE_EPHEMERAL)
                _volumes[ctx.guild.id] = volume / 100
    except KeyError:
        await ctx.send("Not playing!", delete_after=S.DELETE_EPHEMERAL)
    except Exception:
        await ctx.send(_JUKEBOX_ERROR, ephemeral=True, delete_after=S.DELETE_COMMAND_ERROR)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def queue(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    names = _list_names.get(ctx.guild.id)
    if not names:
        await ctx.send("No songs waiting in the queue.", delete_after=S.DELETE_EPHEMERAL)
        return

    message = "Songs in the queue:\n"
    for i, name in enumerate(names[:15], 1):
        message += f"{i}. {name}\n"
    await ctx.send(message, delete_after=S.DELETE_MINUTE)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def shazam(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    try:
        song = _voice_clients[ctx.guild.id].now_playing
        await ctx.send(f"Song: `{song}`", delete_after=S.DELETE_MINUTE)
    except KeyError:
        await ctx.send("Not playing!", delete_after=S.DELETE_EPHEMERAL)


@commands.hybrid_command(with_app_command=True)
@commands.guild_only()
async def shuffle_queue(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    queue = _queues.get(ctx.guild.id)
    names = _list_names.get(ctx.guild.id)
    if not queue or queue.empty() or not names:
        await ctx.send("Queue is empty or not initialized.", delete_after=S.DELETE_EPHEMERAL)
        return

    queue_list = list(queue._queue)
    random.shuffle(queue_list)
    _queues[ctx.guild.id] = asyncio.Queue()
    for item in queue_list:
        await _queues[ctx.guild.id].put(item)

    random.shuffle(names)
    _list_names[ctx.guild.id] = names
    await ctx.send("Queue shuffled!", delete_after=S.DELETE_EPHEMERAL)


@tasks.loop(minutes=1)
async def check_inactivity():
    current_time = asyncio.get_event_loop().time()
    for guild_id, last_active in list(_last_active_time.items()):
        if current_time - last_active > TIMEOUT_SECONDS:
            voice_client = _voice_clients.get(guild_id)
            if voice_client and not voice_client.is_playing():
                await voice_client.disconnect()
                del _voice_clients[guild_id]
                del _last_active_time[guild_id]
                log.info(f"Disconnected due to inactivity: {guild_id}")


@check_inactivity.before_loop
async def before_check_inactivity():
    await CLIENT.wait_until_ready()


async def setup(bot: commands.Bot):
    global CLIENT

    bot.add_command(play)
    bot.add_command(play_playlist)
    bot.add_command(stop)
    bot.add_command(pause)
    bot.add_command(resume)
    bot.add_command(volume)
    bot.add_command(queue)
    bot.add_command(next)
    bot.add_command(shazam)
    bot.add_command(shuffle_queue)  # Add shuffle_queue command
    CLIENT = bot
    check_inactivity.start()


if __name__ == "__main__":
    pass
