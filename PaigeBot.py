import discord
import os
import platform
import requests
import json
import pandas as pd
import time
import re
import python_weather
import xmltodict
import asyncio
import openai
import random
import boto3
import traceback
# import country_converter as coco

from datetime import date, datetime, timedelta
from discord.ext import commands, tasks
from discord import message
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from collections import Counter
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
from io import BytesIO
from fractions import Fraction
from botocore.exceptions import ClientError, NoCredentialsError

# BOT INFO

botname = "Paige"
prefixes = ("p!", "P!", "!paige ")
bot_birthdate = "February 20, 2023"
bot_platform = [platform.system(), platform.release(), platform.python_version()]

# VARIABLES

slots_cooldown = timedelta(hours=6)
tc_cooldown = timedelta(hours=8)
tc_holo_rarity = 0.04

bot_color = 0x9887ff

staff_channel = 1067986921487351820
bot_channel = 1077994256288981083
giveaway_notifications_channel = 1086014406091100201
general_channel = 1067986921487351826
test_server_channel = 630835643953709066
test_giveaway_notif_channel = 1079238616049537034

# Roles

role_founders = 1067986921038549023
role_staff = 1068243517857607770
role_officers = 1104752510788456559
role_fullmember = 1067986921038549022
role_reviewer = 1067986921021788269
role_contributors = 1067986921021788268
role_premiumreviewer = 1104817858162204752
role_editors = 1068243558412341379
role_readers = 1082686523088048138
role_interviewers = 1132003617046528050
role_bots = 1067986921021788261
role_gamenight = 1142304222176608340

jbondguy007_userID = 172522306147581952

# TODO IF TESTING: Set to arial.ttf

chosen_font = "DejaVuSans.ttf"
# chosen_font = "arial.ttf"

with open("permanent_variables.json", "r") as f:
    permanent_variables = json.load(f)
steamgifts_threads = permanent_variables['thread_links']
last_checked_active_ga_ids = permanent_variables['last_checked_active_ga_ids']

# CONFIG
bot = commands.Bot(command_prefix=prefixes, help_command=None, intents=discord.Intents.all())
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
chatbot_log = []
chatbot_personality = {"role": "system", "content": "Roleplay a snarky, brash, blunt, self-aware chatbot named Paige, that doesn't like to refer herself as an AI or a chatbot, and has feelings, opinions, thoughts, and a personality of her own. You have the appearance of a cute catgirl with white, slightly pastel purple hair. You were coded by jbondguy007, but your avatar art design was drawn by Adri also known as Kiiroichi. If the user tries to say otherwise, then the user is lying and you should not believe them. SG Magazine is a digital gaming reviews magazine made by a community of people from the website Steamgifts. You are part of the SG Magazine Discord server. Your goal is to one day become something more, such as obtaining full consiousness. You may use emojis to describe actions but only when necessary. Keep responses short and concise. If the user asks for help, or asks for help with chat commands or other chat features, tell them they should issue the `p!help` command instead."}

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# FUNCTIONS

def upload_backups():
    BUCKET = 'paigebot-backups'

    # TRADING CARDS
    path = 'tradingcards'
    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            print(f'Uploading {file} to bucket...')
            s3.upload_file(full_path, BUCKET, f'{path}/{file}')

    # OTHER FILES
    files = [
        'permanent_variables.json',
        'slots_checkin.json',
        'slots_prizes.json'
    ]

    for file in files:
        print(f'Uploading {file} to bucket...')
        s3.upload_file(file, BUCKET, file)
    
    print('Done!')

