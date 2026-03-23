import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = int(os.getenv("GUILD_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))


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


# Interações de botões e modais
@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Botão de whitelist
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "whitelist":
            modal = discord.ui.Modal(title="Whitelist - Informações")
            nome_input = discord.ui.TextInput(label="Digite seu nome", custom_id="nome", style=discord.TextStyle.short, required=True)
            id_input = discord.ui.TextInput(label="Digite sua ID", custom_id="id", style=discord.TextStyle.short, required=True)
            modal.add_item(nome_input)
            modal.add_item(id_input)
            await interaction.response.send_modal(modal)

    # Submissão do modal
    elif interaction.type == discord.InteractionType.modal_submit:
        if interaction.data["custom_id"] == "whitelist_modal":
            # Extrai valores do modal
            nome = interaction.data["components"][0]["components"][0]["value"]
            id_val = interaction.data["components"][1]["components"][0]["value"]

            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("❌ Erro ao obter informações do servidor.", ephemeral=True)
                return

            try:
                member = await guild.fetch_member(interaction.user.id)
                is_owner = guild.owner_id == interaction.user.id

                if not is_owner:
                    await member.edit(nick=f"{id_val} - {nome}")

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
                    f"✅ Você foi whitelisted!\nSeu nickname foi alterado para: **{id_val} - {nome}**{aviso_owner}",
                    ephemeral=True
                )
            except Exception as e:
                print(e)
                await interaction.response.send_message(
                    "❌ Ocorreu um erro ao tentar whitelistar você. Verifique se o cargo do bot está acima dos seus cargos na hierarquia do servidor.",
                    ephemeral=True
                )


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN não definido nas variáveis de ambiente.")

bot.run(TOKEN)
