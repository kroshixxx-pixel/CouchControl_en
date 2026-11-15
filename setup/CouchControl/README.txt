# CouchControl — Installation

CouchControl lets you control your Windows PC through your personal Telegram bot.

## Install

1. Run `CouchControl-Setup.exe`.
2. Enter the token for your Telegram bot, created with @BotFather.
3. Enter your numeric Telegram User ID.
4. Wait for setup to finish.
5. Open your bot in Telegram and send `/start`.

The installer prepares a private Python runtime, installs the required packages and saves your Telegram settings. It does not need to remove or modify other system-wide Python installations.

The installer offers an option to start CouchControl automatically when you sign in to Windows.

## Mini App

The Mini App interface is in the `CouchControl` folder. The screenshot request is sent to the bot. The touchpad requires a configured HTTPS tunnel to reach the local PC API. Keyboard and action tiles are currently placeholders.

## Stop the bot

Use the stop option in the Telegram bot menu. After confirmation, CouchControl exits. To connect again, launch CouchControl on the PC using its Start menu or desktop shortcut. Stopping the bot does not shut down Windows.

## Requirements

- 64-bit Windows 10 or Windows 11.
- Internet access during installation and while using the bot.
- Your own Telegram bot and its token.
- Your numeric Telegram User ID.

## Important

- Never share your bot token or publish the `.env` file.
- The PC must be powered on and connected to the internet for the bot to respond.
- CouchControl must be running on the PC being controlled.
- If installation fails, inspect `%TEMP%\\CouchControl-install-diagnostic.log` and, if present, `%TEMP%\\CouchControl-Python-install.log`.
