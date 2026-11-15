# 🤖 CouchControl — manual setup guide (legacy)

This guide describes the older manual source-based setup. For the current installer workflow, use the repository's [README](../README.md) or [English README](../README.en.md), and build the installer from `setup/CouchControl/`.

## 1. Prepare

1. Install Python 3.12 if you are using this legacy source layout: https://www.python.org/downloads/release/python-31210/
2. If required by your setup, enable **Add Python to PATH**.
3. Download the CouchControl source archive.
4. Extract it to a convenient folder.

## 2. Create a Telegram bot

1. Open Telegram and find [@BotFather](https://t.me/BotFather).
2. Send `/newbot`.
3. Choose a display name for your bot.
4. Choose a username ending in `bot`.
5. Copy the token and keep it private.

## 3. Install dependencies

Open PowerShell in the source folder and run:

```powershell
py -3.12 -m venv .venv
```

If PowerShell blocks activation scripts, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Confirm with `Y`, then run:

```powershell
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure the bot

1. Copy `.env.example` to a new file named `.env`.
2. Open `.env` in a text editor.
3. Put your BotFather token after `BOT_TOKEN=`.
4. Keep `ALLOWED_USER_ID=0` for the first launch.
5. Save the file.

## 5. First launch

Run:

```powershell
python bot.py
```

Open your bot in Telegram and send `/myid`. The bot replies with your numeric Telegram user ID.

1. Stop the program with Ctrl+C.
2. Open `.env`.
3. Replace `ALLOWED_USER_ID=0` with your numeric ID.
4. Save the file and start the bot again:

```powershell
python bot.py
```

5. Send `/start` to the bot.

## 6. Windows startup

The current installer can create a Windows sign-in startup entry. Prefer that option over manually editing startup scripts.

## Security notes

- Use your own Telegram bot and token.
- Never share or publish the `.env` file.
- Do not publish your bot token.
- Keep your Telegram account protected.
- The PC must be powered on and not sleeping for the bot to respond.
