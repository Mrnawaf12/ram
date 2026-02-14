import discord
from discord.ext import commands, tasks
import random
import json
import os
from datetime import datetime
import pytz
import requests

# ================== إعدادات البوت ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
SA_TZ = pytz.timezone("Asia/Riyadh")

# ================== المدن ==================
SAUDI_CITIES = {
    "makkah": "Makkah",
    "madinah": "Madinah",
    "riyadh": "Riyadh"
}

# ================== الصور ==================
GOOGLE_DRIVE_IMAGES = [
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212035931603108/18.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212036438982656/DLImage.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212037206802442/DLImage1.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212038070571028/1.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212038456705176/2.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212038905233483/6.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212039521927210/5.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212040155136030/3.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212040721498244/4.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212041316962458/14.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212605899767921/IMG_9342.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212606428381246/IMG_9343.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212607023976539/12.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212607875416064/16.jpg",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212608722534461/IMG_9231.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212609381171242/IMG_9232.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212609691422874/IMG_9233.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212610156986410/IMG_9234.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212610425421989/IMG_9335.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212610681405550/IMG_9338.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212781255229656/IMG_9517.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212781645430918/IMG_9518.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212782152810506/IMG_9519.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212782395953286/IMG_9345.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212784539238573/IMG_9349.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212784954478653/IMG_9366.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212785323573418/IMG_9387.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212785965564065/IMG_9472.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212786699571260/IMG_9499.JPG",
    "https://cdn.discordapp.com/attachments/1315325300468355102/1472212787185848381/IMG_9514.JPG"
]

daily_images = {}

# ================== حساب أذان المغرب ==================
def get_maghrib_time(city):
    url = "https://api.aladhan.com/v1/timingsByCity"
    params = {
        "city": SAUDI_CITIES[city],
        "country": "Saudi Arabia",
        "method": 4
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    maghrib = data["data"]["timings"]["Maghrib"]
    hour, minute = map(int, maghrib.split(":"))
    return hour, minute

# ================== حفظ / تحميل ==================
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(daily_images, f, ensure_ascii=False, indent=2)

def load_data():
    global daily_images
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            daily_images = json.load(f)

# ================== المهمة اليومية ==================
@tasks.loop(minutes=1)
async def daily_task():
    now = datetime.now(SA_TZ)

    for channel_id, data in list(daily_images.items()):
        h, m = get_maghrib_time(data["city"])
        data["hour"] = h
        data["minute"] = m

        if now.hour == h and now.minute == m:
            if data["day_count"] >= data["max_days"]:
                del daily_images[channel_id]
                save_data()
                continue

            channel = bot.get_channel(int(channel_id))
            if not channel:
                continue

            img = random.choice(data["images"])

            embed = discord.Embed(
                title=f"🖼️ الصورة اليومية {data['day_count'] + 1}/30",
                color=0x2ecc71
            )
            embed.set_image(url=img)
            embed.set_footer(
                text=f"{data['city'].capitalize()} | حقوق nawaf @_i42"
            )

            await channel.send(embed=embed)

            data["day_count"] += 1
            save_data()

# ================== الواجهة ==================
class SetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.channel = None
        self.admin = None
        self.city = None

        self.add_item(ChannelSelect())
        self.add_item(AdminSelect())
        self.add_item(CitySelect())

    @discord.ui.button(label="✅ تفعيل الإرسال", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button):
        if not self.channel or not self.admin or not self.city:
            return await interaction.response.send_message(
                "❌ اختر الروم + المسؤول + المدينة",
                ephemeral=True
            )

        h, m = get_maghrib_time(self.city)

        daily_images[str(self.channel.id)] = {
            "hour": h,
            "minute": m,
            "day_count": 0,
            "max_days": 30,
            "images": GOOGLE_DRIVE_IMAGES,
            "admin_id": self.admin.id,
            "city": self.city
        }

        save_data()
        if not daily_task.is_running():
            daily_task.start()

        await interaction.response.send_message(
            f"✅ تم التفعيل بنجاح\n\n"
            f"📢 الروم: {self.channel.mention}\n"
            f"👤 المسؤول: {self.admin.mention}\n"
            f"🌍 المدينة: {self.city}\n"
            f"🕌 وقت الإرسال: أذان المغرب",
            ephemeral=True
        )

# ================== Select Menus ==================
class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="📢 اختر الروم",
            channel_types=[discord.ChannelType.text],
            max_values=1
        )

    async def callback(self, interaction):
        self.view.channel = self.values[0]
        await interaction.response.defer()

class AdminSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="👤 اختر المسؤول",
            max_values=1
        )

    async def callback(self, interaction):
        self.view.admin = self.values[0]
        await interaction.response.defer()

class CitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="مكة المكرمة", value="makkah"),
            discord.SelectOption(label="المدينة المنورة", value="madinah"),
            discord.SelectOption(label="الرياض", value="riyadh"),
        ]
        super().__init__(
            placeholder="🌍 اختر المدينة",
            options=options
        )

    async def callback(self, interaction):
        self.view.city = self.values[0]
        await interaction.response.defer()

# ================== أوامر Slash ==================
@bot.tree.command(name="setup", description="⚙️ إعداد الإرسال اليومي")
async def setup_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🕌 بوت رمضان",
        description="اختَر الروم + المسؤول + المدينة\n📸 الإرسال تلقائي وقت أذان المغرب",
        color=0x5865F2
    )
    await interaction.response.send_message(
        embed=embed,
        view=SetupView(),
        ephemeral=True
    )

@bot.tree.command(name="status", description="📊 حالة الجداول")
async def status_cmd(interaction: discord.Interaction):
    if not daily_images:
        return await interaction.response.send_message(
            "📭 لا توجد جداول نشطة",
            ephemeral=True
        )

    embed = discord.Embed(title="📊 الجداول النشطة", color=0x00bcd4)
    for cid, d in daily_images.items():
        embed.add_field(
            name=f"<#{cid}>",
            value=f"{d['day_count']}/30 | {d['city']}",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== Ready ==================
@bot.event
async def on_ready():
    load_data()
    if not daily_task.is_running():
        daily_task.start()

    await bot.tree.sync()
    print(f"🤖 {bot.user} جاهز للعمل")

# ================== تشغيل ==================
bot.run("OTA5NDE5MTIxNzczNTE4OTA4.GEPlXO.FBnfREpGX0Uzs3_Ks3Mzch9bPKqO57IC0ffvSI")
