import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime

# =========================
# 토큰
# =========================

TOKEN = os.getenv("TOKEN")

# =========================
# 인텐트
# =========================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

tree = bot.tree

# =========================
# 역할 ID
# =========================

SOLO_ROLE_ID = 111111111111111111
COUPLE_ROLE_ID = 222222222222222222
MARRIAGE_ROLE_ID = 333333333333333333

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
        json.dump(
            couples,
            f,
            ensure_ascii=False,
            indent=4
        )

# =========================
# 역할 처리
# =========================

async def update_roles(
    guild,
    user1,
    user2,
    type_,
    remove=False
):

    solo_role = guild.get_role(SOLO_ROLE_ID)
    couple_role = guild.get_role(COUPLE_ROLE_ID)
    marriage_role = guild.get_role(MARRIAGE_ROLE_ID)

    target_role = (
        marriage_role
        if type_ == "우결"
        else couple_role
    )

    for member in [user1, user2]:

        if remove:

            if target_role in member.roles:
                await member.remove_roles(
                    target_role
                )

            if solo_role not in member.roles:
                await member.add_roles(
                    solo_role
                )

        else:

            if solo_role in member.roles:
                await member.remove_roles(
                    solo_role
                )

            if target_role not in member.roles:
                await member.add_roles(
                    target_role
                )

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

    # 봇 방지
    if user1.bot or user2.bot:

        await interaction.response.send_message(
            "❌ 봇은 선택할 수 없습니다.",
            ephemeral=True
        )
        return

    # 자기 자신 방지
    if user1.id == user2.id:

        await interaction.response.send_message(
            "❌ 자기 자신과는 불가능합니다.",
            ephemeral=True
        )
        return

    gid = str(interaction.guild.id)

    if gid not in couples:
        couples[gid] = {}

    # 이미 관계 중인지 검사
    for data in couples[gid].values():

        users = [
            data["user1"],
            data["user2"]
        ]

        if user1.id in users:

            await interaction.response.send_message(
                f"❌ {user1.mention} 님은 이미 관계 중입니다.",
                ephemeral=True
            )
            return

        if user2.id in users:

            await interaction.response.send_message(
                f"❌ {user2.mention} 님은 이미 관계 중입니다.",
                ephemeral=True
            )
            return

    # 날짜 처리
    if start_date:

        try:
            start = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            )

        except:

            await interaction.response.send_message(
                "❌ 날짜 형식은 YYYY-MM-DD 입니다.",
                ephemeral=True
            )
            return

    else:
        start = datetime.now()

    days = (
        datetime.now() - start
    ).days + 1

    # 임베드 생성
    embed = discord.Embed(
        title=f"💖 {type_} 탄생!",
        color=discord.Color.pink()
    )

    embed.description = (
        f"({start.strftime('%Y-%m-%d')} ~ X / "
        f"{days}일째)\n\n"
        f"{user1.mention} 💗 "
        f"{user2.mention}\n\n"
        f"💬 한마디 : "
        f"{message_text}"
    )

    message = await interaction.channel.send(
        embed=embed
    )

    # 저장
    couples[gid][str(message.id)] = {

        "type": type_,
        "user1": user1.id,
        "user2": user2.id,
        "start_date": start.strftime(
            "%Y-%m-%d"
        ),
        "message": message_text
    }

    save_data()

    # 역할 변경
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

@tree.command(
    name="우결",
    description="우결 생성"
)
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

@tree.command(
    name="커플",
    description="커플 생성"
)
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

@tree.command(
    name="파기",
    description="관계 파기"
)
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

        users = [
            data["user1"],
            data["user2"]
        ]

        if (
            본인.id in users
            and 상대.id in users
        ):

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

    days = (
        end - start
    ).days + 1

    # 기존 임베드 수정
    try:

        old_message = await interaction.channel.fetch_message(
            int(target_key)
        )

        embed = discord.Embed(
            title=f"💔 {target_data['type']} 종료",
            color=discord.Color.dark_gray()
        )

        embed.description = (
            f"({target_data['start_date']} ~ "
            f"{end.strftime('%Y-%m-%d')} / "
            f"{days}일째)\n\n"
            f"{본인.mention} 💗 "
            f"{상대.mention}\n\n"
            f"💬 한마디 : "
            f"{target_data['message']}"
        )

        await old_message.edit(
            embed=embed
        )

    except:
        pass

    # 역할 제거
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
# /커플목록
# =========================

