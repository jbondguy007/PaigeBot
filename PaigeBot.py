import discord
import os
from discord import message
import platform
import requests
import json
import pandas as pd

from discord.ext import commands, tasks
from dotenv import load_dotenv

# BOT INFO

botname = "Paige"
prefixes = ("p!", "!paige ")
bot_birthdate = "February 20, 2023"
bot_platform = [platform.system(), platform.release(), platform.python_version()]

# VARIABLES

embed_color = 0x0044bb

with open("permanent_variables.json", "r") as f:
    permanent_variables = json.load(f)

steamgifts_threads = permanent_variables['thread_links']

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

def fetch_deadlines():
    url = 'https://www.steamgifts.com/discussion/kvEdg/'
    html = requests.get(url).content
    df_list = pd.read_html(html)
    df = df_list[0]
    result = df.set_index('Assigned').T.to_dict('dict')
    return result

# def sg_names_checker(users):

#     results = []
#     fake_users = []

#     for user in users:

#         link = f"https://www.steamgifts.com/user/{str(user)}"

#         r = requests.get(link)
#         redirected = True if r.status_code == 404 else r.url != link

#         results.append({user: redirected})

#         if redirected:
#             fake_users.append(user)
    
#     return(fake_users)

# BOT EVENTS

@bot.event
async def on_ready():
    if bot.user.id == 823385752486412290:
        bot.command_prefix = ("fb!", "foxy!")
    print("Logged in as {}".format(bot.user, bot.command_prefix))
    print("Ready!")
    await bot.change_presence(status=discord.Status.online,
        activity=discord.Activity(name="for prefix: p!", type=discord.ActivityType.watching))
    
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
    await ctx.send(f"Main thread: <{steamgifts_threads['main']}>\nScreenshot of the Month thread: <{steamgifts_threads['screenshots']}>")

@bot.command()
async def rules(ctx):
    await ctx.send(f"{botname} recommends reading the rules! <https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/3/3758852249517826899/>")

@bot.command()
async def deadline(ctx, username):

    deadlines_list = fetch_deadlines()

    if username in deadlines_list:
        user_deadline = deadlines_list[username]

        embedVar = discord.Embed(title=f"Deadlines for {username}", description="", color=embed_color)
        embedVar.add_field(
            name="Game",
            value=user_deadline['Game'],
            inline=False
        )
        embedVar.add_field(
            name="Deadline",
            value=user_deadline['Deadline'],
            inline=False
        )
        embedVar.add_field(
            name="Status",
            value="https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/4/3758852249517533958/",
            inline=False
        )

        await ctx.send(embed=embedVar)
    
    else:
        await ctx.send(f"No assignment found for username `{username}`!")

# HELP COMMANDS

@bot.command()
async def help(ctx):

    threads_list = list(steamgifts_threads)
    threads_list = ", ".join(threads_list)

    embedVar = discord.Embed(title="Commands", description="", color=embed_color)
    embedVar.add_field(
        name="\nPublic Commands",
        value=f"""
        **test**
        Simple test command. Check if the bot is alive!

        **help**
        Displays this message.

        **info**
        Information about me, {botname}!

        **threads**
        Lists relevant Steamgifts threads.

        **rules**
        Provides a link to the rules.

        **deadline** `username`
        Checks if `username` has any task assigned this wave. Case sensitive.
        """,
        inline=True
    )
    embedVar.add_field(
        name="Staff Commands",
        value=f"""
        **updatethread** `thread` `link`
        Update the `link` to a `thread` (`{threads_list}`)

        **checkusers** `usernames`
        Verifies if a list of `usernames` (separated by spaces or newlines) matches a profile on Steamgifts.

        **deadlines**
        Lists all assignments and deadlines for this wave.
        """,
        inline=True
    )

    # embedVar.add_field(name="test", value="Simple test command. Check if the bot is alive!", inline=False)
    # embedVar.add_field(name="help", value="Displays this message.", inline=False)
    # embedVar.add_field(name="info", value=f"Information about me, {botname}!", inline=False)
    # embedVar.add_field(name="threads", value="Lists relevant Steamgifts threads.", inline=False)
    # embedVar.add_field(name="rules", value="Provides a link to the rules.", inline=False)

    await ctx.send(embed=embedVar)

# MODERATOR COMMANDS

@bot.command()
@commands.has_any_role("Staff", "Founders", "Mad Scientist")
async def updatethread(ctx, thread, link):

    if thread in steamgifts_threads:
        permanent_variables['thread_links'][thread] = link
        with open("permanent_variables.json", "w") as f:      # write back to the json file
            json.dump(permanent_variables, f)

        await ctx.send(f"Thread `{thread}` set to `{link}`.")

    else:
        threads_list = list(steamgifts_threads)
        threads_list = "\n".join(threads_list)
        await ctx.send(f"Thread `{thread}` not found. Please use one of the following thread name arguments to set thread links:\n`{threads_list}`")

@bot.command()
@commands.has_any_role("Staff", "Founders", "Mad Scientist")
async def checkusers(ctx, *users):

    results = []
    fake_users = []

    msg = await ctx.send(f"Processing... {len(results)}/{len(users)}")

    # Function

    for user in users:

        link = f"https://www.steamgifts.com/user/{str(user)}"
        r = requests.get(link)

        redirected = True if r.status_code == 404 else r.url != link
        results.append({user: redirected})

        if redirected:
            fake_users.append(user)
        
        await msg.edit(content=f"Processing... {len(results)}/{len(users)}")

    # End function

    fake_users = "\n".join(fake_users)
    await ctx.send(f"**Fake users:**\n{fake_users}")

    await msg.edit(content=f"Done! {len(results)}/{len(users)}")

@bot.command()
@commands.has_any_role("Staff", "Founders", "Mad Scientist")
async def deadlines(ctx):

    deadlines_list = fetch_deadlines()

    embedVar = discord.Embed(title=f"Deadlines", description="List of all assignments for this wave. Details and statuses: https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/4/3758852249517533958/", color=embed_color)

    for user in deadlines_list:
        embedVar.add_field(
            name=user,
            value=f"- {deadlines_list[user]['Game']}\n- Deadline: {deadlines_list[user]['Deadline']}",
            inline=False
        )

    await ctx.send(embed=embedVar)

bot.run(TOKEN)