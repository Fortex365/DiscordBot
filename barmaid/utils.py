import discord

def create_embed(title, description):
        embed = discord.Embed(title=title, description=description)
        return embed