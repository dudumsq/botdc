import discord
from discord.ext import commands
import os

# Intents necessárias
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Pega variáveis de ambiente
GUILD_ID = int(os.getenv("GUILD_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
TOKEN = os.getenv("DISCORD_TOKEN")

# Modal para whitelist
class WhitelistModal(discord.ui.Modal, title="Whitelist - Informações"):
    nome = discord.ui.TextInput(label="Digite seu nome", required=True)
    id = discord.ui.TextInput(label="Digite sua ID", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        if not guild:
            await interaction.response.send_message(
                "❌ Erro ao obter servidor.", ephemeral=True
            )
            return

        try:
            guild_member = await guild.fetch_member(member.id)
            is_owner = guild.owner_id == member.id

            if not is_owner:
                await guild_member.edit(nick=f"{self.id.value} - {self.nome.value}")

            role_whitelist = discord.utils.get(guild.roles, name="Whitelisted")
            role_unverified = discord.utils.get(guild.roles, name="UNVERIFIED")
            role_membro = discord.utils.get(guild.roles, name="Membros")

            if role_whitelist:
                await guild_member.add_roles(role_whitelist)
            if role_membro:
                await guild_member.add_roles(role_membro)
            if role_unverified:
                await guild_member.remove_roles(role_unverified)

            aviso = ""
            if is_owner:
                aviso = "\n⚠️ Você é o dono do servidor — não dá pra mudar seu nick."

            await interaction.response.send_message(
                f"✅ Você foi whitelisted!\nNick: {self.id.value} - {self.nome.value}{aviso}",
                ephemeral=True,
            )

        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao aplicar whitelist.", ephemeral=True
            )

# Botão de whitelist
class WhitelistView(discord.ui.View):
    @discord.ui.button(label="✅ Whitelist", style=discord.ButtonStyle.green)
    async def whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistModal())

# Evento de ready
@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

    if not GUILD_ID or not CHANNEL_ID:
        print("⚠️ GUILD_ID ou CHANNEL_ID não definidos.")
        return

    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID) if guild else None

    if not channel:
        print("❌ Canal não encontrado")
        return

    embed = discord.Embed(
        title="Whitelist do servidor",
        description="Clique no botão abaixo para se whitelistar.\nInforme seu nome e ID.",
        color=discord.Color.green(),
    )
    embed.add_field(name="Status do Bot", value="🟢 Online e funcionando")

    await channel.send(embed=embed, view=WhitelistView())

# Roda o bot
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN não definido nas variáveis de ambiente.")
bot.run(TOKEN)
