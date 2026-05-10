# 🕵️ Vigia Pro — Monitor de Infraestrutura via Telegram

Bot de monitorização de servidores e serviços web com alertas em tempo real pelo Telegram. O Vigia Pro verifica periodicamente se os seus serviços estão online e notifica imediatamente em caso de queda ou recuperação.

## 💡 O que o projeto faz

- Monitora múltiplos servidores e URLs em segundo plano
- Envia alertas no Telegram quando um serviço fica **offline** ou volta a ficar **online**
- Evita spam: só notifica quando o estado muda (online → offline ou vice-versa)
- Permite gerenciar os servidores monitorados direto pelo Telegram, sem reiniciar o programa
- Persiste os dados entre reinicializações (servidores em JSON, último update em arquivo)
- Gera logs completos em arquivo para auditoria

## 🛠️ Tecnologias utilizadas

- Python 3
- [Requests](https://pypi.org/project/requests/) — verificação HTTP dos serviços e integração com a API do Telegram
- [python-dotenv](https://pypi.org/project/python-dotenv/) — gestão segura de credenciais
- [Logging](https://docs.python.org/3/library/logging.html) — registro de eventos em arquivo e console
- [Telegram Bot API](https://core.telegram.org/bots/api)

## ▶️ Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/vigia-pro.git
cd vigia-pro
```

### 2. Instale as dependências

```bash
pip install requests python-dotenv
```

### 3. Configure as credenciais

Crie um arquivo `.env` na raiz do projeto:

```
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

> - Crie um bot pelo [@BotFather](https://t.me/BotFather) no Telegram para obter o token
> - Obtenha seu Chat ID conversando com o [@userinfobot](https://t.me/userinfobot)

### 4. Execute

```bash
python vigia_infra.py
```

O bot enviará uma mensagem de confirmação no Telegram ao iniciar.

## 🤖 Comandos disponíveis no Telegram

| Comando | Descrição |
|---|---|
| `/add <nome> <url>` | Adiciona um servidor para monitorar |
| `/del <nome>` | Remove um servidor |
| `/list` | Lista todos os servidores cadastrados |
| `/check` | Força uma verificação imediata de todos os serviços |
| `/help` | Exibe a lista de comandos |

## 📸 Exemplo de alertas recebidos no Telegram

```
🟢 Vigia Pro iniciado! Use /help para ver os comandos.

🚨 Google está OFFLINE!

✅ Google voltou a estar ONLINE!
```

## 📁 Estrutura do projeto

```
vigia-pro/
├── vigia_infra.py      # Código principal
├── servidores.json     # Base de dados dos servidores (gerado automaticamente)
├── last_update_id.txt  # Controle de updates do Telegram (gerado automaticamente)
├── vigia.log           # Log de eventos (gerado automaticamente)
├── .env                # Credenciais (não versionado)
├── .gitignore
└── README.md
```

> ⚠️ Nunca suba o arquivo `.env` para o GitHub. Adicione-o ao `.gitignore`.

## 🔒 Segurança

O bot aceita comandos **apenas do Chat ID configurado no `.env`**, bloqueando qualquer outro remetente automaticamente.