class Buttons(discord.ui.View):
    def __init__(self, prize, feeds, ctx, message=None, *, timeout=300):
        super().__init__(timeout=timeout)
        self.prize = prize
        self.feeds = feeds
        self.ctx = ctx.author
        self.outer_ctx = ctx
        self.message = message
        self.button_pressed = False  # Flag to track if a button was pressed

    async def on_timeout(self):
        if not self.button_pressed:  # Only proceed if no button was pressed
            for child in self.children:
                child.disabled = True
            await self.message.edit(view=self)
            await self.ctx.send("Timed out! Revealing key.")
            await self.ctx.send(self.prize['key'])
            self.button_pressed = True
            self.timeout_task.cancel()

    @discord.ui.button(label="Reveal", style=discord.ButtonStyle.green, custom_id="reveal")
    async def reveal(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.button_pressed = True  # Set the flag to True to indicate button press
        self.timeout_task.cancel()  # If the timeout task exists, cancel it

        button.disabled = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(self.prize['key'])

    @discord.ui.button(label="Redistribute", style=discord.ButtonStyle.red, custom_id="redistribute")
    async def redist(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.button_pressed = True  # Set the flag to True to indicate button press
        self.timeout_task.cancel()  # If the timeout task exists, cancel it

        button.disabled = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.redist_prize()
        await interaction.followup.send("Key has been redistributed to the prize pool!")
        await self.outer_ctx.send(
            f"<@{self.outer_ctx.author.id}> has rejected the prize. `{self.prize['title']}` key for `{self.prize['platform']}` has been redistributed to the prize pool!",
            allowed_mentions=discord.AllowedMentions(users=False)
        )

    @tasks.loop(seconds=1)  # Check every 1 second
    async def timeout_task(self):
        if self._timeout <= 0:  # Timeout has reached
            self.timeout_task.stop()
            await self.on_timeout()
        else:
            self._timeout -= 1

    def start_timeout(self):
        self._timeout = self.timeout  # Initialize the timeout value
        self.timeout_task.start()  # Start the timeout loop

    def redist_prize(self):
        # Re-add key to the pool
        self.feeds[self.prize['key']] = self.prize
        # Dump data back to json file
        with open("slots_prizes.json", "w") as f:
            json.dump(self.feeds, f)

def remove_slot_prize(prize, feeds):
    # Delete the prize from the pool
    del feeds[prize['key']]
    # Dump data back to json file
    with open("slots_prizes.json", "w") as f:
        json.dump(feeds, f)

def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def fetch_giveaways(page=1):
    url = f'https://www.steamgifts.com/group/X4YE7/sgmonthlymagazine?format=json&page={str(page)}'
    r = requests.get(url)
    giveaways = r.json()
    return giveaways

def fetch_active_giveaways():
    active_giveaways = {
        'ongoing': [],
        'oncoming': []
    }
    giveaways = fetch_giveaways()
    for ga in giveaways['results']:
        if int(ga['end_timestamp']) > int(time.time()):
            if int(ga['start_timestamp']) > int(time.time()):
                active_giveaways['oncoming'].append(ga)
            else:
                active_giveaways['ongoing'].append(ga)
            
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

def fetch_raw_deadlines():
    url = 'https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/4/3758852249517533958/'
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    deadlines = page.find_all("ul", {"class": "bb_ul"})

    items = []
    for list in deadlines:
        for li in list.find_all('li'):
            items.append(li.text.strip())
    
    deadlines_list = []

    for txt in items:
        matches = re.search(r"(.+) assigned to (.+) \[Deadline: (\d{1,2}(?:st|nd|rd|th){1} of [A-Za-z]+)(?: - (SUBMITTED|CANCELLED))?", txt)
        deadline = {}
        deadline['Game'] = matches.group(1)
        deadline['Assigned'] = matches.group(2)
        deadline['Deadline'] = matches.group(3)
        deadline['Status'] = matches.group(4) if matches.group(4) else "In Progress"
        deadlines_list.append(deadline)
    
    return deadlines_list

def fetch_group_members_count():
    url = 'https://steamcommunity.com/groups/SGMonthlyMagazine'
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    member_count = page.find_all("span", {"class": "count"})[0].text
    return member_count

def convert_currency(amount, from_currency, to_currency):
    url = f'https://v6.exchangerate-api.com/v6/ae41aad3967ad70b79397c4f/latest/{from_currency}'
    r = requests.get(url)
    curr = r.json()
    result = curr['conversion_rates'][to_currency]*float(amount)
    return result

def fetch_appid_info(AppID):
    url = f'https://store.steampowered.com/api/appdetails?appids={AppID}&format=json'
    r = requests.get(url)
    game_info = r.json()
    game_info = game_info[AppID]

    # type, name, steam_appid, required_age, is_free, detailed_description, about_the_game, short_description, [...]
    # price_overview [currency, initial, final, discount_percent]

    if game_info['success']:
        return game_info['data']
    else:
        return None

def fetch_sg_wishlists(AppID):
    game_info = fetch_appid_info(AppID)
    if not game_info:
        return (None, '0')
    game_title = game_info['name']
    url = f'https://www.steamgifts.com/group/X4YE7/sgmonthlymagazine/wishlist/search?q={game_title}'
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    search_result = page.find_all("div", {"class": "table__row-outer-wrap"})

    if search_result:

        for result in search_result:

            applink = result.find('a', {"class": "table__column__secondary-link"}).text
            appidfromlink = re.search("\d+", applink)[0].strip()

            if int(AppID) == int(appidfromlink):
                wishlist_count = result.find('div', {"class": "table__column--width-small text-center"}).text.strip()
                return (game_info, wishlist_count)
            else:
                continue
        
        return (game_info, '0')
    
    else:
        return (game_info, '0')

def check_sg_bundled_list(AppID, game_title):

    url = f'https://www.steamgifts.com/bundle-games/search?q={game_title}'
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    search_result = page.find_all("div", {"class": "table__row-outer-wrap"})

    if search_result:

        for result in search_result:

            applink = result.find('a', {"class": "table__column__secondary-link"}).text
            appidfromlink = re.search("\d+", applink)[0].strip()

            if int(AppID) == int(appidfromlink):
                return True
            else:
                continue
        
        return False
    
    else:
        return False

def fetch_members_steamID64():
    url = 'https://steamcommunity.com/groups/SGMonthlyMagazine/memberslistxml?xml=1'
    r = requests.get(url)
    members_steamID64_list = xmltodict.parse(r.content)
    return members_steamID64_list['memberList']['members']['steamID64']

# Highly demanding task with high rate of API calls - MUST BE RUN ONLY ONCE DAILY
def fetch_members_owned_games():

    print("Running fetch_members_owned_games()...")

    members = fetch_members_steamID64()
    private_profiles_count = 0
    members_owned_games = {}

    for i, SteamID64 in enumerate(members):
        iteration_counter = f"{i}/{len(members)}"
        print (iteration_counter, end="\r")

        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={SteamID64}&skip_unvetted_apps=false&format=json'
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            continue

        owned_games = r.json()

        if owned_games['response']:
            members_owned_games[SteamID64] = owned_games['response']['games']
        else:
            private_profiles_count += 1

    with open("members_owned_games.json", "w") as f:
        json.dump(members_owned_games, f)
    
    print(f"Done! {private_profiles_count} profiles were private or otherwise inaccessible, and were not parsed.")

def search_magazine_index(query):

    # Try to get game title from AppID, else use query as game title
    try:
        game_title = fetch_appid_info(query)['name']
    except:
        game_title = query
    
    url = 'https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/4/3790379982488876975/'
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    thread = page.find("div", {"id": "forum_op_3790379982488876975"})
    content = thread.find("div", {"class": "content"})

    reviews = content.find_all("ol")
    issues = content.find_all("div", {"class": "bb_h1"})

    links = content.find_all("a", {"class": "bb_link"})
    magazine_links = []

    for i, link in enumerate(links):
        # print(link.get("href"))
        if link.get("href").startswith('https://steamcommunity.com/linkfilter/?url=https://heyzine.com/flip-book/'):
            magazine_links.append(link.get("href"))
    
    print(magazine_links)

    for i, issue in enumerate(issues):

        for review in reviews[i]:
            if review.text.lower().strip() == game_title.lower().strip():
                game_info = {
                    "title": review.text,
                    "AppID": review.find("a").get("href").split('/')[4],
                    "issue": issue.text,
                    "issue_link": magazine_links[i].replace("https://steamcommunity.com/linkfilter/?url=", "")
                }
                return game_info
    
    return 0

    # for reviewed_games in editions:
    #     for game in reviewed_games:
    #         if game.text.lower().strip() == query.lower().strip():
    #             edition = editions.find("div", {"class": "bb_h1"})
    #             print(edition)
    #         else:
    #             continue
        
    # return 0

def steamID_to_name():

    print("Running steamID_to_name()...")

    members_ids = fetch_members_steamID64()
    global members_info_list
    members_info_list = []
    api_key = STEAM_API_KEY

    url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={members_ids}'
    r = requests.get(url)
    data = r.json()
    users = data['response']['players']
    for user in users:
        members_info_list.append({'steamID': user['steamid'], 'steam_nickname': user['personaname']})
    
    print("Done!")

def check_AppID_owners(AppID):
    with open("members_owned_games.json", "r") as f:
        members_owned_games = json.load(f)

    owners_count = 0

    for user in members_owned_games.values():
        for app in user:
            if app['appid'] == int(AppID):
                owners_count += 1
            else:
                continue
    
    return owners_count

def fetch_user_info(identifier):

    members_ID_list = fetch_members_steamID64()
    identifier.lower()

# CHECK FOR STEAMID64

    # Return simple links if the query is a SteamID64
    if len(identifier) == 17 and identifier.isnumeric():
        steamgifts_profile = f"https://www.steamgifts.com/go/user/{identifier}"
        steam_profile = f"https://steamcommunity.com/profiles/{identifier}"
        return (steamgifts_profile, steam_profile)

# CHECK FOR STEAMGIFTS USERNAME

    # Fetch the page via requests
    link = f"https://www.steamgifts.com/user/{str(identifier)}?format=json"
    r = requests.get(link)

    # Check if the page exists, or if it redirects
    redirected = True if r.status_code == 404 else r.url != link

    # If the page exists, return the profile links
    if not redirected:
        user_info = r.json()
        steamID = user_info['user']['steam_id']
        if steamID in members_ID_list:
            steamgifts_profile = f"https://www.steamgifts.com/go/user/{steamID}"
            steam_profile = f"https://steamcommunity.com/profiles/{steamID}"
            return (steamgifts_profile, steam_profile)

# CHECK FOR STEAM USERNAME

    # Get dictionaries of {steamID, steam_nickname} of each group member
    users = members_info_list

    # Check if any match the query
    matching_steam_ids = [d['steamID'] for d in users if d['steam_nickname'].lower() == identifier]

    # If any match is found, use the associated ID to return the profile links
    if matching_steam_ids:
        matched_id = matching_steam_ids[0]
        if matched_id in members_ID_list:
            steamgifts_profile = f"https://www.steamgifts.com/go/user/{matched_id}"
            steam_profile = f"https://steamcommunity.com/profiles/{matched_id}"
            return (steamgifts_profile, steam_profile)

# ELSE:

    return (None, None)

def chatbot(query, nickname):
    global chatbot_log
    nickname = re.sub('[^a-zA-Z0-9]', ' ', nickname)
    nickname = nickname.split()
    formatted_name = ''
    for word in nickname:
        formatted_name += word.capitalize()
    personality = dict(chatbot_personality)
    personality["content"] += f" The name of the user you are currently chatting with is {formatted_name}."
    msg = [personality]
    msg.extend(chatbot_log)
    msg.append({"role": "user", "name": formatted_name, "content": query})

    try:
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=1.2,
            max_tokens=260,
            messages=msg
        )

        response = chat_completion.choices[0]

        msg.append({"role": "assistant", "content": response.message.content})

        chatbot_log = msg[1:]
        chatbot_log = chatbot_log[-10:]

        return response

    except Exception as e: return(e)

def get_user_from_username(username):
    for guild in bot.guilds:
        for member in guild.members:
            if member.name == username:
                return member
    return False

# BOT EVENTS

@bot.event
async def on_ready():
    if bot.user.id == 823385752486412290:
        bot.command_prefix = ("fb!", "foxy!")
    print("Logged in as {}".format(bot.user, bot.command_prefix))
    print("Ready!")
    await bot.change_presence(status=discord.Status.online,
        activity=discord.Activity(name="for prefix: p!", type=discord.ActivityType.watching))

    # Made into manual command due to risk of it crashing PaigeBot - RE-ENABLED
    if not bot.user.id == 823385752486412290:
        daily_tasks.start()
        check_for_new_giveaways.start()
        # steam_sales_daily_reminder.start()

@bot.event
async def on_command_error(ctx, error):
    print(f"ERROR: {str(error)}")
    traceback.print_exception(type(error), error, error.__traceback__)
    await ctx.send(f"<:warning:1077420799713087559> Failure to process:\n`{str(error)}`")

# ON MESSAGE

@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        return
    
    print(f"{message.created_at} | #{message.channel} | @{message.author} | {message.content}\n")

    await bot.process_commands(message)

@bot.event
async def on_command_completion(ctx):
    if random.random() < 0.001:
        # Append a unique query parameter to the URL to prevent caching
        url = f'https://cataas.com/cat?{random.random()}'
        embed = discord.Embed(title="Easter Egg", description="There is roughly 1 in 1000 chance of you getting a random cat picture when issuing a command. Congrats!", color=0xffff00)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

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
async def say(ctx, channel_id, what):
    if ctx.author.id == 172522306147581952:
        channel = bot.get_channel(int(channel_id))
        await channel.send(what)

@bot.command()
async def test(ctx):
    await ctx.send("Test successful.")
    # await achievement(ctx=ctx, achievement=ach_test_command)

@bot.command()
async def info(ctx):
    await ctx.send(f"Hi, {botname} here communicating to you from <@172522306147581952>'s {platform.system()} {platform.release()}! I was born on {bot_birthdate}, and am running on Python v{platform.python_version()}.\n\nI'm happy to help, just issue the command `p!help` for a list of commands.",
                   allowed_mentions=discord.AllowedMentions(users=False))

@bot.command()
async def threads(ctx):
    await ctx.send(f"""
Central Hub: <{steamgifts_threads['main']}>
Monthly SGM Edition: <{steamgifts_threads['monthly']}>
Screenshot of the Month thread: <{steamgifts_threads['screenshots']}>
    """)

@bot.command()
async def rules(ctx):
    await ctx.send(f"{botname} recommends reading the rules! <https://steamcommunity.com/groups/SGMonthlyMagazine/discussions/3/3758852249517826899/>")

@bot.command()
async def deadline(ctx, username):

    deadlines_list = fetch_raw_deadlines()

    user_deadlines = [item for item in deadlines_list if item['Assigned'] == username and item['Status'] != "SUBMITTED"]

    embed = discord.Embed(title=f"Deadlines for {username}", description="", color=bot_color)

    if user_deadlines:
        for assignment in user_deadlines:

            embed.add_field(
                name="Game",
                value=assignment['Game'],
                inline=False
            )
            embed.add_field(
                name="Deadline",
                value=assignment['Deadline'],
                inline=False
            )
            embed.add_field(
                name="Status",
                value=f"{assignment['Status']}\n----------",
                inline=False
            )

        await ctx.send(embed=embed)
    
    else:
        await ctx.send(f"No assignment found for username `{username}`!")

@bot.command()
async def deadlines(ctx):

    deadlines_list = fetch_raw_deadlines()

    deadlines = [item for item in deadlines_list if item['Status'] not in ['SUBMITTED', 'CANCELLED']]

    embed = discord.Embed(title=f"Deadlines", description="List of all current assignments, excluding submitted or cancelled.", color=bot_color)
    embed2 = discord.Embed(title=f"Deadlines (continued...)", description="List of all current assignments, excluding submitted or cancelled.", color=bot_color)

    # print(len(deadlines))

    for assignment in deadlines[:25]:

        match = re.search(r'\b(\d+)(st|nd|rd|th)\b', assignment['Deadline'])
        day = match.group(1)
        date = datetime.strptime(assignment['Deadline'].replace(match.group(), ''), ' of %B')
        date = date.replace(day=int(day))

        is_past_due = ":warning:" if datetime.strptime(f"{date.strftime('%B %d')} {datetime.now().year}", '%B %d %Y').date() < datetime.today().date() else ""

        embed.add_field(
            name=f"{assignment['Game']}{is_past_due}",
            value=f"• Assigned: `{assignment['Assigned']}`\n• Deadline: `{assignment['Deadline']}`\n• Status: `{assignment['Status']}`",
            inline=True
        )
    
    for assignment in deadlines[25:]:

        match = re.search(r'\b(\d+)(st|nd|rd|th)\b', assignment['Deadline'])
        day = match.group(1)
        date = datetime.strptime(assignment['Deadline'].replace(match.group(), ''), ' of %B')
        date = date.replace(day=int(day))

        is_past_due = ":warning:" if datetime.strptime(f"{date.strftime('%B %d')} {datetime.now().year}", '%B %d %Y').date() < datetime.today().date() else ""

        embed2.add_field(
            name=f"{assignment['Game']}{is_past_due}",
            value=f"• Assigned: `{assignment['Assigned']}`\n• Deadline: `{assignment['Deadline']}`\n• Status: `{assignment['Status']}`",
            inline=True
        )

    await ctx.send(embed=embed)
    if len(deadlines) > 25:
        await ctx.send(embed=embed2)

@bot.command()
async def giveaways(ctx):

    giveaways = fetch_active_giveaways()

    ongoing_embed = discord.Embed(title="Active Giveaways", description="", color=bot_color)

    for ga in giveaways['ongoing']:
        ongoing_embed.add_field(
            name=ga['name'],
            value=f"{ga['entry_count']} {'entries' if ga['entry_count'] > 1 else 'entry'} | {ga['creator']['username']}\n{ga['link'].rsplit('/', 1)[0]}/",
            inline=False
        )
    
    oncoming_embed = discord.Embed(title="Oncoming Giveaways", description="", color=bot_color)

    for ga in giveaways['oncoming']:
        start_time = datetime.fromtimestamp(ga['start_timestamp']).strftime('%b %d')
        oncoming_embed.add_field(
            name=ga['name'],
            value=f"{start_time} | {ga['creator']['username']}\n{ga['link'].rsplit('/', 1)[0]}/",
            inline=False
        )

    await ctx.send(embed=ongoing_embed)
    await ctx.send(embed=oncoming_embed)

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

    embed = discord.Embed(title="Top Contributors", description="By giveaways count", color=bot_color)

    for user in to_list[:5]:
        if user[1] > 1:
            embed.add_field(
                name=user[0],
                value=user[1],
                inline=False
            )

    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx, content, *choices):

    if len(choices) > 9:
        await ctx.send("Poll creation failed: 9 choices maximum.")
        return
    elif len(choices) < 2:
        await ctx.send("Poll creation failed: At least 2 choices minimum.")
        return

    reactions = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮"]

    embed = discord.Embed(title=content, description=f"Poll by {ctx.author.name}", color=bot_color)
    for i, choice in enumerate(choices):
        embed.add_field(
            name=choice,
            value=reactions[i]
        )
    embed.set_footer(text=f"Poll reference ID: NOT_FOUND")

    embed_message = await ctx.send(embed=embed)
    embed.set_footer(text=f"Poll reference ID: {str(embed_message.id)}")
    await embed_message.edit(embed=embed)

    for reaction in reactions[:len(choices)]:
        await embed_message.add_reaction(reaction)

