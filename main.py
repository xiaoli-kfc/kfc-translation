import discord
import deepl
import os
from flask import Flask
from threading import Thread

# ==========================================
# ▼ 24時間稼働用の設定 ▼
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
# ▼ ボットの設定 ▼
# ==========================================

DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# チャンネル設定
CHANNEL_MAP = {
    # === KFC-Discordの設定 ===
    1449657975156375642: "JA",      # 日本語
    1449658053409640549: "EN-US",   # 英語 (米国)
    1449658202445578420: "KO",      # 韓国語
    1449658106115264634: "ZH-HANS", # 中国語（簡体字）
    1455205802771087410: "VI",      # ベトナム語
    # === シーズン用の設定 ===
    1449421788374368367: "JA",      
    1449421871593423031: "EN-US",   
    1449422067547111525: "KO",      
    1449421823178707075: "ZH-HANS", # 中国語（簡体字）
}

# ==========================================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
translator = deepl.Translator(DEEPL_API_KEY)

@client.event
async def on_ready():
    print(f'=== ログイン成功: {client.user} ===')

@client.event
async def on_message(message):
    # ▼ 診断用ログ：メッセージ受信確認
    print(f"受信: {message.content} (チャンネルID: {message.channel.id})")

    if message.author.bot:
        return

    # ▼ 診断用ログ：対象外チャンネルの確認
    if message.channel.id not in CHANNEL_MAP:
        print(f"対象外のチャンネルのため無視します: {message.channel.id}")
        return

    # === 使用量確認コマンド ===
    if message.content == "!usage":
        try:
            usage = translator.get_usage()
            await message.channel.send(f"📊 今月の使用量: {usage.character.count:,} / {usage.character.limit:,} 文字")
        except Exception as e:
            await message.channel.send(f"使用量の取得に失敗しました: {e}")
        return

    # 画像URL取得
    image_urls = ""
    if message.attachments:
        for attachment in message.attachments:
            image_urls += f"\n{attachment.url}"

    original_text = message.content
    if not original_text and not image_urls:
        return

    # 送信先を探す
    for target_channel_id, target_lang in CHANNEL_MAP.items():
        if target_channel_id == message.channel.id:
            continue

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
            print(f"翻訳送信エラー: {e}")

# ==========================================
# ▼ 診断付き起動シーケンス (修正版) ▼
# ==========================================

print("=== 診断開始 ===", flush=True)

# 1. トークンのチェック（Webサーバー起動前に実行）
if DISCORD_BOT_TOKEN is None:
    print("【重大エラー】Tokenが読み込めていません！RenderのEnvironment Variablesの設定を確認してください。", flush=True)
elif len(DISCORD_BOT_TOKEN) < 50:
    print(f"【警告】Tokenが短すぎます（{len(DISCORD_BOT_TOKEN)}文字）。コピペミスの可能性があります。", flush=True)
else:
    print("Tokenは正常に読み込まれています。", flush=True)

# 2. 目覚まし機能（Webサーバー）を起動
# ※ 診断が終わってからWebサーバーを動かします
print("Webサーバーを起動します...", flush=True)
keep_alive()

# 3. Botのログイン試行
print("Botのログインを試行します...", flush=True)

try:
    client.run(DISCORD_BOT_TOKEN)
except Exception as e:
    # エラー内容を強制表示
    print(f"【起動エラー発生】: {e}", flush=True)
