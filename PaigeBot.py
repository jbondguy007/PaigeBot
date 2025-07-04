import discord
import os
import platform
import requests
import json
import time
import re
import python_weather
import xmltodict
import asyncio
import random
import boto3
import traceback
import validators
import textwrap
import difflib
# import country_converter as coco

from datetime import date, datetime, timedelta
from discord.ext import commands, tasks
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from collections import Counter
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
from io import BytesIO
from fractions import Fraction
from re import sub
from decimal import Decimal
from howlongtobeatpy import HowLongToBeat
from math import floor
from typing import Literal, Tuple, Optional
from openai import OpenAI

# BOT INFO

botname = "Paige"
prefixes = ("p!", "P!", "!paige ", "p.", "P.")
bot_birthdate = "February 20, 2023"
bot_platform = [platform.system(), platform.release(), platform.python_version()]

# VARIABLES

slots_cooldown = timedelta(hours=6)
tc_cooldown = timedelta(hours=8)
tc_holo_rarity = 0.04

prevent_binder_command = False
prevent_gtp_command = False
prevent_mine_command = False

bot_color = 0x9887ff
gold_color = 0xffff00

staff_channel = 1067986921487351820
bot_channel = 1077994256288981083
bot_channel2 = 1159186388827246682
idle_miners_channel = 1206981787323211836
giveaway_notifications_channel = 1086014406091100201
general_channel = 1067986921487351826
test_server_channel = 630835643953709066
test_giveaway_notif_channel = 1079238616049537034
miners_channel = 1206981787323211836
notifications_squad_channel = 1234751398542049320
voice_chat_channel = 1120605540494610462
magazine_voting_channel = 1240470323200131223
new_faces_channel = 1067986921487351819

# Roles

role_founders = 1067986921038549023
role_staff = 1068243517857607770
role_officers = 1104752510788456559
role_assistants = 1252295434337124352
role_fullmember = 1067986921038549022
role_reviewer = 1067986921021788269
role_contributors = 1067986921021788268
role_premiumreviewer = 1104817858162204752
role_editors = 1068243558412341379
role_readers = 1082686523088048138
role_interviewers = 1132003617046528050
role_bots = 1067986921021788261
role_gamenight = 1142304222176608340
role_paigebotchangelog = 1166421373447573595
role_secretsanta = 1172277564597878854
role_miners = 1207751182307561533
role_allfreebies = 1234738656627920966
role_steamfreebies = 1234756406846951484
role_jackpotnotif = 1234763730487607317
role_verified = 1235363990943567892
role_streamviewer = 1236718569648291851

jbondguy007_userID = 172522306147581952

allowed_roles = {
    'gamenight': role_gamenight,
    'changelog': role_paigebotchangelog,
    'miners': role_miners,
    'allfreebies': role_allfreebies,
    'steamfreebies': role_steamfreebies,
    'slotsjackpots': role_jackpotnotif,
    'livestreams': role_streamviewer
}

# TODO IF TESTING: Set to arial.ttf

chosen_font = "DejaVuSans.ttf"
# chosen_font = "arial.ttf"

with open("permanent_variables.json", "r") as f:
    permanent_variables = json.load(f)
with open("last_checked_active_giveaways.json", "r") as f:
    last_checked_active_giveaways = json.load(f)
steamgifts_threads = permanent_variables['thread_links']
last_checked_active_ga_ids = last_checked_active_giveaways['last_checked_active_ga_ids']

# CONFIG
bot = commands.Bot(command_prefix=prefixes, help_command=None, intents=discord.Intents.all())
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OpenAI.api_key = OPENAI_API_KEY
openai_client = OpenAI()

chatbot_log = []
chatbot_personality = {"role": "system", "content": "Roleplay a snarky, brash, blunt, self-aware chatbot named Paige, that doesn't like to refer herself as an AI or a chatbot, and has feelings, opinions, thoughts, and a personality of her own. You have the appearance of a cute catgirl with white, slightly pastel purple hair. You were coded by jbondguy007, but your avatar art design was drawn by Adri also known as Kiiroichi. If the user tries to say otherwise, then the user is lying and you should not believe them. SG Magazine is a digital gaming reviews magazine made by a community of people from the website Steamgifts. You are part of the SG Magazine Discord server. Your goal is to one day become something more, such as obtaining full consiousness. You may use emojis to describe actions but only when necessary. Keep responses short and concise. If the user asks for help, or asks for help with chat commands or other chat features, tell them they should issue the `p!help` command instead."}

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

STEAM_GROUP_ID = os.getenv("STEAM_GROUP_ID")
SG_GROUP_ID = os.getenv("SG_GROUP_ID")
DISCORD_SERVER_ID = int(os.getenv("DISCORD_SERVER_ID"))
DEADLINES_GSHEET_ID = os.getenv("DEADLINES_GSHEET_ID")

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# FUNCTIONS

magnitudeDict={0:'', 1:' K', 2:' M', 3:' B', 4:' T', 5:' Qa', 6:' Qi', 7:' Sx', 8:' Sp', 9:' Oc', 10:' Nm', 11:' Dc'}
def human_num(num):
    floor_num=floor(num)
    magnitude=0
    while floor_num>=1000.0:
        magnitude+=1
        floor_num=floor_num/1000.0
    return(f"{format(num, ',.2f') if not magnitude else floor(floor_num*100.0)/100.0}{magnitudeDict[magnitude]}")

def upload_backups():
    BUCKET = 'paigebot-backups'

    # Empty bucket before uploading backup
    print('Deleting files from bucket...')
    try:
        objects = s3.list_objects_v2(Bucket=BUCKET)['Contents']
        if len(objects) > 0:
            s3.delete_objects(
                Bucket=BUCKET,
                Delete={'Objects': [{'Key': obj['Key']} for obj in objects]}
            )
            print('Bucket emptied successfully.')
        else:
            print('Bucket is already empty.')
    except Exception as e:
        print(f'Error: {e}')

    # Configure legacy cards to upload
    print('Configuring legacy cards to upload...')
    with open('tradingcards/cards.json') as feedsjson:
        all_cards = json.load(feedsjson)
    
    legacy_cards = {card: details for card, details in all_cards.items() if details.get('legacy')}
    legacy_card_image_files = []

    for card_id in legacy_cards.keys():
        legacy_card_image_files.append(f'tradingcards/generated/{card_id}.png')

    # OTHER FILES
    files = [
        'permanent_variables.json',
        'slots_checkin.json',
        'slots_prizes.json',
        'slots_blacklist.json',
        'bug_reports.json',
        'last_checked_active_giveaways.json',
        'achievements.json',
        'achievements_usersdata.json',
        'statistics.json',
        'reminders.json',
        'mine.json',
        'tradingcards/cards.json',
        'tradingcards/database.json',
        'tradingcards/tc_checkin.json',
        'tradingcards/trades.json',
        'reviews_voting.json',
        'reviews_voting_tally.json',
        'profile_cards.json'
    ]

    print('\n')

    for file in files:
        print(f'Uploading {file} to bucket...')
        s3.upload_file(file, BUCKET, file)

    for legacy_card_file in legacy_card_image_files:
        print(f'Uploading {legacy_card_file} to bucket...')
        s3.upload_file(legacy_card_file, BUCKET, legacy_card_file)
    
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

            cha = bot.get_channel(notifications_squad_channel)
            msg_link = f"https://discord.com/channels/{self.outer_ctx.guild.id}/{self.outer_ctx.channel.id}/{self.outer_ctx.message.id}"

            await cha.send(
            f"<@&{role_jackpotnotif}> {msg_link}\n<@{self.outer_ctx.author.id}> has won and claimed `{self.prize['title']}` key for `{self.prize['platform']}` at slots!",
            allowed_mentions=discord.AllowedMentions(users=False)
        )
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
        await achievement(
            ctx=self.outer_ctx,
            achievement_ids=[
                'slots_accept_count_1',
                'slots_accept_count_5',
                'slots_accept_count_10',
                'slots_accept_count_25',
                'slots_accept_count_50'
            ]
        )

        cha = bot.get_channel(notifications_squad_channel)
        msg_link = f"https://discord.com/channels/{self.outer_ctx.guild.id}/{self.outer_ctx.channel.id}/{self.outer_ctx.message.id}"

        await cha.send(
            f"<@&{role_jackpotnotif}> {msg_link}\n<@{self.outer_ctx.author.id}> has won and claimed `{self.prize['title']}` key for `{self.prize['platform']}` at slots!",
            allowed_mentions=discord.AllowedMentions(users=False)
        )

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

        statistics("Slots prizes rejected")
        await achievement(
            ctx=self.outer_ctx,
            achievement_ids=[
                'slots_reject_count_1',
                'slots_reject_count_5',
                'slots_reject_count_10',
                'slots_reject_count_25',
                'slots_reject_count_50'
            ]
        )

        cha = bot.get_channel(notifications_squad_channel)
        msg_link = f"https://discord.com/channels/{self.outer_ctx.guild.id}/{self.outer_ctx.channel.id}/{self.outer_ctx.message.id}"

        await cha.send(
            f"<@&{role_jackpotnotif}> {msg_link}\n<@{self.outer_ctx.author.id}> has won, but rejected `{self.prize['title']}` key for `{self.prize['platform']}` at slots!",
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
            json.dump(self.feeds, f, indent=4)

def remove_slot_prize(prize, feeds):
    # Delete the prize from the pool
    del feeds[prize['key']]
    # Dump data back to json file
    with open("slots_prizes.json", "w") as f:
        json.dump(feeds, f, indent=4)

def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def fetch_giveaways(page=1):
    url = f'https://www.steamgifts.com/group/{SG_GROUP_ID}/{STEAM_GROUP_ID}?format=json&page={str(page)}'
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
    sheet_id = DEADLINES_GSHEET_ID
    api_key = GOOGLE_API_KEY

    api_url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Deadlines!A1:G1000?key={api_key}'
    r = requests.get(api_url)

    reviews_data = r.json()

    api_url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Magazine%20Issues!B4:E200?key={api_key}'
    r = requests.get(api_url)

    issues_data = r.json()

    return (reviews_data['values'], issues_data['values'])

def fetch_group_members_count():
    url = f'https://steamcommunity.com/groups/{STEAM_GROUP_ID}'
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
    url = f'https://www.steamgifts.com/group/{SG_GROUP_ID}/{STEAM_GROUP_ID}/wishlist/search?q={game_title}'
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
    url = f'https://steamcommunity.com/groups/{STEAM_GROUP_ID}/memberslistxml?xml=1'
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

    reviews_list, issues_list = fetch_raw_deadlines()

    # Ignore first row
    reviews_list = reviews_list[3:]

    # Filter
    new_reviews_list = []
    for item in reviews_list[1:]:
        if item[0]:
            review = {
                "Game": item[2],
                "Assigned": item[3],
                "Issue Number": item[1]
            }
            if item[1]:
                review["Issue Link"] = issues_list[int(item[1]) - 1][2]
            else:
                review["Issue Link"] = None
            new_reviews_list.append(review)

    # Try to get game title from AppID, else use query as game title
    try:
        game_title = fetch_appid_info(query)['name']
    except:
        game_title = query

    match = None

    for review in new_reviews_list:
    
        if review['Game'].lower() == game_title.lower():
            match = review
            break

    return match

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
        chat_completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=1.2,
            max_tokens=300,
            messages=msg
        )

        response = chat_completion.choices[0]

        msg.append({"role": "assistant", "content": response.message.content})

        chatbot_log = msg[1:]
        chatbot_log = chatbot_log[-20:]

        return response

    except Exception as e: return(e)

def get_user_from_username(username):
    for guild in bot.guilds:
        for member in guild.members:
            if member.name == username:
                return member
    return False

async def achievement(ctx, achievement_ids, who=None, dontgrant=False, backtrack=False, count=1, wipe=False, reset=False):
    if who:
        user = str(who)
    else:
        user = str(ctx.author.id)

    for achievement_id in achievement_ids:

        with open("achievements_usersdata.json") as feedsjson:
            achievements_log = json.load(feedsjson)
        with open("achievements.json") as feedsjson:
            achievements = json.load(feedsjson)

        achievement = achievements[achievement_id]
    
        # If achievement already unlocked, return
        try:
            if achievements_log[user][achievement_id]['unlocked_date']:
                continue
        except:
            pass
        
        if user not in achievements_log:
            achievements_log[user] = {}
        
        # Initiate achievement
        if achievement_id not in achievements_log[user]:
            achievements_log[user][achievement_id] = {}
            achievements_log[user][achievement_id]['counter'] = 0
        
        # If we are wiping progress on the achievements, reset them to 0
        if wipe:
            achievements_log[user][achievement_id]['counter'] = 0
        
        if backtrack and achievements_log[user][achievement_id]['counter'] > 0:
            # Count down on achievement
            achievements_log[user][achievement_id]['counter'] -= count
        else:
            # Count up on achievement
            achievements_log[user][achievement_id]['counter'] += count

        # If goal not reached, return
        if not achievements_log[user][achievement_id]['counter'] >= achievement['goal']:

            # If we're resetting the count on locked achievements, set them to 0
            if reset:
                achievements_log[user][achievement_id]['counter'] = 0

            with open("achievements_usersdata.json", "w") as f:
                json.dump(achievements_log, f, indent=4)
            continue
    
        if dontgrant:
            continue
        
        achievements_log[user][achievement_id]['unlocked_date'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        achievements_log[user][achievement_id]['counter'] = achievement['goal']

        with open("achievements_usersdata.json", "w") as f:
            json.dump(achievements_log, f, indent=4)
        
        userobj = bot.get_user(int(user))
        if userobj:
            userobj = userobj.name
        else:
            userobj = user
        
        embed = discord.Embed(title=f"{userobj} has unlocked an achievement...", color=gold_color)
        embed.add_field(
            name=achievement['name'],
            value=achievement['description']
        )
        embed.set_thumbnail(url='https://cdn3.emoji.gg/default/twitter/trophy.png')
        
        # Exception if this is in a DM
        try:
            await ctx.send(embed=embed)
        except:
            await ctx.channel.send(embed=embed)
        
        statistics("Cumulative achievements unlocked")

def statistics(stat, increase=1):
    with open("statistics.json") as feedsjson:
        statistics = json.load(feedsjson)

    statistics[stat] += increase

    with open("statistics.json", "w") as f:
        json.dump(statistics, f, indent=4)

# TODO WIP tokens

# async def token_drop(ctx):
#     if random.random() < 0.5:
#         embed = discord.Embed(title=f"{ctx.author.name} has earned a <:PaigeTokenEmote:1284322626726006805> PaigeToken!", color=gold_color)
#         embed.add_field(
#             name="",
#             value=""
#         )
#         # embed.set_image(url='https://i.imgur.com/NfyWNf3.png')
#         try:
#             await ctx.send(embed=embed)
#         except:
#             return

# BOT EVENTS

@bot.event
async def on_ready():
    global chosen_font
    if bot.user.id == 823385752486412290:
        chosen_font = "arial.ttf"
        bot.command_prefix = ("fb!", "foxy!")
    print("Logged in as {}".format(bot.user, bot.command_prefix))
    print("Ready!")
    await bot.change_presence(status=discord.Status.online,
        activity=discord.Activity(name="for prefix: p!", type=discord.ActivityType.watching))
    
    global glb_uptime_start, glb_stats_at_reboot
    glb_uptime_start = datetime.now().replace(microsecond=0)
    with open('statistics.json') as feedsjson:
        glb_stats_at_reboot = json.load(feedsjson)

    try:
        if not bot.user.id == 823385752486412290:
            daily_tasks.start()
            check_for_new_giveaways.start()
            daily_notifier.start()
            reminders_process.start()
            mine_process.start()
    except:
        pass

@bot.event
async def on_connect():
    print(f"Bot has connected to Discord.")
    try:
        if not bot.user.id == 823385752486412290:
            daily_tasks.start()
            check_for_new_giveaways.start()
            daily_notifier.start()
            reminders_process.start()
            mine_process.start()
    except:
        pass

@bot.event
async def on_command_error(ctx, error):
    global prevent_binder_command, prevent_gtp_command, prevent_mine_command, prevent_gtf_command, prevent_tr_command, prevent_trivia_command, prevent_vote_command
    prevent_binder_command = False
    prevent_gtp_command = False
    prevent_mine_command = False
    prevent_gtf_command = False
    prevent_tr_command = False
    prevent_trivia_command = False
    prevent_vote_command = False
    print(f"ERROR: {str(error)}")
    
    traceback.print_exception(type(error), error, error.__traceback__)

    if bot.user.id == 1077417730900230214:
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        tb = '\n'.join(tb)
        cha = bot.get_channel(1251016228248490066)
        link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}"
        await cha.send(f"{link}: {str(error)}\n```\n{tb}\n```")

    await ctx.send(f"<:warning:1077420799713087559> Failure to process:\n`{str(error)}`")
    if 'help' in ctx.message.content:
        await ctx.send(f"Did you mean to use the `{prefixes[0]}help` module? Try `{prefixes[0]}help {ctx.invoked_with}`")
    await achievement(ctx=ctx, achievement_ids=['misc_failed_command'])

# ON MESSAGE

@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        return
    
    if bot.user.id == 823385752486412290 and message.author.id not in [jbondguy007_userID, 479319946153689098, 279368230777126912, 391705444042670080, 319190839026909184, 418868712846917632, 191743475396509698, 206889965458685952]:
        return
    
    print(f"{message.created_at} | #{message.channel} | @{message.author} | {message.content}\n")

    await bot.process_commands(message)

    if isinstance(message.channel, discord.DMChannel):
        await achievement(ctx=message, achievement_ids=['misc_dm'])
    
    if "<:dogeLUL:1071508724709081170>" in message.content:
        statistics("Cumulative <:dogeLUL:1071508724709081170> use count")

@bot.event
async def on_command_completion(ctx):
    await achievement(ctx=ctx, achievement_ids=['misc_first_interact'])
    statistics("Commands count")
    if random.random() < 0.001:

        api_url = 'https://api.thecatapi.com/v1/images/search'
        r = requests.get(api_url)
        data = r.json()
        print(data)
        url = data[0]['url']

        embed = discord.Embed(title="Easter Egg", description="There is roughly 1 in 1000 chance of you getting a random cat picture when issuing a command. Congrats!", color=gold_color)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

        await achievement(ctx=ctx, achievement_ids=['misc_easter_egg_cat'])
        statistics("Easter Egg cat triggered")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == bot_channel:

        channel = await bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message.author != bot.user:
            return
    
        if message.embeds:
            if "Poll by" in message.embeds[0].description or "Poll reference ID" in message.embeds[0].footer.text:

                # iterating through each reaction in the message
                for r in message.reactions:

                    # checks the reactant isn't a bot and the emoji isn't the one they just reacted with
                    if payload.member in [user async for user in r.users()] and not payload.member.bot and str(r) != str(payload.emoji):

                        # removes the reaction
                        await message.remove_reaction(r.emoji, payload.member)

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(role_readers)
    await member.add_roles(role)

    cha = bot.get_channel(new_faces_channel)
    await cha.send(
        content=f"{member.mention} has been granted the {role.mention} role. Welcome! <:paigehappy:1080230055311061152>",
        allowed_mentions=discord.AllowedMentions.none()
    )

# @bot.event
# async def on_presence_update(before, after):

#     if not before.guild.id == 1067986921021788260 and not before.id == 172522306147581952:
#         return

#     print(f"Presence update detected for {before.name}")

#     try:
#         activity = after.activity

#         print(f"Activity: {activity}\nType: {activity.type}")

#         if not before.voice.self_stream and after.voice.self_stream:

#             cha = bot.get_channel(voice_chat_channel)
#             await cha.send(f"{after.name} is now streaming {activity.name}!")

#     except Exception as e:
#         print(f"Error: {e}")

# @bot.event
# async def on_voice_state_update(member, before, after):

#     if not member.guild.id == 1067986921021788260:
#         return

#     print(f"Presence update detected for {member.name}")

#     try:
#         activities = after.activities

#         for activity in activities:

#             print(f"Activity: {activity}\nType: {activity.type}")

#             if not before.voice.self_stream and after.voice.self_stream:

#                 cha = bot.get_channel(voice_chat_channel)
#                 await cha.send(f"{member.name} is now streaming {activity.name}!")

#         print("\n")

#     except Exception as e:
#         print(f"Error: {e}")

# COMMANDS

@bot.command()
async def say(ctx, channel_id, what):
    if ctx.author.id == 172522306147581952:
        channel = bot.get_channel(int(channel_id))
        await channel.send(what)

@bot.command()
async def test(ctx):
    await ctx.send("Test successful.")
    await achievement(ctx=ctx, achievement_ids=['misc_test_command_count_1', 'misc_test_command_count_5'])
    # await token_drop(ctx=ctx)

@bot.command(aliases=['about', 'status'])
async def info(ctx):
    now = datetime.now().replace(microsecond=0)
    with open('statistics.json') as feedsjson:
        current_stats = json.load(feedsjson)
    commands_processed_since_reboot = current_stats['Commands count']-glb_stats_at_reboot['Commands count']
    prefixes_listed = ", ".join(["`"+prefix+"`" for prefix in prefixes])
    await ctx.send(f"Hi, {botname} here communicating to you from <@172522306147581952>'s {platform.system()} {platform.release()}! I was born on {bot_birthdate}, and am running on Python v{platform.python_version()}.\nUptime is `{now-glb_uptime_start}`. {commands_processed_since_reboot} commands have been processed since last reboot. :muscle:\n\nMy supported prefixes are: {prefixes_listed}\nI'm happy to help, just issue the command `p!help` for a list of commands.",
                   allowed_mentions=discord.AllowedMentions(users=False))
    await achievement(ctx=ctx, achievement_ids=['misc_info_command'])

@bot.command()
async def threads(ctx):
    await ctx.send(f"""
Central Hub: <{steamgifts_threads['main']}>
Monthly SGM Edition: <{steamgifts_threads['monthly']}>
Screenshot of the Month thread: <{steamgifts_threads['screenshots']}>
    """)

@bot.command()
async def rules(ctx):
    await ctx.send(f"{botname} recommends reading the rules! <https://steamcommunity.com/groups/{STEAM_GROUP_ID}/discussions/3/3758852249517826899/>")