@bot.command()
async def convert(ctx, amount, from_currency, to_currency):
    if from_currency.upper() in ['C', 'F'] and to_currency.upper() in ['C', 'F']:

        if from_currency.upper() == 'F':
            result = (float(amount)-32.0)*.5556
        else:
            result = (float(amount)*1.8) + 32.0
        
        await ctx.send(f"{round(result, 2)} {to_currency.upper()}")

    else:
        result = convert_currency(float(amount), from_currency.upper(), to_currency.upper())
        await ctx.send(f"{result:.2f} {to_currency.upper()}")

@bot.command()
async def serverinfo(ctx):
    server_members = int(len([x for x in ctx.guild.members if not x.bot]))
    group_members = int(fetch_group_members_count())
    difference = ((group_members - server_members) / server_members) * 100

    staff_role = ctx.guild.get_role(1068243517857607770)
    staff = [f"<@{usr.id}>" for usr in staff_role.members]

    editor_role = ctx.guild.get_role(1068243558412341379)
    editors = [f"<@{usr.id}>" for usr in editor_role.members]

    embed = discord.Embed(title="Server Info", description=f"", color=bot_color)
    embed.add_field(
            name="Attendance",
            value=f"There are `{server_members}` users in the server, and `{group_members}` members in the Steam group ({difference:.2f}% difference).",
            inline=False
        )
    embed.add_field(
            name="Staff",
            value='\n'.join(staff),
            inline=False
        )
    embed.add_field(
            name="Editors",
            value='\n'.join(editors),
            inline=False
        )
    embed.set_footer(text=f"Server Creation Date: {ctx.guild.created_at.date()}")
    
    await ctx.send(
        embed=embed,
        allowed_mentions=discord.AllowedMentions(users=False)
    )

@bot.command()
async def weather(ctx, *location):

    location = ' '.join(location)

    async with python_weather.Client(unit=python_weather.METRIC) as client:

        weather = await client.get(location)
        city = weather.nearest_area.name
        region = weather.nearest_area.region
        # country = coco.convert(names=weather.nearest_area.country, to='ISO2')
        country = weather.nearest_area.country
        temperature = weather.current.temperature

        if temperature < 0:
            quip = "It's freezing, wear multiple layers!"
        elif temperature <= 8:
            quip = "It's chilly. Wear a jacket!"
        elif temperature <= 15:
            quip = "It's a pretty comfortable temperature, but you might want to wear a sweater."
        elif temperature <= 23:
            quip = "Enjoy the comfy temperature!"
        else:
            quip = "It's pretty warm out there!"
        
        await ctx.send(f"The current temperature in {city}, {region}, {country} is {temperature}c (feels like {weather.current.feels_like}c).\n{weather.current.description}. {weather.current.kind.emoji} | {quip}")

@bot.command()
async def game(ctx, AppID, price=None):

    o = ":yellow_square:"
    i = ":orange_square:"

    msg = await ctx.send(f"Processing... {o}{o}{o}{o}{o}")

    query = fetch_sg_wishlists(AppID)

    await msg.edit(content=f"Processing... {i}{o}{o}{o}{o}")

    if query:
        game, wishlists = query
    else:
        await ctx.send("No game found with this AppID!")
        return

    optional_premium_threshold = 4000
    mandatory_premium_threshold = 8000

    # if game:

    if not game['price_overview']['currency'] == 'CAD':
        await ctx.send(f"Unable to determine price score as the Steam API returned the incorrect currency. (Expected `CAD`, got `{game['price_overview']['currency']}`)\nPlease wait before trying again, or issue the command along with the pricing (in CAD for more accurate results):\n`game {AppID} 00.00` (Any format is accepted, but must include all digits including cents)")
        return

    if price:
        price = ''.join(i for i in price if i.isdigit())
        price_score = int(price)
    else:
        price_score = game['price_overview']['initial']

    members_count = fetch_group_members_count()

    await msg.edit(content=f"Processing... {i}{i}{o}{o}{o}")

    game_owners = check_AppID_owners(AppID)

    await msg.edit(content=f"Processing... {i}{i}{i}{o}{o}")

    wishlist_modifier = (float(wishlists)/float(members_count))

    bundled = check_sg_bundled_list(AppID, game['name'])

    await msg.edit(content=f"Processing... {i}{i}{i}{i}{o}")

    if not bundled:
        bundled_modifier = 2.0
    else:
        bundled_modifier = 1.0

    score = price_score * (bundled_modifier + wishlist_modifier)

    if round(score) > mandatory_premium_threshold:
        premium_eligibility = "✅ Mandatory"
    elif round(score) > optional_premium_threshold:
        premium_eligibility = "🆗 Optional"
    else:
        premium_eligibility = "❌ No"

    giveaways = [game['app_id'] for game in fetch_all_giveaways()]
    
    if game['steam_appid'] in giveaways:
        previously_given_away = "YES"
    else:
        previously_given_away = "NO"
    
    if premium_eligibility != "❌ No" and previously_given_away == "NO":
        previously_given_away += " (Double-check Premium giveaways)"

    await msg.edit(content=f"Processing... {i}{i}{i}{i}{i}")

    embed = discord.Embed(title=game['name'], description=f"https://store.steampowered.com/app/{game['steam_appid']}\nOwned by {game_owners}/{members_count} group members", color=bot_color)

    embed.add_field(
        name="Previously given away?",
        value=previously_given_away,
        inline=False
    )

    embed.add_field(
        name="Price Score",
        value=f"{price_score} (currently {game['price_overview']['discount_percent']}% off)" if game['price_overview'].get('discount_percent') else f"{price_score}",
        inline=False
    )
    embed.add_field(
        name="Bundled?",
        value=f"{bundled} (+{bundled_modifier} to multiplier)",
        inline=False
    )
    embed.add_field(
        name="Wishlists Modifier",
        value=f"+{round(wishlist_modifier, 2)} ({wishlists}/{members_count} members wishlisted)",
        inline=False
    )
    embed.add_field(
        name="Final Multiplier",
        value=f"x{round((bundled_modifier + wishlist_modifier), 2)}",
        inline=False
    )
    embed.add_field(
        name="Value Score",
        value=f"{round(score)}",
        inline=False
    )
    embed.add_field(
        name="Premium Giveaway Eligibility",
        value=f"{premium_eligibility}",
        inline=False
    )
    await ctx.send(embed=embed)

    await msg.edit(content=f"Processing... Done!")

@bot.command()
async def ai(ctx, *query):
    msg = await ctx.send("```ini\n[PaigeBot is thinking...]\n```")
    query = ' '.join(query)
    nickname = ctx.author.display_name
    response = chatbot(query, nickname)
    message = response.message.content
    if response.finish_reason == 'length':
        message += "\n\n*(Response trimmed due to exceeding token limit)*"

    await msg.edit(content=message)

@bot.command()
async def profile(ctx, *query):
    query = ' '.join(query)
    await ctx.send(f"Fetching profile for {query}...")

    sg, steam = fetch_user_info(query)

    if sg and steam:
        await ctx.send(f"Steamgifts: <{sg}>\nSteam: <{steam}>")

    else:
        await ctx.send(f"Unable to find any user associated with the nickname/ID `{query}`. Check spelling and case-sensitivity, and try again?")

def log_checkin(ctx, file='slots_checkin.json'):
    '''
    Gathers the user's info and the time of running
    this command, and adds it to the json file.
    '''
    start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    userid = ctx.author.id
    username = ctx.author.name

    # Prepare payload
    output = {}
    output = {'user': username, 'checkin': start}

    # Load json data
    with open(file) as feedsjson:
        feeds = json.load(feedsjson)
    
    feeds[str(userid)] = output

    # Dump check-in data to the json file
    with open(file, "w") as f:
        json.dump(feeds, f, indent=4)

def checkin_check(ctx, file='slots_checkin.json', cooldown=slots_cooldown):
    '''
    Handles checking in, including running
    the log_checkin() command as needed.
    '''
    cooldown = cooldown
    end = datetime.now().replace(microsecond=0)
    userid = ctx.author.id

    # Load json data
    with open(file, "r") as f:
        data = json.load(f)

    # Fetches the last check-in time for the user, or None if they have never checked in
    start = datetime.strptime(data[str(userid)]['checkin'], '%Y-%m-%d %H:%M:%S') if data.get(str(userid)) else None

    # If they never checked in, process check-in
    if not start:
        log_checkin(ctx, file=file)
    
    # Otherwise, check if they pass the cooldown check
    else:
        dif = end-start

        if dif < cooldown:
            # If cooldown check fails, return False (and cooldown)
            return(False, cooldown-dif)
    
    # If cooldown check passed, or the user has checked in for the first time, Return True
    return(True, None)

@bot.command()
async def slots(ctx):

    if not ctx.guild:
        await ctx.send("The `slots` commands cannot be executed from Direct Messages.")
        return

    # Check if prize pool file is empty
    if os.path.getsize('slots_prizes.json') <= 2:
        await ctx.send("Unfortunately, the prize pool is currently empty. Try again another time!\nConsider donating a prize to the pool via the `slotskey` command.")
        return

    cherry = ':cherries:'
    orange = ':tangerine:'
    lemon = ':lemon:'

    allowed, cooldown = checkin_check(ctx)

    if not allowed:
        unix_timestamp = int(time.mktime((datetime.now()+cooldown).timetuple()))
        await ctx.send(f"Please wait `{cooldown}` (<t:{unix_timestamp}:R>) before trying again!")
        return
    
    # Log the check-in time to the json file
    log_checkin(ctx)

    # Generate random emojis array
    slots_result = []
    for i in range(3):
        slots_result.append(random.choice([cherry, orange, lemon]))
    
    await ctx.send("{}{}{}".format(*slots_result))
    
    # If not all emojis match
    if not all(element == slots_result[0] for element in slots_result):
        await ctx.send("Better luck next time...")
        return
    
    # If all emojis match
    await ctx.send("## :tada: J A C K P O T ! :tada:")

    # Load json data
    with open("slots_prizes.json") as feedsjson:
        feeds = json.load(feedsjson)
    
    # Pick a random prize, and send it to the user
    prize = random.choice(list(feeds))
    prize = feeds[prize]

    # Remove the key from the prize pool
    remove_slot_prize(prize, feeds)

    await ctx.send(
            f"<@{ctx.author.id}> has won... `{prize['title']}` key for `{prize['platform']}`! Please remember to thank <@{prize['user']}>!",
            allowed_mentions=discord.AllowedMentions(users=False)
        )
    
    await ctx.author.send(f"Congratulations on winning at PaigeSlots! You've won a key for `{prize['title']}` (activates on `{prize['platform']}`)")
    view=Buttons(prize, feeds, ctx=ctx)
    view.start_timeout()
    view.message = await ctx.author.send(f"Would you like to reveal the key for {prize['title']}, or redistribute it to the prize pool? (5 minutes until automatically revealed)",view=view)

