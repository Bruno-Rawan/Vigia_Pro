import os
import time
import logging
import requests
import json
from urllib.parse import urlparse
from dotenv import load_dotenv
import sys

# Força UTF-8 no stdout do Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FILE_DB = "servidores.json"
FILE_LAST_ID = "last_update_id.txt"

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)),
    logging.FileHandler("vigia.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# Estado em memória para evitar spam de alertas
status_anterior = {}


# ====================== GESTÃO DE DADOS ======================
def carregar_servidores():
    if os.path.exists(FILE_DB):
        try:
            with open(FILE_DB, "r") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Erro ao carregar servidores: {e}")
    return {"Google": "http://8.8.8.8"}


def salvar_servidores(dados):
    try:
        with open(FILE_DB, "w") as f:
            json.dump(dados, f, indent=4)
    except Exception as e:
        log.error(f"Erro ao salvar servidores: {e}")


def carregar_last_id():
    """Persiste o último update_id para não reprocessar mensagens ao reiniciar."""
    if os.path.exists(FILE_LAST_ID):
        try:
            with open(FILE_LAST_ID, "r") as f:
                return int(f.read().strip())
        except Exception:
            pass
    return 0


def salvar_last_id(update_id):
    try:
        with open(FILE_LAST_ID, "w") as f:
            f.write(str(update_id))
    except Exception as e:
        log.error(f"Erro ao salvar last_id: {e}")


def url_valida(url):
    """Valida se a string é uma URL com esquema e host."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


# ====================== AUTENTICAÇÃO ======================
def remetente_autorizado(update):
    """Aceita apenas mensagens do CHAT_ID configurado."""
    chat_id = str(update.get("message", {}).get("chat", {}).get("id", ""))
    return chat_id == str(CHAT_ID)


# ====================== TELEGRAM ======================
def enviar_mensagem(texto):
    if not TOKEN or not CHAT_ID:
        log.error("TOKEN ou CHAT_ID não configurados!")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "HTML"}

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            log.warning(f"Telegram retornou status {r.status_code}: {r.text}")
        return r.status_code == 200
    except Exception as e:
        log.error(f"Erro ao enviar mensagem para o Telegram: {e}")
        return False


# ====================== COMANDOS ======================
AJUDA = (
    "🤖 <b>Comandos disponíveis:</b>\n\n"
    "/add &lt;nome&gt; &lt;url&gt; — Adiciona um servidor\n"
    "/del &lt;nome&gt; — Remove um servidor\n"
    "/list — Lista todos os servidores\n"
    "/check — Força verificação imediata\n"
    "/help — Exibe esta ajuda"
)


def processar_comando(msg, servidores):
    """Processa o comando recebido e retorna os servidores (possivelmente alterados)."""

    if msg == "/help" or msg == "/start":
        enviar_mensagem(AJUDA)

    elif msg.startswith("/add "):
        partes = msg.split(maxsplit=2)
        if len(partes) != 3:
            enviar_mensagem("⚠️ Uso correto: /add <b>nome</b> <b>url</b>")
            return servidores
        nome, url = partes[1], partes[2]
        if not url_valida(url):
            enviar_mensagem(f"⚠️ URL inválida: <code>{url}</code>")
            return servidores
        servidores[nome] = url
        salvar_servidores(servidores)
        # Remove do estado anterior para forçar nova verificação
        status_anterior.pop(nome, None)
        enviar_mensagem(f"✅ <b>Adicionado:</b> {nome} → <code>{url}</code>")
        log.info(f"Servidor adicionado: {nome} = {url}")

    elif msg.startswith("/del "):
        nome = msg.split(maxsplit=1)[1].strip()
        if nome in servidores:
            del servidores[nome]
            salvar_servidores(servidores)
            status_anterior.pop(nome, None)
            enviar_mensagem(f"🗑️ <b>Removido:</b> {nome}")
            log.info(f"Servidor removido: {nome}")
        else:
            enviar_mensagem(f"⚠️ Servidor <b>{nome}</b> não encontrado.")

    elif msg == "/list":
        if servidores:
            lista = "\n".join([f"• <b>{n}</b>: <code>{u}</code>" for n, u in servidores.items()])
            enviar_mensagem(f"📋 <b>Servidores cadastrados:</b>\n{lista}")
        else:
            enviar_mensagem("Nenhum servidor cadastrado.")

    elif msg == "/check":
        enviar_mensagem("🔍 Verificação manual iniciada...")
        verificar_servicos(servidores, forcar=True)

    else:
        enviar_mensagem(f"❓ Comando desconhecido. Use /help para ver os comandos.")

    return servidores


def verificar_comandos(last_update_id, servidores):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 10}

    try:
        res = requests.get(url, params=params, timeout=15).json()
        new_last_id = last_update_id

        for update in res.get("result", []):
            new_last_id = update["update_id"]

            # Ignora updates sem mensagem de texto
            msg = update.get("message", {}).get("text", "").strip()
            if not msg:
                continue

            # Bloqueia remetentes não autorizados
            if not remetente_autorizado(update):
                log.warning(f"Mensagem ignorada de chat não autorizado: {update}")
                continue

            servidores = processar_comando(msg, servidores)

        if new_last_id != last_update_id:
            salvar_last_id(new_last_id)

        return new_last_id, servidores

    except Exception as e:
        log.error(f"Erro ao verificar comandos: {e}")
        return last_update_id, servidores


# ====================== MONITORIZAÇÃO ======================
def verificar_servicos(servidores, forcar=False):
    """
    Verifica cada serviço e envia alerta apenas na transição de estado
    (online → offline ou offline → online), evitando spam de mensagens.

    forcar=True envia o status atual de todos, independente do estado anterior.
    """
    for nome, url in servidores.items():
        try:
            resposta = requests.get(url, timeout=6)
            online = resposta.status_code == 200
        except Exception:
            online = False

        estava_online = status_anterior.get(nome, True)  # Assume online no arranque

        if forcar:
            emoji = "✅" if online else "🚨"
            estado = "ONLINE" if online else "OFFLINE"
            enviar_mensagem(f"{emoji} <b>{nome}</b>: <b>{estado}</b>")
        else:
            if not online and estava_online:
                enviar_mensagem(f"🚨 <b>{nome}</b> está <b>OFFLINE</b>!")
                log.warning(f"OFFLINE: {nome} ({url})")
            elif online and not estava_online:
                enviar_mensagem(f"✅ <b>{nome}</b> voltou a estar <b>ONLINE</b>!")
                log.info(f"ONLINE: {nome} ({url})")

        status_anterior[nome] = online


# ====================== LOOP PRINCIPAL ======================
if __name__ == "__main__":
    log.info("🕵️ Vigia Pro Online - Iniciado!")

    if not TOKEN or not CHAT_ID:
        log.error("TELEGRAM_TOKEN e TELEGRAM_CHAT_ID são obrigatórios no .env")
        exit(1)

    last_id = carregar_last_id()
    servidores = carregar_servidores()

    enviar_mensagem("🟢 <b>Vigia Pro</b> iniciado! Use /help para ver os comandos.")

    while True:
        try:
            last_id, servidores = verificar_comandos(last_id, servidores)
            verificar_servicos(servidores)
            time.sleep(15)
        except KeyboardInterrupt:
            log.info("Encerrado pelo utilizador.")
            enviar_mensagem("🔴 <b>Vigia Pro</b> encerrado.")
            break
        except Exception as e:
            log.error(f"Erro inesperado no loop principal: {e}")
            time.sleep(15)