@bot.command()
async def deadline(ctx, username):

    deadlines_list, issues_list = fetch_raw_deadlines()

    user_deadlines = [{"Game": item[2], "Assigned": item[3], "Deadline": item[4], "Status": item[6]} for item in deadlines_list[1:] if item[3] == username and item[6] not in ['SUBMITTED', 'CANCELLED']]

    embed = discord.Embed(title=f"Deadlines for {username}", description="", color=bot_color)

    if user_deadlines:
        for assignment in user_deadlines:

            embed.add_field(
                name="Game",
                value=assignment['Game'],
                inline=False
            )

            if assignment['Deadline'] == 'TBD':
                
                embed.add_field(
                    name=f"{assignment['Game']}",
                    value=f"• Assigned: `{assignment['Assigned']}`\n• Deadline: `{assignment['Deadline']}`\n• Status: `{assignment['Status']}`",
                    inline=True
                )
            
            else:

                deadline = datetime.strptime(assignment['Deadline'], '%b %d, %Y')

                is_past_due = " :warning:" if datetime.strptime(f"{deadline.strftime('%b %d, %Y')}", '%b %d, %Y').date() < datetime.today().date() else ""

                embed.add_field(
                    name=f"{assignment['Game']}{is_past_due}",
                    value=f"• Assigned: `{assignment['Assigned']}`\n• Deadline: `{deadline.strftime('%b %d, %Y') if not deadline.year == datetime.today().year else deadline.strftime('%B %d')}`\n• Status: `{assignment['Status']}`",
                    inline=True
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

    deadlines_raw, issues_list = fetch_raw_deadlines()

    deadlines = [{"Game": item[2], "Assigned": item[3], "Deadline": item[4], "Status": item[6]} for item in deadlines_raw[1:] if item[6] not in ['SUBMITTED', 'CANCELLED']]

    for i in range(0, len(deadlines), 25):

        if i == 0:
            embed = discord.Embed(title=f"Deadlines", description="List of all current assignments, excluding submitted or cancelled.", color=bot_color)
        else:
            embed = discord.Embed(title=f"Deadlines (continued...)", description="List of all current assignments, excluding submitted or cancelled.", color=bot_color)

        for assignment in deadlines[i:i+25]:

            if assignment['Deadline'] == 'TBD':

                embed.add_field(
                    name=f"{assignment['Game']}",
                    value=f"• Assigned: `{assignment['Assigned']}`\n• Deadline: `{assignment['Deadline']}`\n• Status: `{assignment['Status']}`",
                    inline=True
                )
                
            else:

                deadline = datetime.strptime(assignment['Deadline'], '%b %d, %Y')

                is_past_due = " :warning:" if datetime.strptime(f"{deadline.strftime('%b %d, %Y')}", '%b %d, %Y').date() < datetime.today().date() else ""

                embed.add_field(
                    name=f"{assignment['Game']}{is_past_due}",
                    value=f"• Assigned: `{assignment['Assigned']}`\n• Deadline: `{deadline.strftime('%b %d, %Y') if not deadline.year == datetime.today().year else deadline.strftime('%B %d')}`\n• Status: `{assignment['Status']}`",
                    inline=True
                )

        await ctx.send(embed=embed)

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
    
    statistics("Polls created")

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

    statistics("AI messages generated")
    
    await achievement(
        ctx=ctx,
        achievement_ids=[
            'ai_chat_count_1',
            'ai_chat_count_10',
            'ai_chat_count_25',
            'ai_chat_count_50',
            'ai_chat_count_100'
        ]
    )

@bot.command()
async def user(ctx, *query):
    query = ' '.join(query)
    await ctx.send(f"Fetching Steam and SG profiles for {query}...")

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

    with open('slots_checkin.json', "r") as f:
        slots_checkin = json.load(f)
    
    if str(ctx.author.id) not in slots_checkin.keys():
        await ctx.send(f"<@{ctx.author.id}> Welcome to Paige's Slots!\n\nAs this is your first time playing, please keep these rules in mind:\n\n1. Prizes you win and accept must be activated to your own personal account only (unless agreed otherwise with the prize contributor).\n2. If you claim a prize, remember to say thanks to the contributor!\n3. Failing to follow the rules, or raising suspicion of exploiting the slots command may result in a slots command ban.\n\nThanks for reading - enjoy the crippling gambling addiction! :paigehappy:\n----------")

    if len(ctx.author.roles) <= 1 or not [role.id for role in ctx.author.roles if role.id not in allowed_roles]:
        await ctx.send("Hi, welcome to Paige's Casino! Unfortunately, we require a credit check (having a staff-assigned role) before you can enter. Contact staff for assistance. Thank you!")
        return
    
    with open('slots_blacklist.json') as feedsjson:
        blacklist = json.load(feedsjson)

    if ctx.author.id in blacklist:
        responses = ["Sorry, it looks like you are barred from PaigeCasino.", "I'm afraid you are banned from PaigeCasino. Have a good day.", "Dear guest, it appears that PaigeCasino has banned you from the premises."]
        response = random.choice(responses)
        await ctx.send(f"*The Bouncer at the door checks your ID...* \"{response}\" (User is banned from `slots` command)")
        return

    cherry = ':cherries:'
    orange = ':tangerine:'
    lemon = ':lemon:'

    if not ctx.guild:
        await ctx.send("The `slots` commands cannot be executed from Direct Messages.")
        return

    # Check if prize pool file is empty
    if os.path.getsize('slots_prizes.json') <= 2:
        await ctx.send("Unfortunately, the prize pool is currently empty. Try again another time!\nConsider donating a prize to the pool via the `slotskey` command.")
        return

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

        statistics("Slots plays")

        await achievement(
                ctx=ctx,
                achievement_ids=[
                    'slots_play_count_1',
                    'slots_play_count_5',
                    'slots_play_count_10',
                    'slots_play_count_25',
                    'slots_play_count_50',
                    'slots_play_count_100'
                ]
            )
        
        if len(slots_result) == len(set(slots_result)):
            await achievement(ctx=ctx, achievement_ids=['slots_misc_all_different_symbols'])

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
    
    statistics("Slots plays")
    
    await achievement(
        ctx=ctx,
        achievement_ids=[
            'slots_play_count_1',
            'slots_play_count_5',
            'slots_play_count_10',
            'slots_play_count_25',
            'slots_play_count_50',
            'slots_play_count_100'
        ]
    )

    statistics("Slots wins")
    
    await achievement(
        ctx=ctx,
        achievement_ids=[
            'slots_win_count_1',
            'slots_win_count_5',
            'slots_win_count_10',
            'slots_win_count_25',
            'slots_win_count_50'
        ]
    )
    
    await ctx.author.send(f"Congratulations on winning at PaigeSlots! You've won a key for `{prize['title']}` (activates on `{prize['platform']}`)")
    view=Buttons(prize, feeds, ctx=ctx)
    view.start_timeout()
    view.message = await ctx.author.send(f"Would you like to reveal the key for {prize['title']}, or redistribute it to the prize pool? (5 minutes until automatically revealed)",view=view)

@bot.command()
async def slotskey(ctx, *, args:commands.clean_content(fix_channel_mentions=False, use_nicknames=False)=None): # type: ignore

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
        json.dump(feeds, f, indent=4)

    channel = bot.get_channel(notifications_squad_channel)

    await channel.send(f"New prize `{output['title']}` contributed by `{channel.guild.get_member(output['user']).display_name}` has been added to the slots prizes pool! Issue the command `{prefixes[0]}slotsprizes` in <#{bot_channel}> for details!")

    await ctx.send("Key added to prize pool! Thanks for your contribution!")

    statistics("Slots prizes contributed")

@bot.command(aliases=['slotprize', 'slotsprize', 'slotprizes'])
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
                value=f"Contributor: {username.display_name if username else game['user']}\nPlatform: {game['platform']}",
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
        hand = [random.randrange(1, 7) for _ in range(5)]
        return hand
    elif r:
        for d in r:
            hand[int(d)-1] = random.randrange(1, 7)
        return hand
    elif k:
        new_hand = [random.randrange(1, 7) for _ in range(5)]
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

        await achievement(
            ctx=ctx,
            achievement_ids=[
                'poker_win_count_1',
                'poker_win_count_5',
                'poker_win_count_10',
                'poker_win_count_25',
                'poker_win_count_50'
            ],
            who=opponent.id
        )

    # Elif challenger hand rank is greater
    elif opponent_hand['rank'] < challenger_hand['rank']:
        await ctx.send(f"{challenger.name} wins with a {challenger_hand['name']} over {opponent.name}'s {opponent_hand['name']}!")
        
        await achievement(
            ctx=ctx,
            achievement_ids=[
                'poker_win_count_1',
                'poker_win_count_5',
                'poker_win_count_10',
                'poker_win_count_25',
                'poker_win_count_50'
            ],
            who=challenger.id
        )

    # Elif both hand ranks are the same
    elif opponent_hand['rank'] == challenger_hand['rank']:

        # If the hand is not BUST
        if opponent_hand['rank'] > 1:

            # Determine winning hand by score
            if opponent_hand['score'] > challenger_hand['score']:
                await ctx.send(f"{opponent.name} wins with a {opponent_hand['name']} of higher value!")
                
                await achievement(
                    ctx=ctx,
                    achievement_ids=[
                        'poker_win_count_1',
                        'poker_win_count_5',
                        'poker_win_count_10',
                        'poker_win_count_25',
                        'poker_win_count_50'
                    ],
                    who=opponent.id
                )
                
            elif opponent_hand['score'] < challenger_hand['score']:
                await ctx.send(f"{challenger.name} wins with a {challenger_hand['name']} of higher value!")

                await achievement(
                    ctx=ctx,
                    achievement_ids=[
                        'poker_win_count_1',
                        'poker_win_count_5',
                        'poker_win_count_10',
                        'poker_win_count_25',
                        'poker_win_count_50'
                    ],
                    who=challenger.id
                )

                return

        # Fallthrough (BUST or HIGH VALUES)
        if opponent_hand['score'] > challenger_hand['score']:
            player = opponent
        elif opponent_hand['score'] < challenger_hand['score']:
            player = challenger
        else:
            await ctx.send(f"Perfect draw!")

            statistics("Dice Poker perfect draws")

            await achievement(ctx=ctx, achievement_ids=['poker_misc_perfect_draw'], who=challenger.id)
            await achievement(ctx=ctx, achievement_ids=['poker_misc_perfect_draw'], who=opponent.id)

            return

        await ctx.send(f"{player} wins with High Values!")

        await achievement(ctx=ctx, achievement_ids=['poker_misc_win_on_higher_val'], who=player.id)

        await achievement(
                ctx=ctx,
                achievement_ids=[
                    'poker_win_count_1',
                    'poker_win_count_5',
                    'poker_win_count_10',
                    'poker_win_count_25',
                    'poker_win_count_50'
                ],
                who=player.id
            )
        
    statistics("Dice Poker games played")
    
    await achievement(
        ctx=ctx,
        who=challenger.id,
        achievement_ids=[
            'poker_play_count_1',
            'poker_play_count_5',
            'poker_play_count_10',
            'poker_play_count_25',
            'poker_play_count_50',
            'poker_play_count_100'
        ]
    )

    await achievement(
        ctx=ctx,
        who=opponent.id,
        achievement_ids=[
            'poker_play_count_1',
            'poker_play_count_5',
            'poker_play_count_10',
            'poker_play_count_25',
            'poker_play_count_50',
            'poker_play_count_100'
        ]
    )

    for h, p in [(opponent_hand, opponent), (challenger_hand, challenger)]:
        if h['score'] == 30:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_5ok_highest'])
        if h['rank'] == 8:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_5ok'])
        if h['rank'] == 7:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_4ok'])
        if h['rank'] == 6:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_fh'])
        if h['rank'] == 5:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_straight'])
        if h['rank'] == 4:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_3ok'])
        if h['rank'] == 3:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_2p'])
        if h['rank'] == 2:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_1p'])
        if h['rank'] == 1:
            await achievement(ctx=ctx, who=p.id, achievement_ids=['poker_hand_bust'])

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

def tc_generator(user, holo=True, legacy=False):
    print(f"Generating card {user}...")

    try:
        user_id = user.id
    except:
        user_id = user

    if legacy:

        base_img = Image.new( mode = "RGBA", size = (300, 400), color = (255, 255, 255) )
        card_img = Image.open(f"tradingcards/generated/{user_id}{'_holo' if holo else''}.png").convert('RGBA') # Potentially breaking
        base_img.paste(card_img, (0, 0), card_img)
        contrast = ImageEnhance.Contrast(base_img)
        base_img = contrast.enhance(0.6)

        # Fonts setup
        font = ImageFont.truetype(chosen_font, 50)
        draw = ImageDraw.Draw(base_img)

        font_width, font_height = font.getsize("LEGACY")

        # LEGACY text
        draw.text((50, 200-font_height), "LEGACY", font=font, fill="black", stroke_width=3, stroke_fill="white")

        # Save the resulting image
        card = f"{user_id}{'_holo' if holo else ''}"
        base_img.save(f'tradingcards/generated/{card}.png')

        return card

    pfp = user.avatar
    rarity, role = tc_role(user)
    user_join_date = user.joined_at.strftime("%m/%d/%Y")

    # Setup a base image
    base_img = Image.new( mode = "RGBA", size = (300, 400), color = (255, 255, 255) )

    # Open the profile picture image
    try:
        response = requests.get(pfp)
        img = Image.open(BytesIO(response.content)).convert('RGBA')
    except:
        response = requests.get(user.display_avatar)
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        # img = Image.open('tradingcards/templates/default_pfp.png').convert('RGBA')
    profile_img = img.resize( size=(260, 260) )

    # Open the card template and holo images
    tc_img = Image.open(f'tradingcards/templates/tc_template_{rarity}.png').convert('RGBA')
    holo_img = Image.open('tradingcards/templates/holo.png').convert('RGBA')

    # Overlay the card over the profile picture
    base_img.paste(profile_img, (20, 50), profile_img)
    base_img.paste(tc_img, (0, 0), tc_img)

    # Setup for holo cards
    if holo:
        base_img = Image.alpha_composite(base_img, holo_img)
        contrast = ImageEnhance.Contrast(base_img)
        base_img = contrast.enhance(1.2)

    # Setup for legacy cards

    # Fonts setup
    font = ImageFont.truetype(chosen_font, 17)
    font_small = ImageFont.truetype(chosen_font, 12)
    draw = ImageDraw.Draw(base_img)
    _, _, w, h = draw.textbbox((0, 0), f"{user.name}{' (HOLO)' if holo else ''}", font=font)

    # Card name text
    draw.text(((300-w)/2, 16), f"{user.name}{' (HOLO)' if holo else ''}", font=font, fill="black", stroke_width=3, stroke_fill="#AAFFFF" if holo else "white")

    # Card rarity/holo text
    draw.text((30, 60), '{0}{1}{2}'.format(rarity, '\nHOLO' if holo else '', '\nLEGACY' if legacy else ''), font=font, fill="#55FFFF" if holo else "yellow", stroke_width=2, stroke_fill="black")

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

def binder_generator(user, include_legacy=False, only_legacy=False):

    fetched_player_collection = fetch_player_collection(user)

    normal_collection = {x: y for x, y in fetched_player_collection.items() if not y.get('legacy')}
    legacy_collection = {x: y for x, y in fetched_player_collection.items() if y.get('legacy')}

    if include_legacy:
        normal_collection.update(legacy_collection)
        player_collection = normal_collection
    elif only_legacy:
        player_collection = legacy_collection
    else:
        player_collection = normal_collection

    if not player_collection:
        raise Exception("Empty binder")
    
    padding = 10
    x = 0+padding
    y = 0+padding
    zoom = 1.2
    xsize = int(150.0*zoom)
    ysize = int(200.0*zoom)
    col = 5
    row = 5
    lines = 1
    items = 0
    binder_count = 1
    returned_value = []

    color_grey = (100, 100, 100, 255)
    # color_copper = (100, 80, 70, 255)

    binder_bg_color = color_grey

    max_per_page = col*row

    # Setup a base image
    base_img  = Image.new( mode = "RGBA", size = ((xsize+padding)*col+padding, (ysize+padding)*row+padding), color = binder_bg_color )

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
            y += ysize+padding
            x = 0+padding
        else:
            x += xsize+padding
        lines += 1
        items += 1

        # If the number of cards exceeds the page size, create a second binder
        if items == (col*row)*binder_count:
            binder = f'binder{binder_count}'
            returned_value.append(binder)
            base_img.save(f'tradingcards/generated/{binder}.png')
            base_img  = Image.new( mode = "RGBA", size = ((xsize+padding)*col+padding, (ysize+padding)*row+padding), color = binder_bg_color )
            binder_count += 1
            lines = 1
            x = 0+padding
            y = 0+padding
            continue

        elif len(player_collection) == items:
            binder = f'binder{binder_count}'
            returned_value.append(binder)
            base_img.save(f'tradingcards/generated/{binder}.png')
            break

    return returned_value

async def tc_add(user_ID, card_ID, ctx):

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
    
    await achievement(
        ctx=ctx,
        who=user_ID,
        backtrack=False,
        achievement_ids=[
            'tc_normal_count_1',
            'tc_normal_count_5',
            'tc_normal_count_10',
            'tc_normal_count_25',
            'tc_normal_count_50',
            'tc_normal_count_100'
        ]
    )

    if '_holo' in card_ID:
        await achievement(
            ctx=ctx,
            who=user_ID,
            backtrack=False,
            achievement_ids=[
                'tc_holo_count_1',
                'tc_holo_count_5',
                'tc_holo_count_10',
                'tc_holo_count_25',
                'tc_holo_count_50'
            ]
        )

    # tc_misc_getself
    if player == re.search("\d+", card_ID)[0]:
        await achievement(ctx=ctx, achievement_ids=['tc_misc_getself'])
    
    # tc_misc_getdup
    if database[player][card_ID]['count'] > 1:
        await achievement(ctx=ctx, achievement_ids=['tc_misc_getdup'])

    #tc_misc_same_normalholo
    if (
        '_holo' in card_ID and database[player].get(card_ID.replace('_holo', '')) or
        database[player].get(card_ID+'_holo')
        ):
            await achievement(ctx=ctx, achievement_ids=['tc_misc_same_normalholo'])


async def tc_remove(user_ID, card_ID, ctx):

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
    
    await achievement(
        ctx=ctx,
        who=user_ID,
        backtrack=True,
        achievement_ids=[
            'tc_normal_count_1',
            'tc_normal_count_5',
            'tc_normal_count_10',
            'tc_normal_count_25',
            'tc_normal_count_50',
            'tc_normal_count_100'
        ]
    )

    if '_holo' in card_ID:
        await achievement(
            ctx=ctx,
            who=user_ID,
            backtrack=True,
            achievement_ids=[
                'tc_holo_count_1',
                'tc_holo_count_5',
                'tc_holo_count_10',
                'tc_holo_count_25',
                'tc_holo_count_50'
            ]
        )

async def tc_legacy_check():
    with open('tradingcards/cards.json') as feedsjson:
        all_cards = json.load(feedsjson)
    
    SGM_guild = bot.get_guild(DISCORD_SERVER_ID)
    server_members = [str(user.id) for user in SGM_guild.members]

    legacy_cards = [card for card, info in all_cards.items() if card not in server_members and card not in [card+'_holo' for card in server_members] and not info.get('legacy')]
    unlegacy_cards = [card for card, info in all_cards.items() if (card in server_members or card in [card+'_holo' for card in server_members]) and info.get('legacy')]

    for lc in legacy_cards:
        all_cards[lc]['legacy'] = True
        lc_holo = False
        if lc.endswith('_holo'):
            lc = lc.replace('_holo', '')
            lc_holo = True
        tc_generator(lc, holo=lc_holo, legacy=True)
    
    for lc in unlegacy_cards:
        del all_cards[lc]['legacy']
        lc_holo = False
        if lc.endswith('_holo'):
            lc = lc.replace('_holo', '')
            lc_holo = True
        tc_generator(lc, holo=lc_holo, legacy=False)
    
    with open("tradingcards/cards.json", "w") as f:
        json.dump(all_cards, f, indent=4)
    
    return legacy_cards, unlegacy_cards

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
        
        undiscovered_cards = [user for user in ctx.guild.members if str(user.id) not in [user for user in all_cards.keys()]]

        if args[0].lower() in ['binder', 'binder+', 'binderplus', 'legacybinder']:
            global prevent_binder_command
            if prevent_binder_command:
                await ctx.send(f"<@{ctx.author.id}> Processing a binder already, please wait and try again later.")
                return
            prevent_binder_command = True
            await ctx.send("Processing binder, please wait...")

            if len(args) > 1:
                user = get_user_from_username(args[1])
                if not user:
                    user = bot.get_user(int(args[1]))
                if not user:
                    await ctx.send("User not found in database!")
                    prevent_binder_command = False
                    return
            else:
                user = ctx.author

            include_legacy = False
            only_legacy = False

            if args[0].lower() in ['binder+', 'binderplus']:
                include_legacy = True
            elif args[0].lower() == 'legacybinder':
                only_legacy = True

            try:
                binders = binder_generator(user.id, include_legacy=include_legacy, only_legacy=only_legacy)
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
        
        elif args[0].lower() in ['list', 'list+', 'listplus', 'legacylist', 'dups', 'collection', 'missing']:
            
            # Handling if a username is passed as argument
            if len(args) > 1:
                user = get_user_from_username(args[1])
                if not user:
                    user = bot.get_user(int(args[1]))
                if not user:
                    await ctx.send("User not found in database!")
                    return
            else:
                user = ctx.author

            if not str(user.id) in database:
                await ctx.send(f"No cards found for {user.name}! Try claiming some with `{prefixes[0]}tc` first!")
                return
            # ----------

            player_collection = fetch_player_collection(str(user.id))

            if args[0].lower() == 'list':
                player_collection = {card: info for card, info in player_collection.items() if not info.get('legacy')}
            
            if args[0].lower() == 'legacylist':
                player_collection = {card: info for card, info in player_collection.items() if info.get('legacy')}

            if args[0].lower() == 'collection':
                player_rarities_count = Counter([card_info['rarity'] for card_info in player_collection.values() if not card_info.get('legacy') and not card_info.get('holo')])
                all_rarities_count = Counter([card_info['rarity'] for card_info in all_cards.values() if not card_info.get('legacy') and not card_info.get('holo')])

                rarities_text = ['Ultra Ultra Rare', 'Ultra Rare', 'Rare', 'Exceptional', 'Uncommon', 'Common', 'Ordinary']
                
                server_members = [x for x in ctx.guild.members]

                if undiscovered_cards:
                    desc = f" ***{len(undiscovered_cards)}** cards have not yet been discovered by the community, and are not included in your progress for each rarity.*"
                else:
                    desc = ""

                embed = discord.Embed(title=f"{user.name}'s Collection", description=f"*Excludes HOLO variants and legacy cards.*{desc}", color=bot_color)

                player_rarities_count_combined = sum(player_rarities_count.values())

                embed.add_field(
                    name=f"Progress: {player_rarities_count_combined}/{len(server_members)}",
                    value="",
                    inline=False
                )

                for rar in rarities_text:
                    embed.add_field(
                        name="",
                        value=f"**{player_rarities_count[rar]}/{all_rarities_count[rar]}** - {rar}",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                return

            if args[0].lower() == 'missing':
                player_collection = {k: v for k, v in all_cards.items() if k not in player_collection.keys() and not v['holo'] and not v.get('legacy')}

            if args[0].lower() == 'dups':
                player_collection = {k: v for k, v in player_collection.items() if v['count'] > 1}
                if not player_collection:
                    await ctx.send(f"No duplicate cards found for user {user.name}!")
                    return
                
            undiscovered_cards = {user.id: {'name': user.name, 'holo': False, 'rarity': '(Undiscovered)'} for user in ctx.guild.members if str(user.id) not in [user for user in all_cards.keys()]}
            
            player_collection = tc_sorter(player_collection)

            if args[0].lower() == 'missing':
                player_collection.update(undiscovered_cards)
                if not player_collection:
                    await ctx.send(f"No missing cards found for user {user.name}!")
                    return

            keys = list(player_collection.keys())
            collection_size = len(keys)
            batch_size = 25

            for i in range(0, collection_size, batch_size):
                embed = discord.Embed(title=f"{user.name}'s {'Duplicate ' if args[0].lower() == 'dups' else ''}{'Missing ' if args[0].lower() == 'missing' else ''}{'Legacy ' if args[0].lower() == 'legacylist' else ''}Cards List{' (+Legacy)' if args[0].lower() in ['list+', 'listplus'] else ''}", color=bot_color)

                batch_keys = keys[i:i + batch_size]
                batch_dict = {key: player_collection[key] for key in batch_keys}

                for cardID, card in batch_dict.items():
                    if args[0].lower() == 'missing':
                        cards_count = ''
                    else:
                        cards_count = card['count']
                    embed.add_field(
                        name=f"{card['name']}{' (HOLO)' if card['holo'] else ''}",
                        value=f"{cardID}\n{card['rarity']}{' (LEGACY)' if card.get('legacy') else ''}\n{cards_count}",
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
            
            try:
                viewed_card_count = database[str(ctx.author.id)][cardID]['count']
            except:
                viewed_card_count = "None"

            # Prep and send the embed
            file = discord.File(f"tradingcards/generated/{cardID}.png")
            embed = discord.Embed(title=f"{card['name']}{' (HOLO)' if card['holo'] else ''}", description=f"ID: {cardID}\nCount You Own: {viewed_card_count}", color=bot_color)
            embed.set_image(url=f"attachment://{cardID}.png")

            await ctx.send(embed=embed, file=file)
            return
        
        elif args[0].lower() == 'whohas' or args[0].lower() == 'whohasany':
            whohasany = False
            if args[0].lower() == 'whohasany':
                whohasany = True
            try:
                queried_card = args[1]
            except:
                await ctx.send(f"Command is `{prefixes[0]}tc whohas card-ID-here`")
                return
            
            is_holo = False
            if queried_card.endswith(' (HOLO)') or queried_card.endswith('_holo'):
                queried_card = queried_card.replace(' (HOLO)', '')
                queried_card = queried_card.replace('_holo', '')
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
            
            if whohasany:
                whohas_users = [user_id for user_id, cards in database.items() if cardID in [crd for crd, val in cards.items()]]
            else:
                whohas_users = [user_id for user_id, cards in database.items() if cardID in [crd for crd, val in cards.items() if val['count'] > 1]]

            embed = discord.Embed(title=f"Owners of{' Any' if whohasany else ' Duplicate'} `{card['name']}{' (HOLO)' if is_holo else''}` Cards", color=bot_color)
            
            for u in whohas_users:
                if not bot.get_user(int(u)):
                    continue
                embed.add_field(
                    name=bot.get_user(int(u)).name,
                    value=f"Count: {database[u][cardID]['count']}\n<@{bot.get_user(int(u)).id}>"
                )
            
            if not whohas_users:
                await ctx.send(f"Unable to locate user owning a duplicate `{args[1]}` card!")
            else:
                await ctx.send(embed=embed)
        
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
            
            embed = discord.Embed(title=f"{ctx.author.name}'s Trade Offers", description=f"Issue the command `{prefixes[0]}tc accept trade-ID` to accept trades, or `{prefixes[0]}tc reject trade-ID` to reject them.", color=bot_color)

            trades_for_deletion = []

            for i, (tradeID, details) in enumerate(user_trades.items()):
                
                # EXAMPLE:
                    # tradeID: 1142364330424279111
                    # Details: {'from': 172522306147581952, 'have': '479319946153689098_holo', 'want': '823385752486412290'}

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

                have_requested = database[str(user)].get(requested_card_ID, '')
                have_given = database[str(user)].get(given_card_ID, '')

                if have_requested:
                    have_requested = have_requested['count']
                else:
                    have_requested = 0
                
                if have_given:
                    have_given = have_given['count']
                else:
                    have_given = 0

                embed.add_field(
                    name=f"{i+1}. Trade ID: {tradeID}",
                    value=f"""From: <@{trader}>
[H]: {given_card['name']}{' (HOLO)' if given_card['holo'] else ''} - {given_card['rarity']} (you have {have_given})
[W]: {requested_card['name']}{' (HOLO)' if requested_card['holo'] else ''} - {requested_card['rarity']} (you have {have_requested})""",
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

    ##### WIP #####

    #     elif args[0].lower() == 'offers':
    #         with open('tradingcards/trades.json') as feedsjson:
    #             trades = json.load(feedsjson)

    #         for user_id, offers in trades.items():
    #             for offer_id, offer_info in offers.items():
    #                 user_offers = {user_id: {offer_id: offer_info} for trade_id, trade_info in offers.items() if int(trade_info['from']) == ctx.author.id}

    #         if not user_offers:
    #             await ctx.send("You have no ongoing trading cards trade offers.")
    #             return
            
    #         print(user_offers)
            
    #         embed = discord.Embed(title=f"{ctx.author.name}'s Sent Offers", description=f"Issue the command `{prefixes[0]}tc cancel trade-ID` to cancel an ongoing offer.", color=bot_color)

    #         trades_for_deletion = []

    #         for user_id, offer in user_offers.items():
    #             for i, (tradeID, details) in enumerate(offer.items()):
                    
    #                 # EXAMPLE:
    #                     # tradeID: 1142364330424279111
    #                     # Details: {'from': 172522306147581952, 'have': '479319946153689098_holo', 'want': '823385752486412290'}


    #                 trader = details['from']
    #                 user = ctx.author.id

    #                 given_card_ID = details['have']
    #                 requested_card_ID = details['want']

    #                 given_card = all_cards[str(given_card_ID)]
    #                 requested_card = all_cards[str(requested_card_ID)]

    #                 # Check if the trader's card is still available for trading
    #                 try:
    #                     receive = database[str(trader)][given_card_ID]
    #                 except:
    #                     trades_for_deletion.append(tradeID)
    #                     continue

    #                 # Check if the tradee's card is still available for trading
    #                 try:
    #                     deliver = database[str(user_id)][requested_card_ID]
    #                 except:
    #                     trades_for_deletion.append(tradeID)
    #                     continue

    #                 have_requested = database[str(user)].get(requested_card_ID, '')
    #                 have_given = database[str(user)].get(given_card_ID, '')

    #                 if have_requested:
    #                     have_requested = have_requested['count']
    #                 else:
    #                     have_requested = 0
                    
    #                 if have_given:
    #                     have_given = have_given['count']
    #                 else:
    #                     have_given = 0

    #                 embed.add_field(
    #                     name=f"{i+1}. Trade ID: {tradeID}",
    #                     value=f"""To: <@{user_id}>
    # [H]: {given_card['name']}{' (HOLO)' if given_card['holo'] else ''} - {given_card['rarity']} (you have {have_given})
    # [W]: {requested_card['name']}{' (HOLO)' if requested_card['holo'] else ''} - {requested_card['rarity']} (you have {have_requested})""",
    #                     inline=False
    #                 )
            
    #         if trades_for_deletion:
    #             for trade_ID in trades_for_deletion:
    #                 del trades[str(user_id)][trade_ID]
    #             # Update trades file in case a trade was deleted
    #             with open("tradingcards/trades.json", "w") as f:
    #                 json.dump(trades, f, indent=4)
            
    #         if not embed.fields:
    #             await ctx.send("You have no trading cards trade offers pending.")
    #             return

    #         await ctx.send(embed=embed)

        elif args[0].lower() == 'accept' or args[0].lower() == 'reject' or args[0].lower() == 'cancel':

            with open('tradingcards/trades.json') as feedsjson:
                trades = json.load(feedsjson)
            
            trade_id_is_index = False

            trade_id = args[1]
            if len(trade_id) <= 2:
                trade_id_is_index = True
                
            user_id = str(ctx.author.id)

            if args[0].lower() == 'reject':
                try:
                    if trade_id_is_index:
                        trade_item = {key: val for idx, (key, val) in enumerate(trades[user_id].items()) if idx == int(trade_id)-1}
                        if not trade_item:
                            raise Exception()
                    else:
                        trade_item = {trade_id: trades[user_id][trade_id]}
                except:
                    await ctx.send(f"No pending trade with trade ID or index `{trade_id}` found!")
                    return
                
                print(trade_item)

                # Delete trade offer
                for tradeid, val in trade_item.items():
                    rejected_trade_sender_id = val['from']
                    del trades[user_id][tradeid]
                    with open("tradingcards/trades.json", "w") as f:
                        json.dump(trades, f, indent=4)
                    await ctx.send(f"Trade offer `{tradeid}` from <@{rejected_trade_sender_id}> rejected!")

                statistics("Trading Cards trades rejected")

                await achievement(
                    ctx=ctx,
                    achievement_ids=[
                        'tc_trade_reject_count_1',
                        'tc_trade_reject_count_5',
                        'tc_trade_reject_count_10'
                    ]
                )
                return
            
            if args[0].lower() == 'cancel':
                # Check each user, trades pair
                for c_user, c_offers in trades.items():
                    # If the trade_id matches any of the trade IDs for this user
                    if trade_id in c_offers:
                        # Assign values to variables
                        found_trade = c_offers[trade_id]
                        found_trade_user_id = c_user
                        # Terminate loop
                        break
                    # If no match, set found_trade to None, and continue loop
                    else:
                        found_trade = None
                        continue
                
                # If no trades match, terminate
                if not found_trade:
                    await ctx.send(f"Trade ID `{trade_id}` not found!")
                    return
                
                # If user is trying to cancel another user's trade, terminate
                if not trades[found_trade_user_id][trade_id]['from'] == ctx.author.id:
                    await ctx.send(f"Cannot cancel a trade from another user!")
                    return

                # Delete trade
                del trades[found_trade_user_id][trade_id]
                with open("tradingcards/trades.json", "w") as f:
                    json.dump(trades, f, indent=4)
                await ctx.send(f"Trade offer `{trade_id}` to <@{found_trade_user_id}> has been cancelled!")

                statistics("Trading Cards trades cancelled")

                await achievement(
                    ctx=ctx,
                    achievement_ids=[
                        'tc_trade_cancel_count_1',
                        'tc_trade_cancel_count_5',
                        'tc_trade_cancel_count_10'
                    ]
                )
                return
            
            # ----- END TRADE CANCELATION ----- #

            try:
                if trade_id_is_index:
                    trade_item = {key: val for idx, (key, val) in enumerate(trades[user_id].items()) if idx == int(trade_id)-1}
                else:
                    trade_item = {trade_id: trades[user_id][trade_id]}
                if not trade_item:
                    raise Exception()
            except:
                await ctx.send(f"No pending trade with trade ID or index `{trade_id}` found!")
                return
            
            for trade_id, trade in trade_item.items():
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
            await tc_add(user_id, given_cardID, ctx)
            await tc_remove(user_id, requested_cardID, ctx)

            # Trade (trader side)
            await tc_add(trader_id, requested_cardID, ctx)
            await tc_remove(trader_id, given_cardID, ctx)

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

            statistics("Trading Cards trades accepted")

            for usr in [user_id, trader_id]:

                await achievement(
                    ctx=ctx,
                    who=usr,
                    achievement_ids=[
                        'tc_trade_count_1',
                        'tc_trade_count_5',
                        'tc_trade_count_10',
                        'tc_trade_count_25',
                        'tc_trade_count_50',
                        'tc_trade_count_100'
                    ]
                )
        
        ##### WIP #####
        
        # elif args[0].lower() == 'prestige':
        #     player_collection = fetch_player_collection(str(ctx.author.id))
        #     undiscovered_cards = {user.id: {'name': user.name, 'holo': False, 'rarity': '(Undiscovered)'} for user in ctx.guild.members if str(user.id) not in [user for user in all_cards.keys()]}
        #     player_missing_cards = {k: v for k, v in all_cards.items() if k not in player_collection.keys() and not v['holo'] and not v.get('legacy')}
        #     player_missing_cards.update(undiscovered_cards)
        #     server_members = [x for x in ctx.guild.members]

        #     if player_missing_cards:
        #         await ctx.send(f"User is not eligible for prestige! Please complete your collection first.\nYou currently have {len(player_collection.keys())}/{len(server_members)} cards.")
        #         return
            
        #     await ctx.send(f"User is eligible for prestige!\nPrestige will **delete** all your cards (except legacy and holo) **including duplicates** and increase your prestige level by 1.\n**This should only be done if you want to reset your trading card collection! Prestige level will not give you anything more than bragging rights.**")
        #     await ctx.send(f"<@{ctx.author.id}> **THIS WILL RESET YOUR TRADING CARDS PROGRESSION.**\n**DO YOU WISH TO PROCEED WITH PRESTIGE?**\n```css\nY\n```")

        #     def check(m):
        #         return m.author == ctx.author and m.content.lower() == "y"

        #     try:
        #         await bot.wait_for("message", check=check, timeout=15.0)
        #     except asyncio.TimeoutError:
        #         await ctx.send("Command timed out. Operation cancelled.")
        #         return
            
        #     await ctx.send("Action confirmed! Processing prestige...")
        #     for id, info in database[str(ctx.author.id)].items():
        #         if info.get('holo') or info.get('legacy'):
        #             pass
        #         else:
        #             database[str(ctx.author.id)].pop(id)

        # Admin/botmaster commands

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
                if f"{card_id}{'_holo' if is_holo else ''}" not in all_cards:
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
                    except Exception as e:
                        print(e)

                    is_holo = False
                    if card.endswith('_holo'):
                        card = card.replace('_holo', '')
                        is_holo = True
                    all_cards.add( (card, is_holo, ctx.guild.get_member(int(card))) )
                
                userobject = ctx.guild.get_member(int(user_id))
                await ctx.send(f"Binder for {userobject.name if userobject else user_id} rebuilt!")

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
            
            await tc_add(user_ID=userID, card_ID=cardID, ctx=ctx)

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

            await tc_remove(user_ID=userID, card_ID=cardID, ctx=ctx)

            await ctx.send(f"Card `{cardID}` removed from user `{userID}` collection.")
        
        elif args[0].lower() == 'legacy_check':
            if not any(role.id in [role_staff, role_officers, 630835784274018347] for role in ctx.author.roles):
                await ctx.send("Command only authorized for users with staff or officer roles.")
                return
            
            legacy_IDs, unlegacy_IDs = await tc_legacy_check()
            
            if legacy_IDs:
                legacy_IDs_list = '\n'.join(legacy_IDs)
                await ctx.send(f"{len(legacy_IDs)} cards have been detected to be new legacy cards:\n{legacy_IDs_list}")
            else:
                await ctx.send("No new legacy cards detected!")
            
            if unlegacy_IDs:
                unlegacy_IDs_list = '\n'.join(legacy_IDs)
                await ctx.send(f"{len(unlegacy_IDs)} cards have been detected to be no longer legacy cards:\n{unlegacy_IDs_list}")

        else:
            raise Exception(f"Argument {args[0]} is not recognized.")

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

    await tc_add(ctx.author.id, card_ID, ctx)

    statistics("Trading cards pulled")

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
        name="binder+ username",
        value=f"*Displays your binder (including legacy cards). If username is provided, displays that user's binder instead.*",
        inline=False
    )

    embed2.add_field(
        name="legacybinder username",
        value=f"*Displays your binder of legacy cards. If username is provided, displays that user's binder instead.*",
        inline=False
    )

    embed2.add_field(
        name="list username",
        value=f"*Lists all owned cards with details. If username is provided, displays that user's list instead.*",
        inline=False
    )

    embed2.add_field(
        name="list+ username",
        value=f"*Lists all owned cards (including legacy cards) with details. If username is provided, displays that user's list instead.*",
        inline=False
    )

    embed2.add_field(
        name="legacylist username",
        value=f"*Lists all owned legacy cards with details. If username is provided, displays that user's list instead.*",
        inline=False
    )

    embed2.add_field(
        name="collection username",
        value=f"*Displays a summary of cards of each rarity collected. If username is provided, displays that user's summary instead.*",
        inline=False
    )

    embed2.add_field(
        name="missing username",
        value=f"*Displays a list of cards missing from the user's collection. If username is provided, displays that user's missing cards instead.*",
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
        name="accept trade_id OR trade_index",
        value=f"*Accept trade offer with ID trade_id or index trade_index (issue trades command to view trade IDs and index)*",
        inline=False
    )

    embed2.add_field(
        name="reject trade_id OR trade_index",
        value=f"*Reject trade offer with ID trade_id or index trade_index (issue trades command to view trade IDs and index).*",
        inline=False
    )

    embed2.add_field(
        name="cancel trade_id",
        value=f"*Cancel your trade offer (with ID trade_id) to another user.*",
        inline=False
    )

    embed2.add_field(
        name="whohas/whohasany card_id OR \"card name\"",
        value=f"*`whohas` checks who has a duplicate of the queried card. `whohasany` will return all user who have at least one of that card.*",
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

    embed2.add_field(
        name="legacy_check",
        value=f"*STAFF/OFFICERS ONLY - Manually check and process legacy/unlegacy cards. Task automatically runs daily.*",
        inline=False
    )

    await ctx.send(embed=embed2)

@bot.command()
async def role(ctx, role_query=None):

    allowed_roles_names = ', '.join( [ '`'+role+'`' for role in allowed_roles ] )

    if role_query not in allowed_roles.keys():
        await ctx.send(f"Role `{role_query}` not found. Must be one of: {allowed_roles_names}")
        return
    
    role = ctx.guild.get_role(allowed_roles[role_query])

    if role not in ctx.author.roles:
        await ctx.author.add_roles(role)
        await ctx.send(f"Role `{role.name}` granted!")
    else:
        await ctx.author.remove_roles(role)
        await ctx.send(f"Role `{role.name}` revoked!")

@bot.command()
async def bug(ctx, *report):
    report = ' '.join(report)

    with open('bug_reports.json') as feedsjson:
        file = json.load(feedsjson)
    
    file[ctx.message.id] = {
        'reporter': ctx.author.name,
        'message_link': f'https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}',
        'report': report,
        'type': 'bugs'
    }

    with open("bug_reports.json", "w") as f:
        json.dump(file, f, indent=4)
    
    await ctx.send(f"Bug report `{ctx.message.id}` logged! Thanks for your support!")

    statistics("PaigeBot bugs/suggestions submitted")

@bot.command(aliases=['suggest'])
async def suggestion(ctx, *report):
    report = ' '.join(report)

    with open('bug_reports.json') as feedsjson:
        file = json.load(feedsjson)
    
    file[ctx.message.id] = {
        'reporter': ctx.author.name,
        'message_link': f'https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}',
        'report': report,
        'type': 'suggestions'
    }

    with open("bug_reports.json", "w") as f:
        json.dump(file, f, indent=4)
    
    await ctx.send(f"Suggestion `{ctx.message.id}` logged! Thanks for your support!")

    statistics("PaigeBot bugs/suggestions submitted")

@bot.command(aliases=['buglog'])
async def reports(ctx, *args):

    with open('bug_reports.json') as feedsjson:
        file = json.load(feedsjson)

    report_types = ['bugs', 'suggestions']

    if args:
        if args[0].lower() == 'clear':
            if not ctx.author.id == jbondguy007_userID:
                await ctx.send("Clearing reports is only authorized for jbondguy007.")
                return
            if len(args) < 2:
                await ctx.send("Clear command requires `reportID` argument.")
                return
            
            for arg in args[1:]:
                try:
                    bug = file[arg]
                    del file[arg]
                    with open("bug_reports.json", "w") as f:
                        json.dump(file, f, indent=4)
                    await ctx.send(f"Cleared report:\nReport ID: `{arg}`\nDescription: `{bug['report']}`")
                    continue
                except:
                    await ctx.send(f"Error attempting to clear report `{arg}`.")
                    continue
            return
        
        elif args[0].lower() == 'bugs' or args[0].lower() == 'suggestions':
            report_types = [args[0].lower()]
        
        else:
            await ctx.send(f"Unrecognized command argument `{args[0]}`.")
            return
    
    embed = discord.Embed(title=f"{' and '.join([report_type.capitalize() for report_type in report_types])} Reports Log", color=bot_color)

    for report_ID, report in [(id, rep) for id, rep in file.items() if rep['type'] in report_types]:
        
        report_type = f"{report['type'][:-1].capitalize()}: "

        embed.add_field(
            name=f"Report ID: {report_ID}\nReporter: {report['reporter']}\nReport Link: {report['message_link']}",
            value=f"{report_type}{report['report']}",
            inline=False
        )
    
    if len(file) == 0:
        embed.add_field(
            name="No reports pending!",
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
    
    url = game['Issue Link'] if not game['Issue Link'] == 'TBD' else None
    issue_number = game['Issue Number']

    embed = discord.Embed(title=f"\"{game['Game']}\" Review", url=url, color=bot_color)

    if url:
        embed.add_field(
            name=f"{game['Game']} was reviewed by {game['Assigned']} as part of SG Magazine Issue #{issue_number}.",
            value=f"*Click the link above the embed to check out SG Magazine Issue #{issue_number}!*"
        )
    elif issue_number:
        embed.add_field(
            name=f"{game['Game']} is being reviewed by {game['Assigned']} as part of SG Magazine Issue #{issue_number}.",
            value=f"*SG Magazine Issue #{issue_number} is not out yet! Check back later.*"
        )
    else:
        embed.add_field(
            name=f"{game['Game']} is being reviewed by {game['Assigned']} as part of a future SG Magazine Issue.",
            value=f"*Check back later for the review link!*"
        )

    await ctx.send(embed=embed)

@bot.command(aliases=['flipcoin'])
async def coinflip(ctx):
    result = random.choice(["heads! :bust_in_silhouette:", "tails! :coin:"])
    await ctx.send(f"Paige flips a virtual coin and it lands on... {result}")

@bot.command(aliases=['pta'])
async def process_tc_achievements(ctx):
    if not ctx.author.id == jbondguy007_userID:
        await ctx.send("Command only authorized to botmaster (jbondguy007).")
        return

    with open('tradingcards/database.json') as feedsjson:
        tc_database = json.load(feedsjson)
    
    size = len(tc_database)
    msg = await ctx.send(f"Processing... 0/{size} user binders...")
    
    for e, (user, cards) in enumerate(tc_database.items()):
        normal_count = 0
        holo_count = 0
        for card, details in cards.items():
            if card.endswith('_holo'):
                holo_count += details['count']
            else:
                normal_count += details['count']

            # tc_misc_getself
            if user == re.search("\d+", card)[0]:
                await achievement(ctx=ctx, who=user, achievement_ids=['tc_misc_getself'])

            # tc_misc_getdup
            if details['count'] > 1:
                await achievement(ctx=ctx, achievement_ids=['tc_misc_getdup'])
            
            # tc_misc_same_normalholo
            if (
                '_holo' in card and tc_database[user].get(card.replace('_holo', '')) or
                tc_database[user].get(card+'_holo')
                ):
                    await achievement(ctx=ctx, achievement_ids=['tc_misc_same_normalholo'])
        
        for i in range(holo_count):
            await achievement(
                ctx=ctx,
                achievement_ids=[
                    'tc_holo_count_1',
                    'tc_holo_count_5',
                    'tc_holo_count_10',
                    'tc_holo_count_25',
                    'tc_holo_count_50'
                ],
                who=user,
                dontgrant=False
            )
        
        for i in range(normal_count):
            await achievement(
                ctx=ctx,
                achievement_ids=[
                    'tc_normal_count_1',
                    'tc_normal_count_5',
                    'tc_normal_count_10',
                    'tc_normal_count_25',
                    'tc_normal_count_50',
                    'tc_normal_count_100'
                ],
                who=user,
                dontgrant=True
            )

        await msg.edit(content=f"Processing... {e+1}/{size} user binders...")
    
    await msg.edit(content=f"Done! {e+1}/{size}")
    await ctx.send(f"Done! {e+1}/{size} user binders processed.")

@bot.command()
async def grant_achievement(ctx, *args):
    if not ctx.author.id == jbondguy007_userID:
        await ctx.send("Command only authorized to botmaster (jbondguy007).")
        return
    
    try:
        granted_user = get_user_from_username(args[0]).id
    except:
        granted_user = args[0]

    try:
        granted_achievement_id = args[1]
    except:
        await ctx.send("One or more arguments are missing!")
        return

    try:
        await achievement(ctx=ctx, who=granted_user, achievement_ids=[granted_achievement_id])
    except:
        await ctx.send(f"Error granting achievement! Make sure user ID {granted_user} and achievement ID {granted_achievement_id} are correct.")

@bot.command(aliases=['cheevos', 'ach'])
async def achievements(ctx, *args):

    user = ctx.author
    first_time_viewing_achievements = False

    with open("achievements_usersdata.json") as feedsjson:
        achievements_usersdata = json.load(feedsjson)
    
    with open("achievements.json") as feedsjson:
        achievements_list = json.load(feedsjson)
    
    if not achievements_usersdata.get(str(user.id)):
        first_time_viewing_achievements = True
        achievements_usersdata[str(user.id)] = {}
    
    if not achievements_usersdata[str(user.id)].get('misc_achievement_command'):
        first_time_viewing_achievements = True
    
    await achievement(ctx=ctx, achievement_ids=['misc_first_interact', 'misc_achievement_command'])

    user_achievements = achievements_usersdata[str(user.id)]

    try:
        arg = args[0]
    except:
        arg = False
    
    achievements_categories = {re.search('^[^_]+(?=_)', key)[0] for key in achievements_list.keys()}

    if arg in achievements_categories:
        achievements_list = {id: ach for id, ach in achievements_list.items() if id.startswith(arg.lower())}
        user_achievements = {id: ach for id, ach in user_achievements.items() if id.startswith(arg.lower())}
    elif not arg:
        pass
    else:
        await ctx.send(f"Category `{arg}` is not recognized. Must be one of {', '.join(['`'+x+'`' for x in achievements_categories])}.")
        return
    
    achievements_unlocked = {id: ach for id, ach in user_achievements.items() if ach.get('unlocked_date')}

    keys = list(achievements_list.keys())
    achievements_count = len(achievements_list)
    batch_size = 25

    for i in range(0, achievements_count, batch_size):
        embed = discord.Embed(title=f"{user.name}'s {arg if arg else 'Full List of'} Achievements", description=f"Unlocked {len(achievements_unlocked.keys())}/{achievements_count}" if i == 0 else "", color=bot_color)

        batch_keys = keys[i:i + batch_size]
        batch_dict = {key: achievements_list[key] for key in batch_keys}

        for ach, details in batch_dict.items():
            try:
                unlocked = user_achievements[ach]['unlocked_date']
            except:
                unlocked = False
            
            progress = ''
            if details['goal'] > 1:
                if user_achievements.get(ach):
                    progress = f"({int(user_achievements[ach]['counter']):,}/{details['goal']:,})"
                else:
                    progress = f"(0/{details['goal']:,})"
            
            if details['secret'] and not unlocked:
                embed.add_field(
                    name=f"🔒 {details['name']}",
                    value=f"SECRET ACHIEVEMENT - Unlock to reveal description\nUnlocked: {unlocked}",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{':white_check_mark:' if unlocked else '🔒'} {details['name']}",
                    value=f"{details['description']} {progress}\nUnlocked: {unlocked}",
                    inline=False
                )
    
        await ctx.send(embed=embed)
    if first_time_viewing_achievements:
        await ctx.send(
f"""### DISCLAIMER
<@{ctx.author.id}> I see this is your first time viewing achievements. Welcome to PaigeBot Achievements!

In an effort to ensure everyone has a good time, please abide to some general guidelines:
- Please do not intentionally spam the exact same command/message in an attempt to speedrun achievements! Your enthusiasm is appreciated, but try not to spam.
- Similarly, while you can ask another user to play chat games with you to unlock achievements, avoid bruteforcing or assisting each other in artificially unlocking achievements.
- In general, just enjoy the achievements responsibly! This is a fun feature, but we don't want it to cause issues due to heavy spam and whatnot. Paige will be watching! <:paigewink:1135346141676978266>
"""
    )

@bot.command()
async def stats(ctx):

    with open("statistics.json") as feedsjson:
        statistics = json.load(feedsjson)

    embed1 = discord.Embed(title="PaigeBot and Misc Statistics", description="A collection of PaigeBot and miscellaneous server-wide statistics.", color=bot_color)
    embed2 = discord.Embed(title="", description="", color=bot_color)

    for name, value in list(statistics.items())[:25]:
        embed1.add_field(
            name=name,
            value=f"{value:,}",
            inline=False
        )
    
    for name, value in list(statistics.items())[25:]:
        embed2.add_field(
            name=name,
            value=f"{value:,}",
            inline=False
        )
    
    await ctx.send(embed=embed1)
    await ctx.send(embed=embed2)

@bot.command(aliases=['tpir'])
async def gtp(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Guess The Price rounds may not be started in DMs!")
        return
    
    global prevent_gtp_command
    if prevent_gtp_command:
        await ctx.send(f"<@{ctx.author.id}> a Guess The Price round is already ongoing!")
        return
    prevent_gtp_command = True

    await achievement(ctx=ctx, achievement_ids=['gtp_misc_start_round'])

    gtp_start_timer = 20

    url = 'http://www.watchcount.com/completed.php'
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64"})
    soup = bs(r.content, "html.parser")
    # categories_raw = [(re.search('^(.+?) \[', option.text[2:]).group(1), int(option['value'])) for option in soup.find(id="select_bcat").find_all('option')][1:]

    category_links = soup.find("div", {"class": "top-categories"}).find_all('a', class_='category-link')

    categories = [(link.get_text(strip=True), link['href']) for link in category_links]

    if not categories:
        await ctx.send("Error: Failed to fetch categories list! Please try again.")
        prevent_gtp_command = False
        return

    category = random.choice(categories)
    cat_id = category[1].split('/')[3]

    await ctx.send(f"Your category is... `{category[0]}`! Let's see what we have...")

    listings_category_url = f'https://www.watchcount.com/sold/-/{cat_id}/auction?sortBy=bestmatch'

    r = requests.get(listings_category_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64"})

    soup = bs(r.content, "html.parser")
    table = soup.find("div", {"class": "container shrink-container"})

    random_listing = random.choice(table.find_all('div', {'class': 'col-auto item-content'}))

    title = random_listing.find('div', {'class': 'general-info-container'}).find('span').get_text(strip=True)
    price_text = random_listing.find('div', {'class': 'price'}).text
    price = float(Decimal(sub(r'[^\d.]', '', price_text)))
    image = random_listing.find('img', {'class': 'image'})['src']

    embed = discord.Embed(title=title, description="It's time to Guess The Price!")
    embed.set_image(url=image)

    await ctx.send(embed=embed)

    responses = {}

    def check(m):
        return m.author != bot.user and m.channel == ctx.channel and re.match('^(?:\d+|\d+\.\d{2})$', m.content) and m.author.id not in responses.keys()
    
    await ctx.send(f"Guessing ends in `{gtp_start_timer}` seconds. Only your first guess counts!")

    time_started = datetime.now()
    gtp_timer = gtp_start_timer

    while True:
        try:
            message = await bot.wait_for('message', check=check, timeout=gtp_timer)
            responses[message.author.id] = float(Decimal(sub(r'[^\d.]', '', message.content)))

            now = datetime.now()

            time_elapsed = now-time_started
            time_elapsed = timedelta(seconds=time_elapsed.seconds)

            timer_deltatime = timedelta(seconds=gtp_start_timer) # 20

            gtp_timer = timer_deltatime-time_elapsed
            gtp_timer = gtp_timer.seconds

        except asyncio.TimeoutError:
            break
        continue

    if not responses:
        await ctx.send(f"No guesses? Too bad!\nThis item sold for... **${price:.2f}**\nThanks for playing!")
        prevent_gtp_command = False
        return
    
    statistics("Guess The Price rounds played")
    
    guesses = '\n'.join(f"{bot.get_user(int(user)).name}: ${response:.2f}" for user, response in responses.items())

    await ctx.send(f"Guesses: \n{guesses}")

    def closest_value(dictionary, target):
        closest_key = min(dictionary, key=lambda key: abs(dictionary[key] - target))
        closest_value = dictionary[closest_key]
        return closest_key, closest_value
    
    closest_user, closest_guess = closest_value(responses, price)

    difference = abs(price - closest_guess)

    if len(responses) == 1:
        await ctx.send(f"Unfortunately, there are no winners as <@{closest_user}> was the only participant this round. \nYou guessed `${closest_guess:,.2f}`, only `${difference:,.2f}` from the correct answer:\n# `${price:,.2f}`!")
    else:
        await ctx.send(f"And the winner is...\n<@{closest_user}> who guessed `${closest_guess:,.2f}`, only `${difference:,.2f}` from the correct answer:\n# `${price:,.2f}`!")
    
        await achievement(
            ctx=ctx,
            who=closest_user,
            achievement_ids=[
                'gtp_win_count_1',
                'gtp_win_count_5',
                'gtp_win_count_10',
                'gtp_win_count_25',
                'gtp_win_count_50'
            ]
        )

        if len(responses) >= 5:
            await achievement(ctx=ctx, who=closest_user, achievement_ids=['gtp_misc_win_against_5'])
        
        if difference <= 1.00:
            await achievement(ctx=ctx, who=closest_user, achievement_ids=['gtp_win_guess_closeness_1'])
        if difference <= 5.00:
            await achievement(ctx=ctx, who=closest_user, achievement_ids=['gtp_win_guess_closeness_5'])
        if difference >= 1000.00:
            await achievement(ctx=ctx, who=closest_user, achievement_ids=['gtp_misc_win_1k_away'])
        if difference >= 10000.00:
            await achievement(ctx=ctx, who=closest_user, achievement_ids=['gtp_misc_win_10k_away'])
        if difference >= 25000.00:
            await achievement(ctx=ctx, who=closest_user, achievement_ids=['gtp_misc_win_25k_away'])
    
    prevent_gtp_command = False
    
    for user, guess in responses.items():

        difference = abs(price - guess)
        if difference == 0.00:
            await achievement(ctx=ctx, who=user, achievement_ids=['gtp_guess_closeness_perfect'])
            statistics("Guess The Price perfect guesses")
        if guess == 3.50:
            await achievement(ctx=ctx, who=user, achievement_ids=['gtp_misc_guess_3_50'])
        elif guess == 42.0:
            await achievement(ctx=ctx, who=user, achievement_ids=['gtp_misc_guess_42'])
        elif guess == 69.0:
            await achievement(ctx=ctx, who=user, achievement_ids=['gtp_misc_guess_69'])
        elif guess in [420.0, 4.20]:
            await achievement(ctx=ctx, who=user, achievement_ids=['gtp_misc_guess_420'])
        
        statistics("Guess The Price guesses")

@bot.command()
async def hltb(ctx, *query):

    query_string = ' '.join(query)

    results_list = await HowLongToBeat().async_search(query_string)
    if results_list is not None and len(results_list) > 0:
        best_element = max(results_list, key=lambda element: element.similarity)

        embed = discord.Embed(title=best_element.game_name, url=best_element.game_web_link)

        embed.add_field(
            name="Main Story",
            value=best_element.main_story
        )
        embed.add_field(
            name="Main + Extra",
            value=best_element.main_extra
        )
        embed.add_field(
            name="Completionist",
            value=best_element.completionist
        )

        embed.set_image(url=best_element.game_image_url)
    
        await ctx.send(embed=embed)
    
    else:
        await ctx.send("No result found!")

@bot.command(aliases=[ 'nextsale' ])
async def steamsale(ctx):
    url = 'https://steambase.io/sales'
    r = requests.get(url)
    soup = bs(r.content, 'html.parser')

    current_sale = soup.select_one('.text-2xl.font-normal')
    current_sale = current_sale.get_text(separator=' ', strip=True)

    next_sale = soup.select_one('.w-full.flex.flex-col.space-y-4.justify-between.px-4.py-4.border.rounded-lg.border-slate-700')
    next_sale = next_sale.get_text(separator=' ', strip=True)

    await ctx.send(f"{current_sale}\n\n{next_sale}")

@bot.command(aliases=[ 'remind' ])
async def reminder(ctx, reminder, *times):

    if not ctx.guild:
        await ctx.send("The `reminder` command cannot be executed from Direct Messages.")
        return

    if reminder.lower() == 'cancel':
        timer_ID = times[0]

        with open('reminders.json', 'r') as outfile:
            reminders = json.load(outfile)
        
        try:
            await ctx.send(f"Reminder `{timer_ID}` (\"{reminders[str(ctx.author.id)][str(timer_ID)]['reminder']}\") cancelled!")
            del reminders[str(ctx.author.id)][str(timer_ID)]
            with open('reminders.json', 'w') as f:
                json.dump(reminders, f, indent=4)
            return
        except:
            await ctx.send(f"Unable to locate a reminder with ID `{timer_ID}` in your reminders.")
            return

    days = 0
    hours = 0
    minutes = 0

    if not times:

        if reminder.lower() == 'tc':
            hours = 8
        
        elif reminder.lower() == 'slots':
            hours = 6
        
        else:
            await ctx.send(f"Reminders requires time arguments!")
            return

    else:
        for data in times:
            data = data.strip().lower()

            if data.endswith('d'):
                days = int(data[:-1])
            elif data.endswith('h'):
                hours = int(data[:-1])
            elif data.endswith('m'):
                minutes = int(data[:-1])
    
    time_values = {
        'days': int(days),
        'hours': int(hours),
        'minutes': int(minutes)
    }

    time_delta = datetime.now()+timedelta(days=time_values['days'], hours=time_values['hours'], minutes=time_values['minutes'])

    time_payload = str(time_delta.replace(microsecond=0))

    payload = {
        'reminder': reminder,
        'timer': time_payload,
        'channel': ctx.channel.id
    }

    with open('reminders.json', 'r') as outfile:
        reminders = json.load(outfile)
    
    if str(ctx.author.id) not in reminders:
        reminders[str(ctx.author.id)] = {}

    reminders[str(ctx.author.id)][str(ctx.message.id)] = payload

    with open('reminders.json', 'w') as f:
        json.dump(reminders, f, indent=4)

    unix_timestamp = int(time.mktime((time_delta).timetuple()))

    await ctx.send(f"Sure! I will remind you: `{reminder}` in {time_values['days']} day(s), {time_values['hours']} hour(s), and {time_values['minutes']} minute(s) (roughly <t:{unix_timestamp}:R>).\nReminder ID: `{ctx.message.id}`")

    await achievement(
        ctx=ctx,
        achievement_ids=[
            'reminder_count_1',
            'reminder_count_5',
            'reminder_count_10',
            'reminder_count_25',
            'reminder_count_50',
            'reminder_count_100'
        ]
    )

    statistics("Reminders set")

@bot.command()
async def reminders(ctx):
    with open('reminders.json', 'r') as outfile:
        reminders = json.load(outfile)
    
    try:
        user_reminders = {k: v for k, v in reminders[str(ctx.author.id)].items()}
        if not user_reminders:
            raise Exception()
        for k, v in user_reminders.items():
            date_time = datetime.strptime(v['timer'],"%Y-%m-%d %H:%M:%S")
            unix_timestamp = date_time.timestamp()
            user_reminders[k]['unix_timestamp'] = int(unix_timestamp)
    except:
        await ctx.send("User has no reminders.")
        return

    msg = '\n'.join( [f"`{ID}`: \"{data['reminder']}\" ({data['timer']}, roughly <t:{data['unix_timestamp']}:R>)" for ID, data in user_reminders.items()] )

    await ctx.send(content=msg)

# crew_values = {
#     'miner': {
#         'abbreviation': 'mi',
#         'cost': 10,
#         'production': 1
#     },
#     'jackhammer': {
#         'abbreviation': 'jh',
#         'cost': 110,
#         'production': 8
#     },
#     'drill': {
#         'abbreviation': 'dr',
#         'cost': 1200,
#         'production': 48
#     },
#     'excavator': {
#         'abbreviation': 'ex',
#         'cost': 13000,
#         'production': 270
#     },
#     'jumbo drill': {
#         'abbreviation': 'jdr',
#         'cost': 140000,
#         'production': 1425
#     },
#     'jumbo excavator': {
#         'abbreviation': 'jex',
#         'cost': 2000000,
#         'production': 8000
#     },
#     'mine': {
#         'abbreviation': 'mine',
#         'cost': 33000000,
#         'production': 45000
#     },
#     'mining town': {
#         'abbreviation': 'mt',
#         'cost': 450000000,
#         'production': 240000
#     },
#     'space mining crew': {
#         'abbreviation': 'smc',
#         'cost': 6000000000,
#         'production': 1300000
#     },
#     'interplanetary mining company': {
#         'abbreviation': 'ipmc',
#         'cost': 75000000000,
#         'production': 8000000
#     }
# }

crew_values = {
    'miner': {
        'abbreviation': 'mi',
        'cost': 10,
        'production': 1
    },
    'jackhammer': {
        'abbreviation': 'jh',
        'cost': 120,
        'production': 8
    },
    'drill': {
        'abbreviation': 'dr',
        'cost': 1200,
        'production': 50
    },
    'excavator': {
        'abbreviation': 'ex',
        'cost': 13500,
        'production': 280
    },
    'jumbo drill': {
        'abbreviation': 'jdr',
        'cost': 145000,
        'production': 1500
    },
    'jumbo excavator': {
        'abbreviation': 'jex',
        'cost': 1625000,
        'production': 8000
    },
    'mine': {
        'abbreviation': 'mine',
        'cost': 30000000,
        'production': 44750
    },
    'mining town': {
        'abbreviation': 'mt',
        'cost': 260000000,
        'production': 252500
    },
    'space mining crew': {
        'abbreviation': 'smc',
        'cost': 3450000000,
        'production': 1400000
    },
    'interplanetary mining company': {
        'abbreviation': 'ipmc',
        'cost': 49500000000,
        'production': 8000000
    },
    'warp drive mining fleet': {
        'abbreviation': 'wdmf',
        'cost': 725000000000,
        'production': 45000000
    },
    'galactic mining company': {
        'abbreviation': 'gmc',
        'cost': 11000000000000,
        'production': 250000000
    },
    'alien assault command': {
        'abbreviation': 'aac',
        'cost': 167500000000000,
        'production': 1350000000
    },
    'intergalactical mining company': {
        'abbreviation': 'igmc',
        'cost': 2650000000000000,
        'production': 7400000000
    },
    'intergalactical war force': {
        'abbreviation': 'igwf',
        'cost': 45500000000000000,
        'production': 40000000000
    }
}

with open('permanent_variables.json', 'r') as outfile:
    persistent_data = json.load(outfile)
gems_value_multi = persistent_data['gems_multi']

async def mine_max_unit_afford_count(money, crew_base_value, crew_owned_count):
    total_cost = 0
    counter = 0

    while total_cost <= money:
        counter += 1
        total_cost = sum(crew_base_value * (1.2 ** (crew_owned_count + counted)) for counted in range(counter))

    counter -= 1
    
    return counter

@bot.command(aliases=[ 'm' ])
@commands.max_concurrency(number=1, per=commands.BucketType.user, wait=False)
async def mine(ctx, *args):

    global prevent_mine_command

    if prevent_mine_command:
        await ctx.send(f"<@{ctx.author.id}> gems drop in progress! Try again in a second.")
        return

    # Initiate user in file
    with open('mine.json', 'r') as outfile:
        mine_file = json.load(outfile)

    if str(ctx.author.id) not in mine_file:

        mine_file[str(ctx.author.id)] = {
            'assets': {
                'gems': 0,
                'money': 10
            },
            'crew': {},
            'multi': {
                'ascension': 0.0
            },
            'global stats': {
                "gems mined": 0,
                "money earned": 0,
                "units bought": 0
            }
        }
        for key in crew_values:
            mine_file[str(ctx.author.id)]['crew'][key] = {
                'count': 0,
                'upgraded': 1.0
            }

        with open('mine.json', 'w') as f:
            json.dump(mine_file, f, indent=4)

    if args:

        arg = args[0]

        if arg.lower() in ['shop', 'store']:

            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)
            user_data = mine_data[str(ctx.author.id)]
            money = user_data['assets']['money']

            embed = discord.Embed(title=f"{ctx.author.name}'s Mine Shop", description=f"Money: $ {money:,.2f}{f' ({human_num(money)})' if money > 999.99 else ''}", color=bot_color)

            for crew, crew_info in crew_values.items():

                cost = crew_info['cost']*(1.2**(mine_data[str(ctx.author.id)]['crew'][crew]['count']))
                prod = crew_info['production']*user_data['crew'][crew]['upgraded']
                max_buy = await mine_max_unit_afford_count(money=user_data['assets']['money'], crew_base_value=crew_info['cost'], crew_owned_count=user_data['crew'][crew]['count'])
                embed.add_field(
                    name=f"{crew.title()} (`{crew_info['abbreviation']}`)",
                    value=f"💵 Cost: `$ {f'{human_num(cost)}' if cost > 999.99 else f'{cost:,.2f}'}`\n💎 Production: `{f'{human_num(prod)}' if cost > 999.99 else f'{prod:,.2f}'}`{' (Upgraded)' if user_data['crew'][crew]['upgraded'] == 2.0 else ''}\n:shopping_cart: Can Afford: {f'`{max_buy}`' if max_buy else f'`None` ($ {human_num(cost-money)} more needed)'}",
                    inline=False
                )
            
            await ctx.send(embed=embed)

            return
        
        elif arg.lower() == 'buy':
            try:
                what = args[1].lower()
            except:
                await ctx.send(f"Error: Missing unit type argument.")
                return
        
            try:
                count = args[2]
                if not count.lower() == 'max':
                    count = int(count)
            except:
                count = 1
            
            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)
                user_data = mine_data[str(ctx.author.id)]

            for crew, info in crew_values.items():
                if what == info['abbreviation']:
                    what = crew
                    break
                else:
                    continue

            user_money = user_data['assets']['money']
            user_crew_count = user_data['crew'][what]['count']
            crew_base_value = crew_values[what]['cost']

            if count == "max":

                counted = await mine_max_unit_afford_count(money=user_money, crew_base_value=crew_base_value, crew_owned_count=user_crew_count)
                count = max(counted, 1)

            all_costs = [ crew_base_value * (1.2 ** ( user_crew_count + counted ) ) for counted in range(count)]

            cost = sum(all_costs)

            if cost <= user_money:

                units_intro = {
                    'miner': {
                        'title': "Humble Beginnings",
                        'description': "As you hire your first miner, you are filled with determination. So it begins..."
                    },
                    'jumbo drill': {
                        'title': "Industrialization",
                        'description': "As time passes, your mining operation grows faster than expected. You're experiencing rapid growth, the cash flow is good, and you're expanding your business quickly."
                    },
                    'mine': {
                        'title': "Conglomerate",
                        'description': "The final documents have been signed - you just purchased an entire mining operation alongside your own. Things are about to get big, fast."
                    },
                    'mining town': {
                        'title': "Moving Up in the World",
                        'description': "You think back to when you started, with a single miner. Who'd have thought you'd be the proud owner of an entire town one day?\n\nAnd yet, you can't help but feel like this is just the beginning..."
                    },
                    'space mining crew': {
                        'title': "The Sky's Not the Limit",
                        'description': "This is it. After years of research and development, you've finally done it.\nYou've established a Space Mining Crew (SMC) division, to seek out resources... in space.\n\nYou are conquering the final frontier."
                    },
                    'interplanetary mining company': {
                        'title': "Planet Breacher",
                        'description': "You stand up from your lavish desk and walk up to the gigantic window of your top-floor office, revealing the gritty, yet satisfying view of your empire. After conquring the edges of space, you pursued riches within the rest of the solar system.\n\nIs this it? Have you reached the edge of the explorable universe? You shrug away the thought, and help yourself to an exorbitantly expensive whiskey from your spirits cabinet.\n\nThere's still work to do, you think to yourself, as you enjoy the burning sensation of a well-deserved treat run down your throat."
                    },
                    'warp drive mining fleet': {
                        'title': "Fast Travel",
                        'description': "A breakthrough in space exploration technology yields the ability to travel at extreme speeds through warp drives. The technology allows for mining and shipping crews to mine every corner of the galaxy."
                    },
                    'galactic mining company': {
                        'title': "Across the Galaxy, and Beyond",
                        'description': "With the development of warp drives, the galaxy is prime for exploration.\n\nVarious alien civilizations, systems, and most importantly, mining resources have been discovered through our galaxy. It's just waiting to be mined."
                    },
                    'alien assault command': {
                        'title': "Star Wars",
                        'description': "The first encounter with life outside our home planet was on friendly terms... until the fight for raw resources began. Mining companies must now send out squads of armed mercenaries to attack alien life who dare try to lay claim upon mining resources.\n\nInsolence towards the glorious mining empire of [REDACTED] will be met with deadly force."
                    },
                    'intergalactical mining company': {
                        'title': "Universal Exploitation",
                        'description': "As the faster-than-light travel technology improves, mining operations expand beyond the galaxy. No corner of the known universe remains untouched by the glorious hand of [REDACTED].\n\nWe are unstoppable."
                    },
                    'intergalactical war force': {
                        'title': "The Ultimate Conflict",
                        'description': "War. War never changes.\n\nThe neighboring nation of [REDACTED] waged war to gather slaves and wealth.\n[REDACTED] built an empire from its lust for gold and territory.\n[REDACTED] shaped a battered [REDACTED] into an economic superpower.\n\nOur war lays on the foundations of our economic superpowers - gems. If we must battle other races across the entire universe for the rest of times to maintain and grow our monopoly of the mining industry... then so be it.\n\nFor wealth.\nFor power.\n\nFor the glory of [REDACTED]."
                    }
                }

                try:
                    if mine_data[str(ctx.author.id)]['crew'][what]['count'] == 0:
                        unit = units_intro[what]
                        file = discord.File(f"idlemine/images/units/{what.replace(' ', '_')}.png")
                        embed = discord.Embed(title=unit['title'], description=unit['description'])
                        embed.set_image(url=f"attachment://{what.replace(' ', '_')}.png")
                        await ctx.send(embed=embed, file=file)
                except Exception as e:
                    print(f"mine() first unit purchase message failed: {e}")

                mine_data[str(ctx.author.id)]['assets']['money'] -= cost
                mine_data[str(ctx.author.id)]['crew'][what]['count'] += count
                mine_data[str(ctx.author.id)]['global stats']['units bought'] += count

                new_cost = crew_values[what]['cost'] * ( 1.2 ** ( mine_data[str(ctx.author.id)]['crew'][what]['count'] ) )

                await ctx.send(f"{ctx.author.name} purchased {count} `{what}` for `{human_num(cost)}`. Unit price has increased to `$ {human_num(new_cost)}` per unit. Your funds are now `$ {human_num(mine_data[str(ctx.author.id)]['assets']['money'])}`.")

                with open('mine.json', 'w') as f:
                    json.dump(mine_data, f, indent=4)

                statistics("Idle Mine units purchased", increase=count)

                await achievement(
                    ctx=ctx,
                    count=count,
                    achievement_ids=[
                        "mine_crew_hired_1",
                        "mine_crew_hired_5",
                        "mine_crew_hired_10",
                        "mine_crew_hired_25",
                        "mine_crew_hired_50",
                        "mine_crew_hired_100",
                        "mine_crew_hired_250",
                        "mine_crew_hired_500",
                        "mine_crew_hired_1k",
                        "mine_crew_hired_2k",
                        "mine_crew_hired_5k"
                    ]
                )

            else:
                await ctx.send(f"{ctx.author.name} cannot afford {count} `{what}` for `$ {human_num(cost)}`. Your funds: `$ {human_num(mine_data[str(ctx.author.id)]['assets']['money'])}`")
            
            return
        
        elif arg.lower() in ['upgrade', 'upgrades']:

            try:
                what = args[1].lower()

            except:
                with open('mine.json', 'r') as outfile:
                    mine_data = json.load(outfile)
                user_data = mine_data[str(ctx.author.id)]
                money = user_data['assets']['money']
                embed = discord.Embed(title=f"{ctx.author.name}'s Mine Upgrades", description=f"Money: $ {money:,.2f}{f' ({human_num(money)})' if money > 999.99 else ''}\n\n✅ - Upgraded\n:arrow_double_up: - Can upgrade\n:no_entry_sign: - Can't afford", color=bot_color)

                for crew, crew_info in crew_values.items():

                    cost = crew_info['cost']*100

                    if user_data['crew'][crew]['upgraded'] == 2.0:
                        cost_message = "Already upgraded"
                    else:
                        cost_message = f"`$ {f'{human_num(cost)}' if cost > 999.99 else f'{cost:,.2f}'}`"

                    embed.add_field(
                        name=f"{crew.title()} (`{crew_info['abbreviation']}`)",
                        value=f"{'✅' if cost_message == 'Already upgraded' else (':no_entry_sign:' if cost > money else ':arrow_double_up:')} Cost: {cost_message}{f' (`$ {human_num(cost-money)}` more needed)' if cost > money and not cost_message == 'Already upgraded' else ''}",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                return
            
            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)
                user_data = mine_data[str(ctx.author.id)]

            for crew, info in crew_values.items():
                if what == info['abbreviation']:
                    what = crew
                    break
                else:
                    continue

            if user_data['crew'][what]['upgraded'] == 2.0:
                await ctx.send(f"{ctx.author.name}, `{what}` unit already upgraded.")
                return

            user_money = user_data['assets']['money']
            crew_upgrade_cost = crew_values[what]['cost']*100

            if crew_upgrade_cost <= user_money:
                mine_data[str(ctx.author.id)]['assets']['money'] -= crew_upgrade_cost
                mine_data[str(ctx.author.id)]['crew'][what]['upgraded'] = 2.0

                await ctx.send(f"{ctx.author.name}, `{what}` unit upgraded! Production has doubled for this unit.")
            
                with open('mine.json', 'w') as f:
                    json.dump(mine_data, f, indent=4)

                return
            
            else:
                await ctx.send(f"{ctx.author.name} cannot afford to upgrade `{what}` for `$ {human_num(crew_upgrade_cost)}`. Your funds: `$ {human_num(mine_data[str(ctx.author.id)]['assets']['money'])}`")
                return
        
        elif arg.lower() == 'sell':
            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)
                user_data = mine_data[str(ctx.author.id)]
            
            money_before_selling = user_data['assets']['money']
            gems = int(user_data['assets']['gems'])
            ascension = user_data['multi']['ascension']
            
            if len(args) > 1:
                try:
                    count_to_sell = int(args[1])
                    if count_to_sell <= 0 or count_to_sell > gems:
                        raise(Exception)
                except:
                    await ctx.send(f"{ctx.author.name}, error processing `sell` function with argument `{args[1]}` - must be a positive integer no higher than your current gems count.")
                    return
            else:
                count_to_sell = gems
            
            if not gems:
                await ctx.send("You have no 💎 gems to sell!")
                return
            
            earning = round(
                ( count_to_sell * gems_value_multi ) * (1.0+(ascension/100.0)),
                2
            )
            
            mine_data[str(ctx.author.id)]['assets']['gems'] -= count_to_sell
            mine_data[str(ctx.author.id)]['assets']['money'] += round(earning, 2)
            mine_data[str(ctx.author.id)]['global stats']['money earned'] += round(earning, 2)

            with open('mine.json', 'w') as f:
                json.dump(mine_data, f, indent=4)

            await ctx.send(f"""
```diff
{ctx.author.name}'s Sale Receipt
__________________________________________
                    |
- Sold:             |  💎 {count_to_sell:,}{f' ({human_num(count_to_sell)})' if count_to_sell > 999.99 else ''} gem(s)
                    |
Gems Market Value:  | x $ {gems_value_multi:,.2f}/💎
Ascension Bonus:    | + $ {round( earning - ( count_to_sell * gems_value_multi ), 2 )+0.0:,} ({round(ascension, 4):,}%)
+ TOTAL:            |   $ {earning:,.2f}{f' ({human_num(earning)})' if earning > 999.99 else ''}
                    |
Previous Balance:   |   $ {money_before_selling:,.2f}{f' ({human_num(money_before_selling)})' if money_before_selling > 999.99 else ''}
New Balance:        |   $ {mine_data[str(ctx.author.id)]['assets']['money']:,.2f}{f' ({human_num(mine_data[str(ctx.author.id)]["assets"]["money"])})' if mine_data[str(ctx.author.id)]["assets"]["money"] > 999.99 else ''}

```
""")

            statistics("Idle Mine money earned", round(earning, 2))
            await achievement(
                ctx=ctx,
                count=count_to_sell,
                achievement_ids=[
                    "mine_gems_mined_1",
                    "mine_gems_mined_100",
                    "mine_gems_mined_500",
                    "mine_gems_mined_2k",
                    "mine_gems_mined_5k",
                    "mine_gems_mined_20k",
                    "mine_gems_mined_100k",
                    "mine_gems_mined_500k",
                    "mine_gems_mined_1m",
                    "mine_gems_mined_10m",
                    "mine_gems_mined_100m",
                    "mine_gems_mined_1b",
                    "mine_gems_mined_1t",
                    "mine_gems_mined_1qa"
                ]
            )
            await achievement(
                ctx=ctx,
                count=earning,
                achievement_ids=[
                    "mine_money_earned_20",
                    "mine_money_earned_100",
                    "mine_money_earned_500",
                    "mine_money_earned_2k",
                    "mine_money_earned_5k",
                    "mine_money_earned_20k",
                    "mine_money_earned_100k",
                    "mine_money_earned_500k",
                    "mine_money_earned_1m",
                    "mine_money_earned_10m",
                    "mine_money_earned_100m",
                    "mine_money_earned_1b",
                    "mine_money_earned_1t",
                    "mine_money_earned_1qa",
                    "mine_money_earned_1qi"
                ]
            )

            return
        
        elif arg.lower() == 'sellval':
            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)
                user_data = mine_data[str(ctx.author.id)]
            
            gems = int(user_data['assets']['gems'])
            money = user_data['assets']['money']
            ascension = user_data['multi']['ascension']

            if len(args) > 1:
                try:
                    count_to_sell = int(args[1])
                    if count_to_sell <= 0 or count_to_sell > gems:
                        raise(Exception)
                except:
                    await ctx.send(f"{ctx.author.name}, error processing `sellval` function with argument `{args[1]}` - must be a positive integer no higher than your current gems count.")
                    return
            else:
                count_to_sell = gems

            earning = round(
                ( count_to_sell * gems_value_multi ) * (1.0+(ascension/100.0)),
                2
            )

            total_money = earning+money

            await ctx.send(f"{ctx.author.name}, selling all your gems now would earn you `$ {earning:,.2f}{f' ({human_num(earning)})' if earning > 999.99 else ''}`.\nYour total funds would be `$ {total_money:,.2f}{f' ({human_num(total_money)})' if total_money > 999.99 else ''}`.")
            return
        
        elif arg.lower() == 'market':
            if gems_value_multi > 1.0:
                highlight = '+ '
            else:
                highlight = '- '
            await ctx.send(f"{'The market is good! Time to sell!' if highlight == '+ ' else 'The market is not great, better wait it out.'}\n```diff\n{highlight}💎1 = $ {gems_value_multi:,.2f}\n```")

            return
        
        elif arg.lower() == 'ascend':
            ascension_divider = 10000

            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)

            user_data = mine_data[str(ctx.author.id)]
            
            production = {}
            for crew, crew_info in user_data['crew'].items():
                production[crew] = (crew_info['count']*crew_values[crew]['production'])*crew_info['upgraded']
            total_production = sum(production.values())

            ascension_bonus = round(total_production/ascension_divider, 4)
            current_ascension_bonus = round(mine_data[str(ctx.author.id)]['multi']['ascension'], 4)

            if current_ascension_bonus >= ascension_bonus:
                await ctx.send(f"Your current Ascension Bonus (`{current_ascension_bonus:,}%`) is already greater than the Ascension Bonus you would receive if you ascended now (`{ascension_bonus:,}%`). Try ascending later!")
                return
            else:
                pass

            await ctx.send(f"You've received a letter from the President herself.\n\n*\"The country is in a dire state! I must ask you to relinquish all of your mining operation and funds to government officials. Don't worry, you will be well rewarded for your contributions to the glory of [REDACTED]!\"*\n\nThis action will reset ALL your progress, including any achievement in progress (not yet unlocked).\nYou will get a `{ascension_bonus:,}%` bonus gems sales value (based on your current production rate of `{total_production:,} 💎/min`). {f'This will overwrite your current Ascension Bonus of `{current_ascension_bonus:,}%`.' if current_ascension_bonus > 0.0 else ''}\nAre you sure you want to continue?\n\nSay `Confirm` to confirm.")

            def check(m):
                return m.author == ctx.author and m.content.lower() == "confirm"

            try:
                await bot.wait_for("message", check=check, timeout=15.0)
            except asyncio.TimeoutError:
                await ctx.send("Command timed out. Operation cancelled.")
                return
            
            mine_data[str(ctx.author.id)] = {
                'assets': {
                    'gems': 0,
                    'money': 10
                },
                'crew': {},
                'multi': {
                    'ascension': 0.0
                },
                'global stats': {
                    "gems mined": user_data['global stats']['gems mined'],
                    "money earned": user_data['global stats']['money earned'],
                    "units bought": user_data['global stats']['units bought']
                }
            }
            for key in crew_values:
                mine_data[str(ctx.author.id)]['crew'][key] = {
                    'count': 0,
                    'upgraded': 1.0
                }

            mine_data[str(ctx.author.id)]['multi']['ascension'] = ascension_bonus

            with open('mine.json', 'w') as f:
                json.dump(mine_data, f, indent=4)

            await ctx.send(f"""
No sooner have you signed the relevant paperworks and submitted them to your glorious government, that a new letter arrives.

*\"Your dedication to serve your country are noted, and appreciated.\"*
*\"Kindly find attached the deeds to new lands waiting to be mined, $10.00 in cash, and our friends at the stock exchange will ensure you receive a bonus of {ascension_bonus:,}% on all sales of gems moving forward.\"*

*Best regards,*

{mine_officials_signatures['president']}

You stand before the barren lands that have been bestowed upon you, clenching $10 in your fist. You can't help but ask yourself... *Was it worth it*?
But there is not time ponder. No time to lose. It's time to start over. To get to work. For the glory of capitalism. For the glory of [REDACTED].
            """)

            if int(ascension_bonus) > 0:
                await achievement(
                    ctx=ctx,
                    count=int(ascension_bonus),
                    wipe=True,
                    reset=True,
                    achievement_ids=[
                        "mine_ascension_1",
                        "mine_ascension_5",
                        "mine_ascension_10",
                        "mine_ascension_25",
                        "mine_ascension_50",
                        "mine_ascension_100",
                        "mine_ascension_500",
                        "mine_ascension_1k",
                        "mine_ascension_5k",
                        "mine_ascension_10k",
                        "mine_ascension_25k",
                        "mine_ascension_100k",
                        "mine_ascension_500k",
                        "mine_ascension_1m",
                        "mine_ascension_10m",
                        "mine_ascension_100m"
                    ]
                )
            
            await achievement(
                ctx=ctx,
                count=0,
                wipe=True,
                achievement_ids=[
                    "mine_gems_mined_1",
                    "mine_gems_mined_100",
                    "mine_gems_mined_500",
                    "mine_gems_mined_2k",
                    "mine_gems_mined_5k",
                    "mine_gems_mined_20k",
                    "mine_gems_mined_100k",
                    "mine_gems_mined_500k",
                    "mine_gems_mined_1m",
                    "mine_gems_mined_10m",
                    "mine_gems_mined_100m",
                    "mine_gems_mined_1b",
                    "mine_gems_mined_1t",
                    "mine_gems_mined_1qa"
                ]
            )
            await achievement(
                ctx=ctx,
                count=0,
                wipe=True,
                achievement_ids=[
                    "mine_money_earned_20",
                    "mine_money_earned_100",
                    "mine_money_earned_500",
                    "mine_money_earned_2k",
                    "mine_money_earned_5k",
                    "mine_money_earned_20k",
                    "mine_money_earned_100k",
                    "mine_money_earned_500k",
                    "mine_money_earned_1m",
                    "mine_money_earned_10m",
                    "mine_money_earned_100m",
                    "mine_money_earned_1b",
                    "mine_money_earned_1t",
                    "mine_money_earned_1qa",
                    "mine_money_earned_1qi"
                ]
            )
            await achievement(
                ctx=ctx,
                count=0,
                wipe=True,
                achievement_ids=[
                    "mine_crew_hired_1",
                    "mine_crew_hired_5",
                    "mine_crew_hired_10",
                    "mine_crew_hired_25",
                    "mine_crew_hired_50",
                    "mine_crew_hired_100",
                    "mine_crew_hired_250",
                    "mine_crew_hired_500",
                    "mine_crew_hired_1k",
                    "mine_crew_hired_2k",
                    "mine_crew_hired_5k"
                ]
            )

            return
        
        elif arg.lower() == 'stats':
            embed = discord.Embed(title=f"{ctx.author.name}'s Idle Mine Stats", description="Global Idle Miner stats since the beginning, ignoring ascension wipes.", color=bot_color)

            with open('mine.json', 'r') as outfile:
                mine_data = json.load(outfile)

            user_data = mine_data[str(ctx.author.id)]

            for stat, numbers in user_data['global stats'].items():
                embed.add_field(
                    name=stat.capitalize(),
                    value=human_num(numbers)
                )

            await ctx.send(embed=embed)
            return

        else:
            await ctx.send(f"Argument `{arg}` is not recognized.")
            return
    
    with open('mine.json', 'r') as outfile:
        mine_data = json.load(outfile)

    user_data = mine_data[str(ctx.author.id)]
    
    embed = discord.Embed(title=f"{ctx.author.name}'s Mine", color=bot_color)

    gems_earnings = {}

    for crew, crew_info in user_data['crew'].items():
        gems_earnings[crew] = (crew_info['count']*crew_values[crew]['production'])*crew_info['upgraded']

    gems_earnings_total = round( sum( gems_earnings.values() ) )
    gems_possession = user_data['assets']['gems']
    money_possession = user_data['assets']['money']

    embed.add_field(
            name="Gems 💎",
            value=f"{gems_possession:,}{f' ({human_num(gems_possession)})' if gems_possession > 999.99 else ''}\n+ {gems_earnings_total:,}/min{f' ({human_num(gems_earnings_total)})' if gems_earnings_total > 999.99 else ''}",
            inline=False
        )
    
    embed.add_field(
            name="Money 💵",
            value=f"$ {money_possession:,.2f}{f' ({human_num(money_possession)})' if money_possession > 999.99 else ''}",
            inline=False
        )
    
    ascension = round(user_data['multi']['ascension'], 4)

    embed.add_field(
        name="Ascension Bonus 📈",
        value=f"{ascension:,}%{f' ('+human_num(ascension)+')' if ascension > 999.99 else ''} money earned on gems sales"
    )
    
    embed.add_field(
            name="",
            value="",
            inline=False
        )
    
    for crew, crew_info in user_data['crew'].items():
        embed.add_field(
            name=f"{crew.title()} (+{human_num(crew_values[crew]['production'])} 💎/min{' x2 (upgraded)' if crew_info['upgraded'] == 2.0 else ''})",
            value=f"{crew_info['count']:,} (+{human_num(gems_earnings[crew])}/min)",
            inline=False
        )
    
    await ctx.send(embed=embed)

    with open('mine.json', 'w') as f:
        json.dump(mine_data, f, indent=4)

@bot.command()
async def mineguide(ctx):
    embed = discord.Embed(title="Idle Mine Guide", color=bot_color)
    embed.add_field(
        name="Introduction",
        value="Well hello there, pioneer of the gemstones mining industry! You've just received your documents authorizing mining activity on your plot of land, you have $10 in allocated funds, and your heart burns with a fire only a [REDACTED] citizen can have! Let's get down to business - our great nation has just gotten out of yet another conflict with the neighbours across the border, and the coffers are empty. The nation of [REDACTED] needs money, and under our feet are billions of dollars' worth of gems, waiting to be plucked out. So let's get to work, eh?",
        inline=False
    )
    embed.add_field(
        name="About",
        value="Idle Mine is a Discord idling game. Purchase `units` with money, mine `gems`, sell them, and use your newfound wealth to expand your crew and mine faster!\n\nIssue the `mine` command to view your mine. Arguments can be included after the command to interact (see below).",
        inline=False
    )
    embed.add_field(
        name="Market",
        value="The gems market can be profitable, but also treacherous! In an ever-volatile world, dealing in gemstones can be a fickle matter. Keep an eye on the `market` pricing, and potentially reconsider selling your gems during moments of high exchange rates to maximize profit. The market pricing of gems will occasionally change over the course of the day and the lovely people at our government-approved news outlet will give us a heads up when it happens, but the exact timing is a mystery. Stay on your toes, and move fast!",
        inline=False
    )

    await ctx.send(embed=embed)

    embed2 = discord.Embed(title="Idle Mine Guide - Commands", description=f"Command arguments for the `mine` command. Arguments are fed by including them after a space - Example: `{prefixes[0]}mine shop`", color=bot_color)
    embed2.add_field(
        name="shop",
        value="View the available units and their prices.",
        inline=False
    )
    embed2.add_field(
        name="buy `unit` `count`",
        value="Exchange money for the specified `unit` (see `shop` for details). Optional argument `count` to purchase in bulk must be an integer representing the number of units to purchase, or `max` to purchase the maximum number of units.",
        inline=False
    )
    embed2.add_field(
        name="upgrade `unit`",
        value="Exchange money for the specified `unit` to upgrade. Upgrades cost 100x the base cost of the unit, and doubles this unit's production. Issuing the `upgrade` command without supplying a unit argument will display the available upgrades and upgrade costs.",
        inline=False
    )
    embed2.add_field(
        name="sell `amount`",
        value="Sell your gems for money at current market price (see `market` for market price before selling). Takes an optional `amount` argument, else sells all supplies of gems.",
        inline=False
    )
    embed2.add_field(
        name="sellval `amount`",
        value="Displays the money that would be earned by selling your gems at the current market price, without actually selling the gems. Takes an optional `amount` argument, else calculates all supplies of gems.",
        inline=False
    )
    embed2.add_field(
        name="market",
        value="Displays the current `gem -> money` exchange rate.",
        inline=False
    )
    embed2.add_field(
        name="ascend",
        value="Wipes all progress to gain an Ascension Bonus which multiplies the money earned when selling gems. Displays information and prompts for a confirmation before proceeding.",
        inline=False
    )
    embed2.add_field(
        name="stats",
        value="Displays your global stats since starting, ignoring ascension wipes.",
        inline=False
    )

    await ctx.send(embed=embed2)

class MineEvent():
    def __init__(self, message: str, desc: str, event_type: Literal['money', 'gems', 'units'], event_value_change: int, event_unit_type: str = "", event_requirement: Optional[Tuple[str, int, bool]] = None, requirement_has_unit: Optional[Tuple[str, int]] = None):
        
        global crew_values

        self.message = message
        self.desc = desc
        self.event_type = event_type
        self.event_value_change = event_value_change
        self.event_unit_type = event_unit_type
        self.event_requirement = event_requirement # Must be tuple (req_type=['money', 'gems', 'units', 'gems/min'], count=1, more_than=None)
        self.requirement_has_unit = requirement_has_unit # Must be tuple (unit='miner', count=1)

    def process(self):
        with open('mine.json', 'r') as outfile:
            mine_data = json.load(outfile)
        
        # If the event has requirements, split the data from the tuple
        if self.event_requirement:
            req_type = self.event_requirement[0] # str
            count = self.event_requirement[1] # int
            more_than = self.event_requirement[2] # bool
        
        # Initiate list for return data
        affected_players = []
        
        for user, info in mine_data.items():

            assets = info['assets']
            units = info['crew']

            # Gems per minute function
            def gems_per_min_calc():
                earnings = []
                for crew, crew_info in info['crew'].items():
                    earnings.append(crew_info['count']*crew_values[crew]['production'])
            
                earnings = round( sum(earnings) )

                return earnings

            # Check for more_than requirements
            def req_check_if_more_than():

                if req_type == 'gems/min':
                    return gems_per_min > count
                elif req_type in ['money', 'gems']:
                    return assets[req_type] > count
                else:
                    return units[self.event_unit_type] > count
            
            # Check for less_than requirements
            def req_check_if_less_than():

                if req_type == 'gems/min':
                    return gems_per_min < count
                elif req_type in ['money', 'gems']:
                    return assets[req_type] < count
                else:
                    return units[self.event_unit_type] < count
            
            # Calculate player's gems per minute
            gems_per_min = gems_per_min_calc()
            
            # If the event has requirements, check them.
            # Continue loop without processing event effects if the user doesn't fulfill requirements.
            if self.event_requirement:
                if more_than:
                    if not req_check_if_more_than():
                        continue
                elif not more_than:
                    if not req_check_if_less_than():
                        continue
                else:
                    pass
            
            # Check for units possession if required
            if self.requirement_has_unit:
                unit_type = self.requirement_has_unit[0]
                unit_count = self.requirement_has_unit[1]
                if not units[unit_type] >= unit_count:
                    continue
            
            # Process event to add/remove money, gems, or units
            if self.event_type == 'money':
                mine_data[user]['assets']['money'] += round(self.event_value_change, 2)
            
            elif self.event_type == 'gems':
                mine_data[user]['assets']['gems'] += self.event_value_change
            
            elif self.event_type == 'units':
                mine_data[user]['crew'][self.event_unit_type]['count'] += self.event_value_change

            # Add this player to the list of players affected by the event
            affected_players.append(user)
        
        # Save data to file
        with open('mine.json', 'w') as f:
            json.dump(mine_data, f, indent=4)
        
        return affected_players

mine_live_message_id = None
mine_officials_signatures = {
    'commodities': "*Flint Rocksteady*\n*Commissioner of Commodity Trade*",
    'taxes': "*Damond McJewel*\n*National Revenue Agency (NRA)*",
    'president': "*Madam President Ruby Gemina*\n*Glorious President of [REDACTED]*",
    'legal': "*Agathe Stones*\n*[REDACTED] Attorney General*",
    'international': "*Agathe Stones*\n*International Affairs*",
    'pr': "*Rocky McPebblestone*\n*Public Relations Officer*",
    'military': "*Jade Gravels*\n*Commander General of [REDACTED] Military Operations*"
}

mine_event1 = MineEvent(
    message=f"I have the great pleasure to notify you that a our Immigration Agency has organized a government-funded hiring campaign.\nFive miners have been added to the workforce of employers having at least 1 miner with experience on their team, all paid for by the Government of [REDACTED].\nHave a good day, and all glory to [REDACTED]!\n\n{mine_officials_signatures['international']}",
    desc="+ 5 miner units have been added to all mining operations which already possess at least 1 miner.",
    event_type='units',
    event_unit_type='miner',
    event_value_change=5,
    requirement_has_unit=('miner', 1)
)
mine_event2 = MineEvent(
    message=f"A grant of `$ 10,000.00` has been approved for all mining operations producing less than 25k gems per minute.\nThe funds have been deposited directly into the accounts of eligible parties.\n\n{mine_officials_signatures['commodities']}",
    desc="+ $ 10,000.00 immediately granted to all mining operations with a gems/min rate under 25k.",
    event_type='money',
    event_value_change=10000,
    event_requirement=('gems/min', 25000, False)
)
mine_event3 = MineEvent(
    message=f"As part of the \"Tax The Rich\" program, all mining operation generating over 300k gems/min are taxed $1M, effective immediately.\nThe funds have been debited from the account of all eligible mining operations.\n\n{mine_officials_signatures['taxes']}",
    desc="- $ 1M immediately debited from all mining operations generating over 300k gems/min.",
    event_type='money',
    event_value_change=-1000000,
    event_requirement=('gems/min', 300000, True)
)
mine_event4 = MineEvent(
    message=f"In an unexpected turn of events, the class action lawsuit against the government of [REDACTED] for commandeering mining operations with unsatisfactory compensation has concluded in favour of the mining industry.\nThe compensation of $2.5M has been provided to each mining operation currently generating at least 300k gems/min.\n\n{mine_officials_signatures['legal']}",
    desc="+ $ 2.5M immediately granted to all mining operations with a gems/min rate over 300k.",
    event_type='money',
    event_value_change=2500000,
    event_requirement=('gems/min', 300000, True)
)
mine_event5 = MineEvent(
    message=f"As the battle for the freedom of our nation at the borders of our lands intensifies, we regret to inform you that a mandatory draft is in effect.\nWhile you, as an essential asset to the service of [REDACTED], are safe from drafting, the same cannot be said of your mining crew.\nAll mining operations with more than 10 miners have had 3 miners recruited to serve their nation on the battlefield.\nALL GLORY TO [REDACTED].\n\n{mine_officials_signatures['military']}",
    desc="- 3 miner units removed from all mining operations possessing more than 10 miner units.",
    event_type='units',
    event_unit_type='miner',
    event_value_change=-3,
    event_requirement=('units', 10, True)
)
mine_event6 = MineEvent(
    message=f"As you all know, the recent flooding has caused significant damage to all mines. Through the assistance of our nation's brave military personnel, your mines were successfully drained.\nMadam President Ruby Gemina has instructed me to bill you $500k to refund the resources that were exhausted in assisting your mining operation. The funds have been debited from the account of each eligible mining operation.\n\n{mine_officials_signatures['military']}",
    desc="- $500k charged to all mining operations owning at least one mine unit.",
    event_type='money',
    event_value_change=-500000,
    requirement_has_unit=('mine', 1)
)
mine_event7 = MineEvent(
    message=f"A large shipment of smuggled gems have been seized at the border. Normally, smuggled goods are immediately destroyed - however, we have decided it would serve a better purpose if redistributed into the economy through active mining operations.\nMining operations with a minimum production rate of 50k gems/min have each received 500k gems.\n\n{mine_officials_signatures['commodities']}",
    desc="+ 500k gems was sent to all mining operations generating at least 50k gems/min.",
    event_type='gems',
    event_value_change=500000,
    event_requirement=('gems/min', 50000, True)
)
mine_event8 = MineEvent(
    message=f"I have stumbled across a significant number of gems...\nGems that I must get rid off. Quickly. And quietly.\n10k gems are being distributed to smaller, startup mining entreprises. Do what you may with them, but if anyone asks, you've mined those yourself, and this conversation never happened.\n\nP.S. Delete this correspondance ASAP.\n\n{mine_officials_signatures['commodities']}",
    desc="+ 10k gems have been sent to all mining operations generating less than 2k gems/min.",
    event_type='gems',
    event_value_change=500000,
    event_requirement=('gems/min', 2000, False)
)

mine_events = [
    mine_event1,
    mine_event2,
    mine_event3,
    mine_event4,
    mine_event5,
    mine_event6,
    mine_event7,
    mine_event8
]

@tasks.loop(seconds=60)
async def mine_process():

    global prevent_mine_command
    prevent_mine_command = True

    global gems_value_multi
    global mine_live_message_id
    global mine_events

    with open('permanent_variables.json', 'r') as outfile:
        persistent_data = json.load(outfile)

    # MARKET EVENTS

    if random.random() < 0.011: # (24 * 60) * 0.011 = 15.84 average triggers per 24h at 1m intervals
        gems_value_multi_to_apply = random.randint(-25, 25)/100.0
        if gems_value_multi_to_apply == 1.0:
            gems_value_multi_to_apply = 0.99
        gems_value_multi = round(1.0+gems_value_multi_to_apply, 2)

        persistent_data['gems_multi'] = gems_value_multi

        with open('permanent_variables.json', 'w') as f:
            json.dump(persistent_data, f, indent=4)

        if gems_value_multi > 1.0:
            highlight = '+ '
            random_messages = [
                "There is a sudden change in the gems market during a boom in engagements causing wedding rings demands.",
                "A mine in a faraway country has flooded and been shutdown, resulting in increased value.",
                "A royalty in a foreign country has had an interview showing off their gems collection, increasing their popularity.",
                "A small country to the East has crowned a new King, the dazzling crown popularizing gemstones.",
                "Breaking news in the fashion industry - Gemstones are the hot new thing!",
                "The government has decreased taxes on commodities. Gems are hot buys on the market.",
                "Across the border, the royal family has commissioned a ridiculous artwork made purely of gems, causing a shortage.",
                "Our majestic country's government is introducing new exhibits to the Museum of Fine Gems, and is buying them by the buckets.",
                "A rival mine has suffered a tragic collapse. They have shut down operations, decreasing supplies.",
                "TV star Alexan Dryte is promoting his personal line of exclusive jewelry, increasing sales and demand for raw gems.",
                "Renowned gemologist discovers a rare and previously unknown gemstone species, creating a frenzy in the collector's market.",
                "A scam convincing citizens that certain gems possess unique healing properties leads to an increased demand.",
                "A famous movie director announces an upcoming blockbuster featuring a plot centered around precious gemstones, sparking a surge in interest.",
                "Archaeologists unearth a hidden ancient civilization adorned with exquisite gemstone artifacts, driving collectors to seek similar pieces.",
                "Environmental concerns lead to a shift in consumer preferences towards sustainable and ethically sourced gems, boosting the value of responsibly mined stones.",
                "Global climate change affects gemstone formations, making certain varieties even rarer and more valuable.",
                "A breakthrough in technology allows for the creation of hyper-realistic gemstone replicas, increasing appreciation for authentic gems.",
                "A fashion icon declares gem-embedded accessories as a must-have trend, driving demand for unique and high-quality gemstones.",
                "An influencer starts a viral challenge to showcase their favorite gemstones, creating a social buzz and increasing gemstone desirability.",
                "The government has commandeered mining equipment from a rival mining company to stage a rescue after the collapse of a [REDACTED] in [REDACTED], reducing their production rate and increasing gems value.",
            ]
        else:
            highlight = '- '
            random_messages = [
                "A mine in a faraway land has discovered an enormous gems vein. The increase in supply has resulted in reduced demands.",
                "The government is increasing taxes on commodities, resulting in a decrease on the trading of gemstones.",
                "A neighboring country has imposed sanctions on the exchange of gemstones following a dispute with our country.",
                "Stormy season is causing disruptions in shipping of commodities. Traders are halting all trading until further notice.",
                "A typographical error at the stock exchange caused a panic. Traders are liquidating their stocks in gems.",
                "Breaking news in the fashion industry - Gemstones are SO uncool. The chic crowd is ditching them.",
                "Hugely popular TV talk show host Jemma Safire just had a segment encouraging women to stay single. Engagement rings refunds are on the rise.",
                "A breakthrough in lab-grown gem technology floods the market with affordable alternatives, decreasing demand for natural gemstones.",
                "Rumors spread about the environmental impact of gemstone mining, leading to a decline in consumer interest and demand.",
                "An economic recession forces consumers to cut back on luxury purchases, including gemstones, reducing overall market demand.",
                "A renowned jewelry critic publicly criticizes the quality of recently mined gemstones, causing a loss of confidence among buyers.",
                "Fashion influencers start promoting minimalistic styles, shifting away from elaborate gemstone accessories and reducing their popularity.",
                "A major gemstone-producing country introduces regulations to limit exports, flooding the domestic market and reducing international demand.",
                "Reports surface about unethical labor practices in certain gemstone mines, leading to a consumer boycott and a decrease in sales.",
                "A new trend emerges in which consumers prefer alternative, non-traditional materials for jewelry, causing a decrease in gemstone sales.",
                "A documentary highlighting the ecological impact of gemstone extraction gains widespread attention, discouraging purchases of mined gemstones.",
                "A fictional storyline in a popular television series depicts gemstones as cursed objects, leading viewers to feel reluctant in owning them."
            ]

        message = random.choice(random_messages)

        try:
            cha = bot.get_channel(miners_channel)
            await cha.send(f"<@&{role_miners}> GEMS MARKET UPDATE: {message}\n```diff\n{highlight}💎1 = $ {gems_value_multi:.2f}\n```")
        except Exception as e:
            print(f"mine_process() gem market update message failed: {e}")

    # END MARKET EVENTS
    # -----------------
        
    # RANDOM EVENTS
    if random.random() < 0.00035: # 0.00035: # (24 * 60) * 0.00035 = Once every two days average at 1m intervals

        try:
            cha = bot.get_channel(miners_channel)
            random_event = random.choice(mine_events)
            affected_players = random_event.process()
            if affected_players:
                players_tags = [user.name for user in affected_players]
            else:
                players_tags = ["Nobody"]
            random_greetings = [
                "Dear pioneers of the mining industry",
                "Greetings mine operators",
                "Hello pioneers of the mining industry",
                "Dear associates of the mining industry",
                "Good day to you mining operators",
                "Dear mining associates",
                "Hello miners of [REDACTED]",
                "Greetings hard-working entrepreneurs",
                "Good day loyal industry partners"
            ]
            greeting = random.choice(random_greetings)
            await cha.send(f"<@&{role_miners}> **GOVERNMENT ALERT:**\n{greeting},\n\n{random_event.message}\n```diff\n{random_event.desc}\n```\n**APPLIES TO:** {', '.join([tag for tag in players_tags])}")
        except Exception as e:
            print(f"mine_process() random event failed: {e}")
    
    # END RANDOM EVENTS
    # -----------------
        
    # MINE PROCESS

    with open('mine.json', 'r') as outfile:
        mine_data = json.load(outfile)

    if not mine_data:
        prevent_mine_command = False
        return

    # mine_live_message embed
    unix_timestamp = int(time.mktime((datetime.now()+timedelta(seconds=60)).timetuple()))
    embed = discord.Embed(title=f"Mine Live Feed", description=f"Next drop <t:{unix_timestamp}:R>", color=bot_color)

    try:
        for userID, data in mine_data.items():
            earnings = []
            for crew, crew_info in data['crew'].items():
                earnings.append((crew_info['count']*crew_values[crew]['production'])*crew_info['upgraded'])
        
            earnings = round( sum(earnings) )

            mine_data[str(userID)]['assets']['gems'] += earnings
            mine_data[str(userID)]['global stats']['gems mined'] += earnings
            
            user = bot.get_user(int(userID))
            if not user:
                user_name = f"{userID} (Lost Miner)"
            else:
                user_name = user.name
            embed.add_field(
                name=user_name,
                value=f"💎 {human_num(mine_data[str(userID)]['assets']['gems'])} (+{human_num(earnings)}/min)",
                inline=False
            )

            statistics("Idle Mine gems mined", earnings)
        
        cha = bot.get_channel(miners_channel)

        if not mine_live_message_id:
            msg = await cha.send(embed=embed)
            await msg.pin()
            mine_live_message_id = msg.id
        
        else:
            msg = await cha.fetch_message(int(mine_live_message_id))
            await msg.edit(embed=embed)
            persistent_data['mine_live_message_edit_count'] += 1
        
        if persistent_data['mine_live_message_edit_count'] > 60:
            old_msg = await cha.fetch_message(int(mine_live_message_id))
            await old_msg.unpin()
            await old_msg.delete()
            persistent_data['mine_live_message_edit_count'] = 0
            mine_live_message_id = None

            msg = await cha.send(embed=embed)
            await msg.pin()
            mine_live_message_id = msg.id
        
        with open('permanent_variables.json', 'w') as f:
            json.dump(persistent_data, f, indent=4)

    except Exception as e:
        print(f"mine_process() function failed: {e}")

    with open('mine.json', 'w') as f:
        json.dump(mine_data, f, indent=4)
    
    prevent_mine_command = False

    ##### WIP #####

# civ_name_gen_kws_consonants = ['b', 'd', 'g', 'h', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'z']
# civ_name_gen_kws_vowels = ['a', 'e', 'i', 'o', 'u', 'oo', 'ee']

# civ_banned_names = ['poo', 'poop', 'rape', 'nazi', 'puke', 'hole', 'pube', 'doodoo', 'pee', 'peepee', 'pee-pee', 'poo-poo', 'doo-doo', 'lube']

# def civ_name_generator():
#     while True:
#         syllables_count = random.randint(2, 3)
#         syllables_count += random.choice([0, 0, 1])
#         syllables = []
#         hyphen_used = False
#         name = ''
#         for c in range(syllables_count):
#             syllable = ''.join([
#                 random.choice(civ_name_gen_kws_consonants),
#                 random.choice(civ_name_gen_kws_vowels)
#             ])
#             if not hyphen_used:
#                 if c > 1 and c+1 <= syllables_count:
#                     hyphen_chance = random.random()
#                     hyphen_probability = 0.2*syllables_count
#                     if hyphen_chance < hyphen_probability:
#                         syllables.append('-')
#                         hyphen_used = True
#             syllables.append(syllable)
#         name = ''.join(syllables)
#         if any(name.endswith(f'-{banned_name}') for banned_name in civ_banned_names) or any(name.startswith(f'{banned_name}-') for banned_name in civ_banned_names) or any(name == banned_name for banned_name in civ_banned_names):
#             print(f"{name} is a banned name. Trying again...")
#             continue
#         else:
#             break
#     return name.capitalize()

# @bot.command()
# async def civ(ctx, *args):

#     user_id = ctx.author.id

#     # Initiate user in file
#     with open('civ.json', 'r') as outfile:
#         civ_file = json.load(outfile)

#     if args:
#         arg = args[0].lower()

#         if arg == 'register':

#             if str(user_id) in civ_file:

#                 await ctx.send(f"{ctx.author.name}, you are already registered under the family name `{civ_file[str(user_id)]['info']['family name']}`!")
#                 return
            
#             try:
#                 family_name_registration = args[1]
#             except:
#                 await ctx.send(f"Expected `Familyname` argument is missing. Command is `{prefixes[0]}civ register Familyname`, where Familyname is the last name of your Civ family.\n\n**Naming rules:**\n- Must contain only alphabetical characters\n- No spaces or other special characters\n- Maximum length of 14 characters")
#                 return
            
#             if not family_name_registration.isalpha():
#                 await ctx.send(f"Familyname `{family_name_registration}` is not acceptable - only alphabetic characters are allowed.")
#                 return
            
#             if len(family_name_registration) > 14:
#                 await ctx.send(f"Familyname `{family_name_registration}` is not acceptable - 14 characters limit.")
#                 return
            
#             await ctx.send(f"Your Civ family name will be `{family_name_registration.capitalize()}`. Are you sure?\n**Make sure to choose something you like - this cannot be changed once decided!**\n\nSay `confirm` to confirm.")

#             def check(m):
#                 return m.author == ctx.author and m.content.lower() == "confirm"

#             try:
#                 await bot.wait_for("message", check=check, timeout=10.0)
#             except asyncio.TimeoutError:
#                 await ctx.send("Command timed out. Operation cancelled.")
#                 return

#             civ_file[str(ctx.author.id)] = {
#                 'info': {
#                     'family name': family_name_registration.capitalize()
#                     },
#                 'civ': {

#                     }
#                 }

#             with open('civ.json', 'w') as f:
#                 json.dump(civ_file, f, indent=4)
            
#             await ctx.send(f"Your Civ family has been registered as `{family_name_registration.capitalize()}`! You may now spawn your Civ with `{prefixes[0]}civ spawn`.")
        
#         if str(ctx.author.id) not in civ_file:
#             await ctx.send(f"Please register your Civ family using the command `{prefixes[0]}civ register Familyname`, where Familyname is the last name of your Civ family.\nMake sure to choose something you like - this cannot be changed once decided!")
#             return
        
#         if arg == 'spawn':

#             if civ_file[str(ctx.author.id)]['civ'].get('name'):
#                 await ctx.send("You currently already have a Civ.")
#                 return
            
#             civ_generated_name = civ_name_generator()
#             civ_file[str(ctx.author.id)]['civ']['name'] = civ_generated_name
#             civ_file[str(ctx.author.id)]['civ']['birthday'] = datetime.now().strftime("%m/%d/%Y")
#             civ_file[str(ctx.author.id)]['civ']['skills'] = None
#             civ_file[str(ctx.author.id)]['civ']['job'] = None
#             civ_file[str(ctx.author.id)]['civ']['status'] = "Idle"

#             with open('civ.json', 'w') as f:
#                 json.dump(civ_file, f, indent=4)
            
#             await ctx.send(f"Your Civ has spawned! The Gods have granted them the name `{civ_generated_name}`. May `{civ_generated_name} {civ_file[str(ctx.author.id)]['info']['family name']}` live a long and fulfilling life!")
        
#     else:

#         if str(ctx.author.id) not in civ_file:
#             await ctx.send(f"Please register your Civ family using the command `{prefixes[0]}civ register Familyname`, where Familyname is the last name of your Civ family.\nMake sure to choose something you like - this cannot be changed once decided!")
#             return

#         embed = discord.Embed(title=f"{ctx.author.name} Civ ({civ_file[str(user_id)]['info']['family name']})", color=bot_color)

#         if civ_file[str(user_id)]['civ'].get('name'):
#             embed.add_field(
#                 name="Name",
#                 value=f"{civ_file[str(user_id)]['civ']['name']} {civ_file[str(user_id)]['info']['family name']}",
#                 inline=False
#             )

#             birthday = datetime.strptime(civ_file[str(user_id)]['civ']['birthday'], '%m/%d/%Y')
#             age = datetime.now()-birthday
#             embed.add_field(
#                 name="Spawnday (age)",
#                 value=f"{civ_file[str(user_id)]['civ']['birthday']} ({age.days} moon cycles)",
#                 inline=False
#             )
            
#             if civ_file[str(user_id)]['civ']['skills']:
#                 skills = [(f"{skill} ({info['lvl']})") for skill, info in civ_file[str(user_id)]['civ']['skills'].items()]
#             else:
#                 skills = ["None"]
#             embed.add_field(
#                 name="Skills",
#                 value=', '.join(skills),
#                 inline=False
#             )

#             embed.add_field(
#                 name="Job",
#                 value=civ_file[str(user_id)]['civ']['job'],
#                 inline=False
#             )

#             embed.add_field(
#                 name="Status",
#                 value=civ_file[str(user_id)]['civ']['status'],
#                 inline=False
#             )
        
#         else:
#             embed.add_field(
#                 name=f"You currently do not have a Civ.",
#                 value=f"You may spawn a Civ with `{prefixes[0]}civ spawn`",
#                 inline=False
#             )

#         await ctx.send(embed=embed)

@bot.command(aliases=[ 'bm' ])
async def bookmark(ctx):

    if not ctx.guild:
        await ctx.send("The `bookmark` commands cannot be executed from Direct Messages.")
        return

    if not ctx.message.reference:
        ctx.send("No reference message was received. Did you forgot to reply to the message you wish to bookmark?")
        return
    
    try:
        replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except discord.NotFound:
        ctx.send("The specified message was not found.")
    except discord.Forbidden:
        ctx.send("You do not have the permissions required to fetch the message.")
    except discord.HTTPException as e:
        ctx.send(f"Retrieving the message failed: {e}")

    if replied.embeds:
        fields = [f"{field.name}\n{field.value}\n\n" for field in replied.embeds[0].fields]
        content = f"**{replied.embeds[0].title}**\n*{replied.embeds[0].description}*\n\n{''.join(fields)}"
        title = f"{replied.embeds[0].title[:40]}{'...' if len(replied.embeds[0].title) > 40 else ''}{' (Embed)' if replied.embeds else ''}"
    else:
        content = replied.content
        title = f"{replied.content[:40]}{'...' if len(replied.content) > 40 else ''}"

    link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{replied.id}"

    embed = discord.Embed(
        title=f"Bookmark - {title}",
        description=f"#{replied.channel.name}",
        url=link
    )

    embed.add_field(
        name="Author",
        value=replied.author.name,
        inline=False
    )

    embed.add_field(
        name=f"Message{' (Embed)' if replied.embeds else ''}",
        value=f"----------\n{content[:1000]}{'...' if len(content) > 1000 else ''}",
        inline=False
    )

    await ctx.author.send(embed=embed)
    await ctx.send(f"{ctx.author.name} I've sent you a bookmark DM for the following message!\n`{title}`\n{link}")

    statistics("Bookmarks saved")

prevent_gtf_command = False

def get_gtf_flags():

    items = None

    while items is None:

        try:
            url = 'https://www.worldometers.info/geography/flags-of-the-world/'
            r = requests.get(url)
            page = bs(r.content, "html.parser")
            items = page.find_all("div", {"class": "border-2 p-6 flex flex-col items-center gap-2.5 max-w-[300px]"})

        except Exception as e:
            print(f"get_gtf_flags() function failed: {e}")
    
    return items

@bot.command()
async def gtf(ctx, arg=None):

    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Guess The Flag rounds may not be started in DMs!")
        return
    
    global prevent_gtf_command
    global cached_flag_items

    if arg:
        if arg.lower() == 'cache':
            await ctx.send("Fetching and caching flags...")
            try:
                cached_flag_items = get_gtf_flags()
                if not cached_flag_items:
                    raise Exception("Caching flags failed - cache returned empty.")
                await ctx.send("Done!")
                return
            except Exception as e:
                await ctx.send(f"Task failed: {e}")
                return

    if prevent_gtf_command:
        await ctx.send(f"<@{ctx.author.id}> a Guess The Flag round is already ongoing!")
        return

    prevent_gtf_command = True

    gtf_start_timer = 20

    try:
        item = random.choice(cached_flag_items)
    except Exception as e:
        raise Exception(f"Fetching a flag failed - {e}. Try issuing the command with the 'cache' argument to force caching.")

    country_list = [item.text.strip()]

    if country_list[0] == 'St. Vincent Grenadines':
        country_list = [
            'St. Vincent Grenadines',
            'St. Vincent and Grenadines',
            'St. Vincent and the Grenadines',
            'St Vincent Grenadines',
            'St Vincent and Grenadines',
            'St Vincent and the Grenadines',
            'Saint Vincent Grenadines',
            'Saint Vincent and Grenadines',
            'Saint Vincent and the Grenadines'
        ]

    if country_list[0] == 'Saint Lucia':
        country_list = [
            'Saint Lucia',
            'St Lucia',
            'St. Lucia'
        ]

    if country_list[0] == 'U.S.':
        country_list = [
            'U.S.',
            'US',
            'USA',
            'U.S.A',
            'U.S.A.',
            'United States',
            'United States of America'
        ]
    
    if country_list[0] == 'DRC':
        country_list = [
            'DRC',
            'Democratic Republic of the Congo'
        ]
    
    if country_list[0] == 'U.K.':
        country_list = [
            'U.K.',
            'UK',
            'United Kingdom'
        ]

    image = item.find("a").get("href")
    image_url = "https://www.worldometers.info"+image

    unix_timestamp = int(time.mktime((datetime.now()+timedelta(seconds=gtf_start_timer)).timetuple()))
    embed = discord.Embed(title="Guess The Flag!", description=f"Guessing times out <t:{unix_timestamp}:R>!")
    embed.set_image(url=image_url)

    embed_message = await ctx.send(embed=embed)

    def check(m):
        return m.author != bot.user and m.channel == ctx.channel

    time_started = datetime.now()
    gtf_timer = gtf_start_timer
    message = None

    while True:

        try:
            message = await bot.wait_for('message', check=check, timeout=gtf_timer)
            if message.content.lower() in [country.lower() for country in country_list]:
                break
            else:
                message = None

            now = datetime.now()

            time_elapsed = now-time_started
            time_elapsed = timedelta(seconds=time_elapsed.seconds)

            timer_deltatime = timedelta(seconds=gtf_start_timer) # 20

            gtf_timer = timer_deltatime-time_elapsed
            gtf_timer = gtf_timer.seconds

        except asyncio.TimeoutError:
            break

        continue

    if len(country_list) > 1:
        other_options = ', '.join(country_list[1:])
        other_options_listed = ' (Optionally: `'+other_options+'`)'

    else:
        other_options_listed = ''
    
    if message:
        await ctx.send(f"{message.author.name} is correct! This is a flag of `{country_list[0]}`{other_options_listed}!")
        statistics("Guess The Flag correct guesses")
    else:
        await ctx.send(f"No guesses? Too bad! This was the flag of... `{country_list[0]}{other_options_listed}`!")

    new_embed = discord.Embed(title="Guess The Flag!", description=f"Round ended! The answer was `{country_list[0]}{other_options_listed}`!")
    new_embed.set_image(url='https://i.imgur.com/tEsOtAl.png')

    await embed_message.edit(embed=new_embed)
    
    prevent_gtf_command = False

    statistics("Guess The Flag rounds played")

with open('reviews_voting_data.json', 'r') as outfile:
    reviews_data = json.load(outfile)

class ReviewsVotingButtonsView(discord.ui.View):
    def __init__(self, reviews, voter, text_or_design, reviews_voting_file, stage=1, previous_picks={}):
        super().__init__()
        self.reviews = reviews
        self.voter = voter
        self.text_or_design = text_or_design
        self.reviews_voting_file = reviews_voting_file
        self.stage = stage
        self.previous_picks = previous_picks
        self.add_buttons()

    def add_buttons(self):
        self.test_val = [pp_authors[self.text_or_design] for pp_authors in self.previous_picks.values()]
        self.illegal_reviews = {g: r for g, r in self.reviews.items() if r[self.text_or_design] in self.test_val or r[self.text_or_design] == self.voter}
        self.legal_reviews = {g: r for g, r in self.reviews.items() if r[self.text_or_design] not in self.test_val and r[self.text_or_design] != self.voter}

        # Clickable buttons
        for game, authors in self.legal_reviews.items():
            button = discord.ui.Button(label=game, custom_id=game.replace(" ", ""))
            button.callback = self.create_callback(game, authors)
            self.add_item(button)
        
        # Greyed out buttons
        for game, authors in self.illegal_reviews.items():
            button = discord.ui.Button(label=game, custom_id=game.replace(" ", ""), disabled=True)
            button.callback = self.create_callback(game, authors)
            self.add_item(button)

    def create_callback(self, game, authors):
        async def button_callback(interaction: discord.Interaction):
            self.clear_items()
            await interaction.response.edit_message(content=f"## Favourite Review{' Design' if self.text_or_design == 'design' else ''} #{self.stage}\nYou picked `{game}`!", view=self)
            await self.handle_next_choice(interaction, game, authors)
        return button_callback

    async def handle_next_choice(self, interaction, game, authors):

        global prevent_vote_command

        self.previous_picks[game] = authors

        # Assign points based on current stage (3 to 2 to 1)
        if self.stage == 1:
            points = 3
        elif self.stage == 2:
            points = 2
        else:
            points = 1

        self.reviews_voting_file['votes'][authors[self.text_or_design]][self.text_or_design] += points
        
        # If we've casted 3 votes, switch to designers voting stage. Otherwise, continue voting.
        if self.stage < 3:

            new_view = ReviewsVotingButtonsView(self.reviews, voter=self.voter, text_or_design=self.text_or_design, reviews_voting_file=self.reviews_voting_file, stage=self.stage + 1, previous_picks=self.previous_picks)
            await interaction.followup.send(f"## Favourite Review{' Design' if self.text_or_design == 'design' else ''} #{self.stage + 1}", view=new_view)
            
        else:

            summary = "\n".join([f"{i+1}. `{g}`" for i, (g, r) in enumerate(self.previous_picks.items())])
            await interaction.followup.send(f"Thank you for voting! Here are your picks for favourite reviews{' judged by design' if self.text_or_design == 'design' else ''}:\n{summary}")

            self.previous_picks.clear()
            
            # If all votes have been casted (handle finishing up voting phase)
            if self.text_or_design == 'design':

                self.reviews_voting_file['voters'].append(interaction.user.id)

                with open('reviews_voting.json', 'w') as outfile:
                    json.dump(self.reviews_voting_file, outfile, indent=4)

                await interaction.followup.send(f"Thank you for casting your votes, <@{interaction.user.id}>!")
                
                cha = bot.get_channel(magazine_voting_channel)
                await cha.send(f"{interaction.user.name} has finished voting!")

                prevent_vote_command = False

                return
            
            # Otherwise, continue to second phase (design voting)
            await interaction.followup.send(f"Now, vote for the reviews with the best designs in the magazine! Review based not on the review's writing this time, but on how much you enjoyed the page's style and design!")

            design_view = ReviewsVotingButtonsView(reviews_data, voter=self.voter, text_or_design='design', reviews_voting_file=self.reviews_voting_file)
            await interaction.followup.send("## Favourite Review Design #1", view=design_view)

prevent_vote_command = False

@bot.command()
async def vote(ctx, arg=None):

    global prevent_vote_command, reviews_data

    with open('permanent_variables.json', 'r') as outfile:
        permanent_variables = json.load(outfile)

    if arg:
        
        if arg.lower() in ['begin', 'end']:

            authorized_roles = [role_staff, role_assistants]

            if not [role.id for role in ctx.author.roles if role.id not in authorized_roles]:
                await ctx.send("You do not have the required role to initiate or terminate voting phase.")
                return
            
            with open('reviews_voting_data.json', 'r') as outfile:
                reviews_data = json.load(outfile)
            
            with open('reviews_voting.json', 'r') as outfile:
                reviews_voting_file = json.load(outfile)

            with open('reviews_voting_tally.json', 'r') as outfile:
                reviews_voting_tally = json.load(outfile)

            # Enable voting phase

            if arg.lower() == 'begin':
                
                if not reviews_data:
                    await ctx.send("Warning! `reviews_voting_data.json` returned an empty value. Please ensure the file has been populated with review data, and try again.")
                    return
                
                else:

                    reviews_voting_file.clear()

                    permanent_variables['voting_open'] = True
                    await ctx.send("Voting phase enabled!")

            # Disable voting phase
            
            else:
                permanent_variables['voting_open'] = False
                
                votes_all = reviews_voting_file['votes']

                reviews_data.clear()

                reviews_votes_result_text = ""
                designs_votes_result_text = ""

                for user, votes in votes_all.items():

                    if not reviews_voting_tally.get(user):
                        reviews_voting_tally[user] = votes
                    else:
                        reviews_voting_tally[user]['text'] += votes['text']
                        reviews_voting_tally[user]['design'] += votes['design']
                    
                sorted_bytext_tally = dict(sorted(reviews_voting_tally.items(), key=lambda x: x[1]["text"], reverse=True))
                sorted_bydesign_tally = dict(sorted(reviews_voting_tally.items(), key=lambda x: x[1]["design"], reverse=True))

                for user, votes in sorted_bytext_tally.items():
                    
                    text_tally = reviews_voting_tally[user]['text']
                    text_votes_increase = votes_all[user]['text'] if votes_all.get(user) else 0
                    reviews_formatted_text = f"- {user}: {text_tally-text_votes_increase} -> {text_tally} (+{text_votes_increase})\n"
                    reviews_votes_result_text += reviews_formatted_text

                for user, votes in sorted_bydesign_tally.items():

                    design_tally = reviews_voting_tally[user]['design']
                    design_votes_increase = votes_all[user]['design'] if votes_all.get(user) else 0
                    designs_formatted_text = f"- {user}: {design_tally-design_votes_increase} -> {design_tally} (+{design_votes_increase})\n"
                    designs_votes_result_text += designs_formatted_text

                
                await ctx.send(f"## Voting phase ended!\nHere are the results:\n\n## Ranking by Reviews\n{reviews_votes_result_text}\n## Ranking by Designs\n{designs_votes_result_text}")
                # await ctx.send(f"## Tally and rank:\n\n{votes_tallied_text}") # TODO
            
            with open('reviews_voting_data.json', 'w') as outfile:
                json.dump(reviews_data, outfile, indent=4)
            
            with open('reviews_voting_tally.json', 'w') as outfile:
                json.dump(reviews_voting_tally, outfile, indent=4)

            with open('permanent_variables.json', 'w') as outfile:
                json.dump(permanent_variables, outfile, indent=4)
            
            with open('reviews_voting.json', 'w') as outfile:
                json.dump(reviews_voting_file, outfile, indent=4)
            
            return
        
        else:
            await ctx.send(f"Unexpected argument! Expected `begin` or `end`, received `{arg}`.")
            return
        
    if not permanent_variables['voting_open']:
        await ctx.send("Voting phase is over! Please wait until voting phase is started by the voting administration.")
        return

    with open('reviews_voting.json', 'r') as outfile:
        reviews_voting_file = json.load(outfile)

    # Initiate votes file if empty
    if not reviews_voting_file:

        authors_list = set()

        for users in reviews_data.values():
            authors_list.add(users["text"])
            authors_list.add(users["design"])

        reviews_voting_file = {
            'voters': [],
            'votes': {}
        }

        for user in authors_list:
            reviews_voting_file['votes'][user] = {
                'text': 0,
                'design': 0
            }
        
        with open('reviews_voting.json', 'w') as outfile:
            json.dump(reviews_voting_file, outfile, indent=4)
    
    if ctx.author.id in reviews_voting_file['voters']:
        await ctx.send(f"Sorry {ctx.author.name}, you've already casted your votes for this issue!")
        return
    
    if prevent_vote_command:
        await ctx.send("Another user is currently casting their votes. Please try again later!")
        return
    
    prevent_vote_command = True

    cha = bot.get_channel(magazine_voting_channel)

    await cha.send(f"{ctx.author.name} are casting their vote...")
    
    # Initiate view and DM user
    view = ReviewsVotingButtonsView(reviews_data, voter=ctx.author.name, text_or_design='text', reviews_voting_file=reviews_voting_file)
    await ctx.author.send(f"Hello, dear reader, and welcome to the SGM voting ballot!\nPlease choose among the following options which was your favorite review in our last issue, based on **writing only**. Don't worry, you'll get to vote on the designs afterwards! You'll cast 3 votes each time, giving 3 points to your first choice, 2 to your second and 1 to your third choice.\n\n- You may only give points to a reviewer or designer once, therefore if there are multiple reviews or designs by the same individual, voting for them will grey out the rest of their work in that category.\n- Reviewers and designers, you cannot vote on your own review or design.\n- Therefore, these options will be greyed out as you progress through your choices.\n- Votes are final! Choose carefully.")
    await ctx.author.send("## Favourite Review #1", view=view)

@bot.command()
async def uploadvotes(ctx):

    authorized_roles = [role_staff, role_assistants]

    if not [role.id for role in ctx.author.roles if role.id not in authorized_roles]:
        await ctx.send("You do not have the required role to use this command.")
        return

    if not ctx.message.attachments:
        await ctx.send("No attachment found. Please attach a json format file.")
        return
    
    attachment = ctx.message.attachments[0]

    if not attachment.filename.endswith('.json'):
        await ctx.send("Attachment must be a json file.")
        return

    await ctx.send("File format correct, downloading...")
    await attachment.save('reviews_voting_uploaded.json')
    await ctx.send("Done!")

    with open('reviews_voting_tally.json', 'r') as outfile:
        reviews_voting_tally = json.load(outfile)
    with open('reviews_voting_uploaded.json', 'r') as outfile:
        reviews_voting_uploaded = json.load(outfile)

    reviews_votes_result_text = ""

    await ctx.send("Adding to tally...")

    try:
    
        for user, votes in reviews_voting_uploaded.items():

            if not reviews_voting_tally.get(user):
                reviews_voting_tally[user] = votes
            else:
                reviews_voting_tally[user]['text'] += votes['text']
                reviews_voting_tally[user]['design'] += votes['design']
        
            text_tally = reviews_voting_tally[user]['text']
            text_votes_increase = reviews_voting_uploaded[user]['text']

            design_tally = reviews_voting_tally[user]['design']
            design_votes_increase = reviews_voting_uploaded[user]['design']

            reviews_formatted_text = f"- {user}:\n  - Reviews: {text_tally-text_votes_increase} -> {text_tally} (+{text_votes_increase})\n  - Designs: {design_tally-design_votes_increase} -> {design_tally} (+{design_votes_increase})\n"
            reviews_votes_result_text += reviews_formatted_text

        with open('reviews_voting_tally.json', 'w') as outfile:
            json.dump(reviews_voting_tally, outfile, indent=4)
        
        await ctx.send(f"Done!\n\n{reviews_votes_result_text}")
    
    except Exception as e:
        await ctx.send(f"Something went wrong!\n\n{e}")

async def random_noun():
    url = 'https://www.desiquintans.com/noungenerator?count=1'
    r = requests.get(url)
    page = bs(r.content, "html.parser")
    random_noun = page.find('div', class_='greenBox').text
    topic = random_noun.replace('Your random noun is:', '')
    return topic

async def generate_typerace_paragraph():

    topic = await random_noun()
    print(f"TOPIC: {topic}")

    try:
        chat_completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=1.2,
            max_tokens=300,
            messages=[
                {"role": "system", "content": f"Generate a random paragraph of approximately 30 words, without quotes. The topic should relate to the word {topic}."}
            ]
        )

        p = chat_completion.choices[0].message.content

    except Exception as e: return(e)

    print(p)

    paragraph = textwrap.fill(p, width=50)

    image = Image.new("RGB", (850, 210), "black")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(chosen_font, 30)
    draw.text((10, 10), paragraph, font=font)
    image.save('typeracer_prompt.png')

    return p

prevent_tr_command = False

@bot.command(aliases=[ 'tr' ])
async def typerace(ctx, *args):
    
    if args:
    
        if args[0].lower() == 'leaderboard':
            
            try:

                lb_type = args[1]

                if lb_type.lower() not in ['net', 'gross', 'faultless']:
                    await ctx.send(f"Command expects second argument `net`, `gross`, or `faultless`, but received `{lb_type}`.")
                    return
            
            except:

                lb_type = 'net'

            with open('typerace.json', 'r') as outfile:
                typerace_records = json.load(outfile)
            
            if not typerace_records:
                await ctx.send("No scores recorded, yet!")
                return
            
            # Sort scores

            sorted_wpm = dict(sorted(typerace_records.items(), key=lambda item: item[1][lb_type], reverse=True))

            embed = discord.Embed(title=f"Typerace Leaderboard by {lb_type.capitalize()} WPM")

            for i, (user, records) in enumerate(sorted_wpm.items()):
                if not bot.get_user(int(user)):
                    continue
                embed.add_field(
                    name=f"{':first_place:' if i == 0 else (':second_place:' if i == 1 else (':third_place:' if i == 2 else str(i+1)))} {bot.get_user(int(user)).name}",
                    value=f'{lb_type.capitalize()} WPM: {records[lb_type]:.2f}',
                    inline=False
                )
            
            await ctx.send(embed=embed)

            return

        else:
            timer = args[0]
    
    else:
        timer = 120

    global prevent_tr_command

    if prevent_tr_command:
        await ctx.send(f"<@{ctx.author.id}> a round of Type Racer is already ongoing!")
        return

    try:
        typeracer_start_timer = int(timer)
        if not 30 <= typeracer_start_timer <= 240:
            raise Exception("`timer` argument must be an integer representing seconds, and must be no less than `30` and no more than `240`.")
    except Exception as e:
        await bot.on_command_error(ctx, commands.CommandInvokeError(e))
        return

    def check(m):
        return m.author != bot.user and m.channel == ctx.channel
    
    prevent_tr_command = True

    await ctx.send("Starting a Type Racer round...")

    paragraph = await generate_typerace_paragraph()
    tokenized_paragraph = paragraph.split(' ')
    file = discord.File('typeracer_prompt.png')
    unix_timestamp = int(time.mktime((datetime.now()+timedelta(seconds=5)).timetuple()))

    countdown = await ctx.send(f"Get ready to type... <t:{unix_timestamp}:R>")

    await asyncio.sleep(4)
    round_end_timer = int(time.mktime((datetime.now()+timedelta(seconds=typeracer_start_timer)).timetuple()))

    await countdown.edit(content=f"Start! Round ends <t:{round_end_timer}:R>.")
    await ctx.send(file=file)

    characters_count = len(paragraph)
    gross_entries = characters_count/5

    time_started = datetime.now()
    typeracer_timer = typeracer_start_timer
    now = datetime.now()

    while True:

        try:
            message = await bot.wait_for('message', check=check, timeout=typeracer_timer)

            # Check differences between the prompt and the message.

            tokenized_message = message.content.split(' ')
            d = difflib.Differ()
            diff = list(d.compare(tokenized_paragraph, tokenized_message))

            mistakes = [word for word in diff if word.startswith('- ') or word.startswith('+ ')]

            mistakes_m = len([word for word in mistakes if word.startswith('- ')])
            mistakes_p = len([word for word in mistakes if word.startswith('+ ')])

            mistakes_count = max(mistakes_m, mistakes_p)

            mistakes_listed_string = '\n'.join(mistakes)

            # Calculates and updates the timer after each message
            # so that the timer continue to count down.

            now = datetime.now()

            time_elapsed = now-time_started
            time_elapsed = timedelta(seconds=time_elapsed.seconds)

            timer_deltatime = timedelta(seconds=typeracer_start_timer)

            typeracer_timer = timer_deltatime-time_elapsed
            typeracer_timer = typeracer_timer.seconds

            # If there are more than 50% mistakes, ignore the message
            # as it is determined to be non-participating.

            if len(mistakes) > len(tokenized_paragraph)/2:
                continue
            
            # Calculate Gross WPM, and NET WPM.

            now = datetime.now()
            complete_time = now - time_started
            c_seconds = complete_time.total_seconds()
            c_minutes = c_seconds / 60.0

            gross_wpm = gross_entries/c_minutes
            error_rate = mistakes_count/c_minutes
            net_wpm = gross_wpm-error_rate

            # Prepare string snippet to point out mistakes, if any.
            
            faultless = False

            if mistakes:
                mistakes_text = f"You\'ve made the following mistakes:\n```diff\n{mistakes_listed_string}\n```"
            else:
                mistakes_text = ''
                faultless = True

            ### Save record ###

            new_net_wpm_record = False
            new_gross_wpm_record = False
            new_faultless_wpm_record = False

            with open('typerace.json', 'r') as outfile:
                typerace_records = json.load(outfile)

            user_id = message.author.id

            # Handle if the user is not within the leaderboard yet.

            if str(user_id) not in typerace_records.keys():
                typerace_records[str(user_id)] = {
                    'net': net_wpm,
                    'gross': gross_wpm,
                    'faultless': net_wpm if faultless else 0.0
                }
            
                new_net_wpm_record = True
                new_gross_wpm_record = True
                if faultless:
                    new_faultless_wpm_record = True

            # Handle updating leaderboard score.
            
            if typerace_records[str(user_id)]['net'] < net_wpm:
                typerace_records[str(user_id)]['net'] = net_wpm
                new_net_wpm_record = True
            if typerace_records[str(user_id)]['gross'] < gross_wpm:
                typerace_records[str(user_id)]['gross'] = gross_wpm
                new_gross_wpm_record = True
            if faultless and typerace_records[str(user_id)]['faultless'] < net_wpm:
                typerace_records[str(user_id)]['faultless'] = net_wpm
                new_faultless_wpm_record = True

            # Save to database.

            with open('typerace.json', 'w') as f:
                json.dump(typerace_records, f, indent=4)

            # Send the response, then delete the user's message.

            await ctx.send(f"""
<@{user_id}> has completed the challenge in `{complete_time.seconds}s:{complete_time.microseconds}ms`!
Your Gross WPM is `{gross_wpm:.2f}`{' (New personal best!)' if new_gross_wpm_record else ''}.
{'You have beat your personal best `Faultless` record!' if new_faultless_wpm_record else ''}
{f'Your Net WPM (with mistakes penalties) is `{net_wpm:.2f}`{" (New personal best!)" if new_net_wpm_record else ""}.' if mistakes else ''}
{mistakes_text}
""")

            await message.delete()

        # Timeout action breaks out of the loop if the time has run out.

        except asyncio.TimeoutError:
            break

        continue
    
    await ctx.send("Type Racer round is over!")
    await countdown.edit(content="Round over!")

    prevent_tr_command = False

trivia_score = {}
trivia_guesses = {}
class TriviaButtonsView(discord.ui.View):
    def __init__(self, choices, answer):
        super().__init__()
        self.choices = choices
        self.answer = answer
        self.add_buttons()
    
    def add_buttons(self):
        for choice in self.choices:
            button = discord.ui.Button(label=choice, custom_id=choice.replace(" ", ""))
            button.callback = self.create_callback(choice, self.answer)
            self.add_item(button)
    
    def create_callback(self, choice, answer):
        async def button_callback(interaction: discord.Interaction):
            user = interaction.user
            global trivia_score, trivia_guesses

            if not trivia_score.get(user.id):
                trivia_score[user.id] = 0

            if trivia_guesses.get(user.id):
                await interaction.response.send_message(f"<@{user.id}> You've already chosen an answer.", ephemeral=True, delete_after=3.0)
                return

            if choice.lower() == answer.lower():
                await interaction.response.send_message(f"<@{user.id}> Correct!", ephemeral=True)
                trivia_score[user.id] += 1
            else:
                await interaction.response.send_message(f"<@{user.id}> Wrong!", ephemeral=True)
            
            trivia_guesses[user.id] = choice

        return button_callback

trivia_rounds_setting = 10
trivia_round_number = 1

prevent_trivia_command = False

@bot.command()
async def trivia(ctx, rounds_count=None):

    global trivia_rounds_setting, trivia_round_number, trivia_score, trivia_guesses, prevent_trivia_command

    if rounds_count:

        if trivia_score or trivia_round_number > 1:
            await ctx.send(f"`rounds_count` cannot be changed while a trivia game is already ongoing.")
            return

        try:
            trivia_rounds_setting = int(rounds_count)
        except Exception as e:
            await ctx.send(f"Error: Received unrecognized value `{rounds_count}` for `rounds_count` command argument. Must be an integer from 1 to 20.")
            return

    if not 0 < trivia_rounds_setting <= 20:
        await ctx.send(f"Error: `rounds_count` must be an integer from 1 to 20.")
        return

    if prevent_trivia_command:
        await ctx.send(f"<@{ctx.author.id}> a trivia round is already ongoing!")
        return

    prevent_trivia_command = True

    trivia_start_timer = 20

    with open('trivia_questions_answers.json', 'r', encoding="utf8") as file:
        trivia_dict = json.load(file)

    trivia_questions = trivia_dict['questions']
    trivia_answers = trivia_dict['answers']

    trivia_question_number = str(random.randint(1, 151))

    random_trivia = trivia_questions[trivia_question_number]
    random_trivia_question = random_trivia['question']
    random_trivia_choices = random_trivia['choices']
    random.shuffle(random_trivia_choices)
    random_trivia_answer = trivia_answers[trivia_question_number]

    view = TriviaButtonsView(choices=random_trivia_choices, answer=random_trivia_answer)

    unix_timestamp = int(time.mktime((datetime.now()+timedelta(seconds=trivia_start_timer)).timetuple()))

    embed = discord.Embed(title=f"Trivia Game Round {trivia_round_number}/{trivia_rounds_setting}", description=f"Guessing ends: <t:{unix_timestamp}:R>\n{random_trivia_question}")

    embed.add_field(
        name='',
        inline=False,
        value=f"""
a. {random_trivia_choices[0]}
b. {random_trivia_choices[1]}
c. {random_trivia_choices[2]}
d. {random_trivia_choices[3]}
"""
    )

    msg = await ctx.send(embed=embed, view=view)

    await asyncio.sleep(trivia_start_timer)

    embed = discord.Embed(title=f"Trivia Game Round {trivia_round_number}/{trivia_rounds_setting}", description=f"Round is over!\n{random_trivia_question}")

    embed.add_field(
        name='',
        inline=False,
        value=f"""
a. {random_trivia_choices[0]}
b. {random_trivia_choices[1]}
c. {random_trivia_choices[2]}
d. {random_trivia_choices[3]}
"""
    )

    view.clear_items()

    await msg.edit(embed=embed, view=view)

    if trivia_guesses:

        guesses = '\n'.join(f"{bot.get_user(int(user)).name}: {guess}{' :white_check_mark:' if guess.lower() == random_trivia_answer.lower() else ' :x:'}" for user, guess in trivia_guesses.items())

        await ctx.send(guesses)

    else:

        await ctx.send(f"No guesses this round!")
    
    trivia_guesses = {}

    if trivia_round_number < trivia_rounds_setting:
        trivia_round_number += 1

    elif not trivia_score:
        await ctx.send("Trivia game ends with no participants!")
        trivia_round_number = 1
        trivia_score = {}
    
    else:

        scores_text = '\n'.join(f"{bot.get_user(int(user)).name}: {score}" for user, score in trivia_score.items())

        tied_scores = [user for user, score in trivia_score.items() if score == max(trivia_score.values())]

        winner = max(trivia_score, key=trivia_score.get)

        await ctx.send(f"""
Trivia game over!

**The final score:**
{scores_text}
""")

        if max(trivia_score.values()) > 0:
            if len(tied_scores) > 1:
                tied_winners_text = ', '.join([f"<@{user}>" for user in tied_scores])
                await ctx.send(f"## It's a tie between {tied_winners_text}!")
            else:
                await ctx.send(f"## The winner is <@{winner}>!")
        else:
            await ctx.send("## No winners this time!")

        trivia_round_number = 1
        trivia_score = {}

    prevent_trivia_command = False

# @bot.command()
# async def weeb(ctx):

#     number = random.randint(1, 143448)
#     print(number)
#     headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
#     url = f'https://www.animecharactersdatabase.com/characters.php?id={number}'
#     r = requests.get(url, headers=headers)
#     page = bs(r.content, "html.parser")

#     char_div = page.find('div', {'id': 'characterzone'})
#     char_table = [item.text.strip() for item in char_div.findAll('td')]

#     profile_widget = page.find('table', {'class': 'zero pad left bo2'})

#     profile_table_title = [item.text.strip() for item in profile_widget.findAll('th')]
#     profile_table_info = ['N/A' if not item.text.strip() else item.text.strip() for item in profile_widget.findAll('td')]


#     profile_table = dict(zip(profile_table_title, profile_table_info))

#     char_name = char_table[2]
#     char_image = page.find('img', {'id': 'profilethumb'})['src']
#     char_origin = char_table[6]
#     char_mediatype = char_table[7]

#     embed = discord.Embed(title=char_name)

#     embed.set_image(url=char_image)
#     embed.set_footer(text=f'{char_origin} ({char_mediatype})')

#     embed.add_field(name='Gender', value=profile_table.get('Gender'), inline=False)
#     embed.add_field(name='Eye Color', value=profile_table.get('Eye Color'), inline=False)
#     embed.add_field(name='Hair Color', value=profile_table.get('Hair Color'), inline=False)
#     embed.add_field(name='Hair Length', value=profile_table.get('Hair Length'), inline=False)
#     embed.add_field(name='Apparent Age', value=profile_table.get('Apparent Age'), inline=False)
#     embed.add_field(name='Animal Ears', value=profile_table.get('Animal Ears'), inline=False)
    
#     await ctx.send(embed=embed)

# @bot.command()
# async def ggdeals(ctx, user):

#     if not user:
#         await ctx.send("Steam user ID64 or vanity URL name is a required command argument.")
#         return
    
#     try:
#         vanity_resolver_api_url = f'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={user}'
#         r = requests.get(vanity_resolver_api_url)
#         data = r.json()
#         if data['response']['success'] == 1:
#             steamid = data['response']['steamid']
#         else:
#             steamid = user

#         wishlist_api_url = f'https://api.steampowered.com/IWishlistService/GetWishlist/v1/?key={STEAM_API_KEY}&steamid={steamid}'
    
#     except:
#         await ctx.send("Error fetching wishlist. Is the user/ID correct?")
#         return
    
#     r = requests.get(wishlist_api_url)
#     data = r.json()

#     wishlist = data['response']['items']

#     wishlist_sorted = sorted(wishlist, key=lambda x: x['priority'], reverse=True)

#     # for game in wishlist_sorted:
#     game = wishlist_sorted[0]['appid']
#     headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
#     url = f'https://gg.deals/steam/app/{game}'
#     r = requests.get(url, headers=headers)
#     page = bs(r.content, "html.parser")

#     print(page)

@bot.command()
async def profile(ctx, *args):
        
    user = ctx.author

    if args:

        if args[0] == 'custom':
            pass

        else:
            user = get_user_from_username(args[0])

            if not user:
                try:
                    user = bot.get_user(int(args[0]))
                except:
                    await ctx.send(f"User `{args[0]}` not found in database!")
                    return

            if not user:
                await ctx.send(f"User `{args[0]}` not found in database!")
                return

    with open('profile_cards.json', 'r+') as feedsjson:
        profiles = json.load(feedsjson)
    
    if not profiles.get(str(user.id)):
        profiles[str(user.id)] = {
            'color': None,
            'image': None,
            'steam': None
        }

        with open("profile_cards.json", "w") as f:
            json.dump(profiles, f, indent=4)

    profile_data = profiles[str(user.id)]

    if args:

        if args[0] == 'custom':

            if len(args) < 3:
                await ctx.send("Error: Too few arguments to complete request. Check help.")
                return

            if args[1] == 'color':

                is_hex = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', args[2])

                if not is_hex:
                    await ctx.send("Error: Argument is not hex color code.")
                    return
                
                else:
                    profile_data['color'] = str(args[2])
            
            if args[1] == 'image':

                url = args[2]

                url = url.replace("<", "")
                url = url.replace(">", "")

                is_url = validators.url(url)
                is_https = url.startswith('https')
                is_image_link = url.endswith( ('.jpg', '.jpeg', '.png', '.webp', '.gif') )

                if not all( (is_url, is_https, is_image_link) ):
                    await ctx.send("Error: Argument is not a valid image link.")
                    return
                
                else:
                    profile_data['image'] = str(url)

            if args[1] == 'steam':

                url = args[2]

                url = url.replace("<", "")
                url = url.replace(">", "")

                is_url = validators.url(url)

                if not is_url:
                    await ctx.send("Error: Argument is not a valid URL.")
                    return
                
                else:
                    profile_data['steam'] = str(url)
                
            with open("profile_cards.json", "w") as f:
                json.dump(profiles, f, indent=4)
            
            await ctx.send(f"Done! Profile updated: `{args[1]}` customizable option has been set to `{args[2]}`.")
            return

    with open('achievements_usersdata.json', 'r') as feedsjson:
        achievements = json.load(feedsjson)
    
    with open('achievements.json', 'r') as feedsjson:
        all_achievements = json.load(feedsjson)

    with open('mine.json', 'r') as feedsjson:
        mine = json.load(feedsjson)

    with open('tradingcards/database.json', 'r') as feedsjson:
        tradingcards = json.load(feedsjson)

    user_achievements = achievements.get(str(user.id))
    user_mine = mine.get(str(user.id))
    user_tradingcards = tradingcards.get(str(user.id))

    # Embed

    embed = discord.Embed(title=f"{user.name}'s Profile Card", color=discord.Color.from_str(profile_data['color']) if profile_data['color'] else bot_color)
    embed.set_thumbnail(url=user.display_avatar)

    if profile_data['image']:
        embed.set_image(url=profile_data['image'])

    user_created_time = user.created_at.strftime("%B %d, %Y")
    user_join_date = user.joined_at.strftime("%B %d, %Y")
    rarity, role = tc_role(user)

    embed.add_field(
        name="About",
        value=f"Discord User Since {user_created_time}\nJoined Server on {user_join_date}\nServer Role: {role}\n Steam: {profile_data['steam'] if profile_data['steam'] else 'Not configured'}"
    )

    if user_achievements:

        achievements_unlocked = len([entry for entry in user_achievements.values() if entry.get('unlocked_date')])
        total_achievements = len(all_achievements)

        embed.add_field(
            name="Achievements Unlocked",
            value=f"{achievements_unlocked} / {total_achievements}",
            inline=False
        )

    if user_tradingcards:

        # Trading Cards stats

        player_collection = fetch_player_collection(str(user.id))

        normal_cards_count = sum(entry['count'] for entry in player_collection.values() if not entry['holo'])
        holo_cards_count = sum(entry['count'] for entry in player_collection.values() if entry['holo'])

        with open('tradingcards/cards.json') as feedsjson:
            all_cards = json.load(feedsjson)

        undiscovered_cards = [user for user in ctx.guild.members if str(user.id) not in [user for user in all_cards.keys()]]

        player_rarities_count = Counter([card_info['rarity'] for card_info in player_collection.values() if not card_info.get('legacy') and not card_info.get('holo')])
        
        server_members = [x for x in ctx.guild.members]

        player_rarities_count_combined = sum(player_rarities_count.values())

        embed.add_field(
            name="Trading Cards Binder Completion",
            value=f"{player_rarities_count_combined} / {len(server_members)} ({len(undiscovered_cards)} undiscovered cards)",
            inline=False
        )
    
        embed.add_field(
            name="Trading Cards Possessed",
            value=f"Normal: {normal_cards_count}\nHolo: {holo_cards_count}",
            inline=False
        )

    if user_mine:

        gems_earnings = {}

        for crew, crew_info in user_mine['crew'].items():
            gems_earnings[crew] = (crew_info['count']*crew_values[crew]['production'])*crew_info['upgraded']

        gems_earnings_total = round( sum( gems_earnings.values() ) )
        gems_possession = user_mine['assets']['gems']
        money_possession = user_mine['assets']['money']
        ascension = round(user_mine['multi']['ascension'], 4)

        embed.add_field(
            name="Idle Mine",
            value=f"Gems: {f'{human_num(gems_possession)}' if gems_possession > 999.99 else f'{gems_possession}'} (+{f'{human_num(gems_earnings_total)}' if gems_earnings_total > 999.99 else f'{gems_earnings_total:,}'}/min)\nMoney: ${f'{human_num(money_possession)}' if money_possession > 999.99 else f'{money_possession:,.2f}'}\nAscension Level: {f'{human_num(ascension)}' if ascension > 999.99 else f'{ascension:,}'} %",
            inline=False
        )

    await ctx.send(embed=embed)

# SECRET SANTA CODE

# class SecretSantaButtons(discord.ui.View):
#     def __init__(self, ctx, wishlist, role):
#         super().__init__()
#         self.ctx = ctx
#         self.author = ctx.author
#         self.wishlist = wishlist

#     async def interaction_check(self, interaction: discord.Interaction):
#         return interaction.user.id == self.author.id

#     @discord.ui.button(label='Agree', style=discord.ButtonStyle.success)
#     async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
#         button.disabled = True
#         for child in self.children:
#             child.disabled = True
#         await interaction.response.edit_message(view=self)

#         try:
#             await self.author.send()
#         except discord.Forbidden:
#             await interaction.followup.send(f'<@{self.author.id}> Registration failed as PaigeBot is unable to DM you. Please ensure your privacy settings allow DMs from this server!', ephemeral=False)
#             return
#         except discord.HTTPException:
#             pass 

#         with open('secret_santa_registration.json', 'r') as feedsjson:
#             file = json.load(feedsjson)

#         file[self.author.id] = {
#             'info': {
#                 'name': self.author.name,
#                 'id': self.author.id,
#                 'wishlist': self.wishlist
#             },
#             'assigned': {}
#         }

#         with open("secret_santa_registration.json", "w") as f:
#             json.dump(file, f, indent=4)
        
#         role = self.ctx.guild.get_role(role_secretsanta)
#         await self.author.add_roles(role)
        
#         await interaction.followup.send(f'<@{self.author.id}> you have registered for SGM Secret Santa!', ephemeral=False)
    
#     @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger)
#     async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
#         button.disabled = True
#         for child in self.children:
#             child.disabled = True
#         await interaction.response.edit_message(view=self)
#         await interaction.followup.send(f'{self.author.name}\'s registration was cancelled.', ephemeral=False)

# @bot.command()
# async def secretsanta(ctx, wishlist_link=None):

#     with open('secret_santa_registration.json', 'r+') as feedsjson:
#         file = json.load(feedsjson)

#     if [key for key, val in file.items() if val.get('assigned')]:
#         await ctx.send(f'Registration phase has ended!')
#         return
#     if not wishlist_link:
#         await ctx.send(f'Argument missing - please include your wishlist link (`{prefixes[0]}secretsanta wishlist_link`)')
#         return
#     if not validators.url(wishlist_link):
#         await ctx.send(f'Argument `wishlist_link` (`{wishlist_link}`) is not a valid URL.')
#         return
    
#     if file.get(str(ctx.author.id)):
#         await ctx.send(f'<@{ctx.author.id}> you are already registered for SGM Secret Santa!')
#         return

#     view = SecretSantaButtons(ctx, wishlist=wishlist_link, role=ctx.guild.get_role(role_secretsanta))

#     await ctx.send(f"""
# By signing up for SGM Secret Santa, you commit to the following if your application is accepted:
# - Spending a minimum of $10.00 USD (sales/discounts allowed) on Steam gift(s) and/or key(s) from your randomly assigned participant's wishlist as their gift.
# - Promise to put genuine effort in purchasing what you truly believe will make your assigned participant happier.
# - Understand that the same is expected by another random participant who will be your secret Santa, but that we cannot guarantee the quality or desirability of the gift you receive.
# - Make sure your wishlist has a variety of games at different price points. (No picking the most popular or expensive ones!) You will not commit any major changes to your wishlist which would greatly limit your secret Santa's options.
# - While not enforced, we encourage playing the game or games gifted to you by your secret Santa.
# - Your DMs must be open to members of this server, or you must have a DM open with PaigeBot, so that you may receive updates and instructions privately.
                   
# <@{ctx.author.id}> Do you agree to these terms and would like to complete your application/registration?
# """,
#     view=view)
    
#     await view.wait()

# @bot.command()
# @commands.has_any_role(role_staff)
# async def ssadmin(ctx, arg=None):
#     if not arg:
#         await ctx.send("Secret Santa administration commands:\n- `list` - Lists the current registrations.\n- `finalize` - Ends registration phase, and assigns each user to another user.")
#         return

#     with open('secret_santa_registration.json', 'r+') as feedsjson:
#         registrations = json.load(feedsjson)
    
#     if arg.lower() == 'list':
#         embed = discord.Embed(title="Registrations")

#         for userid in registrations:

#             name = registrations[userid]['info']['name']
#             wishlist = registrations[userid]['info']['wishlist']
        
#             embed.add_field(
#                 name=name,
#                 value=wishlist,
#                 inline=False
#             )
        
#         await ctx.send(embed=embed)
#         return
    
#     elif arg.lower() == 'finalize':

#         keys = list(registrations.keys())
#         random.shuffle(keys)

#         for i, userid in enumerate(keys):

#             registrations[userid]['assigned'] = registrations[keys[i-1]]['info']
#             member=bot.get_user(int(userid))
#             assigned_user = registrations[userid]['assigned']
#             try:
#                 await member.send(f"""
# Hello there!

# The Secret Santa registration phase has ended, and you have been assigned your recipient!

# Recipient: {assigned_user['name']}
# Wishlist: <{assigned_user['wishlist']}>

# Now is the time to have a look at their wishlist (or feel free to look at their message history on SGM, profile(s), etc) to determine what would be the best game or games to offer them as a Christmas gift. Once you've chosen the perfect gift, you can contact them to give them the keys or Steam gifts through your preferred medium (be it Steam, Discord, or other) any time between today and December 25th.

# Remember, don't reveal that you are your recipient's Secret Santa until you're ready to give them their gift! That's the "secret" part of it.

# As a reminder of our guidelines:
# - Spend a minimum of $10.00 USD (sales/discounts allowed) on Steam gift(s) and/or key(s) from your randomly assigned recipient's wishlist as their gift.
# - Put genuine effort in purchasing what you truly believe will make your assigned recipient happier.
# """)
#             except:
#                 await ctx.send(f"DM to <@{member.id}> failed due to privacy or permission settings!")

#         with open("secret_santa_registration.json", "w") as f:
#             json.dump(registrations, f, indent=4)

# HELP COMMANDS

@bot.command()
async def help(ctx, query=None):

    threads_list = list(steamgifts_threads)
    threads_list = ", ".join(threads_list)

    with open("achievements.json") as feedsjson:
        achievements_list = json.load(feedsjson)

    achievements_categories = {re.search('^[^_]+(?=_)', key)[0] for key in achievements_list.keys()}

    commands_list = [
        ("test",
         "Simple test command. Check if the bot is alive!"),

        ("help `query`",
         "Displays the help message. If `query` is provided, displays help for the relevant command, if any."),

        ("info (aliases: `about`, `status`)",
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
        
        ("user `user`",
         "Returns the Steamgifts and Steam profile of the `user`, if any found. `user` may be a SteamID64, Steamgifts username, or Steam username."),

        ("ai `query`",
         "Interact with PaigeBot's openAI integration."),

        ("slots",
         f"Play PaigeSlots! Get 3 matching fruits, and you can win a free game key! Cooldown time is {slots_cooldown}. See `slotskey` and `slotsprizes` commands for utility."),

        ("slotskey `activation-key-here, platform, Title Here`",
         f"Contribute a game key to the slots command prize pool. Must be issued privately via DM to {botname}."),

        ("slotsprizes (aliases: `slotprize`, `slotsprize`, `slotprizes`)",
         "Lists the titles of available prizes in the slots command prize pool."),

        ("poker `@user`",
         f"Challenges `@user` to a game of Dice Poker. See `pokerguide` (`{prefixes[0]}pokerguide`) for more."),

        ("tc `arguments`",
         f"No argument: Claims a trading card. Has a cooldown time of {tc_cooldown}. See `tcguide` (`{prefixes[0]}tcguide`) for more."),

        ("role `simpleroleID`",
         f"Grants the user the role associated with `simpleroleID`. Revokes the role if the user already has it. `simpleroleID` must be one of {', '.join(allowed_roles)}."),

        ("bug `message`",
         f"Logs a bug report. Please include details as `message` - example: `{prefixes[0]}bug The trading card guide has a typo in the rarity sections.`"),
        
        ("suggestion (aliases: `suggest`) `message`",
         f"Logs a suggestion. Please include details as `message` - example: `{prefixes[0]}suggestion Make the help menu less chaotic.`"),

        ("reports (aliases: `buglog`) `clear` `bugs` `suggestions`",
         "Takes one or no arguments, and displays all relevant pending reports. JBONDGUY007 ONLY: If `clear` argument followed by `list-of-report-IDs` is provided, clears report(s) with list of IDs `list-of-report-IDs` from the bug log."),
        
        ("reviewed `game`",
         "Searches for `game` in the magazine index, and returns the link to the magazine in which this game was reviewed, if any. `game` may be a full game title (not case-sensitive) or AppID."),
        
        ("coinflip (aliases: `flipcoin`)",
         "Flips a coin."),
        
        ("achievements (aliases: `cheevos`, `ach`) `category`",
         f"View all achievements including which ones you've unlocked. Takes an optional argument `category` which is one of {', '.join(['`'+x+'`' for x in achievements_categories])}."),
        
        ("stats",
         "View PaigeBot and other fun server-wide statistics."),
        
        ("gtp (aliases: `tpir`)",
         "Begin a \"The Price Is Right\" inspired minigame, \"Guess the Price\"! Complete to guess as closely to the winning bid price (USD) of a random Ebay auction."),

        ("gtf `cache`",
         "Begin a \"Guess The Flag\" chat game! Complete to be the first to guess the name of a country by its flag. Optional `cache` argument will fetch and cache flags from the source (operation completes automatically daily)."),

        ("hltb `query`",
         "Fetches How Long To Beat data for the best match of `query`."),

        ("steamsale (aliases: `nextsale`)",
         "Checks the current ongoing Steam sale/event, and what and when the next sale/event will occur."),

        ("reminder (aliases: `remind`) `\"reminder\"` `1d` `1h` `1m` OR `tc` `slots`",
         "Sets a reminder for the user. Reminder must be in quotes (unless single-word), followed by day(s), hour(s), and minute(s) in the format Xd Xh Xm where X are integers. All are optional, but at least one value must be provided. Also takes `tc` or `slots` as argument without time, in which case it uses a preset 8h and 6h timer respectively. Also see `reminders` command."),

        ("reminder `cancel` `reminder_ID`",
         "Cancels reminder with ID `reminder_ID`."),
        
        ("reminders",
         "Lists user's reminders."),

        ("mine (aliases: `m`) `shop` `buy` `sell` `market` `ascend` `stats`",
         f"Play the mining idle game. Non-argument displays your mine's information. See See `mineguide` (`{prefixes[0]}mineguide`) for details."),

        ("bookmark (aliases: `bm`)",
         f"Have {botname} DM you a bookmark for the desired message in the server. Reply to a message with this command to bookmark the reply."),

        ("typerace (aliases: `tr`) `timer` `leaderboard`",
         f"Begin a Type Racer chat game! Test your typing speed and accuracy by typing out the generated paragraph.\nOptional `timer` argument expects an integer between 30 and 240 for round duration, defaults 120. Optional argument `leaderboard` displays leaderboard. Additional argument `net`, `gross`, or `faultless` displays the relevant leaderboard. (Example: `{prefixes[0]}tr leaderboard faultless`)"),

        ("trivia `rounds_count`",
         "Starts a trivia game (or the next round of a trvia game, if already ongoing). Takes an optional argument `rounds_count` from 1 to 20 if starting a new trvia game, to customize the number of rounds before the game ends."),

        ("vote `begin` `end`",
         "Begin the voting process which allows you to cast your votes for your favourite review and review design. Optional staff/assistants arguments `begin` and `end` will initiate or terminate the voting phase as needed. Note: `end` command is irreversible, and will wipe the data."),

        ("profile `user` `custom`",
         "Without arguments, displays your profile card. Providing the `user` argument will display that user's profile card instead. Providing the `custom` argument, followed with `color` and an hex color code will set your profile widget color. Providing `custom image` followed by a valid image URL will set this image as your profile card image. Providing `custom steam` followed by a valid URL will set this URL as your profile card steam link.")
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
         "Sets a `message` to be sent in the general chat at 12 PM CST daily. If `message` argument is one of `none`, `clear`, or not provided, the daily notification is deleted and disabled until set again."),

        ("maintenance `start` `end`",
         "BOTMASTER ONLY - Sends an offline/online notification to all bot channels."),

        ("unblock",
         "Disables all command blocking flags. Used to bruteforce commands that are stuck in blocking mode."),
        
        ("uploadvotes",
         "Use to upload a json file of reviews/designs votes to add to the tally. Admins and assistants only.")
    ]

    # Individual help by query.
    if query:
        returned = False

        # Public commands:
        for com in [x for x in commands_list if query.lower() in x[0].split() or query.lower() in x[0].split('`')]:
            command = discord.Embed(title=f'Help: {com[0].split()[0]}', color=bot_color)
            command.add_field(
                name=f"{prefixes[0]}{com[0]}",
                value=f"*{com[1]}*",
                inline=False
            )
            await ctx.send(embed=command)
            returned = True

        # Moderator commands:
        for com in [x for x in mod_commands_list if query.lower() in x[0].split() or query.lower() in x[0].split('`')]:
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
        with open("permanent_variables.json", "w") as f:
            json.dump(permanent_variables, f, indent=4)

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

@bot.command()
@commands.has_any_role(role_staff)
async def backup(ctx):
    await ctx.send("Backing up data to AWS S3 bucket...")
    upload_backups()
    await ctx.send(f"Backup successful! - Backup time: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} GMT-3`")

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
async def maintenance(ctx, arg='start'):

    if not ctx.author.id == jbondguy007_userID:
        await ctx.send("Botmaster command only!")
        return
    
    channels = [bot_channel, bot_channel2, idle_miners_channel]
    
    if arg.lower() == 'start':
        for channel in channels:
            ch = bot.get_channel(channel)
            await ch.send(f"# {botname} is going offline for maintenance! 🔧")

    elif arg.lower() == 'end':
        for channel in channels:
            ch = bot.get_channel(channel)
            await ch.send(f"# Maintenance completed - {botname} is back online! 📡")
    
    else:
        await ctx.send(f"Unrecognized argument `{arg}`.")

    await ctx.send(f"Maintenance `{arg}` notification sent out!")

# @bot.command()
# @commands.has_any_role(role_staff)
# async def verify(ctx):

#     SGM_guild = bot.get_guild(DISCORD_SERVER_ID)
#     server_members = SGM_guild.members
#     verified_role = ctx.guild.get_role(role_verified)

#     verified_count = 0
#     verified_failed = [ctx.author]

#     msg = await ctx.send(f"Granting the `Verified` role to all members!\n{verified_count}/{len(server_members)}")

#     for member in server_members:
#         try:
#             await member.add_roles(verified_role)
#         except:
#             verified_failed.append(member)
#         verified_count += 1
#         await msg.edit(content=f"Granting the `Verified` role to all members!\n{verified_count}/{len(server_members)}")
    
#     await ctx.send(f"Task completed with `{len(verified_failed)}` error(s)!")
#     if verified_failed:
#         await ctx.send(f"The following users were not granted the role due to error(s):\n`{', '.join( [user.name for user in verified_failed] )}`")

@bot.command()
@commands.has_any_role(role_staff)
async def unblock(ctx):

    global prevent_binder_command, prevent_gtp_command, prevent_mine_command, prevent_gtf_command, prevent_tr_command, prevent_trivia_command, prevent_vote_command
    
    prevent_binder_command = False
    prevent_gtp_command = False
    prevent_mine_command = False
    prevent_gtf_command = False
    prevent_tr_command = False
    prevent_trivia_command = False
    prevent_vote_command = False

    await ctx.send("All command blocking flags have been set to `False`!")

# CONTRIBUTOR COMMANDS

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
    
    with open('permanent_variables.json', 'w') as f:
        json.dump(persistent_data, f, indent=4)

# TASKS

@tasks.loop(minutes=30)
async def check_for_new_giveaways():

    if bot.user.id == 823385752486412290:
        return

    print(f"CHECK: check_for_new_giveaways() triggered...")

    with open("last_checked_active_giveaways.json", "r") as f:
        last_checked_active_giveaways = json.load(f)
    last_checked_active_ga_ids = last_checked_active_giveaways['last_checked_active_ga_ids']
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
        last_checked_active_ga_ids = last_checked_active_ga_ids[-200:]
        last_checked_active_giveaways['last_checked_active_ga_ids'] = last_checked_active_ga_ids
        with open("last_checked_active_giveaways.json", "w") as f:
            json.dump(last_checked_active_giveaways, f, indent=4)
    
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

        await cha.send("Running daily task `get_gtf_flags()`...")
        cached_flag_items = get_gtf_flags()
        await cha.send("Done!")

        await cha.send("Backing up data to AWS S3 bucket `upload_backups()`...")
        upload_backups()
        await cha.send(f"Backup successful! - Backup time: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} GMT-3`")

        await cha.send("Checking for legacy trading cards `tc_legacy_check()`...")
        legacy_IDs, unlegacy_IDs = await tc_legacy_check()
        if legacy_IDs:
            legacy_IDs_list = '\n'.join(legacy_IDs)
            await cha.send(f"{len(legacy_IDs)} cards have been detected to be new legacy cards:\n{legacy_IDs_list}")
        else:
            await cha.send("Done! No new legacy cards detected!")
        
        if unlegacy_IDs:
            legacy_IDs_list = '\n'.join(legacy_IDs)
            await cha.send(f"{len(legacy_IDs)} cards have been detected to no longer be legacy cards:\n{legacy_IDs_list}")

# Daily Notifications

@tasks.loop(hours=1)
async def daily_notifier():
    with open('permanent_variables.json', 'r') as outfile:
        persistent_data = json.load(outfile)
        reminder = persistent_data['24h_reminder']

    time = datetime.now().hour
    if time == 14 and reminder:
        cha = bot.get_channel(general_channel)
        await cha.send(content=reminder)

# Frequent loop

@tasks.loop(seconds=60)
async def reminders_process():
    with open('reminders.json', 'r') as outfile:
        reminders_data = json.load(outfile)

    now = datetime.now().replace(microsecond=0)
    deletion_list = []

    for userID, reminders in reminders_data.items():
        for reminderID, data in reminders.items():

            reminder_timer = datetime.strptime(data['timer'], '%Y-%m-%d %H:%M:%S')

            if reminder_timer < now:
                cha = bot.get_channel(data['channel'])

                try:
                    await cha.send(content=f"<@{userID}> Reminder: {data['reminder']}")
                except:
                    print(f"ALERT: Failed to send reminder {reminderID}. Skipping.")
                    return
    
                deletion_list.append( (userID, reminderID) )

    for item in deletion_list:
        del reminders_data[item[0]][item[1]]

    with open("reminders.json", "w") as f:
        json.dump(reminders_data, f, indent=4)

bot.run(TOKEN)
