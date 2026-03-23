import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = int(os.getenv("GUILD_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))


# Modal de whitelist como subclasse de discord.ui.Modal
class WhitelistModal(discord.ui.Modal, title="Whitelist - Informações"):
    nome = discord.ui.TextInput(label="Digite seu nome", style=discord.TextStyle.short, required=True)
    id_val = discord.ui.TextInput(label="Digite sua ID", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Erro ao obter informações do servidor.", ephemeral=True)
            return

        member = await guild.fetch_member(interaction.user.id)
        is_owner = guild.owner_id == interaction.user.id

        if not is_owner:
            await member.edit(nick=f"{self.id_val.value} - {self.nome.value}")

        role_whitelist = discord.utils.get(guild.roles, name="Whitelisted")
        role_membros = discord.utils.get(guild.roles, name="Membros")
        role_unverified = discord.utils.get(guild.roles, name="UNVERIFIED")

        if role_whitelist:
            await member.add_roles(role_whitelist)
        if role_membros:
            await member.add_roles(role_membros)
        if role_unverified:
            await member.remove_roles(role_unverified)

        aviso_owner = "" if not is_owner else "\n⚠️ Você é o dono do servidor — o Discord não permite alterar o nickname do dono via bot."

        await interaction.response.send_message(
            f"✅ Você foi whitelisted!\nSeu nickname foi alterado para: **{self.id_val.value} - {self.nome.value}**{aviso_owner}",
            ephemeral=True
        )


# Função para enviar ou atualizar embed de whitelist
async def enviar_embed_whitelist():
    if GUILD_ID == 0 or CHANNEL_ID == 0:
        print("⚠️ GUILD_ID ou CHANNEL_ID não definidos. Embed de whitelist não será enviado.")
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Servidor não encontrado. Verifique o GUILD_ID.")
        return

    canal = guild.get_channel(CHANNEL_ID)
    if not isinstance(canal, discord.TextChannel):
        print("❌ Canal não encontrado ou não é de texto. Verifique o CHANNEL_ID.")
        return

    embed = discord.Embed(
        title="Whitelist do servidor",
        description="Clique no botão abaixo para se whitelistar.\nVocê precisará informar seu **nome** e **ID**.",
        color=discord.Color.green()
    )
    embed.add_field(name="Status do Bot", value="🟢 Online e funcionando")

    # Mensagens fixadas
    pinned_messages = []
    async for m in canal.pins():
        pinned_messages.append(m)
    mensagem_fixada = next((m for m in pinned_messages if m.author == bot.user), None)

    # Histórico de mensagens recentes
    recent_messages = []
    async for m in canal.history(limit=100):
        recent_messages.append(m)

    # Deleta mensagens antigas do bot (exceto a fixada)
    for m in recent_messages:
        if m.author == bot.user and m != mensagem_fixada:
            try:
                await m.delete()
            except:
                pass

    # Cria botão de whitelist
    button = discord.ui.Button(label="✅ Whitelist", style=discord.ButtonStyle.success, custom_id="whitelist")
    view = discord.ui.View()
    view.add_item(button)

    if mensagem_fixada:
        await mensagem_fixada.edit(embed=embed, view=view)
        print(f"🔄 Embed de whitelist atualizado no canal #{canal.name}")
    else:
        msg = await canal.send(embed=embed, view=view)
        await msg.pin()
        print(f"✅ Embed de whitelist enviado no canal #{canal.name}")


# Evento on_ready
@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    await enviar_embed_whitelist()


# Evento para abrir modal quando o botão for clicado
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "whitelist":
            await interaction.response.send_modal(WhitelistModal())


# Rodar o bot
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN não definido nas variáveis de ambiente.")

bot.run(TOKEN)
