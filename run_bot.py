import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import date
import pp_calc as pp
import user_data
import lazer_data
import asyncio
from asyncio import create_task
from dotenv import load_dotenv
from form import InputModal
from beatmap_manager import BeatmapManager

# Load the saved state of the BeatmapManager from a JSON file
manager = BeatmapManager.load_state("beatmap_data.json")
max_directory_size = 5000 * 1024 * 1024  # 5000MB in Bytes

# Load environment variables from a .env file
load_dotenv()

active_messages = {}

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready.
    Initializes the BeatmapManager and loads user data.
    """
    global manager
    main_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(main_path, "mapfolder")
    manager.base_directory = folder_path
    manager.max_directory_size = max_directory_size
    os.makedirs(manager.base_directory, exist_ok=True)
    pp.set_manager(manager)
    user_data.load_osu_user_data()
    lazer_data.load_user_lazer_data()
    print(f"We have logged in as {bot.user}")

@bot.command()
async def help(ctx):
    """
    Sends an embed with a list of available commands.
    """
    embed = discord.Embed(
        title="",
        color=discord.Color.blue()
    )
    embed.set_author(name="Command List", icon_url="https://imgur.com/gxnfAWO.png")
    embed.description = (
        "**!setuser** - Sets osu username for a discord account\n"
        "**!getuser** - Checks osu username for a discord account\n"
        "**!setplaymode** - Sets osu playmode **(Standard or Lazer)**\n"
        "**!getplaymode** - Checks osu playmode for a discord account\n"
        "**!rs -** Checks recently played beatmap score"
    )

    await ctx.send(embed=embed)

@bot.command()
async def setuser(ctx, value: str = None):
    """
    Sets the osu username for the discord user.
    """
    discord_user_id = str(ctx.author.id)
    osu_user_id = pp.get_user(value)
    if not osu_user_id == None:
        user_data.set_osu_user(discord_user_id, osu_user_id)
        await ctx.send(f"**Your osu username has been set to {value}.**")
    else:
        await ctx.send(f"**Osu user was not found, please try again**")

@bot.command()
async def getuser(ctx):
    """
    Retrieves the osu username for the discord user.
    """
    discord_user_id = str(ctx.author.id)
    osu_user_id = user_data.get_osu_user(discord_user_id)
    if not osu_user_id == None:
        username = pp.get_username(osu_user_id)
        await ctx.send(f"**Your osu username is set to {username[0]}**")
    else:
        await ctx.send(f"**User not found, did u set your username correctly?**")

@bot.command()
async def setplaymode(ctx, value:str = None):
    """
    Sets the preferred osu playmode (Standard or Lazer) for the discord user.
    """
    discord_user_id = str(ctx.author.id)
    if not value == None:
        if "lazer" in value.lower():
            playmode = "Lazer"
            lazer_data.set_user_lazer(discord_user_id,playmode)
        elif "standard" in value.lower():
            playmode = "Standard"
            lazer_data.set_user_lazer(discord_user_id,playmode)
        else:
            await ctx.send("**Please select a valid playmode (Lazer or Standard)**")
            return
    else:
        await ctx.send("**Please select a valid playmode (Lazer or Standard)**")
        return

    await ctx.send(f"**Your prefered osu playmode has been set to {playmode}**")

@bot.command()
async def getplaymode(ctx):
    """
    Retrieves the preferred osu playmode for the discord user.
    """
    discord_user_id = str(ctx.author.id)
    playmode = lazer_data.get_user_lazer(discord_user_id)
    if not playmode == None:
        await ctx.send(f"**Your prefered osu playmode is {playmode}**")
    else:
        await ctx.send(f"**You didn't set your prefered playmode yet**")

async def get_map_data(osu_user_id, user, playmode, position, lazer, on_download_start, on_download_fail):
    """
    Retrieves data for the most recent osu play for the specified user.
    """
    recent = pp.get_recent_activity(osu_user_id, 10)
    if recent[1] == 0:
        return None

    score = pp.get_recent_score(recent[0], position)
    beatmap = pp.get_beatmap(recent[0], position)

    full_title = f'{beatmap[2]} [{beatmap[1]}]'
    beatmap_file = await pp.map_download(beatmap, on_download_start, on_download_fail)
    try:
        calc_result = pp.calc_lazer_pp(
            beatmap_file, score[0], score[1], score[2], score[3], score[4], score[5],
            score[6], score[9], score[10], score[11], lazer
        )
    except:
        return

    accuracy = format(score[0] * 100, ".2f")
    n300 = score[1] or 0
    n100 = score[2] or 0
    n50 = score[3] or 0
    misses = score[4] or 0

    map_data = {
        "player": f'{user[0]}',
        "map": f"{full_title} +{calc_result[4]} [{calc_result[2]}★]",
        "result": f"**▸** **{score[7]}** **▸** **{score[8]}PP** ({calc_result[0]}PP for {calc_result[1]}% FC) **▸** {accuracy}%",
        "score_details": f"**▸** x{score[5]}/{calc_result[3]} **▸**  [{n300}/{n100}/{n50}/{misses}]",
        "server": f"osu! {playmode}",
        "user_url": f"{user[1]}",
        "image_url": f"{beatmap[3]}",
        "image_osu_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Osu%21_Logo_2016.svg/512px-Osu%21_Logo_2016.svg.png"
    }
    return map_data, recent

@bot.command()
async def rs(ctx):
    """
    Retrieves and displays the most recent osu play for the discord user.
    """
    current_position = [1]

    async def on_download_start():
        await ctx.send("**Map seen for the first time, please wait**")

    async def on_download_fail():
        await ctx.send("**There has been an unknown error while downloading the map**")

    async def on_input_submit(interaction: discord.Interaction, value):
        current_position[0] = value
        await update_embed(interaction)
        await button_check(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def button_check(interaction: discord.Interaction):
        """
        Updates the state of the navigation buttons based on the current position.
        """
        if current_position[0] == 1:
            button_max_left.disabled = True
            button_left.disabled = True
            button_max_right.disabled = False
            button_right.disabled = False
        elif current_position[0] == map_data[1][1]:
            button_max_right.disabled = True
            button_right.disabled = True
            button_max_left.disabled = False
            button_left.disabled = False
        else:
            button_max_right.disabled = False
            button_right.disabled = False
            button_max_left.disabled = False
            button_left.disabled = False

        await start_timer(interaction.message.id)
        if interaction.response.is_done():
            await interaction.followup.edit_message(interaction.message.id, view=view)
        else:
            await interaction.response.edit_message(view=view)

    async def input_callback(interaction: discord.Interaction):
        """
        Moves to the position based on the input modal submission.
        """
        modal = InputModal((map_data[1][1]), discord.Interaction, on_input_submit)
        await interaction.response.send_modal(modal)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def max_left_callback(interaction: discord.Interaction):
        """
        Moves to the first position in the recent plays list.
        """
        current_position[0] = 1
        await button_check(interaction)
        await update_embed(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def left_callback(interaction: discord.Interaction):
        """
        Moves to the previous position in the recent plays list.
        """
        current_position[0] -= 1
        await button_check(interaction)
        await update_embed(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def max_right_callback(interaction: discord.Interaction):
        """
        Moves to the last position in the recent plays list.
        """
        current_position[0] =map_data[1][1]
        await button_check(interaction)
        await update_embed(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def right_callback(interaction: discord.Interaction):
        """
        Moves to the next position in the recent plays list.
        """
        current_position[0] += 1
        await button_check(interaction)
        await update_embed(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def update_embed(interaction: discord.Interaction):
        """
        Updates the embed with the data for the current position.
        """
        try:
            map_data = await get_map_data(osu_user_id, user, playmode, current_position[0] - 1, lazer, on_download_start, on_download_fail)
            if not map_data:
                if not interaction.response.is_done():
                    await interaction.response.send_message("**Invalid position. No data available.**", ephemeral=True)
                else:
                    await interaction.followup.send("**Invalid position. No data available.**", ephemeral=True)
                return
        except:
            return

        embed = discord.Embed(
            title="",
            color=discord.Color.blue()
        )
        embed.set_author(name=map_data[0]['map'], icon_url=map_data[0]['user_url'])
        embed.description = (
            f"{map_data[0]['result']}\n"
            f"{map_data[0]['score_details']}"
        )
        embed.set_footer(text=f"{map_data[0]['server']}  •  {date.today()}", icon_url=map_data[0]['image_osu_url'])
        embed.set_thumbnail(url=map_data[0]['image_url'])

        if interaction.response.is_done():
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=view)

    async def start_timer(message_id):
        """
        Starts a timer to remove the view after a period of inactivity.
        """
        if message_id in active_messages:
            active_messages[message_id].cancel()

        async def timer_task():
            try:
                await asyncio.sleep(15)
                if message_id in active_messages:
                    await message.edit(view=None)
                    del active_messages[message_id]
            except asyncio.CancelledError:
                pass

        active_messages[message_id] = create_task(timer_task())

    for task in list(active_messages.values()):
        task.cancel()
    active_messages.clear()

    discord_user_id = str(ctx.author.id)
    osu_user_id = user_data.get_osu_user(discord_user_id)
    if osu_user_id:
        user = pp.get_username(osu_user_id)
        if user == None:
            await ctx.send("**User not found, did u set your username correctly?**")
            return
    else:
        await ctx.send("**User not found, did u set your username correctly?**")
        return

    playmode = lazer_data.get_user_lazer(discord_user_id)
    if playmode == None:
        playmode = "Standard"
        lazer = False
    elif playmode == "Standard":
        lazer = False
    else:
        lazer = True

    try:
        map_data = await get_map_data(osu_user_id, user, playmode, 0, lazer, on_download_start, on_download_fail)

        # Create the embed
        embed = discord.Embed(
            title="",
            color=discord.Color.blue()
        )
        embed.set_author(name=map_data[0]['map'], icon_url=map_data[0]['user_url'])
        embed.description = (
            f"{map_data[0]['result']}\n"
            f"{map_data[0]['score_details']}"
        )
        embed.set_footer(text=f"{map_data[0]['server']}  •  {date.today()}", icon_url=map_data[0]['image_osu_url'])
        embed.set_thumbnail(url=map_data[0]['image_url'])
    except:
        result = False
        return

    # Create navigation buttons
    button_max_left = Button(label="◂◂", style=discord.ButtonStyle.secondary)
    button_left = Button(label="◂", style=discord.ButtonStyle.secondary)
    button_input = Button(label="✱", style=discord.ButtonStyle.secondary)
    button_right = Button(label="▸", style=discord.ButtonStyle.secondary)
    button_max_right = Button(label="▸▸", style=discord.ButtonStyle.secondary)

    button_max_left.disabled = True
    button_left.disabled = True

    if map_data[1][1] == 1:
        button_max_right.disabled = True
        button_right.disabled = True

    button_max_left.callback = max_left_callback
    button_left.callback = left_callback
    button_input.callback = input_callback
    button_right.callback = right_callback
    button_max_right.callback = max_right_callback

    view = View()
    view.add_item(button_max_left)
    view.add_item(button_left)
    view.add_item(button_input)
    view.add_item(button_right)
    view.add_item(button_max_right)

    message = await ctx.send(f"**Recent osu! {playmode} Play for {user[0]}:**", embed=embed, view=view)

    await start_timer(message.id)

# Run the bot with the token from the environment variables
bot.run(os.getenv("DISCORD_TOKEN"))
