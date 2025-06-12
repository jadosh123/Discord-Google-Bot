from env import BOT_TOKEN
import discord

TOKEN = BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print('Bot is online!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello World!')


if __name__ == "__main__":
    client = MyClient()
    client.run(TOKEN)
