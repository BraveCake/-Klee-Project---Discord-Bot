import discord
import os
from keep_alive import keep_alive
import random
import translators as ts
import sys
import json
from bs4 import BeautifulSoup
import re
import hashlib
from discord.ext import tasks, commands
import asyncio
from datetime import datetime,timedelta
from time import sleep
# from replit import db #drepricated replit db is no longer needed
import pytz
import requests
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import pytube
from database import Database
from forumTitles import ForumTitles


fdb = Database()
#fdb['dashboard'] = 'klee-dashboard'  #dashboard = name of the channel in which you can have highest acces to klee
#fdb['quick-bot'] = 'true'
kw = [
    "spam", "ping", "team-ping", "wm", "anonymous", "status", 'apps_notifier','statistics',
    'team-auto','teamchat-commands','dashboard','quick-bot'
]
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
async def teamStatistics():
      hits =0
      details= [0]*24
      yesterday =datetime.now()
      yesterday = yesterday - timedelta(hours=yesterday.hour,minutes=yesterday.minute,seconds=yesterday.second)
      tc = client.get_channel(462841576616361987)
      first = ''
      async for msg in tc.history(limit=None,after=yesterday):
           if(first==''):
             first = msg.content
           if (not msg.content.startswith('**(TEAM) ')):
               continue
           hits = hits+1
           details[msg.created_at.hour]=details[msg.created_at.hour]+1
      return [details,hits,first]
def isInACL(author,ACL):
    roles_list= author.roles
    roles_list.append(author.id)
    return len([i for i in roles_list if i in ACL]) !=0
def ping(name):
    if (name == 'disabled'):
        return '1'
    for profile in fdb.keys():
        if profile.startswith('(*'):
            profile_info = eval(fdb[profile])
            if (profile_info["PingName"] == name):
                return '<@!' + profile.lstrip('(*') + '>'
    return '0'
@tasks.loop(hours=1.0)
async def post_statistics():
  if not datetime.now().hour==23:
    return
  statistics = await teamStatistics()
  channel= discord.utils.get(SO_SERVER.channels,name=fdb['statistics'])
  await channel.send('Total messages sent today: '+str(statistics[1])+'\nDetails:'+str(statistics[0])+'\nAverage: '+str(statistics[1]/24)+' message/hour\ncalculated at: '+str(datetime.now())+'\nfirst message sent today: '+statistics[2])
  
def players_info(details): 
  try:
     response = requests.get("http://jarno.pro/stuff/api/ab.php")
     if details:
        return response.json()['RESULTS']
     else:
        return response.json()['COUNT_RESULTS']
  except:
    return 0

def split_message(text): #splits the message to n elements each element length shouldn't exceed 2000 characters
  return [text[i:i+2000] for i in range(0, len(text), 2000)]
@tasks.loop(minutes=5.0)
async def update_join_quit():
    players = set()
    for player in players_info(True):
        players.add(player['name'].replace("'", '').replace('"', ''))
    previous = fdb['!players'].lstrip('{').rstrip('}').replace(' ', '').replace(
        '"', '').replace("'", '').split(',')
    previous = set(previous)
    online = players.difference(previous)
    offline = previous.difference(players)
    fdb['!players'] = str(players)
    result = ['']
    lines = 0
    index = 0
    for name in online:
        result[index] = result[index] + name + ' **(Join)**\n'
        lines = lines + 1
        if (lines >= 50):
            result.append('')
            lines = 0
            index = index + 1
    channel = client.get_channel(917108934664409150)
    for p in result:
        if (len(p) > 0):
            await channel.send(p.replace('@everyone','@ everyone'))
    result = ['']
    index = 0
    lines = 0
    for name in offline:
        result[index] = result[index] + name + ' **(Quit)**\n'
        lines = lines + 1
        if (lines >= 50):
            result.append('')
            lines = 0
            index = index + 1
    for p in result:
        if (len(p) > 0):
            await channel.send(p.replace('@everyone','@ everyone'))


async def dynamic_roster(reaction, user):
    if (reaction.message.author == client.user
            and reaction.message.embeds[0].title == 'Roster'
            and user != client.user):
        result = reaction.message.embeds[0]
        if reaction.emoji == '➡️':
            result.description = so_roster[1]
            so_roster.append(so_roster.pop(0))
            await reaction.message.edit(embed=result)
        elif reaction.emoji == '⬅️':
            result.description = so_roster[len(so_roster) - 1]
            so_roster.insert(0, so_roster.pop())
            await reaction.message.edit(embed=result)


async def dynamic_help(reaction, user):
    if (reaction.message.author == client.user
            and reaction.message.embeds[0].title == 'List of commands'
            and user != client.user):
        result = reaction.message.embeds[0]
        with open('help2.txt', 'r') as h2:
            with open('help.txt', 'r') as h1:
                if reaction.emoji == '➡️':
                    result.description = h2.read()
                    await reaction.message.edit(embed=result)
                elif reaction.emoji == '⬅️':
                    result.description = h1.read()
                    await reaction.message.edit(embed=result)


async def team_chat_mute(message):
    await message.channel.set_permissions(message.author,
                                          read_messages=True,
                                          send_messages=False)
    await client.get_channel(812678973037215754).send(
        message.author.mention + " attempted a forbidden action in " +
        message.channel.name)


def create_profile(ctx, id):
    target_obj = ctx.guild.get_member(int(id))
    if (target_obj is None):
        return False
    fdb['(*' + str(
        id
    )] = '{"Balance":0,"PingName":"","IG-name":"(Required for team chat access)","daily":"","Warns":0}'
    print('stored' + str(id))
    return True


def get_id(tag):
    return tag.lstrip('<').rstrip('>').lstrip('@').lstrip('!').strip()


def get_complete_hash(user, passwrd, session):
    return hex_sha1(
        bytes(hex_sha1(user.encode("utf-8").lower() +
                       passwrd.encode("utf-8")), 'utf-8') +
        bytes(session, 'utf-8'))


def has_mora(source, amount):
    amount = int(amount)
    source = int(eval(fdb['(*' + str(source)])['Balance'])
    if (source >= amount):
        return True
    else:
        return False


def send_mora(source, target, amount):
    amount = int(amount)
    o_source = None
    if not source == '000':
        o_source = eval(fdb['(*' + source])
    o_target = eval(fdb['(*' + target])
    if (not source == '000' and o_source['Balance'] < amount):
        return False
    o_target['Balance'] = o_target['Balance'] + amount
    if not source == '000':
        o_source['Balance'] = o_source['Balance'] - amount
    if not source == '000':
        fdb['(*' + source] = str(o_source)
    fdb['(*' + target] = str(o_target)
    return True


def hex_sha1(value):
    return hashlib.sha1(value).hexdigest()


def get_authenticity_token(html):
    soup = BeautifulSoup(html, "html.parser")
    token = soup.find_all('input', attrs={'type': 'hidden'})
    if not token:
        print('could not find `authenticity_token` on login form')
    result = [token[2].get('name'), token[2].get('value')]
    return result


def online_stats(target):
    stats = ''
    players = players_info(True)
    for player in players:
        if (player['name'].find(target) != -1
                or player['name'].lower().find(target.lower()) != -1):
            stats = "Occupation:" + str(
                player['occupation']) + "\nCash: " + str(
                    player['cash']) + '$\nPlaytime: ' + str(
                        int(player['playtime']) / 60) + 'H\nGroup: ' + str(
                            player['gang']) + '\nSquad: ' + str(
                                player['squad']) + "\nCountry: " + str(
                                    player['country']) + ' :flag_' + str(
                                        player['country']).lower(
                                        ) + ':' + "\nPing: " + str(
                                            player['ping'])
            c = str(player['color']).replace('[', '').replace(']', '').replace(
                "'", "").split(',', 3)
            c = rgb_to_hex(int(c[0]), int(c[1]), int(c[2]))
            return (discord.Embed(title=str(player['name']),
                                  description=stats,
                                  color=int("0x" +
                                            c, 16)) if len(stats) > 0 else '')


@tasks.loop(minutes=5.0)
async def notify_me():
    for target in fdb.keys():  #check from subscriptions
        notified = 0
        if (target.startswith(' (')):
            if (fdb[target].find('*,') != -1):  #if target was online n= 1
                notified = 1
            stats = online_stats(target.lstrip(' ('))  #gets stats
            if not stats:  # if not online
                if (notified):  #check if he was set as online before
                    fdb[target] = fdb[target].replace('*,',
                                                    '')  #set as not online
                    notified = -1
                else:  #move to the next one
                    continue
            if (notified == 1):
                continue
            subscribers = fdb[target].split(',')  #get list of subscribers
            for subscriber in subscribers:  #notify each one
                if (len(subscriber) < 3):
                    continue
                subscriber = await client.fetch_user(subscriber)
                await subscriber.send(
                    "*" + target.lstrip('( ') + "* Is {}  ".format(
                        "Online" if notified == 0 else "Offline"),
                    embed=stats)
            if (not notified):
                fdb[target] = fdb[target] + '*,'


