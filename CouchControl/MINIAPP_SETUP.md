# CouchControl Mini App — first launch

The Mini App is currently a front-end demo. Its screen preview and controls are placeholders; they do not send input to the PC yet.

## 1. Publish the web interface

1. Open the repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Open the **Actions** tab and wait for **Deploy CouchControl Mini App** to finish successfully.

The expected address is:

https://kroshixxx-pixel.github.io/CouchControl/

## 2. Tell Telegram the Mini App domain

In the official BotFather chat, use `/setdomain` and select your CouchControl bot. Enter:

`kroshixxx-pixel.github.io`

## 3. Update the PC bot

The bot code now has a **📱 Open CouchControl** button. The default web address is already set in `bot.py`. Pull the latest repository version to the PC (or copy the updated `CouchControl/bot.py`), then restart CouchControl.

Do not put your Telegram bot token in GitHub or in the Mini App files. Keep it only in the local `.env` file on the PC.

## Next development stage

Connect the Mini App to the Windows agent through an authenticated HTTPS channel. Until that is implemented, touchpad, keyboard and action buttons are visual demo controls only. The screen area is not a live stream.
