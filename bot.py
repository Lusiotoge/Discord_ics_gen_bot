import discord
from discord.ext import commands
from discord import app_commands
from icalendar import Calendar, Event
from datetime import datetime
from io import BytesIO
import urllib.parse
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")  # 環境変数から取得

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="create_event", description="予定を作成してICSを生成")
@app_commands.describe(
    title="予定のタイトル",
    date="日付 (YYYY-MM-DD)",
    start_time="開始時間 (HH:MM)",
    end_time="終了時間 (HH:MM)"
)
async def create_event(interaction: discord.Interaction, title: str, date: str, start_time: str, end_time: str):
    try:
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message("日付または時間の形式が間違っています。YYYY-MM-DD と HH:MM で入力してください。", ephemeral=True)
        return

    # ICS 作成
    cal = Calendar()
    event = Event()
    event.add("summary", title)
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    cal.add_component(event)

    ics_bytes = BytesIO(cal.to_ical())

    # Google Calendar リンク作成
    gcal_url = (
        "https://calendar.google.com/calendar/r/eventedit?"
        f"text={urllib.parse.quote(title)}&"
        f"dates={start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    )

    await interaction.response.send_message(
        f"予定を作成しました！\n[Google カレンダーに追加]({gcal_url})",
        file=discord.File(ics_bytes, filename=f"{title}.ics")
    )

bot.run(TOKEN)