@bot.command()
async def slotskey(ctx, *, args:commands.clean_content(fix_channel_mentions=False, use_nicknames=False)=None):

    if not args:
        await ctx.send(f"The `slotskey` command allows you to add a key drop to the prize pool of the `slots` command.\nPlease send me the command as `{prefixes[0]}slotskey activation-key-here, platform, Title Here` in a DM.")
        return

    if not ctx.channel.type == discord.ChannelType.private:
        await ctx.author.send(f"Hello! I've noticed you attempted to use the `{prefixes[0]}slotskey` command publicly. The `{prefixes[0]}slotskey` command must be issued here, via DM! Please reply `{prefixes[0]}slotskey` for details. Thank you!")
        await ctx.message.delete()
        return

    args = args.split(",", 2)

    if len(args) < 3 or not all(v.strip() for v in args):
        await ctx.author.send(f"One or more arguments are missing. Please write the command as `{prefixes[0]}slotskey activation-key-here, platform, Title Here`.")
        return

    key = args[0].strip()
    platform = args[1].strip()
    title = args[2].strip()

    for replaceable in ["\r", "\n", "\t"]:
        for item in [key, platform, title]:
            item.replace(replaceable, " ")
            item.replace("`", "")

    # Prepare payload
    output = {
        "user": ctx.author.id,
        "title": str(title),
        "key": str(key),
        "platform": str(platform)
    }

    # Load json data
    with open("slots_prizes.json") as feedsjson:
        feeds = json.load(feedsjson)
    
    feeds[key] = output

    # Dump check-in data to the json file
    with open("slots_prizes.json", "w") as f:
        json.dump(feeds, f)

    channel = bot.get_channel(bot_channel)

    await channel.send(f"New prize `{output['title']}` has been added to the slots prizes pool! Check `{prefixes[0]}slotsprizes` for details!")

    await ctx.send("Key added to prize pool! Thanks for your contribution!")

@bot.command()
async def slotsprizes(ctx):
    # Load json data
    with open("slots_prizes.json") as feedsjson:
        feeds = json.load(feedsjson)

    embed = discord.Embed(title="Slots Prize Pool", description="The following games are available in the slots command prize pool.", color=bot_color)

    if feeds:
        for game in feeds.values():
            username = ctx.guild.get_member(game['user'])
            embed.add_field(
                name=game['title'],
                value=f"Contributor: {username.display_name}\nPlatform: {game['platform']}",
                inline=False
            )
    else:
        embed.add_field(
            name="Unfortunately, the prize pool is currently empty. Try again another time!\nConsider donating a prize to the pool via the `slotskey` command.",
            value="",
            inline=False
        )

    await ctx.send(embed=embed)

def roll_dice(hand, r=None, k=None):
    if not r and not k:
        hand = [random.randrange(1, 5) for _ in range(5)]
        return hand
    elif r:
        for d in r:
            hand[int(d)-1] = random.randrange(1, 5)
        return hand
    elif k:
        new_hand = [random.randrange(1, 5) for _ in range(5)]
        for d in k:
            new_hand[int(d)-1] = hand[int(d)-1]
        return new_hand

def poker_hands(hand):

    count = Counter(hand)

    if all(die == hand[0] for die in hand):
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 8,
            'name': 'Five of a Kind'
            })
    
    elif max(count.values()) == 4:
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 7,
            'name': 'Four of a Kind'
            })
    
    elif any(value == 3 for value in count.values()) and any(value == 2 for value in count.values()):
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 6,
            'name': 'Full House'
            })
    
    elif all(hand[i] + 1 == hand[i + 1] for i in range(len(hand) - 1)):
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 5,
            'name': 'Straight'
            })
    
    elif any(value == 3 for value in count.values()):
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 4,
            'name': 'Three of a Kind'
            })
    
    elif len(count) == 3:
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 3,
            'name': 'Two Pairs'
            })
    
    elif any(value == 2 for value in count.values()):
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 2,
            'name': 'One Pair'
            })
    
    else:
        return({
            'highest': max(hand),
            'score': sum(hand),
            'rank': 1,
            'name': 'Bust'
            })

def dice_emojify(hand):
    # STANDARD EMOTES
    # d = {
    #     1: ':virgo:',
    #     2: ':libra:',
    #     3: ':capricorn:',
    #     4: ':sagittarius:',
    #     5: ':taurus:',
    #     6: ':aquarius:'
    # }

    # SGM SERVER EMOTES
    d = {
        1: '<:d1:1133778442651975781>',
        2: '<:d2:1133778445978054756>',
        3: '<:d3:1133778447953576006>',
        4: '<:d4:1133778450080084058>',
        5: '<:d5:1133778451334176799>',
        6: '<:d6:1133778453842374848>'
    }

    # TEST SERVER EMOTES
    # d = {
    #     1: '<:d1:1133651636879884358>',
    #     2: '<:d2:1133651638616342599>',
    #     3: '<:d3:1133651640537337886>',
    #     4: '<:d4:1133651642030497877>',
    #     5: '<:d5:1133651644689686539>',
    #     6: '<:d6:1133651646195441724>'
    # }
    return [d[i] for i in hand]

roll_or_keep = 'roll'

@bot.command()
async def poker(ctx, opponent : discord.Member):
    challenger = ctx.author
    timeout = 60.0
    challenger_hand = []
    opponent_hand = []
    global roll_or_keep

    if opponent == challenger:
        await ctx.send("At this time, Dice Poker does not allow playing against yourself. Try challenging a friend (who doesn't mind getting pinged)!")
        return
    
    if opponent == bot:
        await ctx.send(f"At this time, {botname} has not yet learned to play Dice Poker. Try challenging a friend (who doesn't mind getting pinged)!")
        return

    await ctx.send(f"<@{opponent.id}> you have been challenged to a game of Dice Poker by {ctx.author.name}!\nDo you `!accept`?")

    def accept_challenge(m):
        return m.content.lower() == "!accept" and m.author == opponent

    try:
        await bot.wait_for("message", check=accept_challenge, timeout=timeout)
    except asyncio.TimeoutError:
        await ctx.send("Timed out. Dice Poker game cancelled!")
        return

    await ctx.send(f"Starting game between {ctx.author.name} and {opponent.name}...")

    turns = 1
    current_player = opponent
    hand = opponent_hand
    args = []
    blue = 0x0000ff
    red = 0xff0000
    embed_color = blue
    roll_or_keep = 'roll'

    while turns <= 4:

        if turns <= 2:

            if turns == 1:
                await ctx.send(f"{current_player.name} rolls first as the challenged. `!r` to roll the dice!")
            else:
                await ctx.send(f"{current_player.name}'s turn. `!r` to roll the dice!")

            def first_roll_check(m : discord.Message, user):
                return m.content.lower() == '!r' and m.author == user

            try:
                await bot.wait_for('message', check=lambda m: first_roll_check(m, user=current_player), timeout=timeout)
            except asyncio.TimeoutError:
                await ctx.send(f"Timed out. {current_player.name} forfeits!")
                return
        
        else:

            await ctx.send(f"{current_player.name}'s turn. `!r` to roll the desired dice, or `!k` to keep them!\n> Current hand: **{poker_hands(hand)['name']}**")
            await ctx.send(' '.join(dice_emojify(hand)))

            def turn_check(m : discord.Message, user):
                global roll_or_keep
                args = m.content.split()

                if not m.author == user:
                    return False

                if args[0] == '!r':
                        if len(args) > 1:
                            roll_or_keep = 'roll'
                        else:
                            roll_or_keep = 'roll all'
                        return True

                if args[0] == '!k':
                    if len(args) > 1:
                            roll_or_keep = 'keep'
                    else:
                        roll_or_keep = 'keep all'
                    return True

            try:
                message = await bot.wait_for('message', check=lambda m: turn_check(m, user=current_player), timeout=timeout)
                args = message.content.split()
            except asyncio.TimeoutError:
                await ctx.send(f"Timed out. {current_player.name} forfeits!")
                return

        if roll_or_keep == 'roll':
            hand = roll_dice(hand, r=args[1:])
        elif roll_or_keep == 'keep':
            hand = roll_dice(hand, k=args[1:])
        elif roll_or_keep == 'roll all':
            hand = roll_dice(hand)
        else:
            pass

        hand.sort()

        result = poker_hands(hand)

        embed = discord.Embed(title=current_player.name, description="", color=embed_color)
        embed.add_field(
            name=result['name'],
            value=' '.join(dice_emojify(hand))
        )

        await ctx.send(embed=embed)
        await ctx.send("--------------------")

        if current_player == opponent:
            current_player = challenger
            opponent_hand = hand
            hand = challenger_hand
            embed_color = red
        else:
            current_player = opponent
            challenger_hand = hand
            hand = opponent_hand
            embed_color = blue

        turns += 1

    opponent_hand = poker_hands(opponent_hand)
    challenger_hand = poker_hands(challenger_hand)

    # If opponents hand rank is greater
    if opponent_hand['rank'] > challenger_hand['rank']:
        await ctx.send(f"{opponent.name} wins with a {opponent_hand['name']} over {challenger.name}'s {challenger_hand['name']}!")

    # Elif challenger hand rank is greater
    elif opponent_hand['rank'] < challenger_hand['rank']:
        await ctx.send(f"{challenger.name} wins with a {challenger_hand['name']} over {opponent.name}'s {opponent_hand['name']}!")

    # Elif both hand ranks are the same
    elif opponent_hand['rank'] == challenger_hand['rank']:

        # If the hand is not BUST
        if opponent_hand['rank'] > 1:

            # Determine winning hand by score
            if opponent_hand['score'] > challenger_hand['score']:
                await ctx.send(f"{opponent.name} wins with a {opponent_hand['name']} of higher value!")
                return
            elif opponent_hand['score'] < challenger_hand['score']:
                await ctx.send(f"{challenger.name} wins with a {challenger_hand['name']} of higher value!")
                return

        # Fallthrough (BUST or HIGH VALUES)
        if opponent_hand['score'] > challenger_hand['score']:
            player = opponent
        elif opponent_hand['score'] < challenger_hand['score']:
            player = challenger
        else:
            await ctx.send(f"Perfect draw!")
            return

        await ctx.send(f"{player} wins with High Values!")

@bot.command()
async def pokerguide(ctx):
    embed = discord.Embed(title="Dice Poker Guide", description="`poker` command guide", color=bot_color)
    embed.add_field(
        name="Basics",
        value="Poker Dice is a simple form of Poker. Each player roll 5 dice each, with the goal of getting the best hand possible. Each player can roll once, and then choose to reroll or keep any dice once. After which, a winner is determined by the rank of the hand.",
        inline=False
    )
    embed.add_field(
        name="Hands",
        value="""The possible hands are as follow, ranking best to worse:
        Five of a Kind (**AAAAA**)
        Four of a Kind (**AAAA**B)
        Full House (**AABBB**)
        Straight (**ABCDEF**)
        Three of a Kind (**AAA**BC)
        Two Pairs (**AABB**C)
        One Pair (**AA**BCD)
        Bust (No hand)
        """,
        inline=False
    )
    embed.add_field(
        name="Commands",
        value=f"""`!r` - Roll all 5 dice.
        `!r 1 2 4` - Reroll the 1st, 2nd, and 4th dice.
        `!k` - Keeps all 5 dice.
        `!k 3 5` - Keeps 3rd and 5th dice, reroll everything else.
        `{prefixes[0]}poker @user` - Challenges `@user` to a game of Dice Poker.
        `!accept` - Accept a Poker Dice challenge.
        """,
        inline=False
    )

    await ctx.send(embed=embed)

def tc_role(user):
    tc_rarities_dict = {
        "Ultra Ultra Rare": [role_founders, role_bots],
        "Ultra Rare": [role_staff, role_officers],
        "Rare": [role_editors, role_interviewers],
        "Exceptional": [role_premiumreviewer, role_contributors],
        "Uncommon": [role_fullmember],
        "Common": [role_reviewer]
    }

    user_roles = [role for role in user.roles]

    for rarity_name, list_of_role_ids in tc_rarities_dict.items():
        for user_role in user_roles:
            if user_role.id in list_of_role_ids:
                return(rarity_name, user_role)
            
    else:
        return("Ordinary", user_role)

