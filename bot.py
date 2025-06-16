from env import *
import discord
import requests
import yt_dlp
import os

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

        if message.content:
            if message.content.startswith('.ggl'):
                try:
                    query = message.content.split('.ggl ')[1]
                    final_url = f'{BASE_URL}key={GGL_API}&cx={GGL_CX}&q={query}'
                    search_type = 'web'
                except IndexError as e:
                    print(f'Index error: {e}')
            
            if message.content.startswith('.img'):
                try:
                    query = message.content.split('.img ')[1]
                    final_url = f'{BASE_URL}key={GGL_API}&cx={GGL_CX}&q={query}&searchType=image'
                    search_type = 'img'
                except IndexError as e:
                    print(f'Index error: {e}')
                    
            if message.content.startswith('.link'):
                try:
                    url = message.content.split('.link ')[1]
                    
                    # Configure yt-dlp options
                    ydl_opts = {
                        'format': 'best',  # Get the best quality
                        'quiet': True,
                        'no_warnings': True,
                    }
                    
                    # Download the video
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        video_path = ydl.prepare_filename(info)
                    
                    # Send the video to Discord
                    await message.channel.send(file=discord.File(video_path))
                    
                    # Clean up the downloaded file
                    os.remove(video_path)
                    
                    # Delete the user's message
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        print("Bot doesn't have permission to delete messages")
                    except discord.NotFound:
                        print("Message was already deleted")
                    except Exception as e:
                        print(f"Error deleting message: {str(e)}")
                    
                    return  # Exit the function to prevent further code execution
                    
                except Exception as e:
                    print(f'Error downloading video: {str(e)}')
                    # Try to delete the message even if video download failed
                    try:
                        await message.delete()
                    except:
                        pass
                    return  # Exit the function to prevent further code execution

            # Send request if final url valid
            try:
                response = requests.get(final_url)
            except UnboundLocalError:
                return
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and data['items']:
                    paginator = SearchPaginator(data['items'][:10], search_type)
                    embed = paginator.get_embed()
                    msg = await message.channel.send(embed=embed, view=paginator)
                    paginator.message = msg
                else:
                    await message.channel.send('No search results found.')
            else:
                await message.channel.send(f'Error: {response.status_code}')


class SearchPaginator(discord.ui.View):
    def __init__(self, search_results, search_type='web'):
        super().__init__(timeout=60)  # 60 second timeout
        self.search_results = search_results
        self.current_page = 0
        self.max_pages = len(search_results)
        self.search_type = search_type
        
    def get_embed(self):
        """Create an embed for the current page"""
        if not self.search_results:
            embed = discord.Embed(title="No Results", description="No search results found.")
            return embed
            
        result = self.search_results[self.current_page]
        
        if self.search_type == 'img':
            embed = discord.Embed(
                title=result.get('title', 'No title'),
                color=0x4285f4
            )
            
            # Set the image directly from the link
            image_url = result.get('link')
            if image_url:
                embed.set_image(url=image_url)
            
            # Add context URL if available
            context_link = result.get('image', {}).get('contextLink')
            if context_link:
                embed.add_field(name="Source", value=f"[View Page]({context_link})", inline=False)
        else:
            embed = discord.Embed(
                title=result.get('title', 'No title'),
                description=result.get('snippet', 'No description'),
                url=result.get('link', ''),
                color=0x4285f4
            )
            
            # Add image if available
            if 'pagemap' in result and 'cse_image' in result['pagemap']:
                image_url = result['pagemap']['cse_image'][0].get('src')
                if image_url:
                    embed.set_image(url=image_url)
            
            elif 'pagemap' in result and 'cse_thumbnail' in result['pagemap']:
                thumbnail_url = result['pagemap']['cse_thumbnail'][0].get('src')
                if thumbnail_url:
                    embed.set_thumbnail(url=thumbnail_url)
            
        embed.set_footer(text=f"Page {self.current_page + 1} of {self.max_pages}")
        return embed
    
    @discord.ui.button(label='◀️ Previous', style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        
        # Update button states
        if self.current_page == 0:
            button.disabled = True
        self.next_button.disabled = False
        
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @discord.ui.button(label='Next ▶️', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        
        # Update button states
        if self.current_page >= self.max_pages - 1:
            button.disabled = True
        self.previous_button.disabled = False
        
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
        
    # TODO make delete button
    @discord.ui.button(label='Delete 🗑️', style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the message containing this embed"""
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except discord.NotFound:
            # Message was already deleted
            pass
        except discord.Forbidden:
            # Bot doesn't have permission to delete the message
            await interaction.followup.send("I don't have permission to delete this message.", ephemeral=True)
        except Exception as e:
            # Handle any other errors
            await interaction.followup.send(f"An error occurred while deleting the message: {str(e)}", ephemeral=True)
    
    async def on_timeout(self):
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        # Update the message to show disabled buttons
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass  # Message was deleted
            except discord.HTTPException:
                pass  # Other discord errors


if __name__ == "__main__":
    client = MyClient()
    client.run(TOKEN)
