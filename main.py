import discord
import deepl
import os
import time
from flask import Flask
from threading import Thread

# ==========================================
# ▼ 24時間稼働用
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    Thread(target=run).start()

# ==========================================
# ▼ Bot設定
# ==========================================
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# ▼ 複数サーバー対応チャンネル設定
# { guild_id: { channel_id: target_lang } }
CHANNEL_MAP = {
    # ===== サーバーA =====
    111111111111111111: {   # ← 実際の Guild ID
        1449657975156375642: "JA",
        1449658053409640549: "EN-US",
        1449658202445578420: "KO",
        1449658106115264634: "ZH-HANS",
        1455205802771087410: "VI",       # ← ★ ベトナム語（復活）
    },

    # ===== サーバーB =====
    222222222222222222: {
        1449421788374368367: "JA",
        1449421871593423031: "EN-US",
        1449422067547111525: "KO",
        1449421823178707075: "ZH-HANS",
    }
}

# ==========================================
# ▼ Discord / DeepL
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

translator = deepl.Translator(DEEPL_API_KEY)

# ==========================================
# ▼ 起動ログ
# ==========================================
@client.event
async def on_ready():
    print(f"=== ログイン成功: {client.user} ===", flush=True)

# ==========================================
# ▼ 翻訳関数（リトライ付き）
# ==========================================
def translate_with_retry(text, target_lang, retries=3, delay=1):
    for attempt in range(retries):
        try:
            return translator.translate_text(
                text,
                target_lang=target_lang
            )
        except Exception as e:
            print(f"翻訳失敗（{attempt+1}/{retries}）: {e}", flush=True)
            time.sleep(delay)
    return None

# ==========================================
# ▼ メッセージ受信
# ==========================================
@client.event
async def on_message(message):
    # ① Bot / Webhook 無視
    if message.author.bot:
        return

    # ② 翻訳済み無視
    if message.content.startswith("[TL]"):
        return

    if not message.guild:
        return

    guild_id = message.guild.id

    if guild_id not in CHANNEL_MAP:
        return

    guild_channels = CHANNEL_MAP[guild_id]

    if message.channel.id not in guild_channels:
        return

    original_text = message.content.strip()
    image_urls = "".join(f"\n{a.url}" for a in message.attachments)

    if not original_text and not image_urls:
        return

    print(
        f"受信: {original_text} "
        f"(Guild: {guild_id}, Channel: {message.channel.id})",
        flush=True
    )

    # ======================================
    # ▼ 翻訳元言語 自動判定
    # ======================================
    try:
        detected = translator.translate_text(
            original_text,
            target_lang="EN-US"
        )
        source_lang = detected.detected_source_lang
    except Exception as e:
        print(f"言語判定失敗: {e}", flush=True)
        source_lang = None

    # ======================================
    # ▼ 各チャンネルへ翻訳送信
    # ======================================
    for target_channel_id, target_lang in guild_channels.items():
        if target_channel_id == message.channel.id:
            continue

        # 同じ言語なら送らない
        if source_lang == target_lang:
            continue

        channel = client.get_channel(target_channel_id)
        if not channel:
            continue

        result = translate_with_retry(original_text, target_lang)

        if not result:
            await channel.send(
                f"[TL] **{message.author.display_name}**: ⚠ 翻訳に失敗しました"
            )
            continue

        await channel.send(
            f"[TL] **{message.author.display_name}**: {result.text}{image_urls}"
        )

# ==========================================
# ▼ 起動処理
# ==========================================
print("=== Bot起動開始 ===", flush=True)
keep_alive()

try:
    client.run(DISCORD_BOT_TOKEN)
except Exception as e:
    print(f"起動エラー: {e}", flush=True)