@tasks.loop(hours=24.0)
async def reset_warns():
    for x in fdb.keys():
        if x.startswith('(*'):
            profile = eval(fdb[x])
            profile['Warns'] = 0
            fdb[x] = str(profile)


@tasks.loop(minutes=60.0)
async def lottery():
    if (os.path.getsize("lottery.txt") == 0):
        return
    lottery = open('lottery.txt', 'r')
    winner = str(random.randint(1, 10))
    response = "Ticket " + str(winner) + " is the lucky one of this lottery!"
    for l in lottery:
        l = l.split(':')
        if (l[1].rstrip() == winner):
            winner = l
            break
    if (isinstance(winner, list)):
        response = response + os.linesep + (await client.fetch_user(winner[0]
                                                                    )).mention
        send_mora('000', winner[0], '50000')
    else:
        response = response + os.linesep + "Unfortunately none was able to win it!!"
    await client.get_channel(464028850091851786).send(response)
    lottery.close()
    lottery = open('lottery.txt', 'w')
    lottery.close()


@tasks.loop(minutes=5.0)
async def get_updates():
    response = requests.get("https://cit.gg/")
    d = 0
    content = ''
    days = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
        'Sunday'
    ]
    for l in response.iter_lines():
        if (d < 5 and str(l).startswith("b'<div class=\"sp_block\">")):
            d = d + 1
        if (d > 5):
            for day in days:
                if (str(l).lstrip("b'<br />").startswith(day)):
                    d = -1
                    break
        if (d == -1):
            break
        if (d >= 5):
            if (d == 5):
                l = str(l).replace("b'<div class=\"sp_block\">", '')
            content = content + str(l).strip('\'').strip('b').strip("'").strip(
                '"').strip('<br />') + '\n'
            d = d + 1
    if (content != fdb['updates']):
        fdb['updates'] = content
        channel = client.get_channel(860293711228043264) 
        await channel.send(content)
    if (fdb['apps_notifier'] != 'off'):
        res = connect2forum('https://cit.gg/index.php?board=471.0')
        soup = BeautifulSoup(res, "html.parser")
        element = soup.find("td", {"class": "stats windowbg"})
        current_apps = element.find("p").get_text(separator="*").split('*',
                                                                       1)[1]
                                                                  
        if (fdb['__apps__'] != current_apps):
            so_private =  client.get_channel(934511680388489266)
            await so_private.send(
                '~Ara ~ ara there is a new applicant <:KleeE:867193529620103179>'
            )
            fdb['__apps__'] = current_apps
            res = connect2forum("https://cit.gg/index.php?board=852.0")
            soup = BeautifulSoup(res, "html.parser")
            element = soup.select('.table_grid tr')[4].findChildren(
                'a')[0]['href']
            res = connect2forum(element)
            soup = BeautifulSoup(res, "html.parser")
            app = soup.select('.post_wrapper')[0]
            app_h = open('app_h.txt', 'w')
            app_h.write(
                app.get_text(separator='\n'))
            app_h.close()
            app_h = open('app_h.txt', 'r')
            await so_private.send(      file=(discord.File(app_h)))
            app_h.close()


def rgb_to_hex(r, g, b):
    return '%02x%02x%02x' % (r, g, b)


def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    rgb = [
        int(hex[0:2], base=16),
        int(hex[2:4], base=16),
        int(hex[4:6], base=16)
    ]
    return "#" + hex + " equivalent rgb value is " + str(rgb).strip('[]')


