import disnake, asyncio
from disnake.ext import commands

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dicionário para armazenar sessões ativas por usuário
active_sessions = {}

async def safe_edit(member: disnake.Member, state: bool):
    """
    Muta e deafen (cega) o membro se state for True; 
    caso contrário, reverte ambos.
    """
    try:
        await member.edit(mute=state, deafen=state)
    except disnake.HTTPException as e:
        print(f"Erro ao editar o membro {member.name}: {e}")

async def safe_send_dm(user: disnake.User, message: str):
    """
    Envia mensagem via DM para o usuário, tratando exceções.
    """
    try:
        await user.send(message)
    except Exception as e:
        print(f"Erro ao enviar DM para {user.name}: {e}")

@bot.slash_command(description="Gerencie sua sessão Pomodoro para call com mudo/desmudo e fone")
async def pomodoro(
    interaction: disnake.ApplicationCommandInteraction,
    action: str = commands.Param(choices=["ativar", "desativar"])
):
    # Verifica se o usuário está conectado a um canal de voz
    if interaction.author.voice is None:
        await interaction.response.send_message("Você não está conectado a uma call de voz.", ephemeral=True)
        return

    if action == "ativar":
        if interaction.author.id in active_sessions:
            await interaction.response.send_message("Você já possui uma sessão Pomodoro ativa.", ephemeral=True)
        else:
            task = bot.loop.create_task(pomodoro_session(interaction))
            active_sessions[interaction.author.id] = task
            await interaction.response.send_message("Pomodoro ativado! Sua sessão iniciará com mudo e fone ativados.", ephemeral=True)
    elif action == "desativar":
        if interaction.author.id not in active_sessions:
            await interaction.response.send_message("Você não possui uma sessão Pomodoro ativa.", ephemeral=True)
        else:
            task = active_sessions.pop(interaction.author.id)
            task.cancel()
            await interaction.response.send_message("Pomodoro desativado.", ephemeral=True)

async def pomodoro_session(interaction: disnake.ApplicationCommandInteraction):
    member = interaction.author
    try:
        while True:
            # Período de trabalho: muta e deafen o usuário e envia notificação via DM
            await safe_edit(member, True)
            await safe_send_dm(member, "🍅 Pomodoro iniciado! Você foi mutado e seu fone desativado para focar na call.")
            await asyncio.sleep(25 * 60)  # 25 minutos de trabalho

            # Período de pausa: reverte mudo e deafen e envia notificação via DM
            await safe_edit(member, False)
            await safe_send_dm(member, "⏸️ Hora da pausa! Você foi desmutado e seu fone reativado para conversar.")
            await asyncio.sleep(5 * 60)  # 5 minutos de pausa

            # Notifica o início de um novo ciclo
            await safe_send_dm(member, "🔁 Novo ciclo Pomodoro iniciado!")
    except asyncio.CancelledError:
        # Ao cancelar a sessão, garante que o usuário esteja desmutado e com o fone ativo
        await safe_edit(member, False)
        await safe_send_dm(member, "🛑 Sua sessão Pomodoro foi encerrada. Você foi desmutado e seu fone reativado.")
    except Exception as e:
        print(f"Erro na sessão Pomodoro para {member.name}: {e}")

bot.run("token")
