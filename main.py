import os
import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Interaction, Embed

# ----------------------
# Intents
# ----------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # OBRIGATÓRIO para alterar nicknames e roles
intents.message_content = True  # Necessário se for ler mensagens

# ----------------------
# Bot
# ----------------------
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = int(os.environ.get("GUILD_ID", 0))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

# ----------------------
# Evento on_ready
# ----------------------
@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Servidor não encontrado. Verifique GUILD_ID.")
        return

    channel = guild.get_channel(CHANNEL_ID)
    if not channel or not isinstance(channel, discord.TextChannel):
        print("❌ Canal não encontrado ou não é de texto. Verifique CHANNEL_ID.")
        return

    embed = Embed(
        title="Whitelist do servidor",
        description="Clique no botão abaixo para se whitelistar.\nVocê precisará informar seu **nome** e **ID**.",
        color=discord.Color.green()
    )
    embed.add_field(name="Status do Bot", value="🟢 Online e funcionando")

    # Botão de whitelist
    class WhitelistView(ui.View):
        @ui.button(label="✅ Whitelist", style=ButtonStyle.green, custom_id="whitelist")
        async def whitelist_button(self, interaction: Interaction, button: ui.Button):
            await interaction.response.send_modal(WhitelistModal())

    # Modal para nome e ID
    class WhitelistModal(ui.Modal, title="Whitelist - Informações"):
        nome = ui.TextInput(label="Digite seu nome", style=discord.TextStyle.short, required=True)
        user_id = ui.TextInput(label="Digite sua ID", style=discord.TextStyle.short, required=True)

        async def on_submit(self, interaction: Interaction):
            member = await interaction.guild.fetch_member(interaction.user.id)
            is_owner = interaction.guild.owner_id == interaction.user.id

            # Alterar nickname se não for dono
            if not is_owner:
                try:
                    await member.edit(nick=f"{self.user_id.value} - {self.nome.value}")
                except Exception as e:
                    print(f"Erro ao alterar nickname: {e}")

            # Roles
            role_whitelisted = discord.utils.get(interaction.guild.roles, name="Whitelisted")
            role_membros = discord.utils.get(interaction.guild.roles, name="Membros")
            role_unverified = discord.utils.get(interaction.guild.roles, name="UNVERIFIED")

            if role_whitelisted:
                await member.add_roles(role_whitelisted)
            if role_membros:
                await member.add_roles(role_membros)
            if role_unverified:
                await member.remove_roles(role_unverified)

            aviso_owner = "" if not is_owner else "\n⚠️ Você é o dono do servidor — nickname não alterado."
            await interaction.response.send_message(
                f"✅ Você foi whitelisted!\nSeu nickname foi alterado para: **{self.user_id.value} - {self.nome.value}**{aviso_owner}",
                ephemeral=True
            )

    # Deleta mensagens antigas do bot no canal (exceto fixada)
    try:
        pinned_messages = await channel.pins()
        pinned_bot_msg = next((m for m in pinned_messages if m.author == bot.user), None)
        recent_messages = await channel.history(limit=100).flatten()
        for msg in recent_messages:
            if msg.author == bot.user and msg != pinned_bot_msg:
                await msg.delete()
    except Exception as e:
        print(f"Erro ao limpar mensagens antigas: {e}")

    # Envia embed com botão
    if pinned_bot_msg:
        await pinned_bot_msg.edit(embed=embed, view=WhitelistView())
    else:
        msg = await channel.send(embed=embed, view=WhitelistView())
        await msg.pin()

# ----------------------
# Rodar bot
# ----------------------
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN não definido nas variáveis de ambiente.")

bot.run(TOKEN)
