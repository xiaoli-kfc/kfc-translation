import discord
import deepl
import os
from keep_alive import keep_alive

# ==========================================
# ▼ 設定（ReplitのSecretsから読み込みます） ▼
# ==========================================
DEEPL_API_KEY = os.environ['DEEPL_API_KEY']
DISCORD_BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']

# チャンネル設定（ご自身のIDを入れてください）
CHANNEL_MAP = {
    # === サーバーAの設定 ===
    1449657975156375642: "JA",     # 日本語部屋のID
    1449658053409640549: "EN-US",  # 英語部屋のID (米国英語)
    1449658202445578420: "KO",     # 韓国語部屋のID
    1449658106115264634: "ZH",     # 中国語部屋のID
    1449658465298681897: "RU",     # ロシア語（追加！）
    1449658345677131786: "ES",     # スペイン語（追加！）
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
            # 混信防止（同じサーバー内のみ送信）
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

# 目覚まし用サーバー起動
keep_alive()

# ボット起動
client.run(DISCORD_BOT_TOKEN)