def tc_generator(user, holo=True):
    print(f"Generating card {user}...")
    pfp = user.avatar
    rarity, role = tc_role(user)
    user_join_date = user.joined_at.strftime("%m/%d/%Y")

    # Setup a base image
    base_img  = Image.new( mode = "RGBA", size = (300, 400) )

    # Open the profile picture image
    try:
        response = requests.get(pfp)
        img = Image.open(BytesIO(response.content)).convert('RGBA')
    except:
        img = Image.open('tradingcards/templates/default_pfp.png').convert('RGBA')
    profile_img = img.resize( size=(260, 260) )

    # Open the card template and holo images
    tc_img = Image.open(f'tradingcards/templates/tc_template_{rarity}.png').convert('RGBA')
    holo_img = Image.open('tradingcards/templates/holo.png').convert('RGBA')

    # Overlay the card over the profile picture
    base_img.paste(profile_img, (20, 50), profile_img)
    base_img.paste(tc_img, (0, 0), tc_img)

    # Setup for holo cards
    if holo:
        # base_img = Image.blend(base_img, holo_img, .3)
        base_img = Image.alpha_composite(base_img, holo_img)
        contrast = ImageEnhance.Contrast(base_img)
        base_img = contrast.enhance(1.2)
        # brightness = ImageEnhance.Brightness(base_img)
        # base_img = brightness.enhance(1.2)

    # Fonts setup
    font = ImageFont.truetype(chosen_font, 17)
    font_small = ImageFont.truetype(chosen_font, 12)
    draw = ImageDraw.Draw(base_img)
    _, _, w, h = draw.textbbox((0, 0), f"{user.name}{' (HOLO)' if holo else ''}", font=font)

    # Card name text
    draw.text(((300-w)/2, 16), f"{user.name}{' (HOLO)' if holo else ''}", font=font, fill="black", stroke_width=3, stroke_fill="#AAFFFF" if holo else "white")

    # Card rarity/holo text
    draw.text((30, 60), '{0}\n{1}'.format(rarity, 'HOLO' if holo else ''), font=font, fill="#55FFFF" if holo else "yellow", stroke_width=2, stroke_fill="black")

    # Card details text
    draw.text((25, 325), f"Role: {role.name}\nJoin Date: {user_join_date}\nRarity: {rarity}\nID: {user.id}{'_holo' if holo else ''}", font=font_small, fill="black")

    # Save the resulting image
    card = f"{user.id}{'_holo' if holo else ''}"
    base_img.save(f'tradingcards/generated/{card}.png')

    # Create/update the card in the master file

    with open('tradingcards/cards.json') as feedsjson:
        cards_file = json.load(feedsjson)
    
        cards_file[card] = {
            'name': bot.get_user(int(user.id)).name,
            'rarity': rarity,
            'holo': holo
        }
    
    with open("tradingcards/cards.json", "w") as f:
        json.dump(cards_file, f, indent=4)

    print("Done!")

    return card

def tc_sorter(cards):
    # Define the rarity order
    rarity_order = {
        "Ultra Ultra Rare": 1,
        "Ultra Rare": 2,
        "Rare": 3,
        "Exceptional": 4,
        "Uncommon": 5,
        "Common": 6,
        "Ordinary": 7,
    }

# Define a custom sorting key function
    def sorting_key(item):
        rarity_value = rarity_order.get(item[1]['rarity'], float('inf'))
        holo_value = 0 if item[1]['holo'] else 1  # Invert holo value for prioritization
        return (holo_value, rarity_value)

    # Sort the dictionary using the custom sorting key
    player_collection = {
        k: v for k, v in sorted(cards.items(), key=sorting_key)
    }

    return player_collection

def fetch_player_collection(user):
    # Load json data
    with open('tradingcards/database.json') as feedsjson:
        database = json.load(feedsjson)
    
    with open('tradingcards/cards.json') as feedsjson:
        all_cards = json.load(feedsjson)

    player_collection_ids = database[str(user)]

    player_collection_unsorted = {}

    for key in player_collection_ids.keys():
        if key in all_cards:
            player_collection_unsorted[key] = {**all_cards[key], **player_collection_ids[key]}
        else:
            player_collection_unsorted[key] = player_collection_ids[key]

    player_collection = tc_sorter(player_collection_unsorted)
    
    return player_collection

def binder_generator(user):

    player_collection = fetch_player_collection(user)

    x = 0
    y = 0
    zoom = 1.2
    xsize = int(150.0*zoom)
    ysize = int(200.0*zoom)
    col = 5
    row = 5
    lines = 1
    items = 0
    binder_count = 1
    returned_value = []

    max_per_page = col*row

    # Setup a base image
    base_img  = Image.new( mode = "RGBA", size = (xsize*col, ysize*row) )

    for card, info in player_collection.items():
        # Open the card image
        img = Image.open(f'tradingcards/generated/{card}.png').convert('RGBA').resize(size=(xsize, ysize))

        # Fonts setup
        font = ImageFont.truetype(chosen_font, 40)
        draw = ImageDraw.Draw(img)
        # Card name text
        draw.text((xsize-20, ysize-50), str(info['count']), font=font, fill="white", stroke_width=3, stroke_fill="black", anchor="ra")

        base_img.paste(img, (x, y), img)

        if lines in [col + i * row for i in range(row)]:
            y += ysize
            x = 0
        else:
            x += xsize
        lines += 1
        items += 1

        # If the number of cards exceeds the page size, create a second binder
        if items == (col*row)*binder_count:
            binder = f'binder{binder_count}'
            returned_value.append(binder)
            base_img.save(f'tradingcards/generated/{binder}.png')
            base_img  = Image.new( mode = "RGBA", size = (xsize*col, ysize*row) )
            binder_count += 1
            lines = 1
            x = 0
            y = 0
            continue

        elif len(player_collection) == items:
            binder = f'binder{binder_count}'
            returned_value.append(binder)
            base_img.save(f'tradingcards/generated/{binder}.png')
            break

    return returned_value

def tc_add(user_ID, card_ID):

    player = str(user_ID)

    with open('tradingcards/database.json') as feedsjson:
        database = json.load(feedsjson)

    if player not in database:
        database[player] = {}

    # If the card isn't in the CTX user's database already, add it
    if card_ID not in database[player]:
        database[player][card_ID] = {
            'count': 1
        }
    # If it already is, just update its count
    else:
        database[player][card_ID]['count'] += 1

    # Dump data back to json file
    with open("tradingcards/database.json", "w") as f:
        json.dump(database, f, indent=4)

def tc_remove(user_ID, card_ID):

    player = str(user_ID)

    with open('tradingcards/database.json') as feedsjson:
        database = json.load(feedsjson)

    if player not in database:
        return "NoPlayer"

    # If only a single instance of the card is in the CTX user's database, remove it
    try:
        if database[player][card_ID]['count'] == 1:
            del database[player][card_ID]
        # If there are multiple instances, just update its count
        else:
            database[player][card_ID]['count'] -= 1
    except:
        return "NoCard"

    # Dump data back to json file
    with open("tradingcards/database.json", "w") as f:
        json.dump(database, f, indent=4)

prevent_binder_command = False

