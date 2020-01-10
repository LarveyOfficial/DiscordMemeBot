import pymongo
import asyncio
import Config
import discord
from discord.ext import commands
import logging
import traceback
import praw, requests, re, random, datetime, os, http.client
from prawcore import NotFound

reddit = None
global thesubreddit
global fileend

bot = commands.Bot(command_prefix = "m!", case_insensitive = True)
helpstring = "**De Commands**\n`m!awww` - Random Picture of a Dog/Corgi\n`m!addsub <SubReddit>` - add a SubReddit to your list of SubReddits\n`m!mysubs` - List your SubReddits\n`m!removesub <Subreddit>` - Remove a SubReddit from your list\n`m!image` - Get an image from your list of SubReddits\n`m!purge` - Clears your subreddit list"
version = "a0.0.1"
bot.remove_command("help")

def loginReddit():
    print("Logging into Reddit...")
    global reddit
    reddit = praw.Reddit(client_id = "KXv0ye2WvvyJiw",
                         client_secret = "1xva_JgZ_3Sp46OqROWIFUmxaa8",
                         user_agent = "http://127.0.0.1:65010/authorize_callback")
    print("Logged into Reddit as read only user.")


def getPhotoFromReddit(sub):
    global reddit
    global thesubreddit
    global fileend
    print("Getting an image...")
    submissions = reddit.subreddit(sub).hot(limit = 100)
    i = random.randint(0, 100)
    print("Randomly chose " + str(i))
    for submission in submissions:
        i -= 1
        if i <= 0:
            print("Picked " + submission.url)
            strong = str(submission.url)
            if strong[-4:] == ".gif":
                fileend = ".gif"
            else:
                fileend = ".jpg"
            thesubreddit = str(submission.subreddit)
            return submission.url

def download_from_url(path, url):
    print("Downloading image...")
    with open(path, "wb") as handle:
        response = requests.get(url, stream = True)

        if not response.ok:
            print("Response good you bitch.")

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)
        print("Image downloaded.")


@bot.command(aliases = ["subremove", "deletesub", "subdelete"])
async def removesub(ctx, *, sub : str=None):
    if sub is None:
        embed = discord.Embed(
            title = "ERROR",
            description = "Please provide a subreddit",
            color = 0xED4337
        )
        await ctx.send(embed = embed)
    else:
        the_user = Config.USERS.find_one({'user_id' : ctx.author.id})
        if the_user == None:
            Config.USERS.insert_one({"user_id" : ctx.author.id, subs : []})
            embed = discord.Embed(
                title = "Subreddits",
                description = "You don't have any subreddits\n use m!addsub <SubReddit> to add a SubReddit",
                color = 0xED4337
            )
            await ctx.send(embed = embed)
        else:
            Config.USERS.update_one({"user_id": ctx.author.id}, { "$pull" : { "subs" : sub } } )
            embed = discord.Embed(
                title = "Subreddits",
                description = "Deleted the SubReddit `" + sub + "` from your subreddit list.",
                color = 0xE1306C
            )
            await ctx.send(embed = embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title = "Help",
        description = helpstring,
        color = 0xE1306C
    )
    embed.set_footer(text = version)
    await ctx.send(embed = embed)

@bot.command(aliases = ["sublist", "subs"])
async def mysubs(ctx):
    if Config.USERS.find_one({'user_id': ctx.author.id}) == None:
        Config.USERS.insert_one({"user_id" : ctx.author.id, "subs" : None})
        embed = discord.Embed(
            title = "Subreddits",
            description = "You don't have any subreddits\n use m!addsub <SubReddit> to add a SubReddit",
            color = 0xE1306C
        )
        await ctx.send(embed = embed)
    else:
        the_doc = Config.USERS.find_one({'user_id': ctx.author.id})
        newstring = ""
        array = the_doc["subs"]
        if array != None:
            for ele in array:
                newstring += ele + "\n"
            embed = discord.Embed(
                title = "Subreddits",
                description = "You Subreddits:\n" + newstring,
                color = 0xE1306C
            )
        else:
            embed = discord.Embed(
                title = "Subreddits",
                description = "You don't have any subreddits\n use m!addsub <SubReddit> to add a SubReddit",
                color = 0xE1306C
            )
        await ctx.send(embed = embed)

@bot.command()
async def purge(ctx):
    embed = discord.Embed(
        title = "WARNING",
        description = "Are you sure you want to remove all your SubReddits?",
        color = 0xE1306C
    )
    msg = await ctx.send(embed = embed)
    await msg.add_reaction("🚫")
    await msg.add_reaction("✅")
    while True:
        reaction, reactor = await bot.wait_for("reaction_add")
        if reactor.id is ctx.author.id:
            if reaction.emoji == "🚫":
                embed = discord.Embed(
                title = "Purge Confirmation",
                description = "Canceled Account Purge",
                color = 0xE1306C
                )
                await ctx.send(embed = embed)
                await msg.delete()
                return
            elif reaction.emoji =="✅":
                total = 0
                the_doc = Config.USERS.find_one({"user_id" : ctx.author.id})
                for sub in the_doc['subs']:
                    Config.USERS.update_one({"user_id": ctx.author.id}, { "$pull" : { "subs" : sub } } )
                    total += 1
                embed = discord.Embed(
                title = "Purge Confirmation",
                description = "Succesfully purged: " + str(total) + " SubReddit(s) from your Account!",
                color = 0xE1306C
                )
                await ctx.send(embed = embed)
                await msg.delete()
                return


