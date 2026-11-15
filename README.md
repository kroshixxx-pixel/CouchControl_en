# CouchControl — English version

[Русская версия проекта](https://github.com/kroshixxx-pixel/CouchControl)

**Control your own Windows PC through a personal Telegram bot.**

> **English documentation is available.** This file is the English version of the project documentation. The Russian version is available in [README.md](README.md).

CouchControl is a Windows agent paired with a Telegram bot. It lets an authorized user control selected PC functions from a private Telegram chat.

> **Project status:** CouchControl is under development. Test it on a separate machine before relying on it on your main PC. This document describes the code currently present in this branch; it is not a promise of flawless operation or complete security.

## Features

After the bot starts, send `/start` to display its control menu.

| Section | Current functionality |
|---|---|
| Mouse | Move the cursor in eight directions, left/right click, and scroll |
| Keyboard | Paste text into the active window; send Enter, Esc, Tab, arrow keys, Space, Backspace, Ctrl+C, Ctrl+V and Alt+Tab where implemented |
| Volume | Increase/decrease volume and mute/unmute |
| Media | Play/pause, previous track and next track |
| Shortcuts | Common Windows shortcuts such as Alt+F4, Win+D, Win+I, Ctrl+Shift+Esc, Alt+Tab, Win+E and Win+R |
| Apps | Launch a fixed list of apps: Notepad, Calculator, File Explorer and Paint |
| Capture | Request a desktop screenshot; the installer bot variant also supports a 15-second MP4 recording |
| Power | Lock, shut down or restart the PC. Shutdown/restart require confirmation and are scheduled with a 30-second cancellation window |
| Status | Ask the bot whether its handler is responding |
| Stop bot | Stop the bot process. This does not shut down Windows; launch CouchControl on the PC to start it again |

Some actions happen immediately. Power actions require a separate confirmation.

## Mini App status

The Mini App source is in `CouchControl/` (`index.html`, `app.js`, and `style.css`). Its interface is localized in English. The screenshot request is sent to the bot, and the touchpad can communicate with the local API through an HTTPS tunnel when configured.

**Important:** the keyboard and action tiles in the Mini App are currently visual placeholders and are not connected to PC actions. The Mini App does not provide a live video stream. Do not confuse its demo controls with implemented bot controls.

## How it works

1. CouchControl runs locally on the Windows PC.
2. The agent connects to Telegram using the Telegram Bot API long polling.
3. The owner sends commands using buttons in a private chat with the bot.
4. The bot checks the sender's numeric Telegram user ID and requires a private chat.
5. If authorized, the agent performs the requested action in the current Windows user session.
6. Bot replies, screenshots and supported recordings are sent back through Telegram.

The PC must be powered on, connected to the internet, and have an accessible Windows user session. CouchControl is not a cloud desktop: the control agent runs on the PC being controlled.

### Local web API

The Mini App's local HTTP API binds to `127.0.0.1`, not to all network interfaces. Protected requests check the expected Origin, Telegram Web App init-data signature and the allowed user ID. The current API exposes mouse movement and click operations. These measures do not amount to a full security audit.

## Installation

The installer workflow is designed to:

1. Launch `CouchControl-Setup.exe`.
2. Ask for the user's own Telegram bot token (created with [@BotFather](https://t.me/BotFather)).
3. Ask for the numeric Telegram User ID allowed to control the PC.
4. Prepare a private Python runtime and install the required packages.
5. Save the Telegram settings locally and offer to launch CouchControl.

The installer targets 64-bit Windows 10/11. An internet connection is required during setup to download Python and Python packages. The Inno Setup script includes optional desktop shortcut and Windows sign-in startup tasks.

**The installer is still under development and must be tested on a clean Windows machine.** Successfully compiling the Inno Setup script does not prove that installation or first launch works.

## Security and privacy

CouchControl can control the mouse, keyboard and power state of the PC, so treat its access as sensitive.

### Protections present in the code

- **Telegram user-ID allowlist:** commands are accepted only from the configured user and only in a private chat.
- **No arbitrary chat shell commands:** app launching uses a fixed application list and does not invoke a shell.
- **Power confirmation:** shutdown and restart require a second confirmation and can be cancelled during the 30-second delay.
- **Local API binding:** the Mini App API listens on `127.0.0.1`.
- **Mini App request validation:** the API checks Origin, Telegram init-data signature and the configured user ID.
- **PyAutoGUI failsafe:** the library's standard failsafe is enabled.

### Important limitations

- **The bot token is a secret.** It is stored in the local `.env` file as plain text. Never publish or share this file, and never commit a real token to Git. Only a token-free `.env.example` belongs in the repository.
- **A Telegram user ID is not a substitute for the token.** It restricts who can issue commands, but it cannot protect a bot whose token has been stolen. Revoke a leaked token through @BotFather and generate a new one.
- **PC control has real effects.** Mouse and keyboard actions are performed in the active Windows session. Keep your Telegram account and devices protected.
- **Screenshots and recordings may expose private information.** They are sent through Telegram and can contain messages, documents, notifications or other visible content.
- **Diagnostic logs may contain technical or personal information.** Review and redact them before sharing.
- **Third-party dependencies are part of the trust boundary.** The application depends on Python, external packages and their distribution channels.
- **No independent security audit has been performed.** The project does not guarantee protection against malware on the PC, Telegram account compromise, dependency vulnerabilities or configuration mistakes.

### Recommendations

1. Create a separate Telegram bot for CouchControl.
2. Keep the bot token only in the local `.env` file.
3. Enable Telegram two-step verification and device lock protection.
4. Use CouchControl only on a PC you own or have explicit permission to control.
5. Test it on a non-critical machine before regular use.
6. If the token is exposed, revoke it immediately through @BotFather.

## Requirements

- 64-bit Windows 10 or Windows 11.
- Internet access on the PC.
- Your own Telegram bot and its token.
- The numeric Telegram User ID authorized to control the PC.
- An active Windows user session for desktop control.

## Troubleshooting

If installation fails, inspect these files in the Windows temporary directory:

- `%TEMP%\\CouchControl-install-diagnostic.log`
- `%TEMP%\\CouchControl-Python-install.log`

Review logs for secrets and personal data before sharing them.

## Source layout

- `CouchControl/bot.py` — Telegram bot and button handlers.
- `CouchControl/web_server.py` — local API used by the Mini App.
- `CouchControl/index.html`, `app.js`, `style.css` — Mini App interface.
- `CouchControl/requirements.txt` — Python dependencies.
- `setup/CouchControl/install.ps1` — private Python runtime and dependency setup.
- `setup/CouchControl/CouchControl.iss` — Inno Setup installer script.

Please use GitHub Issues for bug reports and suggestions.

## License

Add a license file before distributing the project, and review the licenses of all third-party dependencies.
