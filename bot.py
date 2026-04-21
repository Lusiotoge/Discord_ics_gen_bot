import discord
from discord.ext import commands
from discord import app_commands
from icalendar import Calendar, Event
from datetime import datetime, timezone, timedelta
from io import BytesIO
import urllib.parse
import os

from dotenv import load_dotenv
load_dotenv()

# ===== TOKEN =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise Exception("DISCORD_BOT_TOKEN が設定されていません")

# ===== INTENTS =====
intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== JST =====
JST = timezone(timedelta(hours=9))


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
    end_time="終了時間 (HH:MM)",
    description="説明（任意）"
)
async def create_event(
    interaction: discord.Interaction,
    title: str,
    date: str,
    start_time: str,
    end_time: str,
    description: str = ""
):
    try:
        start_dt = datetime.strptime(
            f"{date} {start_time}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=JST)

        end_dt = datetime.strptime(
            f"{date} {end_time}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=JST)

    except ValueError:
        await interaction.response.send_message(
            "日付または時間の形式が間違っています。YYYY-MM-DD と HH:MM で入力してください。",
            ephemeral=True
        )
        return

    # ===== ICS作成 =====
    cal = Calendar()
    event = Event()

    event.add("summary", title)
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    if description:
        event.add("description", description)

    cal.add_component(event)

    ics_bytes = BytesIO(cal.to_ical())

    # ===== Google Calendarリンク =====
    gcal_url = (
        "https://calendar.google.com/calendar/r/eventedit?"
        f"text={urllib.parse.quote(title)}&"
        f"details={urllib.parse.quote(description) if description else ''}&"
        f"dates={start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    )

    # ===== 安全ファイル名 =====
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_")).strip()
    file_name = f"{safe_title}.ics"

    embed = discord.Embed(
        title="予定を作成しました",
        description=f"**{title}**",
        color=0x00ffcc
    )

    embed.add_field(
        name="開始",
        value=start_dt.strftime("%Y-%m-%d %H:%M"),
        inline=True
    )

    embed.add_field(
        name="終了",
        value=end_dt.strftime("%Y-%m-%d %H:%M"),
        inline=True
    )

    if description:
        embed.add_field(
            name="説明",
            value=description,
            inline=False
        )

    embed.add_field(
        name="Googleカレンダー",
        value=f"[開く]({gcal_url})",
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        file=discord.File(ics_bytes, filename=file_name)
    )

bot.run(TOKEN)