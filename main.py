import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True  # necessário para algumas interações

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs do servidor e canal
GUILD_ID = int(os.getenv("GUILD_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
TOKEN = os.getenv("DISCORD_TOKEN")

# Modal de whitelist
class WhitelistModal(discord.ui.Modal, title="Whitelist - Informações"):
    nome = discord.ui.TextInput(label="Digite seu nome", required=True)
    id = discord.ui.TextInput(label="Digite sua ID", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        if not guild:
            await interaction.response.send_message(
                "❌ Erro ao obter informações do servidor.", ephemeral=True
            )
            return

        try:
            guild_member = await guild.fetch_member(member.id)
            is_owner = guild.owner_id == member.id

            # Alterar nickname se não for dono
            if not is_owner:
                await guild_member.edit(nick=f"{self.id.value} - {self.nome.value}")

            # Pegar cargos
            role_whitelist = discord.utils.get(guild.roles, name="Whitelisted")
            role_unverified = discord.utils.get(guild.roles, name="UNVERIFIED")
            role_membro = discord.utils.get(guild.roles, name="Membros")

            # Aplicar cargos
            if role_whitelist:
                await guild_member.add_roles(role_whitelist)
            if role_membro:
                await guild_member.add_roles(role_membro)
            if role_unverified:
                await guild_member.remove_roles(role_unverified)

            aviso = ""
            if is_owner:
                aviso = "\n⚠️ Você é o dono do servidor — não é possível mudar seu nickname."

            await interaction.response.send_message(
                f"✅ Você foi whitelisted!\nNick: {self.id.value} - {self.nome.value}{aviso}",
                ephemeral=True,
            )

        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao tentar whitelistar você. Verifique a hierarquia de cargos do bot.",
                ephemeral=True,
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

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Servidor não encontrado.")
        return

    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Canal não encontrado")
        return

    embed = discord.Embed(
        title="Whitelist do servidor",
        description="Clique no botão abaixo para se whitelistar.\nInforme seu nome e ID.",
        color=discord.Color.green()
    )
    embed.add_field(name="Status do Bot", value="🟢 Online e funcionando")

    # Remove mensagens antigas do bot (exceto fixadas)
    pinned = await channel.pins()
    bot_pinned = [m for m in pinned if m.author.id == bot.user.id]
    recent_messages = await channel.history(limit=100).flatten()
    for msg in recent_messages:
        if msg.author.id == bot.user.id and msg not in bot_pinned:
            await msg.delete()

    # Se já existir mensagem fixada do bot, atualiza
    if bot_pinned:
        await bot_pinned[0].edit(embed=embed, view=WhitelistView())
        print(f"🔄 Embed de whitelist atualizado no canal #{channel.name}")
        return

    # Caso contrário, envia nova mensagem e fixa
    msg = await channel.send(embed=embed, view=WhitelistView())
    await msg.pin()
    print(f"✅ Embed de whitelist enviado no canal #{channel.name}")

# Roda o bot
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN não definido nas variáveis de ambiente.")

bot.run(TOKEN)