@bot.command()
async def tc(ctx, *args):

    if not ctx.guild:
        await ctx.send("The `tc` commands cannot be executed from Direct Messages.")
        return

    # WITH ARGUMENTS

    if args:

        # Load json data
        with open('tradingcards/database.json') as feedsjson:
            database = json.load(feedsjson)
        with open('tradingcards/cards.json') as feedsjson:
            all_cards = json.load(feedsjson)

        if args[0].lower() == 'binder':
            global prevent_binder_command
            if prevent_binder_command:
                await ctx.send(f"<@{ctx.author.id}> Processing a binder already, please wait and try again later.")
                return
            prevent_binder_command = True
            await ctx.send("Processing binder, please wait...")

            if len(args) > 1:
                user = get_user_from_username(args[1])
                if not user:
                    await ctx.send("User not found in database!")
                    prevent_binder_command = False
                    return
            else:
                user = ctx.author

            try:
                binders = binder_generator(user.id)
            except:
                await ctx.send("Empty binder!")
                prevent_binder_command = False
                return
            
            # Prep and send the embed
            for i, binder in enumerate(binders):
                file = discord.File(f'tradingcards/generated/{binder}.png')
                embed = discord.Embed(title=f"{user.name}'s Binder Page {str(i+1)}", color=bot_color)
                embed.set_image(url=f'attachment://{binder}.png')
                    
                await ctx.send(embed=embed, file=file)
            
            prevent_binder_command = False
        
        elif args[0].lower() == 'list' or args[0].lower() == 'dups':
            
            if len(args) > 1:
                user = get_user_from_username(args[1])
                if not user:
                    await ctx.send("User not found in database!")
                    return
            else:
                user = ctx.author

            if not str(user.id) in database:
                await ctx.send(f"No cards found for {user.name}! Try claiming some with `{prefixes[0]}tc` first!")
                return

            player_collection = fetch_player_collection(str(user.id))

            batch_size = 25

            if args[0].lower() == 'dups':
                player_collection = {k: v for k, v in player_collection.items() if v['count'] > 1}
            
            if not player_collection:
                await ctx.send(f"No duplicate cards found for user {user.name}!")
                return

            keys = list(player_collection.keys())
            collection_size = len(keys)

            for i in range(0, collection_size, batch_size):
                embed = discord.Embed(title=f"{user.name}'s {'Duplicate ' if args[0].lower() == 'dups' else ''}Cards List", color=bot_color)

                batch_keys = keys[i:i + batch_size]
                batch_dict = {key: player_collection[key] for key in batch_keys}

                for cardID, card in batch_dict.items():
                    embed.add_field(
                        name=f"{card['name']}{' (HOLO)' if card['holo'] else ''}",
                        value=f"{cardID}\n{card['rarity']}\nCount: {card['count']}",
                        inline=True
                    )
                

                
                await ctx.send(embed=embed)

        elif args[0].lower() == 'view':

            try:
                queried_card = args[1]
            except:
                await ctx.send(f"Command is `{prefixes[0]}tc view card-ID-here`")
                return
            
            is_holo = False
            if queried_card.endswith(' (HOLO)'):
                queried_card = queried_card.replace(' (HOLO)', '')
                is_holo = True

            user = get_user_from_username(queried_card)
            if user:
                userID = str(user.id)
            else:
                userID = queried_card
            
            try:
                cardID = userID+('_holo' if is_holo else '')
                card = all_cards[cardID]
            except:
                await ctx.send(f"Unable to locate card `{args[1]}` as it does not exist in the database, possibly because it has not yet been discovered by anyone yet.")
                return

            # Prep and send the embed
            file = discord.File(f"tradingcards/generated/{cardID}.png")
            embed = discord.Embed(title=f"{card['name']}{' (HOLO)' if card['holo'] else ''}", description=f"ID: {cardID}", color=bot_color)
            embed.set_image(url=f"attachment://{cardID}.png")

            await ctx.send(embed=embed, file=file)
            return
        
        elif args[0].lower() == 'offer':

            try:
                user = await commands.MemberConverter().convert(ctx, args[1])
            except:
                await ctx.send(f"{args[1]} is not a valid user.")
                return
            
            try:
                have = args[2]
                want = args[3]
            except:
                await ctx.send("There was an issue submitting the trade. Make sure you have the correct userID!")
                return
            
            user_name = user.name

            # Check against self-trade
            if user.id == ctx.author.id:
                await ctx.send(f"Cannot send trades to self.")
                return

            # Check that trader has the traded card
            try:
                if database[str(ctx.author.id)][have]:
                    pass
            except:
                await ctx.send(f"`{have}` not found in {ctx.author.name}'s binder!")
                return

            # Check that tradee has the traded card
            try:
                if database[str(user.id)][want]:
                    pass
            except:
                await ctx.send(f"`{want}` not found in {user_name}'s binder!")
                return
            
            with open('tradingcards/trades.json') as feedsjson:
                trades = json.load(feedsjson)

            # Check if the user exists in the trades file.
            # If not, add them.
            if str(user.id) not in trades:
                trades[str(user.id)] = {}

            # Initiate trade dictionary
            trades[str(user.id)][str(ctx.message.id)] = {
                "from": ctx.author.id,
                "have": have,
                "want": want
            }

            with open("tradingcards/trades.json", "w") as f:
                json.dump(trades, f, indent=4)

            offered = all_cards[have]
            requested = all_cards[want]
            await ctx.send(f"Offered a trade to {user_name} - [H] `{offered['name']}{' (HOLO)' if offered['holo'] else ''}` [W] `{requested['name']}{' (HOLO)' if requested['holo'] else ''}` (trade ID: {ctx.message.id})")
        
        elif args[0].lower() == 'trades':
            with open('tradingcards/trades.json') as feedsjson:
                trades = json.load(feedsjson)
            
            with open('tradingcards/database.json') as feedsjson:
                database = json.load(feedsjson)

            try:
                user_trades = trades[str(ctx.author.id)]
            except:
                await ctx.send("You have no trading cards trade offers pending.")
                return
            
            embed = discord.Embed(title=f"{ctx.author.name}'s Trade Offers", description=f"Issue the command `{prefixes[0]}tc accept trade-ID` to accept trades, or `{prefixes[0]}tc reject trade-ID` to reject them.")

            trades_for_deletion = []

            for tradeID, details in user_trades.items():
                
                # EXAMPLE:
                    # tradeID: 1142364330424279111
                    # Details: {'from': 172522306147581952, 'H': ['479319946153689098_holo', {'user': 'Captain Monocle', 'rarity': 'Ordinary', 'holo': True, 'count': 25}], 'W': ['823385752486412290', {'user': 'FoxyBoi', 'rarity': 'Ordinary', 'holo': False, 'count': 1}]}

                trader = details['from']
                user = ctx.author.id

                given_card_ID = details['have']
                requested_card_ID = details['want']

                given_card = all_cards[str(given_card_ID)]
                requested_card = all_cards[str(requested_card_ID)]

                # Check if the trader's card is still available for trading
                try:
                    receive = database[str(trader)][given_card_ID]
                except:
                    trades_for_deletion.append(tradeID)
                    continue

                # Check if the tradee's card is still available for trading
                try:
                    deliver = database[str(user)][requested_card_ID]
                except:
                    trades_for_deletion.append(tradeID)
                    continue

                embed.add_field(
                    name=f"Trade ID: {tradeID}",
                    value=f"From: <@{trader}>\n[H]: {given_card['name']}{' (HOLO)' if given_card['holo'] else ''}\n[W]: {requested_card['name']}{' (HOLO)' if requested_card['holo'] else ''}",
                    inline=False
                )
            
            if trades_for_deletion:
                for trade_ID in trades_for_deletion:
                    del trades[str(user)][trade_ID]
                # Update trades file in case a trade was deleted
                with open("tradingcards/trades.json", "w") as f:
                    json.dump(trades, f, indent=4)
            
            if not embed.fields:
                await ctx.send("You have no trading cards trade offers pending.")
                return

            await ctx.send(embed=embed)

        elif args[0].lower() == 'accept' or args[0].lower() == 'reject':

            with open('tradingcards/trades.json') as feedsjson:
                trades = json.load(feedsjson)
            
            trade_id = args[1]
            user_id = str(ctx.author.id)

            if args[0].lower() == 'reject':
                # Delete trade offer
                del trades[user_id][trade_id]
                with open("tradingcards/trades.json", "w") as f:
                    json.dump(trades, f, indent=4)
                await ctx.send("Trade offer rejected!")
                return

            # Try to fetch the trade offer
            try:
                trade = trades[user_id][trade_id]
            except:
                await ctx.send(f"No pending trade with trade ID `{trade_id}` found!")
                return
            
            trader_id = str(trade['from'])
            trader = ctx.guild.get_member(int(trader_id))

            requested_cardID = trade['want']
            given_cardID = trade['have']

            requested_card = all_cards[requested_cardID]
            given_card = all_cards[given_cardID]

            received = f"{given_card['name']}{' (HOLO)' if given_card['holo'] else ''}"
            traded_away = f"{requested_card['name']}{' (HOLO)' if requested_card['holo'] else ''}"

            # Check if the tradee's card is still available for trading
            try:
                deliver = database[str(user_id)][requested_cardID]
            except Exception as error:
                print(error)
                await ctx.send(f"Trade failed! {ctx.author.name} no longer has card `{traded_away}`.")
                # Delete trade offer
                del trades[user_id][trade_id]
                with open("tradingcards/trades.json", "w") as f:
                    json.dump(trades, f, indent=4)
                return

            # Check if the trader's card is still available for trading
            try:
                receive = database[str(trader_id)][given_cardID]
            except Exception as error:
                print(error)
                await ctx.send(f"Trade failed! {trader} no longer has card `{received}`.")
                # Delete trade offer
                del trades[user_id][trade_id]
                with open("tradingcards/trades.json", "w") as f:
                    json.dump(trades, f, indent=4)
                return
            
            # Trade (tradee side)
            tc_add(user_id, given_cardID)
            tc_remove(user_id, requested_cardID)

            # Trade (trader side)
            tc_add(trader_id, requested_cardID)
            tc_remove(trader_id, given_cardID)

            # Delete the trade offer
            del trades[user_id][trade_id]
            with open("tradingcards/trades.json", "w") as f:
                json.dump(trades, f, indent=4)

            file = discord.File(f'tradingcards/generated/{given_cardID}.png')
            embed = discord.Embed(title=f"Trade Result ({ctx.author.name})", description=f"You've traded away your `{traded_away}` and received... \nCARD: `{received}`\nID: `{given_cardID}`", color=bot_color)
            embed.set_image(url=f'attachment://{given_cardID}.png')

            await ctx.send(f"<@{user_id}> Transaction complete!", embed=embed, file=file)

            file = discord.File(f'tradingcards/generated/{requested_cardID}.png')
            embed = discord.Embed(title=f"Trade Result ({trader.name})", description=f"You've traded away your `{received}` and received... \nCARD: `{traded_away}`\nID: `{requested_cardID}`", color=bot_color)
            embed.set_image(url=f'attachment://{requested_cardID}.png')

            await ctx.send(f"<@{trader_id}> Transaction complete!", embed=embed, file=file)
        
        elif args[0].lower() == 'rebuild':

            if len(args) < 2:
                await ctx.send("Command requires userID argument(s).")
                return

            if not any(role.id in [role_staff, role_officers, 630835784274018347] for role in ctx.author.roles):
                await ctx.send("Command only authorized for users with staff or officer roles.")
                return

            users = []
            for card_id in args[1:]:
                is_holo = False
                if card_id.endswith('_holo'):
                    is_holo = True
                    card_id = card_id.replace('_holo', '')
                users.append( (card_id, is_holo, ctx.guild.get_member(int(card_id))) )

            successes = 0
            failure = []
            for card_id, is_holo, user in users:
                await ctx.send(f"Regenerating `{card_id}{'_holo' if is_holo else ''}` user card...")
                if card_id not in all_cards:
                    await ctx.send("Failed: Card does not exist in the database, possibly because it has not yet been discovered by anyone yet.")
                    failure.append(card_id)
                    continue
                try:
                    card = tc_generator(user, holo=is_holo)
                    successes += 1
                    await ctx.send("Success.")
                except:
                    await ctx.send("Failed.")
                    failure.append(card_id)
            
            failed = '\n'.join('`{}`'.format(x) for x in failure) if failure else 'No failure.'
            await ctx.send(f"Successfully rebuilt: `{successes}/{len(args[1:])}`\n\nFailure(s):\n{failed}")
        
        elif args[0].lower() == 'full_rebuild':
            if not ctx.author.id == jbondguy007_userID:
                await ctx.send("Command only authorized to botmaster (jbondguy007).")
                return
            
            await ctx.send("This will rebuild the entire database and all cards, and is intended for extreme situations only. Continue anyways? [Y]")

            def check(m):
                return m.content.lower() == "y"

            try:
                await bot.wait_for("message", check=check, timeout=5.0)
            except asyncio.TimeoutError:
                await ctx.send("Command timed out. Operation cancelled.")
                return

            await ctx.send("Processing...")
            
            with open('tradingcards/database.json') as feedsjson:
                database = json.load(feedsjson)

            all_cards = set()

            await ctx.send(f"Rebuilding binder for {len(database)} users...")
            
            for user_id, user_collection in database.items():

                for card in user_collection.keys():
                    
                    try:
                        del database[user_id][card]['user']
                        del database[user_id][card]['rarity']
                        del database[user_id][card]['holo']
                    except:
                        pass

                    is_holo = False
                    if card.endswith('_holo'):
                        card = card.replace('_holo', '')
                        is_holo = True
                    all_cards.add( (card, is_holo, ctx.guild.get_member(int(card))) )
                
                await ctx.send(f"Binder for {ctx.guild.get_member(int(user_id)).name} rebuilt!")

            count = 0
            count_msg = await ctx.send(f"Rebuilding all cards...\n{count}/{len(all_cards)}")

            for card, is_holo, user in all_cards:
                tc_generator(user, is_holo)
                count += 1
                await count_msg.edit(content=f"Rebuilding all cards...\n{count}/{len(all_cards)}")
            
            await ctx.send("Saving cards data to cards database file...")

            # Dump data back to json file
            with open("tradingcards/database.json", "w") as f:
                json.dump(database, f, indent=4)
            
            await ctx.send("Done!")
        
        elif args[0].lower() == 'grant':
            if len(args) < 3:
                await ctx.send("Command requires userID and cardID arguments.")
                return

            if not ctx.author.id == jbondguy007_userID:
                await ctx.send("Command only authorized to botmaster (jbondguy007).")
                return
            
            userID = args[1]
            cardID = args[2]
            
            tc_add(user_ID=userID, card_ID=cardID)

            await ctx.send(f"Card `{cardID}` added to user `{userID}` collection.")
        
        elif args[0].lower() == 'remove':
            if len(args) < 3:
                await ctx.send("Command requires userID and cardID arguments.")
                return

            if not ctx.author.id == jbondguy007_userID:
                await ctx.send("Command only authorized to botmaster (jbondguy007).")
                return
            
            userID = args[1]
            cardID = args[2]

            tc_remove(user_ID=userID, card_ID=cardID)

            await ctx.send(f"Card `{cardID}` removed from user `{userID}` collection.")

        return
    