@bot.command(aliases = ["subadd"])
async def addsub(ctx, *, subreddit :str=None):
    loginReddit()
    if subreddit is None:
        embed = discord.Embed(
            title = "ERROR",
            description = "Please provide a subreddit",
            color = 0xED4337
        )
        await ctx.send(embed = embed)
    else:
        if Config.USERS.find_one({'user_id': ctx.author.id}) == None:
            Config.USERS.insert_one({"user_id" : ctx.author.id, "subs" : None})
        exists = True
        try:
            reddit.subreddits.search_by_name(subreddit, exact = True)
        except NotFound:
            exists = False
        if exists:
            nono = 0
            the_doc = Config.USERS.find_one({'user_id': ctx.author.id})
            currentlist = the_doc['subs']
            if currentlist == None:
                Config.USERS.update_one({"user_id" : ctx.author.id}, {"$set": {"subs" : [subreddit]}})
                embed = discord.Embed(
                    title = "Added Subreddit",
                    description = "Subreddit `" + subreddit + "` Added to your profile!",
                    color = 0xE1306C
                )
                await ctx.send(embed = embed)
            else:
                for ele in the_doc['subs']:
                    if ele == subreddit:
                        nono += 1

                if nono == 0:
                    Config.USERS.update_one({"user_id" : ctx.author.id}, {"$push": {"subs" : subreddit}})
                    embed = discord.Embed(
                        title = "Added Subreddit",
                        description = "Subreddit `" + subreddit + "` Added to your profile!",
                        color = 0xE1306C
                    )
                    await ctx.send(embed = embed)
                else:
                    embed = discord.Embed(
                        title = "SubReddit",
                        description = "You already have that SubReddit Added",
                        color = 0xED4337
                    )
                    await ctx.send(embed = embed)
        else:
            embed = discord.Embed(
                title = "ERROR",
                description = "That Subreddit dosen't Exist",
                color = 0xED4337
            )
            await ctx.send(embed = embed)


@bot.command(aliases = ["meme"])
async def image(ctx):
    global fileend
    msg = await ctx.send("Loading....")
    loginReddit()
    the_doc = Config.USERS.find_one({'user_id': ctx.author.id})
    array = the_doc['subs']
    str = ""
    for ele in array:
        str += ele + "+"
    if str[len(str) - 1 : ] == "+":
        ready = str[ : len(str) - 1]

    the_meme = getPhotoFromReddit(ready)
    thefile = f"{ctx.author.id}{fileend}"
    download_from_url(thefile, the_meme)
    embed = discord.Embed(
    title = thesubreddit,
    url = the_meme,
    timestamp = datetime.datetime.utcnow(),
    color = 0xE1306C
    )
    file = discord.File(thefile, filename = thefile)
    embed.set_image(url = "attachment://" + thefile)
    await msg.delete()
    try:
        await ctx.send(embed = embed, file = file)
    except:
        embed = discord.Embed(
            title = "ERROR",
            description = "An Unknown Error has occured, Please Try Again",
            color = 0xED4337
        )
        await ctx.send(embed = embed)
    os.remove(thefile)

@bot.command(aliases = ["aw", "aww", "awwww"])
async def awww(ctx):
    msg = await ctx.send("Loading....")
    loginReddit()
    the_meme = getPhotoFromReddit("corgi+dogpictures")
    thefile = str(ctx.author.id) + fileend
    download_from_url(thefile, the_meme)
    embed = discord.Embed(
    title = thesubreddit,
    url = the_meme,
    timestamp = datetime.datetime.utcnow(),
    color = 0xE1306C
    )
    file = discord.File(thefile, filename = thefile)
    embed.set_image(url = "attachment://" + thefile)
    await msg.delete()
    try:
        await ctx.send(embed = embed, file = file)
    except:
        embed = discord.Embed(
            title = "ERROR",
            description = "An Unknown Error has occured, Please Try Again",
            color = 0xED4337
        )
        await ctx.send(embed = embed)
    os.remove(thefile)

@bot.event
async def on_ready():
    print(f"Bot has started succesfully in {len(bot.guilds)} server(s) with {len(bot.users)} users!")
    await bot.change_presence(activity = discord.Activity(type=discord.ActivityType.watching, name="Memes"))

bot.run(Config.TOKEN)
