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
    t = Thread(target=run)
    t.start()

# ==========================================
# ▼ Bot設定
# ==========================================
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# ▼ 複数サーバー対応チャンネル設定
CHANNEL_MAP = {
    # ===== サーバーA =====
    1246838428641919120: {
        1449657975156375642: "JA",
        1449658053409640549: "EN-US",
        1449658202445578420: "KO",
        1449658106115264634: "ZH-HANS",
        # 1455205802771087410: "VI",  # ❌ DeepLはベトナム語非対応のためコメントアウト
    },

    # ===== サーバーB =====
    1301954897620635719: {
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
    # テキストが空なら翻訳せずそのまま返す（画像のみの場合など）
    if not text:
        return None

    for attempt in range(retries):
        try:
            return translator.translate_text(
                text,
                target_lang=target_lang
            )
        except Exception as e:
            print(f"翻訳失敗（{attempt+1}/{retries}） Lang:{target_lang} Error:{e}", flush=True)
            time.sleep(delay)
    return None

# ==========================================
# ▼ メッセージ受信
# ==========================================
@client.event
async def on_message(message):
    # ① Botの投稿は無視
    if message.author.bot:
        return

    # ② 翻訳済みマークがあれば無視
    if message.content.startswith("[TL]"):
        return

    if not message.guild:
        return

    guild_id = message.guild.id

    # サーバーIDが登録されているか確認
    if guild_id not in CHANNEL_MAP:
        return

    guild_channels = CHANNEL_MAP[guild_id]

    # チャンネルIDが登録されているか確認
    if message.channel.id not in guild_channels:
        return

    original_text = message.content.strip()
    image_urls = "".join(f"\n{a.url}" for a in message.attachments)

    # テキストも画像もなければ無視
    if not original_text and not image_urls:
        return

    # ★ 翻訳元言語は「投稿チャンネルの言語」
    source_lang = guild_channels[message.channel.id]

    print(
        f"受信: {original_text} "
        f"(Guild: {guild_id}, Channel: {message.channel.id}, Lang: {source_lang})",
        flush=True
    )

    # 翻訳して他チャンネルへ送信
    for target_channel_id, target_lang in guild_channels.items():
        # 自分自身のチャンネルには送らない
        if target_channel_id == message.channel.id:
            continue

        # 同じ言語設定のチャンネルには送らない
        if source_lang == target_lang:
            continue

        channel = client.get_channel(target_channel_id)
        if not channel:
            print(f"チャンネルが見つかりません: {target_channel_id}", flush=True)
            continue

        # ▼ 修正：テキストがある場合のみ翻訳APIを叩く
        translated_text = ""
        if original_text:
            result = translate_with_retry(original_text, target_lang)
            if result:
                translated_text = result.text
            else:
                # 翻訳失敗したが、画像がある場合は翻訳失敗メッセージを出さずに画像だけ送る手もある
                # ここではエラーメッセージを表示する
                translated_text = "⚠ 翻訳エラー"
        
        # メッセージの組み立て
        # テキストも画像もない場合はスキップ（ありえないが念の為）
        if not translated_text and not image_urls:
            continue

        try:
            # 翻訳テキストが空（画像のみ）の場合の表示調整
            msg_content = ""
            if translated_text:
                msg_content = translated_text
            
            await channel.send(
                f"[TL] **{message.author.display_name}**: {msg_content}{image_urls}"
            )
        except Exception as e:
            print(f"送信エラー: {e}", flush=True)

# ==========================================
# ▼ 起動処理
# ==========================================
print("=== Bot起動開始 ===", flush=True)
keep_alive()

try:
    if not DISCORD_BOT_TOKEN:
        print("エラー: Tokenが設定されていません", flush=True)
    else:
        client.run(DISCORD_BOT_TOKEN)
except Exception as e:
    print(f"起動エラー: {e}", flush=True)
