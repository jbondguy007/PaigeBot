import discord
import os
from discord import message
import platform
import requests
import json
import pandas as pd
import time
from datetime import datetime

from discord.ext import commands, tasks
from dotenv import load_dotenv

# BOT INFO

botname = "Paige"
prefixes = ("p!", "!paige ")
bot_birthdate = "February 20, 2023"
bot_platform = [platform.system(), platform.release(), platform.python_version()]

# VARIABLES

bot_color = 0x9887ff
staff_channel = 1067986921487351820
# bot_channel = 1077994256288981083
bot_channel = 630835643953709066

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
    df = pd.concat(df_list)
    result = df.set_index('Game').T.to_dict('dict')
    return result

def fetch_giveaways(page=1):
    url = f'https://www.steamgifts.com/group/X4YE7/sgmonthlymagazine?format=json&page={str(page)}'
    r = requests.get(url)
    giveaways = r.json()
    return giveaways

def fetch_active_giveaways():
    active_giveaways = []
    giveaways = fetch_giveaways()
    for ga in giveaways['results']:
        if int(ga['end_timestamp']) > int(time.time()):
            active_giveaways.append(ga)
    return active_giveaways

def fetch_all_giveaways():
    giveaways = []
    p=1
    while p <= 2:
        page = fetch_giveaways(page=p)
        giveaways.extend(page['results'])
        if len(page['results']) == page['per_page']:
            p += 1
            continue
        else:
            break
    return giveaways

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

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == bot_channel:

        channel = await bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.author != bot.user:
            return
    
        if message.embeds:
            if "Poll by" not in message.embeds[0].description or "Poll reference ID" not in message.embeds[0].footer.text:
                return

        # iterating through each reaction in the message
        for r in message.reactions:

            # checks the reactant isn't a bot and the emoji isn't the one they just reacted with
            if payload.member in [user async for user in r.users()] and not payload.member.bot and str(r) != str(payload.emoji):

                # removes the reaction
                await message.remove_reaction(r.emoji, payload.member)

# COMMANDS

@bot.command()
async def test(ctx):
    await ctx.send("Test successful.")

@bot.command()
async def info(ctx):
    await ctx.send(f"Hi, {botname} here communicating to you from <@172522306147581952>'s {platform.system()} {platform.release()}! I was born on {bot_birthdate}, and am running on Python v{platform.python_version()}.\n\nI'm happy to help, just issue the command `p!help` for a list of commands.",
                   allowed_mentions=discord.AllowedMentions(users=False))

@bot.command()
async def threads(ctx):
    await ctx.send(f"Main thread: <{steamgifts_threads['main']}>\nScreenshot of the Month thread: <{steamgifts_threads['screenshots']}>")

@bot.command()
async def rules(ctx):
    await ctx.send(f"{botname} recommends reading the rules! <https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/3/3758852249517826899/>")

@bot.command()
async def deadline(ctx, username):

    deadlines_list = fetch_deadlines()
    user_deadlines = {
        key: value for key, value
        in deadlines_list.items()
        # If assigned user matches query username
        if value.get('Assigned') == username
        # And deadline date...
        and datetime.strptime(f"{value.get('Deadline')} {datetime.now().year}", '%B %d %Y').date()
        # ...is later than today's date
        > datetime.today().date()
    }

    if user_deadlines:

        for game, value in user_deadlines.items():

            embedVar = discord.Embed(title=f"Deadlines for {username}", description="", color=bot_color)
            embedVar.add_field(
                name="Game",
                value=game,
                inline=False
            )
            embedVar.add_field(
                name="Deadline",
                value=value['Deadline'],
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

@bot.command()
async def giveaways(ctx):

    if ctx.channel.id in [staff_channel, bot_channel]:
        giveaways = fetch_active_giveaways()
        embedVar = discord.Embed(title="Active Giveaways", description="", color=bot_color)

        for ga in giveaways:
            embedVar.add_field(
                name=ga['name'],
                value=f"{ga['entry_count']} {'entries' if ga['entry_count'] > 1 else 'entry'} | {ga['creator']['username']}\n{ga['link'].rsplit('/', 1)[0]}/",
                inline=False
            )

        await ctx.send(embed=embedVar)
    
    else:
        await ctx.send("Spammy command, kindly issue this command from the <#1077994256288981083> channel to avoid spamming!")

@bot.command()
async def contributors(ctx):
    giveaways = fetch_all_giveaways()
    count = {}
    for i in giveaways:
        count[i['creator']['username']] = count.get(i['creator']['username'], 0) + 1
        ordered_dict = dict(
            sorted(
                count.items(),
                key=lambda
                item: item[1],
                reverse=True
            )
        )
        to_list = [
            (k, v) for k,
            v in ordered_dict.items()
        ]

    embedVar = discord.Embed(title="Top Contributors", description="By giveaways count", color=bot_color)

    for user in to_list[:5]:
        if user[1] > 1:
            embedVar.add_field(
                name=user[0],
                value=user[1],
                inline=False
            )

    await ctx.send(embed=embedVar)

@bot.command()
async def poll(ctx, content, *choices):

    if len(choices) > 9:
        await ctx.send("Poll creation failed: 9 choices maximum.")
        return
    elif len(choices) < 2:
        await ctx.send("Poll creation failed: At least 2 choices minimum.")
        return

    reactions = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮"]

    embedVar = discord.Embed(title=content, description=f"Poll by {ctx.author.name}", color=bot_color)
    for i, choice in enumerate(choices):
        embedVar.add_field(
            name=choice,
            value=reactions[i]
        )
    embedVar.set_footer(text=f"Poll reference ID: NOT_FOUND")

    embed_message = await ctx.send(embed=embedVar)
    embedVar.set_footer(text=f"Poll reference ID: {str(embed_message.id)}")
    await embed_message.edit(embed=embedVar)

    for reaction in reactions[:len(choices)]:
        await embed_message.add_reaction(reaction)

# HELP COMMANDS

@bot.command()
async def help(ctx):

    threads_list = list(steamgifts_threads)
    threads_list = ", ".join(threads_list)

    embedVar = discord.Embed(title="Commands", description="", color=bot_color)
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

        **poll** `"Poll question"` `"choice with spaces"` `choicewithoutspaces` `etc`
        Triggers a poll post in the channel where it is issued. Accepts up to 9 unique choices, each delimited by a space (unless in quotes, in which case the string in quotes becomes a choice)

        **giveaways**
        Lists all current running giveaways. Spammy command, can only be issued from the <#{bot_channel}> channel.

        **contributors**
        Lists up to top 5 contributors by giveaways count.
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
@commands.has_any_role("Staff", "Founders")
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
@commands.has_any_role("Staff", "Founders")
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
@commands.has_any_role("Staff", "Founders")
async def deadlines(ctx):

    deadlines_list = fetch_deadlines()

    embedVar = discord.Embed(title=f"Deadlines", description="List of all current assignments. Details and statuses: https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/4/3758852249517533958/", color=bot_color)

    for user in deadlines_list:
        deadline_date = datetime.strptime(deadlines_list[user]['Deadline'], '%B %d').strftime('%m/%d')
        if deadline_date > datetime.today().strftime('%m/%d'):
            embedVar.add_field(
                name=user,
                value=f"- {deadlines_list[user]['Game']}\n- Deadline: {deadlines_list[user]['Deadline']}",
                inline=False
            )

    await ctx.send(embed=embedVar)

bot.run(TOKEN)