@tree.command(
    name="커플목록",
    description="현재 관계 목록"
)
async def 커플목록(
    interaction: discord.Interaction
):

    gid = str(interaction.guild.id)

    if (
        gid not in couples
        or not couples[gid]
    ):

        await interaction.response.send_message(
            "❌ 현재 관계 없음"
        )
        return

    embed = discord.Embed(
        title="💖 커플 목록",
        color=discord.Color.pink()
    )

    checked = set()

    for data in couples[gid].values():

        users = tuple(
            sorted([
                data["user1"],
                data["user2"]
            ])
        )

        if users in checked:
            continue

        checked.add(users)

        user1 = interaction.guild.get_member(
            data["user1"]
        )

        user2 = interaction.guild.get_member(
            data["user2"]
        )

        if not user1 or not user2:
            continue

        start = datetime.strptime(
            data["start_date"],
            "%Y-%m-%d"
        )

        days = (
            datetime.now() - start
        ).days + 1

        embed.add_field(

            name=f"{data['type']} 💗",

            value=(
                f"{user1.mention} 💗 "
                f"{user2.mention}\n"
                f"📅 {data['start_date']} ~ X\n"
                f"❤️ {days}일째\n"
                f"💬 {data['message']}"
            ),

            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )

# =========================
# D-Day 자동 갱신
# =========================

@tasks.loop(hours=1)
async def update_embeds():

    for guild_id, guild_data in couples.items():

        guild = bot.get_guild(
            int(guild_id)
        )

        if not guild:
            continue

        for message_id, data in guild_data.items():

            try:

                found_message = None

                for channel in guild.text_channels:

                    try:

                        msg = await channel.fetch_message(
                            int(message_id)
                        )

                        found_message = msg
                        break

                    except:
                        continue

                if not found_message:
                    continue

                start = datetime.strptime(
                    data["start_date"],
                    "%Y-%m-%d"
                )

                days = (
                    datetime.now() - start
                ).days + 1

                user1 = guild.get_member(
                    data["user1"]
                )

                user2 = guild.get_member(
                    data["user2"]
                )

                if not user1 or not user2:
                    continue

                embed = discord.Embed(
                    title=f"💖 {data['type']} 탄생!",
                    color=discord.Color.pink()
                )

                embed.description = (
                    f"({data['start_date']} ~ X / "
                    f"{days}일째)\n\n"
                    f"{user1.mention} 💗 "
                    f"{user2.mention}\n\n"
                    f"💬 한마디 : "
                    f"{data['message']}"
                )

                await found_message.edit(
                    embed=embed
                )

            except:
                continue



# =========================
# !커플초기화
# =========================

@bot.command(name="커플초기화")
@commands.has_permissions(administrator=True)
async def 커플초기화(ctx):

    gid = str(ctx.guild.id)

    if gid not in couples or not couples[gid]:

        await ctx.send(
            "❌ 초기화할 데이터 없음"
        )
        return

    # 역할 원복
    for data in couples[gid].values():

        user1 = ctx.guild.get_member(
            data["user1"]
        )

        user2 = ctx.guild.get_member(
            data["user2"]
        )

        if user1 and user2:

            try:

                await update_roles(
                    ctx.guild,
                    user1,
                    user2,
                    data["type"],
                    remove=True
                )

            except:
                pass

    # 데이터 삭제
    couples[gid] = {}

    save_data()

    embed = discord.Embed(
        title="🗑️ 커플 데이터 초기화",
        description=(
            "모든 커플/우결 데이터가 "
            "초기화되었습니다."
        ),
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

# =========================
# 권한 없을 때
# =========================

@커플초기화.error
async def 커플초기화_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ 관리자만 사용 가능합니다."
        )
        
# =========================
# 실행
# =========================

@bot.event
async def on_ready():

    print(f"✅ 로그인 완료 : {bot.user}")

    try:
        synced = await tree.sync()
        print(f"🌸 슬래시 동기화 완료 : {len(synced)}개")

    except Exception as e:
        print(e)

    update_embeds.start()

bot.run(TOKEN)
