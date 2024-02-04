import discord
import re
import datetime
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.none()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)





@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} in {len(bot.guilds)} servers!')
    await tree.sync()

@tree.command(name='ping', description="Sends the bot's latency")
async def ping(interaction: discord.Interaction):
  embed = discord.Embed(title=f"Pong! {round(bot.latency * 1000)}ms")
  await interaction.response.send_message(embed=embed, color=discord.Color.green())


@tree.command(name='help', description='Shows a list of all the commands')
async def help(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title='Help', description='Here is a list of all the commands:', color=discord.Color.blue())
    for command in tree.get_commands():
        if not command.name == 'help':
            embed.add_field(name=command.name, value=command.description, inline=False)
        else:
            embed.add_field(name=command.name, value="You're already here!", inline=False)
    await interaction.followup.send(embed=embed)



class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, emoji='✅')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != interaction.channel.owner:
            await interaction.response.send_message(embed=discord.Embed(title='❌ You are not the owner of this thread.', color=discord.Color.red()), ephemeral=True)
            return
        await interaction.response.send_message(embed=discord.Embed(title='Confirming...', color=discord.Color.green()))
        button.disabled = True
        self.children[1].disabled = True
        await interaction.message.edit(view=self)

        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != interaction.channel.owner:
            await interaction.response.send_message(embed=discord.Embed(title='❌ You are not the owner of this thread.', color=discord.Color.red()), ephemeral=True)
            return
        await interaction.response.send_message(embed=discord.Embed(title='Cancelling...', color=discord.Color.yellow()))
        button.disabled = True
        self.children[0].disabled = True
        await interaction.message.edit(view=self)

        self.value = False
        self.stop()

async def lock_thread(interaction: discord.Interaction, reason:str=None):
    em = discord.Embed(title="🔒 Locked!", description=f"Reason: {reason}" if reason else None, timestamp=datetime.datetime.now(), color=discord.Color.green())
    em.set_footer(text=f'Locked by {interaction.user.name}', icon_url=interaction.user.avatar.url)
    await interaction.channel.send(embed=em)
    await interaction.channel.edit(name='[🔒] ' + interaction.channel.name, locked=True, archived=True, reason=reason if reason else None)


async def unlock_thread(interaction: discord.Interaction, thread: discord.Thread, reason:str=None):
    await interaction.followup.send(embed=discord.Embed(title="🔓 Unlocked!", description=f"Reason: {reason}" if reason else None, color=discord.Color.green()), ephemeral=True)
    await thread.edit(name=thread.name.replace('[🔒] ', ''), locked=False, archived=False, reason=reason or None)
    embed=discord.Embed(
        title="This thread has been unlocked!",
        description=f"Reason: {reason}" if reason else None,
        timestamp=datetime.datetime.now(),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Unlocked by {interaction.user.name}", icon_url=interaction.user.avatar.url)
    await thread.send(embed=embed)


@tree.command(name='lock', description='Locks the thread')
@app_commands.describe(reason='The reason for locking the thread')
async def lock(interaction: discord.Interaction, reason:str=None):
    await interaction.response.defer(ephemeral=True)
    if not isinstance(interaction.channel, discord.Thread):
       await interaction.response.send_message(embed=discord.Embed(title='❌ This command can only be used in <#1199364645274796063>', color=discord.Color.red()), ephemeral=True)
       return
    if not interaction.channel.parent_id == 1199364645274796063:
        await interaction.followup.send(embed=discord.Embed(title='❌ Error', description='This command can only be used in <#1199364645274796063>', color=discord.Color.red()), ephemeral=True)
    view = Confirm()
    if interaction.user == interaction.channel.owner or interaction.permissions.manage_threads or interaction.user.id == 712439467901976660:
        await lock_thread(interaction, reason)
    else:
      await interaction.channel.send(f'<@{interaction.channel.owner_id}>', embed=discord.Embed(title='Do you want to lock this thread?', description=f'Reason: {reason}' if reason else None, color=discord.Color.green()).set_footer(text=f'{interaction.user.name} is requesting to lock this thread.', icon_url=interaction.user.avatar.url), view=view)


      await view.wait()
      if view.value:
        await lock_thread(interaction, reason)
      else:
          await interaction.followup.send(embed=discord.Embed(title="❌ Cancelled", color=discord.Color.red()))



  
@tree.command(name='unlock', description='Unlocks the thread')
@app_commands.describe(thread='The ID or link of the thread to unlock', reason='The reason for unlocking the thread')
async def unlock(interaction: discord.Interaction, thread: str=None, reason:str=None):
    await interaction.response.defer(ephemeral=False)
    if thread is None and isinstance(interaction.channel, discord.Thread):
        thread = interaction.channel.id
    if not thread:
        await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Please either use this command in a thread and/or specify the thread ID/link.', color=discord.Color.red()))
        return
    if str(thread).isdigit():
        thread = await interaction.guild.fetch_channel(int(thread))
    elif re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread):
        thread = await bot.fetch_channel(int(re.match(r'(https?:\/\/)?(ptb\.|canary\.)?discord(app)?\.(com|net)\/channels\/([0-9]+)\/([0-9]+)', thread).group(6)))

    if not isinstance(thread, discord.Thread):
        await interaction.followup.send(embed=discord.Embed(title='❌ Failed', description='Not a thread!', color=discord.Color.red()))
        return
    if not thread.locked and not thread.archived:
        await interaction.followup.send(embed=discord.Embed(title="❌ This thread is already unlocked!", color=discord.Color.red()))
        return
    await unlock_thread(interaction, thread, reason)






bot.run('TOKEN')
