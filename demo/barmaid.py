import discord
from discord.ext import commands
import os

import random
import emoji

import http.client
import json
import urllib.parse

from keep_alive import keep_alive

client = commands.Bot(command_prefix = '.')


@client.event
async def on_ready():
    print("Bot successfully logged in {0.user}".format(client))
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Game(name="Your local bartender!"))


@client.event
async def on_member_join(member):
    print(f'{member} has joined the server.')


@client.event
async def on_member_leave(member):
    print(f'{member} has left the server.')


@client.event
async def on_member_remove(member):
    print(f'{member} has been kicked from the server.')


@client.event
async def on_message(message):
    #_print_mentions_in_msg(message)  #Vypíše do konzole nick+id všech mentions

    #Když bot sám pošle zprávu tak taky reaguje na tento event tak, že nechceme, aby na něj nic prováděl
    if message.author == client.user:
        return

    #---------------------
    #Když botovi píšete DM
    greatings = [
        "Ahoj", "Čau", "Cau", "čau", "cau", "ahoj", "dobrý den", "Dobrý den",
        "zdravím", "Zdravím", "čus", "Čus", "ahoy", "ahojda", "Ahojda", "Ahoy",
        "čauko", "Čauko","howdy","howdy?","Howdy","Howdy?"
    ]
    bot_greatings = [
        "Ahoj", "Ahoy!", "Těší mě!","Howdy!",
        emoji.emojize("Ahoj, pane :slight_smile:"),
        emoji.emojize("Čauky :slight_smile:")
    ]

    if not message.guild:
        msg = message.content

        if _exists_in_list(greatings, msg):  #Když bota pozdravíte
            if msg == "Čauko" or msg == "čauko":
                await message.channel.send(emoji.emojize("Čauko kakauko :joy:"))
                return
            else:
                await message.channel.send(random.choice(bot_greatings))
                return

        #Když bot zprávu nezná, tedy je kompletně náhodná (utahuje si z vás random uppercasem a papouškuje)
        mocking = ''.join(
            random.choice((str.upper, str.lower))(char) for char in
            msg)  #Náhodně nahradí k původní zprávě uppercase písmena
        await message.channel.send(mocking)

    await client.process_commands(message)


#---------------------------
#INTERNAL FUNCTIONS SECTION
#---------------------------


#Interní funkce která vrací zda se v daném seznamu nachází value, predikát
def _exists_in_list(arr, value):
    for i in arr:
        if i == value:
            return True
    return False


#Interní Funkce vypisujici do konzole jméno a discord id
def _print_mentions_in_msg(message):
    mentions = message.mentions
    #print(mentions)  #Vypíše celé pole ve kterém je datová struktura user

    for i in mentions:
        print("Jméno: " + str(i.nick) + " jeho disc id: " + str(i.id))


#--------------------------------
#COMMAND EVENTS SECTION
#--------------------------------


#Ping bota, nikoliv tazatele
@client.command()
async def ping(ctx):
    if ctx.message.guild != None: #Když to není DM
      await ctx.send(f'Pong! {round(client.latency*1000)}ms')


@client.command(aliases=['8ball'])
async def _8ball(ctx, *, q):
    conn = http.client.HTTPSConnection("8ball.delegator.com")
    question = urllib.parse.quote(q)
    conn.request('GET', '/magic/JSON/' + question)
    response = conn.getresponse()
    json_response = json.loads(response.read())
    unwrap = json_response['magic']
    answer = unwrap['answer']

    if ctx.message.guild != None: #Když to není DM
      await ctx.send(f'Q: {q}\nA: {answer}')

@client.command(aliases=['roll'])
async def deathroll(ctx, num):
  num_int = int(num)
  res = random.randint(1,num_int)
  if res > 1:
    await ctx.send(f'<@{ctx.message.author.id}> deathrolled {str(res)}. Range[1-{num}]')
  else:
    await ctx.send(f'<@{ctx.message.author.id}> deathrolled {str(res)} and LOST! Range[1-{num}]')



#--------------------------------
#CODE RUN SECTION
#--------------------------------

#Vytvoření webového serveru, který hosting pinguje co 5m, aby bot byl nepřetržitě aktivní. Repl.it po zavření okna v prohlížeči by nechal pouze hodinu běžet náš program
keep_alive()
#Připojení bota do discord serveru
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
client.run(TOKEN)
