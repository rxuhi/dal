import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TOKEN = "봇토큰"

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =========================
# 역할 ID
# =========================

SOLO_ROLE_ID = 1111111111111
COUPLE_ROLE_ID = 2222222222222
MARRIAGE_ROLE_ID = 3333333333333

# =========================
# 데이터 저장
# =========================

DATA_FILE = "couples.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        couples = json.load(f)
else:
    couples = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(couples, f, ensure_ascii=False, indent=4)

# =========================
# 역할 처리
# =========================

async def update_roles(guild, user1, user2, type_, remove=False):

    solo_role = guild.get_role(SOLO_ROLE_ID)
    couple_role = guild.get_role(COUPLE_ROLE_ID)
    marriage_role = guild.get_role(MARRIAGE_ROLE_ID)

    target_role = marriage_role if type_ == "우결" else couple_role

    for member in [user1, user2]:

        if remove:

            if target_role in member.roles:
                await member.remove_roles(target_role)

            if solo_role not in member.roles:
                await member.add_roles(solo_role)

        else:

            if solo_role in member.roles:
                await member.remove_roles(solo_role)

            if target_role not in member.roles:
                await member.add_roles(target_role)

# =========================
# 관계 생성 함수
# =========================

async def create_love(
    interaction,
    type_,
    user1,
    user2,
    start_date,
    message_text
):

    if user1.bot or user2.bot:
        await interaction.response.send_message(
            "❌ 봇은 선택할 수 없습니다.",
            ephemeral=True
        )
        return

    if user1.id == user2.id:
        await interaction.response.send_message(
            "❌ 자기 자신과는 불가능합니다.",
            ephemeral=True
        )
        return

    gid = str(interaction.guild.id)

    if gid not in couples:
        couples[gid] = {}

    # 이미 관계중인지 검사
    for data in couples[gid].values():

        if user1.id in [data["user1"], data["user2"]]:
            await interaction.response.send_message(
                f"❌ {user1.mention} 님은 이미 관계 중입니다.",
                ephemeral=True
            )
            return

        if user2.id in [data["user1"], data["user2"]]:
            await interaction.response.send_message(
                f"❌ {user2.mention} 님은 이미 관계 중입니다.",
                ephemeral=True
            )
            return

    # 날짜 처리
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            await interaction.response.send_message(
                "❌ 날짜 형식은 YYYY-MM-DD 입니다.",
                ephemeral=True
            )
            return
    else:
        start = datetime.now()

    today = datetime.now()

    days = (today - start).days + 1

    embed = discord.Embed(
        title=f"💖 {type_} 탄생!",
        color=discord.Color.pink()
    )

    embed.description = (
        f"({start.strftime('%Y-%m-%d')} ~ X / {days}일째)\n\n"
        f"{user1.mention} 💗 {user2.mention}\n\n"
        f"💬 한마디 : {message_text}"
    )

    msg = await interaction.channel.send(embed=embed)

    couples[gid][str(msg.id)] = {
        "type": type_,
        "user1": user1.id,
        "user2": user2.id,
        "start_date": start.strftime("%Y-%m-%d"),
        "message": message_text
    }

    save_data()

    await update_roles(
        interaction.guild,
        user1,
        user2,
        type_
    )

    await interaction.response.send_message(
        "✅ 완료!",
        ephemeral=True
    )

# =========================
# /우결
# =========================

@tree.command(name="우결", description="우결 생성")
async def 우결(
    interaction: discord.Interaction,
    본인: discord.Member,
    상대: discord.Member,
    시작날짜: str = None,
    한마디: str = "행복하세요 💖"
):

    await create_love(
        interaction,
        "우결",
        본인,
        상대,
        시작날짜,
        한마디
    )

# =========================
# /커플
# =========================

@tree.command(name="커플", description="커플 생성")
async def 커플(
    interaction: discord.Interaction,
    본인: discord.Member,
    상대: discord.Member,
    시작날짜: str = None,
    한마디: str = "행복하세요 💖"
):

    await create_love(
        interaction,
        "커플",
        본인,
        상대,
        시작날짜,
        한마디
    )

# =========================
# /파기
# =========================

@tree.command(name="파기", description="관계 파기")
async def 파기(
    interaction: discord.Interaction,
    본인: discord.Member,
    상대: discord.Member
):

    gid = str(interaction.guild.id)

    if gid not in couples:
        await interaction.response.send_message(
            "❌ 관계 데이터 없음",
            ephemeral=True
        )
        return

    target_key = None
    target_data = None

    for key, data in couples[gid].items():

        users = [data["user1"], data["user2"]]

        if 본인.id in users and 상대.id in users:
            target_key = key
            target_data = data
            break

    if not target_data:
        await interaction.response.send_message(
            "❌ 해당 관계를 찾을 수 없습니다.",
            ephemeral=True
        )
        return

    start = datetime.strptime(
        target_data["start_date"],
        "%Y-%m-%d"
    )

    end = datetime.now()

    days = (end - start).days + 1

    # 기존 임베드 수정
    try:

        old_message = await interaction.channel.fetch_message(
            int(target_key)
        )

        new_embed = discord.Embed(
            title=f"💔 {target_data['type']} 종료",
            color=discord.Color.dark_gray()
        )

        new_embed.description = (
            f"({target_data['start_date']} ~ "
            f"{end.strftime('%Y-%m-%d')} / {days}일째)\n\n"
            f"{본인.mention} 💗 {상대.mention}\n\n"
            f"💬 한마디 : {target_data['message']}"
        )

        await old_message.edit(embed=new_embed)

    except:
        pass

    await update_roles(
        interaction.guild,
        본인,
        상대,
        target_data["type"],
        remove=True
    )

    del couples[gid][target_key]

    save_data()

    await interaction.response.send_message(
        "💔 파기 완료",
        ephemeral=True
    )

# =========================

@bot.event
async def on_ready():
    print(f"✅ 로그인 완료 : {bot.user}")
    await tree.sync()

bot.run(TOKEN)
