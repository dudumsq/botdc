import os
import discord
from discord.ext import commands
from discord import app_commands

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.members = True          # Necessário para gerenciar nicknames e roles
intents.message_content = True  # Necessário se for ler mensagens do servidor

# ---------- BOT ----------
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = int(os.getenv("GUILD_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------- EVENTO ON_READY ----------
@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Servidor não encontrado. Verifique o GUILD_ID.")
        return
    
    channel = guild.get_channel(CHANNEL_ID)
    if not channel or not isinstance(channel, discord.TextChannel):
        print("❌ Canal não encontrado ou não é de texto. Verifique o CHANNEL_ID.")
        return

    # Embed
    embed = discord.Embed(
        title="Whitelist do servidor",
        description="Clique no botão abaixo para se whitelistar.\nVocê precisará informar seu **nome** e **ID**.",
        color=discord.Color.green()
    )
    embed.add_field(name="Status do Bot", value="🟢 Online e funcionando")
    
    # Botão
    view = discord.ui.View()
    button = discord.ui.Button(label="✅ Whitelist", style=discord.ButtonStyle.success, custom_id="whitelist")
    view.add_item(button)

    # Remove mensagens antigas do bot no canal (exceto a fixada)
    pinned = await channel.pins()
    pinned_msg = next((m for m in pinned if m.author.id == bot.user.id), None)
    
    messages = await channel.history(limit=100).flatten()
    for m in messages:
        if m.author.id == bot.user.id and m != pinned_msg:
            await m.delete()
    
    if pinned_msg:
        await pinned_msg.edit(embed=embed, view=view)
        print(f"🔄 Embed de whitelist atualizado no canal #{channel.name}")
    else:
        msg = await channel.send(embed=embed, view=view)
        await msg.pin()
        print(f"✅ Embed de whitelist enviado no canal #{channel.name}")

# ---------- BOTÃO / MODAL ----------
class WhitelistModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Whitelist - Informações")
        self.add_item(discord.ui.TextInput(label="Digite seu nome", custom_id="nome", required=True))
        self.add_item(discord.ui.TextInput(label="Digite sua ID", custom_id="id", required=True))

    async def callback(self, interaction: discord.Interaction):
        nome = self.children[0].value
        user_id = self.children[1].value
        member = interaction.user
        guild = interaction.guild

        if not member or not guild:
            await interaction.response.send_message("❌ Erro ao obter informações do servidor.", ephemeral=True)
            return

        guild_member = await guild.fetch_member(member.id)
        is_owner = guild.owner_id == member.id

        if not is_owner:
            await guild_member.edit(nick=f"{user_id} - {nome}")

        role_whitelist = discord.utils.get(guild.roles, name="Whitelisted")
        role_unverified = discord.utils.get(guild.roles, name="UNVERIFIED")
        role_member = discord.utils.get(guild.roles, name="Membros")

        if role_whitelist:
            await guild_member.add_roles(role_whitelist)
        if role_member:
            await guild_member.add_roles(role_member)
        if role_unverified:
            await guild_member.remove_roles(role_unverified)

        aviso_owner = "" if not is_owner else "\n⚠️ Você é o dono do servidor — o Discord não permite alterar o nickname do dono via bot."
        await interaction.response.send_message(f"✅ Você foi whitelisted!\nSeu nickname foi alterado para: **{user_id} - {nome}**{aviso_owner}", ephemeral=True)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data.get("custom_id") == "whitelist":
            await interaction.response.send_modal(WhitelistModal())


# ---------- RUN ----------
if not TOKEN or GUILD_ID == 0 or CHANNEL_ID == 0:
    raise ValueError("❌ Verifique se DISCORD_TOKEN, GUILD_ID e CHANNEL_ID estão definidos nas variáveis de ambiente!")

bot.run(TOKEN)