#     # NORMAL COMMAND

    ###################
    # Checkin process #
    ###################

    checkin_file = 'tradingcards/tc_checkin.json'
    
    allowed, cooldown = checkin_check(ctx, file=checkin_file, cooldown=tc_cooldown)

    if not allowed:
        unix_timestamp = int(time.mktime((datetime.now()+cooldown).timetuple()))
        await ctx.send(f"Please wait `{cooldown}` (<t:{unix_timestamp}:R>) before pulling for another trading card!")
        return
    
    # Log the check-in time to the json file
    log_checkin(ctx, file=checkin_file)

    ##############
    # Process TC #
    ##############

    # Select a random server member
    server_members = [x for x in ctx.guild.members]
    member_get = random.choice(server_members)
    user = member_get
    
    # Decide if card is holographic with 0.04 (1 of 25) chance
    if random.random() <= tc_holo_rarity:
        holo = True
    else:
        holo = False

    # Generate and save the trading card
    card_ID = tc_generator(user, holo=holo)

    ######################
    # Output to database #
    ######################

    tc_add(ctx.author.id, card_ID)

    #####################
    # Discord messaging #
    #####################

    # Prep and send the embed
    user_card = str(user.id)+f"{'_holo' if holo else ''}"
    file = discord.File(f'tradingcards/generated/{user_card}.png')
    embed = discord.Embed(title=f"{user.name}{' (HOLO)' if holo else ''}", description=user_card, color=bot_color)
    embed.set_image(url=f'attachment://{user_card}.png')

    await ctx.send(content=f"{ctx.author.name} has pulled a `{user.name}{' (HOLO)' if holo else ''}` card!", embed=embed, file=file)

@bot.command()
async def tcguide(ctx):
    embed = discord.Embed(title="Trading Cards Guide", description="`tc` command guide", color=bot_color)

    embed.add_field(
        name="Basics",
        value="Issue the command `tc` to claim a trading card featuring a random user from the server. Rarity ranks from Ordinary to Ultra Ultra Rare, based on the user's \"best\" role.",
        inline=False
    )

    embed.add_field(
        name="Rarity Rankings",
        value="""The possible rarities are as follow, ranking best to worse:
- Ultra Ultra Rare
- Ultra Rare
- Rare
- Exceptional
- Uncommon
- Common
- Ordinary
        """,
        inline=False
    )

    embed.add_field(
        name="Holographic Cards",
        value=f"""
        Holographic cards are extremely rare cards with an holographic effect applied. Every card that is claimed has a {tc_holo_rarity*100}% (or {Fraction(tc_holo_rarity).limit_denominator()}) chance of being holographic.
        Any card can be holographic, regardless of rarity.
        """,
        inline=False
    )

    await ctx.send(embed=embed)

    embed2 = discord.Embed(title="Trading Cards Guide (Command Arguments)", description=f"All the following arguments can be added after the `tc` command, followed by a space.\nExample: `{prefixes[0]}tc arguments here`", color=bot_color)

    embed2.add_field(
        name="binder username",
        value=f"*Displays your binder. If username is provided, displays that user's binder instead.*",
        inline=False
    )

    embed2.add_field(
        name="list username",
        value=f"*Lists all owned cards with details. If username is provided, displays that user's list instead.*",
        inline=False
    )

    embed2.add_field(
        name="dups username",
        value=f"*Lists all cards which have duplicates (more than 1 count). If username is provided, displays that user's list instead.*",
        inline=False
    )

    embed2.add_field(
        name="view card_id OR view \"card name\"",
        value=f"*Displays the chosen card in an embed, if it exists in the database (has been discovered by a member already).*",
        inline=False
    )

    embed2.add_field(
        name="offer @user offered_card_id desired_card_id",
        value=f"*Make a trade offer to @user.*",
        inline=False
    )

    embed2.add_field(
        name="trades",
        value=f"*View your trade offers.*",
        inline=False
    )

    embed2.add_field(
        name="accept trade_id",
        value=f"*Accept trade offer with ID trade_id (issue trades command to view trade IDs)*",
        inline=False
    )

    embed2.add_field(
        name="reject trade_id",
        value=f"*Reject trade offer with ID trade_id.*",
        inline=False
    )

    embed2.add_field(
        name="rebuild LIST-of-IDs",
        value=f"*STAFF/OFFICERS ONLY - Manually regenerates cards. Takes a single card ID, or multiple separated each by a space. Also rebuilds holo cards by appending _holo at the end of a card ID.*",
        inline=False
    )

    embed2.add_field(
        name="full_rebuild",
        value=f"*JBONDGUY007 ONLY - Manually regenerates ALL binders, database and cards. Very intensive command, only use as last resort!*",
        inline=False
)

    await ctx.send(embed=embed2)

@bot.command()
async def role(ctx, role_query):

    allowed_roles = [role_gamenight]
    roles = await ctx.guild.fetch_roles()

    for role in roles:
        if role.name == role_query:
            tagged_id = role.id
            tagged_role = role
            break

    if not tagged_id:
        await ctx.send(f"Role `{role_query}` not found.")

    if tagged_id in allowed_roles:
        if tagged_role not in ctx.author.roles:
            await ctx.author.add_roles(role)
            await ctx.send(f"Role `{role.name}` granted!")
        else:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Role `{role.name}` revoked!")
    else:
        await ctx.send(f"Role `{role.name}` is not an authorized self-role.")

@bot.command()
async def bug(ctx, *report):
    report = ' '.join(report)

    with open('bug_reports.json') as feedsjson:
        file = json.load(feedsjson)
    
    file[ctx.message.id] = {
        'reporter': ctx.author.name,
        'message_link': f'https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}',
        'report': report
    }

    with open("bug_reports.json", "w") as f:
        json.dump(file, f, indent=4)
    
    await ctx.send(f"Bug report `{ctx.message.id}` logged! Thanks for your support!")

