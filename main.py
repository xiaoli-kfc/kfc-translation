import discord
import deepl
import os
from flask import Flask
from threading import Thread

# ==========================================
# ▼ 24時間稼働用の設定（ここを追加しました） ▼
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ==========================================


# ==========================================
# ▼ ボットの設定 ▼
# ==========================================

# Renderの環境変数からキーを取得
DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# チャンネル設定
CHANNEL_MAP = {
    # === KFC-Discordの設定 ===
    1449657975156375642: "JA",     # 日本語部屋のID
    1449658053409640549: "EN-US",  # 英語部屋のID (米国英語)
    1449658202445578420: "KO",     # 韓国語部屋のID
    1449658106115264634: "ZH",     # 中国語部屋のID
    1449658465298681897: "VI",     # ベトナム語（追加！）
    # === シーズン用の設定 ===
    1449421788374368367: "JA",     # 日本語部屋のID
    1449421871593423031: "EN-US",  # 英語部屋のID (米国英語)
    1449422067547111525: "KO",     # 韓国語部屋のID
    1449421823178707075: "ZH",     # 中国語部屋のID
}

# ==========================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
translator = deepl.Translator(DEEPL_API_KEY)

@client.event
async def on_ready():
    print(f'ログインしました: {client.user}')

@client.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id not in CHANNEL_MAP: return

    # === ここに追加 ===
    if message.content == "!usage":
        usage = translator.get_usage()
        await message.channel.send(f"📊 今月の使用量: {usage.character.count:,} / {usage.character.limit:,} 文字")
        return
    # =================
    # 画像URL取得
    image_urls = ""
    if message.attachments:
        for attachment in message.attachments:
            image_urls += f"\n{attachment.url}"

    original_text = message.content
    if not original_text and not image_urls: return

    # 送信先を探す
    for target_channel_id, target_lang in CHANNEL_MAP.items():
        if target_channel_id == message.channel.id: continue

        try:
            channel = client.get_channel(target_channel_id)
            if not channel or channel.guild.id != message.guild.id:
                continue

            translated_text = ""
            if original_text:
                result = translator.translate_text(original_text, target_lang=target_lang)
                translated_text = result.text
            
            final_message = f"**{message.author.display_name}**: {translated_text}{image_urls}"
            await channel.send(final_message)

        except Exception as e:
            print(f"エラー: {e}")

# 目覚まし機能を起動
keep_alive()

# ボットを起動
client.run(DISCORD_BOT_TOKEN)




