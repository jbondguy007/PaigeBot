import discord
import os
from discord import message
import platform
import requests

from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, time as datetime_time, timedelta
from giphy_client.rest import ApiException
from pprint import pprint

# BOT INFO

botname = "Paige"
prefixes = ("p!", "!paige ")
bot_birthdate = "February 20, 2023"
bot_platform = [platform.system(), platform.release(), platform.python_version()]

# VARIABLES

embed_color = 0x0044bb

# CONFIG
bot = commands.Bot(command_prefix=prefixes, help_command=None, intents=discord.Intents.all())
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# FUNCTIONS

def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def sg_names_checker(users):

    results = []
    fake_users = []

    for user in users:

        link = f"https://www.steamgifts.com/user/{str(user)}"

        r = requests.get(link)
        redirected = True if r.status_code == 404 else r.url != link

        results.append({user: redirected})

        if redirected:
            fake_users.append(user)
    
    return(fake_users)

# BOT EVENTS

@bot.event
async def on_ready():
    print("Logged in as {}".format(bot.user, bot.command_prefix))
    print("Ready!")
    await bot.change_presence(status=discord.Status.online)
    await bot.change_presence(activity=discord.Game("Prefix: p!"))
    
@bot.event
async def on_command_error(ctx, error):
    await ctx.send("<:warning:1077420799713087559> Failure to process:\n`{}`".format(str(error)))

# ON MESSAGE

@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        return

    await bot.process_commands(message)

# COMMANDS

@bot.command()
async def test(ctx):
    await ctx.send("Test successful.")

@bot.command()
async def info(ctx):
    await ctx.send(f"Hi, {botname} here communicating to you from <@172522306147581952>'s {platform.system()} {platform.release()}! I was born on {bot_birthdate}, and am running on Python v{platform.python_version()}.\n\nI'm happy to help, just issue the command `p!help` for a list of commands.")

@bot.command()
async def threads(ctx):
    await ctx.send("Main thread: <https://www.steamgifts.com/discussion/sjQKU/>\n")

@bot.command()
async def rules(ctx):
    await ctx.send("<https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/3/3758852249517826899/>")

# HELP COMMANDS

@bot.command()
async def help(ctx):

    embedVar = discord.Embed(title="Commands", description="", color=embed_color)
    embedVar.add_field(name="test", value="Simple test command. Check if the bot is alive!", inline=False)
    embedVar.add_field(name="help", value="Displays this message.", inline=False)
    embedVar.add_field(name="info", value=f"Information about me, {botname}!", inline=False)
    embedVar.add_field(name="threads", value="Lists relevant Steamgifts threads.", inline=False)
    embedVar.add_field(name="rules", value="Provides a link to the rules.", inline=False)
    await ctx.send(embed=embedVar)

# MODERATOR COMMANDS

@bot.command()
@commands.has_any_role("Staff", "Founders")
async def checkvotes(ctx, *users):
    await ctx.send("Processing...")
    fake_users = sg_names_checker(users)
    fake_users = "\n".join(fake_users)
    await ctx.send(f"**Fake users:**\n{fake_users}")

bot.run(TOKEN)