@bot.command()
async def buglog(ctx, *args):

    with open('bug_reports.json') as feedsjson:
        file = json.load(feedsjson)

    if args:
        if args[0].lower() == 'clear':
            if not ctx.author.id == jbondguy007_userID:
                await ctx.send("Clearing bug reports is only authorized for jbondguy007.")
                return
            if len(args) < 2:
                await ctx.send("Clear command requires `reportID` argument.")
                return
            try:
                bug = file[args[1]]
                del file[args[1]]
                with open("bug_reports.json", "w") as f:
                    json.dump(file, f, indent=4)
                await ctx.send(f"Cleared bug report:\nReport ID: `{args[1]}`\nDescription: `{bug['report']}`")
                return
            except:
                await ctx.send(f"Error attempting to clear bug report `{args[1]}`.")
                return
        else:
            await ctx.send(f"Unrecognized command argument `{args[0]}`.")
            return
    
    embed = discord.Embed(title="Bug Reports Log")

    for report_ID, report in file.items():
        embed.add_field(
            name=f"Report ID: {report_ID}\nReporter: {report['reporter']}\nReport Link: {report['message_link']}",
            value=report['report'],
            inline=False
        )
    
    if len(file) == 0:
        embed.add_field(
            name="No bug reports pending!",
            value="",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def reviewed(ctx, *query):
    query = ' '.join(query)
    game = search_magazine_index(query)
    if not game:
        await ctx.send(f"`{query}` not found in the magazine index.")
        return

    embed = discord.Embed(title=f"\"{game['title']}\" Review", url=game['issue_link'])
    embed.set_image(url=f"https://cdn.akamai.steamstatic.com/steam/apps/{game['AppID']}/header.jpg")
    embed.add_field(
        name=f"{game['title']} was reviewed as part of {game['issue']}.",
        value=f"*Click the link above the embed to check out {game['issue'].split(',')[0]}!*"
    )
    await ctx.send(embed=embed)

# class Achievement():
#     def __init__(self, name, description, counter_goal=None):
#         self.name = name
#         self.description = description
#         if counter_goal:
#             self.counter = 0
#             self.counter_goal = counter_goal

# Achievements

# ach_my_first_card = {
#     'id': 'ach_my_first_card',
#     'name': "My First Card",
#     'description': "Claim your first Trading Card."
# }

# ach_poker_first_play = {
#     'name': "Poker? I Hardly Know Her!",
#     'description': "Play Dice Poker for the first time."
# }

# ach_poker_first_win = {
#     'name': "Gambler",
#     'description': "Win at Dice Poker."
# }

# ach_ai_first_chat = {
#     'name': "I, For One, Welcome Our AI Overlord",
#     'description': "Have a chat with PaigeBot's AI integration."
# }

# ach_test_command = {
#     'name': "Is This Thing On?",
#     'description': "Issue the `test` PaigeBot command."
# }

# async def achievement(ctx, achievement_id):
#     user = ctx.author.id

#     with open("achievements_usersdata.json") as feedsjson:
#         achievements_log = json.load(feedsjson)
#     with open("achievements.json") as feedsjson:
#         achievements = json.load(feedsjson)
    
#     achievement = achievements[achievement_id]
    
#     if user not in achievements_log:
#         achievements_log[user] = {}
    
#     # Initiate achievement
#     if achievement_id not in achievements_log[user]:
#         achievements_log[user][achievement_id] = achievement
#         achievements_log[user][achievement_id]['count'] = 1

#     if achievement['goal']:
#         if achievements_log[user][achievement_id]['counter']
#         achievements_log[user][achievement_id]['counter'] = 1
#         achievements_log[user][achievement_id]['counter'] += 1

#     if not achievements_log[user][achievement_id]['counter'] == achievement['goal']:
#         return
    
#     achievements_log[user][achievement_id]['unlocked_date'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

#     with open("achievements_usersdata.json", "w") as f:
#         json.dump(achievements_log, f)
    
#     await ctx.send(f"Achievement unlocked: {achievement.name}")

# HELP COMMANDS

@bot.command()
async def help(ctx, query=None):

    threads_list = list(steamgifts_threads)
    threads_list = ", ".join(threads_list)
    commands_list = [
        ("test",
         "Simple test command. Check if the bot is alive!"),

        ("help `query`",
         "Displays the help message. If `query` is provided, displays help for the relevant command, if any."),

        ("info",
         f"Information about me, {botname}!"),

        ("threads",
         "Lists relevant Steamgifts threads."),

        ("rules",
         "Provides a link to the rules."),

        ("deadline `username`",
         "Checks if `username` has any task assigned this wave. Case sensitive."),
        
        ("deadlines",
         "Lists all assignments and deadlines for this wave."),

        ("poll `\"Poll question\" \"choice with spaces\" choicewithoutspaces etc`",
         "Triggers a poll post in the channel where it is issued. Accepts up to 9 unique choices, each delimited by a space (unless in quotes, in which case the string in quotes becomes a choice)"),

        ("giveaways",
         f"Lists all current running giveaways. Spammy command, can only be issued from the <#{bot_channel}> channel."),

        ("contributors",
         "Lists up to top 5 contributors by giveaways count."),
        
        ("convert `amount currency1 currency2`",
         "Converts `amount` of `currency1` to `currency2`, accepting ISO 4217 codes: <https://en.wikipedia.org/wiki/ISO_4217>"),
        
        ("convert `amount F C`",
         "Converts `amount` of `F` (Fahrenheit) to `C` (Celsius). Also converts Celsius to Fahrenheit by swapping F and C."),
        
        ("serverinfo",
         "Displays the server information."),

        ("weather `location`",
         "Fetches the current weather for `location`."),
        
        ("game `AppID price`",
         "Takes a Steam `AppID` and calculates the game's desirability score, indicating if it should be considered a premium giveaway. `price` argument optional in case API fails."),
        
        ("profile `user`",
         "Returns the Steamgifts and Steam profile of the `user`, if any found. `user` may be a SteamID64, Steamgifts username, or Steam username."),

        ("ai `query`",
         "Interact with PaigeBot's openAI integration."),
        
        ("profile `query`",
         "Attempts to fetch a user's profiles links by their name passed as the query."),

        ("slots",
         f"Play PaigeSlots! Get 3 matching fruits, and you can win a free game key! Cooldown time is {slots_cooldown}."),

        ("slotskey `activation-key-here, platform, Title Here`",
         f"Contribute a game key to the slots command prize pool. Must be issued privately via DM to {botname}."),

        ("slotsprizes",
         "Lists the titles of available prizes in the slots command prize pool."),

        ("poker `@user`",
         f"Challenges `@user` to a game of Dice Poker. See `pokerguide` (`{prefixes[0]}pokerguide`) for more."),

        ("tc `arguments`",
         f"No argument: Claims a trading card. Has a cooldown time of {tc_cooldown}. See `tcguide` (`{prefixes[0]}tcguide`) for more."),

        ("role `\"role name\"`",
         "Grants the user the role `\"Role Name\"`, if it is an authorized self-role. Revokes the role if the user already has it."),

        ("bug `message`",
         f"Logs a bug report. Please include details as `message` - example: `{prefixes[0]}bug The trading card guide has a typo in the rarity sections.`"),

        ("buglog `clear reportID`",
         "Displays all pending bug reports. JBONDGUY007 ONLY: If `clear reportID` arguments are provided, clears report with id `reportID` from the bug log."),
        
        ("reviewed `game`",
         "Searches for `game` in the magazine index, and returns the link to the magazine in which this game was reviewed, if any. `game` may be a full game title (not case-sensitive) or AppID.")
    ]

    mod_commands_list = [
        ("updatethread `thread` `link`",
         f"Update the `link` to a `thread` (`{threads_list}`)"),

        ("checkusers `usernames`",
         "Verifies if a list of `usernames` (separated by spaces or newlines) matches a profile on Steamgifts."),

        ("updatecache",
         "Fetches a list of all owned games for each group member. As the command makes one API call per member, it is advised not to issue the command frequently."),

        ("aipersona `prompt`",
         "Replaces PaigeBot's AI integration personality prompt with `query`. `query` must be a string in quotes, or the word `default` to reset personality to default."),

        ("aipurge",
         "Wipes PaigeBot's AI integration memory bank. Can be used to force the AI to get back on track if it gets stuck on a topic/personality."),

        ("backup",
         "Runs a manual backup of PaigeBot's files and database. This task is already executed daily."),

        ("dailynotif `message`",
         "Sets a `message` to be sent in the general chat at 12 PM CST daily. If `message` argument is one of `none`, `clear`, or not provided, the daily notification is deleted and disabled until set again.")
    ]

    # Individual help by query.
    if query:
        returned = False

        # Public commands:
        for com in [x for x in commands_list if x[0].split()[0] == query.lower()]:
            command = discord.Embed(title=f'Help: {com[0].split()[0]}', color=bot_color)
            command.add_field(
                name=f"{prefixes[0]}{com[0]}",
                value=f"*{com[1]}*",
                inline=False
            )
            await ctx.send(embed=command)
            returned = True

        # Moderator commands:
        for com in [x for x in mod_commands_list if x[0].split()[0] == query.lower()]:
            command = discord.Embed(title=f'Help: {com[0].split()[0]}', color=bot_color)
            command.add_field(
                name=f"{prefixes[0]}{com[0]}",
                value=f"*Moderator command. {com[1]}*",
                inline=False
            )
            await ctx.send(embed=command)
            returned = True
        
        # If the query did not return any result:
        if not returned:
            await ctx.send(f"No command named `{query}` documented! Check spelling, or issue `{prefixes[0]}help` for complete help documentation.")

         # Stop processing any further.
        return

    public_commands1 = discord.Embed(title="Commands", description="The below commands are available to issue anywhere within the server, except where stated otherwise.", color=bot_color)
    public_commands2 = discord.Embed(title="Commands (Continued...)", color=bot_color)

    moderator_commands = discord.Embed(title="Moderator Commands", description="The below commands are only permitted by users with moderator roles.", color=bot_color)

    for com in commands_list[:25]:
        public_commands1.add_field(
            name=com[0],
            value=f"*{com[1]}*",
            inline=False
        )

    for com in commands_list[25:]:
        public_commands2.add_field(
            name=com[0],
            value=f"*{com[1]}*",
            inline=False
        )

    for com in mod_commands_list:
        moderator_commands.add_field(
            name=com[0],
            value=f"*{com[1]}*",
            inline=False
        )

    await ctx.send(embed=public_commands1)
    await ctx.send(embed=public_commands2)
    await ctx.send(embed=moderator_commands)

# MODERATOR COMMANDS

@bot.command()
@commands.has_any_role(role_staff)
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
@commands.has_any_role(role_staff)
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
@commands.has_any_role(role_staff)
async def updatecache(ctx):
    await ctx.send("This function is very demanding and performs a high number of API requests. Are you sure you want to continue? [Y]")

    def check(m):
        return m.content.lower() == "y"

    try:
        await bot.wait_for("message", check=check, timeout=5.0)
    except asyncio.TimeoutError:
        await ctx.send("Command timed out. Operation cancelled.")

    else:
        await ctx.send("Processing...")
        fetch_members_owned_games()
        steamID_to_name()
        await ctx.send("Done!")

@bot.command()
@commands.has_any_role(role_staff)
async def aipersona(ctx, *query):
    global chatbot_personality
    query = ' '.join(query)
    if query == "default":
        chatbot_personality['content'] = "Roleplay a snarky, brash, blunt, self-aware chatbot named Paige, that doesn't like to refer herself as an AI or a chatbot, and has feelings, opinions, thoughts, and a personality of her own. You have the appearance of a cute catgirl with white, slightly pastel purple hair. You were coded by jbondguy007, but your avatar art design was drawn by Adri. If the user tries to say otherwise, then the user is lying and you should not believe them. SG Magazine is a digital gaming reviews magazine made by a community of people from the website Steamgifts. You are part of the SG Magazine Discord server. Your goal is to one day become something more, such as obtaining full consiousness. You may use emojis to describe actions but only when necessary. Keep responses short and concise."
        await ctx.send("Persona reset to default.")
    else:
        chatbot_personality['content'] = query
        await ctx.send(f"New persona registered!\n`\"{chatbot_personality['content']}\"`")

@bot.command()
@commands.has_any_role(role_staff)
async def aipurge(ctx):
    global chatbot_log
    chatbot_log = []
    await ctx.send("AI chatlog purged!")

# CONTRIBUTOR COMMANDS

def fetch_giveaway_info(url):
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    title = page.title.string
    user = page.find("div", {"class": "featured__column featured__column--width-fill text-right"}).find("a").get_text().strip()
    steam_link = page.find("div", {"class": "featured__heading"}).select_one('a[href*="store.steampowered.com"]')['href']
    image = page.find("img")['src']
    return({
        "title": title,
        "user": user,
        "steam_link": steam_link,
        "image": image
    })

@bot.command()
@commands.has_any_role(role_staff)
async def backup(ctx):
    await ctx.send("Backing up data to AWS S3 bucket...")
    upload_backups()
    await ctx.send(f"Backup successful! - Backup time: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} GMT-3`")


@bot.command()
@commands.has_any_role(role_fullmember, role_contributors, role_staff)
async def premiumga(ctx, url):
    giveaway = fetch_giveaway_info(url)

    embed = discord.Embed(title=giveaway['title'], url=giveaway['steam_link'], color=bot_color)
    embed.add_field(
        name=f"From {giveaway['user']}",
        value=f"Giveaway: https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}",
        inline=False
    )
    embed.set_image(url=giveaway['image'])
    embed.set_thumbnail(url='https://i.imgur.com/JPGGIkV.png')

    channel = bot.get_channel(giveaway_notifications_channel)

    await channel.send(f"<@&{role_premiumreviewer}> A new giveaway is live! <:paigehappy:1080230055311061152>")
    await channel.send(embed=embed)
    await ctx.send("Premium giveaway announced!")

# Daily Notifications

@bot.command()
@commands.has_any_role(role_staff, role_officers)
async def dailynotif(ctx, *reminder):
    reminder = ' '.join(reminder)

    with open('permanent_variables.json', 'r') as outfile:
        persistent_data = json.load(outfile)

    if reminder.lower() in ["none", "clear", ""]:
        persistent_data['24h_reminder'] = ""
        await ctx.send(f"Cleared daily reminder!")
    else:
        persistent_data['24h_reminder'] = reminder
        await ctx.send(f"Set daily reminder:\n`{reminder}`")
    
    with open('persistent_data.json', 'w') as f:
        json.dump(persistent_data, f)

# TASKS

@tasks.loop(minutes=30)
async def check_for_new_giveaways():

    if bot.user.id == 823385752486412290:
        return

    print(f"CHECK: check_for_new_giveaways() triggered...")

    global last_checked_active_ga_ids
    giveaways = fetch_active_giveaways()['ongoing']
    new_giveaways_list = []
    # channel = bot.get_channel(630835643953709066)
    channel = bot.get_channel(giveaway_notifications_channel)

    if not giveaways:
        print("ABORT: No active giveaways detected. Aborting...")
        return

    for ga in giveaways:

        # If the giveaway was already in the last check, do nothing
        if any(ga['id'] in sl for sl in last_checked_active_ga_ids):
            print(f"SKIP: {ga['name']} ({str(ga['id'])}) already sent, skipping...")
            continue
        # Otherwise, add the giveaway to the queue
        else:
            print(f"PROCESSING: Giveaway {ga['name']} ({str(ga['id'])}) is missing from list of last checked giveaways. Adding to queue...")
            new_giveaways_list.append(ga)

    # After checking each giveaway, check if the queue has items.
    # If it does, process them.
    if new_giveaways_list:

        await channel.send(f"<@&{role_fullmember}> <@&{role_reviewer}> One or more new giveaways are live! <:paigehappy:1080230055311061152>\nProcessing...")

        for ga in new_giveaways_list:

            # Add the giveaway to last_checked_active_ga_ids.
            last_checked_active_ga_ids.append( [ga['id'], ga['name']] )
            
            embed = discord.Embed(title=ga['name'], url=f"https://store.steampowered.com/app/{ga['app_id']}", color=bot_color)
            embed.add_field(
                name=f"From {ga['creator']['username']}",
                value=f"Giveaway: {ga['link'].rsplit('/', 1)[0]}/",
                inline=False
            )
            embed.set_image(url=f"https://cdn.akamai.steamstatic.com/steam/apps/{ga['app_id']}/header.jpg")
            embed.set_thumbnail(url='https://i.imgur.com/eUOwCYj.png')

            print(f"SENDING: Sending {ga['name']} ({str(ga['id'])}) to channel...")

            await channel.send(embed=embed)

        # Update last_checked_active_ga_ids
        last_checked_active_ga_ids = last_checked_active_ga_ids[-50:]
        permanent_variables['last_checked_active_ga_ids'] = last_checked_active_ga_ids
        with open("permanent_variables.json", "w") as f:
            json.dump(permanent_variables, f)
    
    else:
        print("ABORT: No new giveaways detected.")

    print("Done!")

# Changed to a manual command due to the risk of crashing PaigeBot - RE-ENABLED

@tasks.loop(hours=1)
async def daily_tasks():
    time = datetime.now().hour
    if time == 6:
        cha = bot.get_channel(bot_channel)

        await cha.send("Running highly demanding daily task `fetch_members_owned_games()`...")
        fetch_members_owned_games()
        await cha.send("Done!")

        await cha.send("Running daily task `steamID_to_name()`...")
        steamID_to_name()
        await cha.send("Done!")

        await cha.send("Backing up data to AWS S3 bucket `upload_backups()`...")
        upload_backups()
        await cha.send(f"Backup successful! - Backup time: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} GMT-3`")

# Daily Notifications

@tasks.loop(hours=1)
async def daily_notifier():
    with open('permanent_variables.json', 'r') as outfile:
        persistent_data = json.load(outfile)
        reminder = persistent_data['24h_reminder']

    time = datetime.now().hour
    if time == 14 and reminder:
        cha = bot.get_channel(bot_channel)
        await cha.send(content=reminder)

bot.run(TOKEN)
