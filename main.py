import discord
import asyncio

TOKEN = "MTIzODQzNjA0NjYzMTQ2OTA2OA.GidIUP.5yvxL3kh_CgY9aASrY5LhnpdeAmGdHvSLznXMo"
CHANNEL_ID = 1239330102160916480  # Replace with your channel ID

intents = discord.Intents.default()
intents.messages = True  # Enable message event

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID and not message.author.bot:
        print(f"새 글 감지: {message.content}")


client.run(TOKEN)