def connect2forum(url):
    cit = requests.Session()
    response = cit.get('https://cit.gg/index.php')
    headers = {
        'authority': 'cit.gg',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'origin': 'https://cit.gg',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent':
        'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
        'accept':
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://cit.gg/index.php?action=login',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    params = (('action', 'login2'), )
    token = get_authenticity_token(response.text)
    hash = get_complete_hash('Klee', os.getenv('PASSWORD'), token[1])
    data = {
        'user': 'Klee',
        'passwrd': '',
        token[0]: token[1],
        'hash_passwrd': hash
    }
    cookies = {
        'SMFCookieCIT':
        os.getenv('cookies'),
        'PHPSESSID': cit.cookies.get_dict()['PHPSESSID']
    }
    res = cit.post('https://cit.gg/index.php?action=login2',
                   headers=headers,
                   params=params,
                   data=data,
                   cookies=cookies)
    res = cit.get(url, headers=headers, cookies=cookies)
    return res.text

def getCitTime():
    London_tz = pytz.timezone('Europe/Paris')
    ct = datetime.now(London_tz)
    return ct.strftime("%H:%M:%S")
  
def calculate(message):
    content = message.split('!calculate ', 1)[1]
    if (re.search('[a-zA-Z]+', content)):
        return
    return eval(content.replace("^", "**"))

def rollDice(message):
    x = int(message.split(' ', 2)[1])
    return random.randint(0, x - 1) + 1

async def cursed(message):
    curse = open('curse.txt', 'r')
    cm = 0
    try:
        for l in curse:
            curse_info = l.split(':')
            curse_info[1] = curse_info[1].replace(os.linesep, '')
            if (curse_info[0] == str(message.author.id)):
                print(curse_info)
                if (curse_info[1] == '1'):
                    print("c1")
                    await message.delete()
                    cm = 2
                elif curse_info[1] == '2':
                    print("c2")
                    cm = 1
                elif curse_info[1] == '3' and cm < 2:
                    print("c3")
                    target = await client.fetch_user(curse_info[0])
                    target = message.guild.get_member(target.id)
                    await message.add_reaction('🐷')
                    await target.edit(nick='Loser')
                elif curse_info[1] == '4' and cm < 2:
                    if (re.search('<:\w+:\d+>', message.content)
                            or re.search('<\w+:\w+:\d+>', message.content)):
                        await message.delete()
                elif curse_info[1] == '5' and cm < 2:
                    print("c5")
                    spam_ratio = random.randint(0, 100)
                    print(spam_ratio)
                    if (spam_ratio < 51):
                        target = '<@' + curse_info[0] + '>'
                        tm = await message.channel.send(target)
                        await tm.delete()
                elif curse_info[1].startswith('p') and cm < 2:
                    print("cp")
                    if (len(curse_info) > 2):
                        await message.add_reaction(
                            discord.utils.get(client.emojis,
                                              name=curse_info[2]))
                        continue
                    emo = str(curse_info[1].split('+')[1])
                    for c in range(0, len(emo)):
                        await message.add_reaction(emo[c])
    finally:
        curse.close()
        return cm


async def modifyRole(ctx, id, role, controller):
    role = discord.utils.get(ctx.guild.roles, name=role)
    target = ctx.guild.get_member(int(get_id(id)))
    if (controller == 1):
        await target.add_roles(role)
    else:
        await target.remove_roles(role)


def unwarn(target):
    profile = eval(fdb['(*' + str(target)])
    profile['Warns'] = 0
    fdb['(*' + str(target)] = str(profile)


@client.event
async def on_ready():
    fdb['test']= 'passed'
    global SO_SERVER,extractRole,EXSO_R,guest_R,SO_R,TSO_R,emperor,empress,prisoner_R,HON_R,SO_Roles,GULAG_ACL,CURSE_ACL,KEY_R
    SO_SERVER = client.get_guild(451993644644171776)
    extractRole = lambda r_id:           discord.utils.get(SO_SERVER.roles,id=r_id)
    EXSO_R = extractRole(742746161563041822)
    guest_R = extractRole(769304697127174186)
    SO_R = extractRole(452369040287989780)
    KEY_R = extractRole(935913018380927046)
    TSO_R = extractRole(452369116611739650)
    emperor = extractRole(786635154432720897)
    empress = extractRole(870694391373770752)
    prisoner_R = extractRole(749576592313024552) 
    HON_R = extractRole(460713877517107220)
    SO_Roles = [SO_R, TSO_R, KEY_R, HON_R]
    GULAG_ACL =[KEY_R,emperor,empress]
    CURSE_ACL= [KEY_R,emperor]
    if fdb['quick-bot']!='off':
      return
    if not get_updates.is_running():
        get_updates.start()
    lottery.start()
    notify_me.start()
    post_statistics.start()
    update_join_quit.start()
    reset_warns.start()
    print('we have logged in as {0.user}'.format(client))
    if (fdb['status'] != 'default'):
        await client.change_presence(activity=discord.Game(name=fdb['status']))


sev = '#FFFFFF'
o = ''
limiter = False
cancel = False
lock = asyncio.Lock()

@client.event
async def on_message(message):
    print(message.content + " from id:" + str(message.author.id))
    
    global m, sev, limiter, kw, so_roster,cancel
    ch = await cursed(message)
    if ch > 0 and message.channel.id != 815610398039867402:  
        return
    if (message.author == client.user):
        return
    if (message.content.startswith('!cast ')):
        member = await SO_SERVER.fetch_member(message.author.id)
        if(SO_R in member.roles):
            if(message.content.count(' ')<3): #incorrect format
                return
            voteData = message.content.split(' ',2) #command survery_id vote
            if(not voteData[1].isnumeric()): #invalid id
                await message.channel.send("please enter a valid vote data !cast vote_id your vote")
                return
            fdb.excute("INSERT INTO votes(survery_id,voter_id,vote) VALUES (%s, %s, %s)",int(voteData[1]),message.author.id,voteData[2])
            message.add_reaction('👍')
            channel_id = fdb.excute("SELECT channel_id FROM survery").fetchone()[0]
            channel = client.get_channel(channel_id)
            resultMessage= await channel.fetch_message(voteData[1])
            resultBoard=message = resultMessage.embeds[0]
            resultBoard.description = resultBoard.description +"**Vote**:"+voteData[2]+"\n"
            await resultMessage.edit(embed=resultBoard)
        return

    if message.guild is None:
        print("Detected an attempt to use me outside State Official Server")
    def is_head(message):
        if not message.author.guild_permissions.administrator:
                return False
        return True
   # response = requests.get("http://jarno.pro/stuff/api/ab.php")
    #players = players_info(True)
    if (message.content.lower() == 'klee'):
        await message.channel.send(' Ta-da! Klee is here!')
    ms = message.content
    if (ms.find(':') != -1
            and (ms.find('(SO)') != -1 or ms.find('TEAM') != -1)):
        ms = ms.split(':', 2)[1]
    ms = ms.lstrip()
    if (fdb['status'] == 'default' and message.content.startswith('There')
            and message.author.id == 462940393093201921):
        await client.change_presence(activity=discord.Game(
            name="with " + str(message.content.split('**', 2)[1]) +
            " State Officials"))

    if (message.channel.name != 'civilian-teamsay'):
        if (ms == '!online'):
            tc = client.get_channel(461207618183233557)
            m = client.get_channel(message.channel.id)
            temp = await tc.send('.online')
            await temp.delete()
            s = 1.3
            if (ms != message.content):
                s = 3.3
            await asyncio.sleep(1.3)
            async for msg in tc.history(limit=50):
                if msg.content.startswith('There are '):
                    temp = msg.content.replace('**', '')
                    await msg.delete()
                    if (s == 3.3):
                        await asyncio.sleep(1.3)
                    await message.channel.send(temp)
                    return
    #fdb['dashboard'] = dashboard
    if (message.content.startswith('!logs')):
        if (message.channel.id != 810279347251839026
                and message.channel.name != fdb['dashboard']):  #so-logs
            await message.channel.send(
                'You do not have permission to use this command!')
            return
        if (limiter == True):
            await message.channel.send(
                'there is already an operation on progress')
            return
        limiter = True
        c = 0
        date_str = '0'
        try:
            date_str = message.content.split(' ', 3)[2]
            sp = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            limiter = False
        target = message.content.split(' ', 2)[1]
        if (not message.content.startswith('!logs+')):
            target = message.content.split(' ', 2)[1].lower()
        tc = client.get_channel(462841576616361987)
        delm = await message.channel.send('Gathering data...')
        async for msg in tc.history(limit=None, after=sp):
            if(cancel == True):
              cancel= False
              return
            if (not msg.content.startswith('(TEAM) ')):
                continue
            user = msg.content.split(':', 2)[0].replace("(TEAM) ", '')
            if (not message.content.startswith('!logs+')):
                user = msg.content.split(':', 2)[0].replace("(TEAM) ",
                                                            '').lower()
            print(c)
            if user.find(target) != -1:
                c = c + 1
        await delm.delete()
        output = target + " has " + str(c) + " lines "
        if (not message.content.endswith('x')):
            output = output + message.author.mention + "\n"
        await message.channel.send(output)
        limiter = False
    elif (message.content.startswith('!lines')):
        if (message.channel.id != 810279347251839026
                and message.channel.name != fdb['dashboard']):  #so-logs
            await message.channel.send(
                'You do not have permission to use this command!')
            return
        if (limiter == True):
            await message.channel.send(
                'there is already an operation on progress')
            return
        limiter = True
        c = 0
        date_str = '0'
        try:
            date_str = message.content.split(' ', 3)[2]
            sp = datetime.strptime(date_str, '%Y-%m-%d')
            target = message.content.split(' ', 2)[1]
        except:
            limiter = False
            await message.channel.send('invalid date')
            return
        if (not message.content.startswith('!lines+')):
            target = message.content.split(' ')[1].lower()
        if (target.find(',') != -1):
            target = target.split(',')
        else:
            target = [target]
        for t in target:
            t = t.strip()
            f = open(t + ' ' + date_str + '.txt', 'w+')
            tc = client.get_channel(462841576616361987)
            # 462841576616361987
            delm = await message.channel.send('Gathering data...')
            async for msg in tc.history(limit=None, after=sp):
                if cancel == True:
                  cancel = False
                  return
                if (msg.content.find('(TEAM) ') == -1):
                    continue
                user = msg.content.split(':', 2)[0].replace("(TEAM) ", '')
                if (not message.content.startswith('!lines+')):
                    user = msg.content.split(':', 2)[0].replace("(TEAM) ",
                                                                '').lower()
                print(c)
                if user.find(t) != -1:
                    f.write(str(msg.created_at) + " " + msg.content + '\n')
                    c = c + 1
            output = t + " has " + str(c) + " lines "
            if (not message.content.endswith('x')):
                output = output + message.author.mention + "\n"
            f.close()
            await delm.delete()
            fr = open(t + ' ' + date_str + '.txt', 'r')
            await message.channel.send(output)
            await message.channel.send(file=(discord.File(fr)))
            fr.close()
            os.remove(t + ' ' + date_str + '.txt')
            c = 0
        limiter = False

    elif (message.content.startswith('.say ')):
        if (message.channel.id == 462841576616361987):  #team-chat
            await message.channel.send(
                'You have received a one warning point for using .say command here once your points exceed 2 you will lose your access to this channel the warning points are reset daily but the access cannot be reteived without intervention'
            )
            await client.get_channel(812678973037215754).send(
                message.author.mention + " attempted a forbidden action in " +
                message.channel.name)
            profile = eval(fdb['(*' + str(message.author.id)])
            if (profile['Warns'] >= 2):
                await team_chat_mute(message)
                return
            profile['Warns'] = profile['Warns'] + 1
            fdb['(*' + str(message.author.id)] = str(profile)

            return
        if (message.channel.id != 461207618183233557):  #so-ingame
            await message.channel.send(
                "You don't have permission to use this command")
            return
        m = message.content.replace('.say', '')
        await message.delete()
        await asyncio.sleep(3.3)
        author = ' (' + str(message.author) + ')'
        if fdb['anonymous'] != 'off':
            author = ""
        if (sev != 'special'):
            await message.channel.send("#FFCA33" + author + " : " + str(sev) +
                                       m)
        else:
            if(len(m)+len(author)+3>38):
              return
            print('special')
            color = {
                "blue": "#0000FF",
                "green": "#008000",
                "yellow": "#ffff00",
                "red": "#FF0000",
                "white": "#FFFFFF",
                "black": "#000000",
                "pink": "#ffc0cb",
                "purple": "#8f2eff"
            }
            t = []
            for e in m:
                t.append(e)
            m = t
            counter = 0
            counter2 = 0
            keys = list(color.keys())
            while (counter < len(m)):
                m.insert(counter, color[keys[random.randint(0, 7)]])
                counter = counter + 2
                if (counter2 >= len(color)):
                    counter2 = 0

            out = ''
            for l in m:
                out += l
            m = out
            await message.channel.send("#FFCA33" + author + " : " + m)
    elif message.content =='!average':
      await message.add_reaction('✅')
      statistics = await teamStatistics()
      await message.channel.send('Total messages sent today: '+str(statistics[1])+'\nDetails:'+str(statistics[0])+'\nAverage: '+str(statistics[1]/24)+' message/hour\ncalculated at: '+str(datetime.now())+'\nfirst message sent today: '+statistics[2])
    elif message.content.startswith('!vote'):
        topic = message.content.split(' ',1)[1]
        type=''
        if('=' in topic and topic.split('=')[-2].endswith(' type')):
            type=topic.split('=')[-1]
            topic = topic.rstrip(' type='+type)
        if (type=='anonymous'):
            resultBoard = discord.Embed(title="Votes",
                          description=topic+"\n\n**Received Votes**:\n",
                          color=int("0x" + "FFD700", 16))
            resultBoard.set_thumbnail(url="https://i.imgur.com/dPFkTVw.png")
            resultBoard.set_author(name=message.author.name,icon_url=message.author.avatar_url)
            vote = await message.channel.send(embed=resultBoard)
            fdb.fdb('INSERT INTO survery (id,author,channel_id) VALUES(%s,%s,%s)',message.id,message.author.name,message.channel.id)
            return

        vote = await message.channel.send(topic + "\n" + "***By " + message.author.name + "***")
        if (type==''):
            await vote.add_reaction('👎')
            await vote.add_reaction('👍')
        if (type.isnumeric()):
            numbers ="0\u20e3 1\u20e3 2\u20e3 3\u20e3 4\u20e3 5\u20e3 6\u20e3 7\u20e3 8\u20e3 9\u20e3".split(' ')
            for index in range(int(type)+1):
                print(numbers[index])
                await vote.add_reaction(numbers[index])



    elif (message.content.startswith('!say ')):
        if (message.channel.id == 461207618183233557):  #so in game
            return
        m = message.content.replace('!say ', '', 1)
        await message.delete()
        if (message.channel.id != 462841576616361987):
            await message.channel.send(m)
            return
        author = ' (' + str(message.author) + ')'
        if (fdb['anonymous'] != 'off'):
            author = ''
        await message.channel.send(".say #ffa500" + str(message.author) +
                                   " : #c5f9f4 " + m)

    if (ms.startswith('!rolldice')):
        await message.channel.send(rollDice(ms))
    if (message.content.startswith('!raisemf')):
        await message.channel.send(
            "https://cdn.discordapp.com/attachments/810279347251839026/810286648171429938/81614871ee87f58b9c92813992e7824d_3927207100981871021.png"
        )
    elif (message.content.startswith('!fire1')):
        await message.channel.send(
            "https://safebooru.org//samples/3114/sample_d02e1cd07c1500778456d10eb4989e9801fe6770.jpg?3240692"
        )
    elif (message.content.startswith('!fire3')):
        await message.channel.send(
            "https://images.wallpapersden.com/image/download/klee-red-eyes-genshin-impact_bGlnbmaUmZqaraWkpJRnZWltrWdlaW0.jpg"
        )
    elif (message.content.startswith('!fire2')):
        await message.channel.send(
            "https://img-9gag-fun.9cache.com/photo/aR79LGM_460s.jpg")
    elif (message.content.startswith('!khelp')):
        helpf = open('help.txt', 'r')
        helpl = discord.Embed(title="List of commands",
                              description=helpf.read(),
                              color=int("0x" + "FFD700", 16))
        helpf.close()
        o_msg = await message.channel.send(embed=helpl)
        await o_msg.add_reaction('⬅️')
        await o_msg.add_reaction('➡️')
    elif ms.startswith("!calculate"):
        await message.channel.send(calculate(ms))
    elif message.content.startswith('!activate'):
        await message.channel.send('.dverify 6411481')
    elif message.content.startswith('!money1'):
        await message.channel.send('https://i.imgur.com/u8YIvwR.png')
    elif message.content.startswith('!money2'):
        await message.channel.send(
            'https://cdn.discordapp.com/attachments/589805576171552769/812157150523949066/unknown.png'
        )
    elif message.content.startswith('!stats'):
        stats = online_stats(message.content.split(' ', 1)[1])
        print(stats)
        if stats:
            await message.channel.send(embed=stats)
        else:
          await message.channel.send("Target not found")
    elif message.content.startswith('!grouponline'):
        players = players_info(True)
        target = message.content.split(' ', 2)[1]
        result = ''
        count = 0
        for player in players:
            if (player['gang'] == target):
                count = count + 1
                if (result != ''):
                    result = result + ', '
                result = result + str(player['name'])
        if (result == ''):
            await message.channel.send("Target not found")
        else:
            color = discord.Embed(title=target,
                                  description=target + ' has ' + str(count) +
                                  " online player(s) : " + result + "\n",
                                  color=int("0x" + "D800EE", 16))
            temp = 'https://cit.gg/mike/online/roster.php?group=' + target
            color.set_image(url=temp)
            color.set_thumbnail(
                url='https://cit.gg/mike/online/whoisonlinemap.php?group=' +
                target)  #image in icon_url

            await message.channel.send(embed=color)
    elif message.content.startswith('!reqtitle'):
        userNtitle = message.content.split(' ', 2)
        values = userNtitle[2].split('discord=',1)
        if(not userNtitle[1].isnumeric()):
            await message.channel.send('please enter a valid user id')
            return
        ForumTitles.update(userNtitle[1],*values)
        await message.add_reaction('✅')
    elif message.content.startswith('!squadonline'):
        players = players_info(True)
        target = message.content.split(' ', 2)[1]
        result = ''
        count = 0
        for player in players:
            if (player['squad'] == target):
                count = count + 1
                if (result != ''):
                    result = result + ', '
                result = result + str(player['name'])
        if (result == ''):
            await message.channel.send("Target not found")
        else:
            color = discord.Embed(title=target,
                                  description=target + ' has ' + str(count) +
                                  " online player(s) : " + result + "\n",
                                  color=int("0x" + "D800EE", 16))
            temp = 'https://cit.gg/mike/online/roster.php?squad=' + target
            color.set_image(url=temp)
            color.set_thumbnail(
                url='https://cit.gg/mike/online/whoisonlinemap.php?squad=' +
                target)
            await message.channel.send(embed=color)
    elif message.content.startswith('!unwarn'):
        if (is_head(message) and KEY_R in message.author.roles):
            target = get_id(message.content.split(' ', 1)[1])
            unwarn(target)

    elif ms == ('!players'):
        if (players_info(False) == 1):
            await message.channel.send("There are " + '0' +
                                       " online player(s) in game")
        else:
            await message.channel.send("There are " +
                                       str(players_info(False)) +
                                       " online player(s) in game")
    elif ms == '!criminals':
        count = 0
        for x in players_info(True):
            if (x['team'] == 'Criminals'):
                count = count + 1
        await message.channel.send("There are " + str(count) +
                                   " online criminal player(s) in game")
    elif ms == '!law':
        count = 0
        for x in players_info(True):
            if (x['team'] == 'Police Service'):
                count = count + 1
        await message.channel.send("There are " + str(count) +
                                   " online law player(s) in game")
    elif ms == '!civilians':
        count = 0
        for x in players_info(True):
            if (x['team'] == 'Unoccupied'):
                count = count + 1
        await message.channel.send("There are " + str(count) +
                                   " online civilian player(s) in game")
    elif message.content == '!country':
      country_stats= {}
      for i in players_info(True):
        if not i['country'] in country_stats:
          country_stats[i['country']]=0
        country_stats[i['country']]=country_stats[i['country']]+1
      details = ''
      for key,value in country_stats.items():
        details= details+key+" "+":flag_"+key.lower()+":"+" : "+str(value)+'\n'
        details = details.replace(':flag_N/A:','') if key=='N/A' else details
      embed =discord.Embed(title="country stats",
                              description=details,
                              color=int("0x" + "FFD700", 16))
      await message.channel.send(embed=embed)
        
    elif message.content=='!staff':
      players = players_info(True)
      output=''
      oc =0
      for player in players:
        if player['name'].startswith('[CIT') or player['name'].startswith('[ICM'):
          oc = oc+1
          output=output+" "+player['name']
      await message.channel.send(""+str(oc)+" online staff member(s)/ICM \n"+output)
    elif ms == '!board':
        await message.channel.send('https://cit.gg/index.php?board=471.0')
    elif ms.startswith('!length '):
        text = ms.split(' ', 1)[1]
        characters = len(text)
        words = len(text.split())
        await message.channel.send('Your text has ' + str(words) +
                                   ' words in and ' + str(characters) +
                                   ' characters')
    elif message.content.startswith('!set '):
        ovalue = message.content.split(' ', 2)[1].lower()
        color = {
            "blue": "#0000FF",
            "green": "#008000",
            "yellow": "#ffff00",
            "red": "#FF0000",
            "white": "#FFFFFF",
            "black": "#000000",
            "pink": "#ffc0cb",
            "purple": "#8f2eff",
            "rainbow": "special"
        }
        try:
            value = color[ovalue]
        except KeyError:
            value = None
        if value is None:
            if not ovalue.startswith('#'):
                sev = ''
                await message.channel.send('please use a valid color name')
                return
            else:
                value = ovalue
        await message.channel.send('color has been set successfully to ' +
                                   message.content.split(' ', 2)[1].lower())
        sev = value

    elif message.content == ('!kill'):
        if message.channel.name != fdb['dashboard']:
            return
        else:
            await client.close()
            await message.add_reaction('✅')
    elif message.content == '!restart':
        if message.channel.name != fdb['dashboard']:
            return
        else:
            await message.add_reaction('✅')
            os.execv(sys.executable, ['python'] + sys.argv)
    elif message.content == '!klee':
        await message.channel.send(
            'https://cdn.discordapp.com/attachments/815610760205565952/817041086190977064/ezgif-2-49a8333fb4f2.gif'
        )
    elif message.content == '!server':
        if message.channel.name != fdb['dashboard']:
            return
        else:
            owner = str(message.guild.owner)
        region = str(message.guild.region)
        guild_id = str(message.guild.id)
        memberCount = str(message.guild.member_count)
        icon = str(message.guild.icon_url)
        desc = message.guild.description
        embed = discord.Embed(
        title=message.guild.name + " Server Information",
        description="description:"+str(desc),
        color=int("0x" + "E67E22", 16))
        embed.set_thumbnail(url=icon)
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Server ID", value=guild_id, inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.add_field(name="Member Count", value=memberCount, inline=True)
        await message.channel.send(embed=embed)
    elif ms.startswith('!time'):
        await message.channel.send(getCitTime())
    elif message.content.startswith('!dictionary'):
      keys=''
      for key in fdb.keys():
         if(key.startswith('!')):
            keys = keys+"\n"+key
      parts = split_message(keys)
      for part in parts:
          await message.channel.send(part)
    elif ms.startswith('!learn+'):
        key = ms.split(' ', 1)[1].split('.',1) if ms.find('.')!=-1 else ms.split(' ',1)[1].split(' ')
        if (key[0] in kw or key[0].startswith('!')):
            return
        fdb['~' + key[0] + '~'] = key[1]
        await message.add_reaction('✅')
    elif ms.startswith('!learn '):
        if ms.startswith('(*'):
            return
        key = ''
        value = ''
        try:
            key = '!' + ms.split(' ', 2)[1]
            if (key in kw):
                return
            value = ms.split(' ', 2)[2]
        except:
            print('exception in learning block')
            return
        if (key == ''):
            return
        fdb[key] = value
        await message.add_reaction('✅')
        return
    elif message.content.startswith('!forget'):
        try:
            key = '!' + message.content.split(' ')[1]
            if (message.content.startswith('!forget+')):
                key = '~' + key + '~'
            del fdb[key]
        finally:
            await message.add_reaction('✅')
            return
        return
    elif message.content.startswith("!forgetall*"):
        if (message.channel.name != fdb['dashboard']):
            return
        for key in fdb.keys():
            del fdb[key]
        await message.channel.send('done')
    elif message.content.startswith('!send2gulag'):
        roles_and_id_list = message.author.roles
        roles_and_id_list.append(message.author.id)
        if (not isInACL(message.author,GULAG_ACL)):
            return
        target = get_id(message.content.split(' ', 2)[1])
        target = message.guild.get_member(int(target))
        await target.add_roles(prisoner_R)
        gulag = open('gulag.txt', 'a')
        gulag.write(str(target.id) + ":")
        rs = 0
        try:
            if (EXSO_R in target.roles):
                await target.remove_roles(EXSO_R)
                gulag.write('EXSO')
                rs = rs + 1
            if (guest_R in target.roles):
                await target.remove_roles(guest_R)
                if (rs > 0):
                    gulag.write('+')
                gulag.write('guest')
                rs = rs + 1
            if (SO_R in target.roles):
                await target.remove_roles(SO_R)
                if (rs > 0):
                    gulag.write('+')
                gulag.write('SO')
                rs = rs + 1
            if (TSO_R in target.roles):
                await target.remove_roles(TSO_R)
                if (rs > 0):
                    gulag.write('+')
                gulag.write('TSO')
                rs = rs + 1
            if (HON_R in target.roles):
                await target.remove_roles(HON_R)
                if (rs > 0):
                    gulag.write('+')
                gulag.write('HON')
                rs = rs + 1
            gulag.write(os.linesep)
            if not message.content.endswith('x'):
                await target.send('Welcome to the gulag')
        except:
            print('gulag exception')
        finally:
            gulag.close()
    elif message.content.startswith('!profile'):
        target = id = None
        note = '\n\n For setting up IG-name use !set-ig <name>\nUse !set-ping <name> to set or change the name which will be used to mention you whether ig or discord you can also disable it by using !set-ig disabled if you find it annoying to be mentioned\n '
        if (message.content == '!profile'):
            target = message.author
            id = message.author.id
        else:
            id = get_id(message.content.split(' ', 1)[1])
            target = message.guild.get_member(int(id))
        try:
            fdb['(*' + str(id)]
        except:
            if not create_profile(message, id):
                await message.channel.send('There\'s no such user')
                print('here:' + str(id))
        des = ''
        info = eval(fdb['(*' + str(id)])
        for key in info:
            if key == 'daily':
                continue
            des = des + key + ':' + str(info[key]) + '\n'

        result = discord.Embed(title=target.name,
                               description=des +'\njoined at:'+str(target.joined_at)+'\n'+ note,
                               color=0)
        result.set_thumbnail(url=target.avatar_url)
        await message.channel.send(embed=result)

    elif message.content.startswith('!set-ping'):
        name = message.content.split(' ', 1)[1]
        if ping(name) != '0':
            await message.channel.send(
                'There\'s a user has that ping name already')
            return
        if ('(*' + str(message.author.id)) not in fdb.keys():
            create_profile(message, message.author.id)
        info = fdb['(*' + str(message.author.id)]
        info = eval(info)
        info['PingName'] = name
        fdb['(*' + str(message.author.id)] = str(info)
        await message.add_reaction('✅')
    elif message.content.startswith('!set-ig'):
        name = message.content.split(' ', 1)[1]
        if len(name) > 20 or re.search(
                "#[A-Fa-f0-9]{6}| [^\0-͡͡͡] |\w+\.[A-Za-z]+", name):
            await message.channel.send("Please use a proper name")
            return
        if '(*' + str(message.author.id) not in fdb.keys():
            create_profile(message, message.author.id)
        info = fdb['(*' + str(message.author.id)]
        info = eval(info)
        info['IG-name'] = name
        fdb['(*' + str(message.author.id)] = str(info)
        await message.add_reaction('✅')
    elif message.content.startswith('!rgb2hex'):
        rgb = message.content.split(' ')
        trgb = rgb[1] + ' ' + rgb[2] + ' ' + rgb[3]
        rgb = rgb_to_hex(int(rgb[1]), int(rgb[2]), int(rgb[3]))
        rgb = discord.Embed(title='The hex value of ' + trgb,
                            description=rgb.upper(),
                            color=int("0x" + rgb, 16))
        await message.channel.send(embed=rgb)
    elif message.content.startswith('!spam'):
        if (fdb["spam"] == "off"):
            return
        l = " "
        word = message.content.split(' ', 2)[2]
        times = int(message.content.split(' ', 2)[1])
        print(times)
        if (times > 100):
            await message.channel.send('that is too much')
            return
        for x in range(int(times)):
            if (fdb["spam"] == "off"):
                return
            await message.channel.send(word + l)
    elif ms.startswith('!ping '):
        if (fdb["ping"] == "off"):
            return
        if (message.channel.id == 462841576616361987
                and fdb['team-ping'] == 'off'):
            if (ms.content != message.content):
                return
        target = ''
        try:
            target = ms.split(' ', 2)[1]
            if target == 'disabled':
                return
        except:
            return
        target = ping(target)
        if (not target == '0'):
            await message.channel.send(target)
            return
    elif message.content.startswith('!free'):
        roles_and_id_list = message.author.roles
        roles_and_id_list.append(message.author.id)
        if (
           len ( [ i for i in roles_and_id_list if i in GULAG_ACL]) ==0)  : 
            return
        target = get_id(message.content.split(' ', 1)[1])
        gulag = open('gulag.txt', 'r')
        output = ''
        user = ''
        if (target != 'all'):
            user = message.guild.get_member(int(target))
            await user.remove_roles(prisoner_R)
        for prisoner in gulag:
            pid = prisoner.split(':')[0]
            if (pid == target or target == 'all'):
                roles = prisoner.split(':')[1].split('+')
                if (target == 'all'):
                    user = message.guild.get_member(int(pid))
                    if (prisoner_R in user.roles):
                        await user.remove_roles(prisoner_R)
                    else:
                        continue
                for r in roles:
                    r = r.rstrip(os.linesep)
                    if (r == 'SO'):
                        await user.add_roles(SO_R)
                    if (r == 'TSO'):
                        await user.add_roles(TSO_R)
                    if (r == 'guest'):
                        await user.add_roles(guest_R)
                    if (r == 'EXSO'):
                        await user.add_roles(EXSO_R)
                    if (r == "HON"):
                        await user.add_roles(HON_R)

            else:
                output = output + prisoner
        gulag.close()
        gulag = open('gulag.txt', 'w')
        gulag.write(output)
    elif message.content.startswith('!curse ') or message.content.startswith(
            '!poison'):
        if ( is_head(message) or  isInACL(message.author,CURSE_ACL)):
                pass
        elif (message.content.startswith('!poison')):
            if (random.randint(1, 100) > 25):
                return
        else:
            return
        curse_info = message.content.split(' ', 2)
        p = False
        if (message.content.startswith('!poison')):
            p = True
        target = 0
        em = 0
        if p:
            target = curse_info[1]
            curse_info[1] = 'p'
            if len(curse_info) > 2:
                em = curse_info[2]
                curse_info[2] = target
            else:
                em = ''
                curse_info.append(target)

        curse = open('curse.txt', 'a+')
        curse_info[2] = get_id(curse_info[2])
        curse.write(curse_info[2] + ':' + curse_info[1])
        if (p):
            curse.write('+' + em)
        curse.write(os.linesep)
        if (not p):
            target = await client.fetch_user(curse_info[2])
            await target.send(
                'You have been cursed the only way to remove the curse is to find an exorcist to get rid of it\nhttps://youtu.be/gsZWYqJ2SHs'
            )
        else:
            target = message.guild.get_member(int(curse_info[2]))
            if (discord.utils.get(message.guild.roles, id=747834986010378300)
                    in target.roles):
                await target.remove_roles(
                    discord.utils.get(message.guild.roles,
                                      id=747834986010378300))
                return  #L50
            if (discord.utils.get(message.guild.roles, id=747834651716092025)
                    in target.roles):
                await target.remove_roles(
                    discord.utils.get(message.guild.roles,
                                      id=747834651716092025))
                return  #L40
            if (discord.utils.get(message.guild.roles, id=747834272702005350)
                    in target.roles):
                await target.remove_roles(
                    discord.utils.get(message.guild.roles,
                                      id=747834272702005350))
                return  #30
            if (discord.utils.get(message.guild.roles, id=465804581788712971)
                    in target.roles):
                await target.remove_roles(
                    discord.utils.get(message.guild.roles,
                                      id=465804581788712971))
                return  #L20
            if (discord.utils.get(message.guild.roles, id=465803850406821889)
                    in target.roles):
                await target.remove_roles(
                    discord.utils.get(message.guild.roles,
                                      id=465803850406821889))
                return  #L10
        curse.close()
    elif message.content.startswith('!remove-curse'):
        if (not discord.utils.get(message.guild.roles, name="Exorcist")
                in message.author.roles):
            return
        curse = open('curse.txt', 'r+')
        target = get_id(message.content.split(' ')[1])
        if (target == 'all'):
            curse = open('curse.txt', 'w')
            curse.close()
            await message.channel.send("all curses have been removed")
            return
        output = ''
        for l in curse:
            if (target == l.split(':')[0]):
                continue
            output = output + l
        curse.close()
        curse = open('curse.txt', 'w')
        curse.write(output)
        await message.channel.send("The curse has been removed successfully")
        curse.close()
    elif message.content.startswith('!banTrials'):
        for member in message.guild.members:
            if (message.author.id == member.id):
                continue
            if (member.id == client.user.id):
                continue
            if (TSO_R in member.roles):
                await member.remove_roles(TSO_R)
                await member.add_roles(SO_R)
    elif ms.startswith('!play'):  #Command for MEE6 no need to report it
        return
    elif message.content == '!settings':
        if message.channel.name != fdb['dashboard']:
            await message.channel.send(
                "You do not have permission to use this command")
            return
        listo = ""
        for key in kw:
            value = str(fdb[key])
            listo = listo + key + " : " + value + os.linesep
        info = discord.Embed(title="Bot Settings",
                             description=listo,
                             color=int("0x" + "E67E22", 16))
        await message.channel.send(embed=info)
        with open('settings.txt', 'r') as settingsf:
          description_embed = discord.Embed(title="options description & details",description=settingsf.read(),color=int("0x" + "FFD700", 16))
          await message.channel.send(embed=description_embed)
    elif message.content.startswith('!settings'):
        input = message.content.split(' ', 2)
        if (input[1] not in kw):
            return
        fdb[input[1]] = input[2]
        if (input[1] == 'status'):
            await client.change_presence(activity=discord.Game(
                name=str(input[2])))
        await message.add_reaction('✅')
    elif ms.startswith('!count'):
        threshold = int(ms.split(' ')[1])
        if (threshold > 60):
            return
        for value in range(1, threshold + 1):
            await message.channel.send(value)
            await asyncio.sleep(3.4)
        await message.channel.send("counting is over!")
    elif message.content.startswith('!give-role') or message.content.startswith('!remove-role'):
        if not is_head(message):
            return
        targetNrole = message.content.split(' ', 2)
        if (message.content.startswith("!give")):
            await modifyRole(message, targetNrole[1], targetNrole[2], 1)
        else:
            await modifyRole(message, targetNrole[1], targetNrole[2], 0)
    elif message.content.startswith('!rename'):
        if not is_head(message) and not KEY_R in message.author.roles:
            return
        info = message.content.split(' ', 2)
        info[1] = get_id(info[1])
        target = message.guild.get_member(int(info[1]))
        if info[2].lower() == '*none':
            info[2] = None
        await target.edit(nick=info[2])
    elif ms.startswith('!convert'):
        url = message.content.split(' ',1)[1] 
        temp_file=pytube.YouTube(url).streams.filter(only_audio=True).first().download()
        msg = await discord.utils.get(client.get_all_channels(), id=947925896256434257).send(file=discord.File(temp_file))
        await message.channel.send(msg.attachments[0].url)
        os.remove(temp_file)
      
    elif message.content.startswith('!sing'):
        client.disconent
        voice = await message.author.voice.channel.connect()
    elif message.content == '!prisoners':
        info = ''
        for member in message.guild.members:
            if (prisoner_R in member.roles and member.id != client.user.id):
                info += str(member.nick) + '(' + str(member.name) + ')' + ", "
        await message.channel.send("There are " + str(info.count(",")) +
                                   " prisoners in the gulag :\n" +
                                   info.rstrip(', '))
    elif ms.startswith('!hex2rgb'):
        await message.channel.send(hex_to_rgb(ms.split(' ', 1)[1]))
    elif ms.startswith('!stimer'):
        info = ms.split(' ', 2)
        await message.add_reaction('✅')
        await asyncio.sleep(int(info[1]) * 60)
        await message.reply("time up" if len(info) < 3 else info[2])
    elif message.content == '!updates':
        response = requests.get("https://cit.gg/")
        d = 0
        content = ''
        days = [
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
            'Sunday'
        ]
        for l in response.iter_lines():
            if (d < 5 and str(l).startswith("b'<div class=\"sp_block\">")):
                d = d + 1
            if (d > 5):
                for day in days:
                    if (str(l).lstrip("b'<br />").startswith(day)):
                        d = -1
                        break
            if (d == -1):
                break
            if (d >= 5):
                if (d == 5):
                    l = str(l).replace("b'<div class=\"sp_block\">", '')
                content = content + str(l).strip('\'').strip('b').strip(
                    "'").strip('"').strip('<br />') + '\n'
                d = d + 1
        await message.channel.send('>>> ' + content)

# elif message.content == '!update_profiles':
#   for profile in fdb.keys():
#    if(profile.startswith('(*')):
#   t=  eval(fdb[profile])
#  del t['warns']
#  fdb[profile]=str(t)
# state = fdb[profile].split(',')
# state= state[len(state)-1]
# if not (state.startswith('warn')): fdb[profile]= fdb[profile].rstrip('}')+ ',"warns":0}'
    elif message.content.startswith('!marry'):
        target = int(get_id(message.content.split(' ')[1]))
        if (target == 810188667342553159):
            await message.channel.send(
                'You cannot marry me you truly baka <a:bongo:747346875426013245>'
            )
            return
        marry = open('marry.txt', 'r')
        for l in marry:
            l = l.split(':')
            if (l[0] == str(message.author.id)
                    or str(message.author.id) == l[1].rstrip(os.linesep)):
                await message.channel.send(
                    "You are already married you cannot have another partner!")
                return
            if (l[0] == str(target) or l[1].rstrip(os.linesep) == str(target)):
                await message.channel.send('You cannot marry a married user!')
                return

        def check(ctx):
            if (ctx.author.id == target and ctx.content.lower() == 'yes'):
                return True

        await message.channel.send(
            message.author.mention + " would like to marry you " +
            message.content.split(' ')[1] +
            " say yes if you are willing to spend your entire life with him/her"
        )
        reply = ''
        try:
            reply = await client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await message.add_reaction('❌')
        if (reply):
            marry = open('marry.txt', 'r')
            for l in marry:
                l = l.split(':')
                if (l[0] == str(target)
                        or l[1].rstrip(os.linesep) == str(target)):
                    await message.channel.send(
                        'You cannot marry a married user!')
                    return
            marry = open('marry.txt', 'a')
            temp = str(message.author.id)
            marry.write(temp + ":" + str(target) + ':' +
                        str(message.created_at) + os.linesep)
            marry.close()
            await message.channel.send(message.author.mention + ":yin_yang:" +
                                       message.content.split(' ')[1] +
                                       "\n A new cople has been born :heart:")
    elif message.content == '!partner':
        marry = open('marry.txt', 'r')
        for l in marry:
            l = l.split(':')
            if (l[0] == str(message.author.id)):
                partner = message.guild.get_member(int(l[1]))
                info = discord.Embed(title="Partner",
                                     description='Name:' + partner.name +
                                     os.linesep + 'Marriage date:' + l[2],
                                     color=int("0x" + "FF69B4", 16))
                await message.channel.send(embed=info)
                return

            elif l[1].rstrip(os.linesep) == str(message.author.id):
                partner = message.guild.get_member(int(l[0]))
                info = discord.Embed(title="Partner",
                                     description='Name:' + partner.name +
                                     os.linesep + 'Marriage date:' + l[2],
                                     color=int("0x" + "FF69B4", 16))
                await message.channel.send(embed=info)
                return
        await message.channel.send(
            "You need to get married first in order to view your partner info")
    elif message.content == '!divorce':
        marry = open('marry.txt', 'r+')
        target = str(message.author.id)
        status = False
        output = ''
        for l in marry:

            if (target == l.split(':')[0]
                    or target == l.split(':')[1].rstrip(os.linesep)):
                status = True
                continue
            output = output + l
        marry.close()
        marry = open('marry.txt', 'w')
        marry.write(output)
        if (status):
            await message.channel.send(
                "You have divorced your partner :broken_heart: ")
        else:
            await message.channel.send('You are not married to divorce!')
        marry.close()
    elif message.content == 'tte':
        cit = requests.Session()
        response = cit.get('https://cit.gg/index.php')
        headers = {
            'authority': 'cit.gg',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'origin': 'https://cit.gg',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent':
            'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
            'accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://cit.gg/index.php?action=login',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        params = (('action', 'login2'), )
        token = get_authenticity_token(response.text)
        hash = get_complete_hash('Klee', os.getenv('PASSWORD'), token[1])
        print(hash)
        data = {
            'user': 'Klee',
            'passwrd': '',
            token[0]: token[1],
            'hash_passwrd': hash
        }
        print(cit.cookies.get_dict()['PHPSESSID'])
        cookies = {
            'SMFCookieCIT':
            os.getenv('cookies'),
            'PHPSESSID': cit.cookies.get_dict()['PHPSESSID']
        }
        res = cit.post('https://cit.gg/index.php?action=login2',
                       headers=headers,
                       params=params,
                       data=data,
                       cookies=cookies)
        print("\n \n Done \n")
        test = open('text.txt', 'w')
        test.write(res.text)
        res = cit.get('https://cit.gg/index.php?board=852.0',
                      headers=headers,
                      cookies=cookies)
        test.write(res.text)
    elif message.content == "!err":
      for key in fdb.keys():
        if key=='!/' or key.startswith('__'):
          print("ERROR"+key)
          continue
        print(key)
    elif message.content == '!roster':
        res = connect2forum('https://cit.gg/index.php?topic=131282.0')
        test = open('text.txt', 'w')
        test.write(res)
        soup = BeautifulSoup(res, "html.parser")
        mydiv = soup.find("div", {"class": "windowbg"})
        fr = open('froster.txt', 'w')
        fr.write(mydiv.get_text(separator='\n').strip())
        fr.close()
        fr = open('froster.txt', 'r')
        so_roster =  fr.read().split(
            '˟',1)[1].split(
            '˟')
        fr.seek(
            0
        )  #read() moves the locaiton pointer to EOF apparently discord uses the pointer while uploading the file content so nothing is being sent
        await message.channel.send(file=discord.File(fr))
        r = discord.Embed(title="Roster",
                          description=so_roster[0],
                          color=int("0x" + "E67E22", 16))
        o_msg = await message.channel.send(embed=r)
        await o_msg.add_reaction('⬅️')
        await o_msg.add_reaction('➡️')
        fr.close()
    #elif message.content=='!02!':
    #fdb['apps_notifier']='true'
    elif message.content == '!daily':
        try:
            fdb['(*' + str(message.author.id)]
        except:
            create_profile(message, message.author.id)
        value = random.randint(150, 300)
        current_date = datetime.now().strftime("%d-%m-%y")
        profile = eval(fdb['(*' + str(message.author.id)])
        if (profile['daily'] == current_date):
            await message.channel.send(
                "You've already received your daily cash today stop being greedy!"
            )
            return
        else:
            profile['Balance'] = value + int(profile['Balance'])
            profile['daily'] = current_date
            fdb['(*' + str(message.author.id)] = str(profile)
        await message.channel.send('>>> ' + str(value) +
                                   "$ has been added to your mora account \n" +
                                   "your current balance is " +
                                   str(profile['Balance']) + "$ now")
    elif message.content == '!balance' or message.content == '!bal':
        try:
            fdb['(*' + str(message.author.id)]
        except:
            create_profile(message, message.author)
        bal = eval(fdb['(*' + str(message.author.id)])['Balance']
        await message.channel.send('>>> Your current balance is $' + str(bal))
    elif message.content=='!cancel':
      if (message.channel.id != 810279347251839026):
        cancel = True
        await message.add_reaction('✅')



    elif message.content == '!rich':
        sorted_dic = {}
        for l in fdb.keys():
            if l.startswith('(*'):

                user = eval(fdb[l])
                l = int(l.lstrip("(*"))
                if user['Balance'] in sorted_dic:
                    value =message.guild.get_member(l)
                    if value is None:
                          continue      
                    sorted_dic[user['Balance']].append(value.name)
                else:
                    if message.guild.get_member(l):
                        sorted_dic[user['Balance']] = [
                            message.guild.get_member(l).name
                        ]
        print(sorted_dic)
        content = ''
        for x in sorted(sorted_dic, reverse=True):
            content = content + str(
                sorted_dic[x]).lstrip('[').rstrip(']').replace(
                    '\'', '') + ' : ' + str(x) + '\n' + " "
        await message.channel.send(">>> ★" + content)
        return
    elif message.content.startswith('!op '):
      if not message.author.guild_permissions.administrator:
               return 
      target = int(get_id(message.content.split(' ',1)[1]))
      target = message.guild.get_member(target)
      for channel in message.guild.text_channels:
         await channel.set_permissions(target, read_messages=True,send_messages=True,read_message_history = True)
    elif message.content.startswith('!write '):
      text = message.content.split(" ",1)[1]
      img = Image.open('write_template.jpg')
      I1 = ImageDraw.Draw(img)
      font_size=65
      length= len(text)
      x= 457
      if(length>7):
        x= 381
        font_size=40
        if length>15 and length <42:
          font_size=30
          text=text[:21]+"\n"+text[21:]
        elif length >42:
          font_size= 15
          i=0
          copy = text
          text=''
          while(i<length):
            if i%40 ==0:
              text=text+'\n'
            text=text+copy[i]
            i=i+1
      myFont = ImageFont.truetype('FreeMono.ttf', font_size)
      I1.text((x, 470), text, font=myFont, fill =(255, 0, 0))
      img.save("modified_wt.jpg")
      with open('modified_wt.jpg', 'rb') as f:
        img = discord.File(f)
        await message.channel.send(file=img)
    elif message.content.startswith('!sm '):
        info = message.content.split(' ')
        amount = info[2]
        target = get_id(info[1])
        response = ""
        if (message.author.id != int(target)):
            if not send_mora(str(message.author.id), target, amount):
                response = "You don't have enought money to complete this transaction."
            else:
                response = "The transaction has been done successfully"
        else:
            response = "Something went wrong your transaction information is not correct"
        await message.channel.send(response)
    elif ms == '!discord':
        await message.channel.send(await message.channel.create_invite())
    elif message.content.startswith('!lottery '):
        ticket = message.content.split(' ', 1)[1].strip()
        if (int(ticket) > 10):
            await message.channel.send(
                "The lottery ticket number should be between 1:10")
            return
        if (send_mora(str(message.author.id), '810188667342553159', 50)):
            lottery = open('lottery.txt', 'r')
            for l in lottery:
                if (l.startswith(str(message.author.id))):
                    await message.channel.send(
                        "You have already bought a lottery ticket you cannot buy more than a one"
                    )
                    send_mora('810188667342553159', str(message.author.id), 50)
                    lottery.close()
                    return
        else:
            await message.channel.send(
                "You do not have enough money to buy a lottery ticket")
            return
        lottery = open('lottery.txt', 'a')
        lottery.write(str(message.author.id) + ":" + ticket + os.linesep)
        lottery.close()
        await message.channel.send(
            "You have bought a lottery ticket successfully good luck!")
    elif message.content.startswith('!hot'):
        info = message.content.split(' ')
        source = str(message.author.id)
        target = get_id(info[1])
        if not (info[2].isnumeric()):
            await message.channel.send("Please use a valid value for your bet")
            return
        if (source == target):
            await message.channel.send(
                "You cannot challenge yourself, stupido ")
            return
        if not has_mora(source, info[2]):
            await message.channel.send(
                'You do not have enough money to do this challenge')
            return
        elif not has_mora(target, info[2]):
            await message.channel.send(
                'Your opponent doesn\'t have enough mora to do this challenge')
            return
        value = info[2]
        await message.channel.send(
            info[1] +
            " Choose Head or Tail to accept the challenge if you win you will get $"
            + value + " from " + message.author.mention)
        rep_ly = " "

        def check(ctx):
            if message.author.id == ctx.author.id:
                return
            nonlocal rep_ly
            if (str(ctx.author.id) == target):
                if (ctx.content.lower().strip() == "head"):
                    rep_ly = "head"
                    return True
                elif (ctx.content.lower().strip() == "tail"):
                    rep_ly = "tail"
                    return True

        try:
            reply = await client.wait_for("message", check=check, timeout=60)
        except:
            message.add_reaction('❌')
        answer = random.randint(1, 2)
        temp = await message.channel.send("Tossing the coin..")
        await asyncio.sleep(3)
        await temp.delete()
        print('the reply is ' + str(reply) + " result =" + str(answer))
        if (answer == 1):
            answer = "head"
        else:
            answer = "tail"
        if (message.content.startswith('!hot.')):
            rep_ly = ''
        if (rep_ly == answer):
            result = "it's a " + answer + "\n" + info[1] + " has won the game"
            send_mora(source, target, value)
        else:
            result = "it's a " + answer + "\n" + message.author.mention + " has won the game"
            send_mora(target, source, value)
        await message.channel.send(result)
    elif message.content.startswith('!kmute'):
        if not is_head(message) and not KEY_R in message.author.roles:
            return
        target = message.guild.get_member(
            int(get_id(message.content.split(' ', 1)[1])))
        await message.channel.set_permissions(target, send_messages=False)
    elif message.content.startswith('!kunmute'):
        if not is_head(message) and not KEY_R in message.author.roles:
            return
        target = message.guild.get_member(
            int(get_id(message.content.split(' ', 1)[1])))
        await message.channel.set_permissions(target, overwrite=None)
    elif message.channel.id == 461207618183233557 and '~' + ms + '~' in fdb.keys(
    ):
        await message.channel.send(fdb['~' + ms + '~'])
    elif ms.startswith('!translate'):
        tsrc = ms.split(' ', 1)[1]
        tlanguage = 'en'
        if (tsrc.startswith('*')):
            tsrc = tsrc.split(' ', 1)
            tlanguage = tsrc[0].strip('*')
            tsrc = tsrc[1]
        await message.channel.send(ts.google(tsrc, to_language=tlanguage))
    elif message.content.startswith('!notify'):
        targets = message.content.split(' ', 1)[1].split(',')
        ss = 'Subscribed Successfully, you will be notified in your dm if the target(s) online'
        for target in targets:
            target = target.strip()
            if (' (' + target) in fdb.keys():
                if str(message.author.id) not in fdb[' (' + target].split(','):
                    fdb[' (' + target] = fdb[' (' + target] + ',' + str(
                        message.author.id)
                else:
                    ss = 'You cannot subscribe to the nofication of a user you\'re already subscribed too!'
                    break
            else:
                fdb[' (' + target] = str(message.author.id) + ','
        await message.channel.send(ss)
    elif message.content.startswith('!unnotify'):
        targets = message.content.split(' ', 1)[1].split(',')
        ss = 'target not found'
        for target in targets:
            target = target.strip()
            if (' (' + target) in fdb.keys():
                fdb[' (' + target] = fdb[' (' + target].replace(
                    str(message.author.id) + ',', '')
                ss = "You have removed your subscription successfully"
        await message.channel.send(ss)

    elif ms.startswith('!'):
        if ms != message.content and message.channel.id != 461207618183233557:
            return
        try:
            verify = ' '
            if ' ' in message.content:
                verify = message.content.split(' ', 1)[1]
            say = ""
            if message.channel.id == 462841576616361987 and verify != '+' and fdb['teamchat-commands']:
                say = ".say "
            await message.channel.send(say + str(fdb[ms]))
        except:
            print('reporting unexisting entity ' + ms)
        finally:
            return
    elif message.channel.id == 462841576616361987 and message.author.id != 463528533143060491 and fdb[
            'team-auto'] != 'off' and message.author.id != 403112358630916096:  #team-say, not the bot/webhook and the option enabled
        author = message.author.id
        profile = None
        try:
            profile = eval(fdb['(*' + str(author)])
            if (profile['IG-name'] == '(Required for team chat access)'):
                raise Exception
        except:
            await message.channel.send(
                "Please confirm your ig-name to access this feature you can confirm it via !set-ig <name> "
            )
            return

        if (len(profile['IG-name']) < 3):
            return
        if (message.content.startswith('.')):
            return
        if (re.search("#[A-Fa-f0-9]{6}| [^\0-͡͡͡] |\w+\.[A-Za-z]+",
                      message.content) or profile['Warns'] >= 2):
            await team_chat_mute(message)
            return
        async with lock:
          if (fdb['anonymous'] != 'off'):
              author = ''
          rank = '#ffffff'
          for r in SO_Roles:
              if (r in message.author.roles):
                  rank = '#ffa500'
                  break
          await message.channel.send(".say " + rank + profile['IG-name'] +
                                   " : #c5f9f4 " + message.content)
          await asyncio.sleep(3.5)


@client.event
async def on_reaction_add(reaction, user):
    await dynamic_help(reaction, user)
    await dynamic_roster(reaction, user)


@client.event
async def on_reaction_remove(reaction, user):
    await dynamic_help(reaction, user)
    await dynamic_roster(reaction, user)


@client.event
async def on_member_join(member):
    tc = discord.utils.get(SO_SERVER.channels,name=fdb['wm'])
    await tc.send('Welcome to our server ' + member.mention)


@client.event
async def on_member_remove(member):
    tc = discord.utils.get(SO_SERVER.channels,name=fdb['wm'])
    await tc.send('Bye bye ' + member.name + ', you will be missed.')
keep_alive()
client.run(os.getenv('TOKEN'))
