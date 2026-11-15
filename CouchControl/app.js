(() => {
  const tg = window.Telegram?.WebApp;
  if (tg) { tg.ready(); tg.expand(); }
  const tabs = [...document.querySelectorAll(".tab")];
  const titles = {touchpad:"Mouse",keyboard:"Keyboard",buttons:"Buttons"};
  const counts = {touchpad:"01 / 03",keyboard:"02 / 03",buttons:"03 / 03"};
  const hints = {
    touchpad:"Hold one of the eight arrows to move the PC cursor.",
    keyboard:"Keyboard controls will be added in a future update.",
    buttons:"Action buttons will be added in a future update."
  };
  tabs.forEach(tab => tab.addEventListener("click", () => {
    const mode = tab.dataset.mode;
    tabs.forEach(item => item.classList.toggle("active", item === tab));
    document.querySelectorAll(".mode-view").forEach(view => view.classList.toggle("active", view.id === mode + "-view"));
    document.getElementById("mode-title").textContent = titles[mode];
    document.querySelector(".mode-count").textContent = counts[mode];
    document.getElementById("demo-hint").textContent = hints[mode];
  }));

  const screenshotButton = document.getElementById("send-screenshot");
  const screenshotStatus = document.getElementById("screenshot-status");
  screenshotButton?.addEventListener("click", () => {
    if (!tg?.initData || typeof tg.sendData !== "function") {
      screenshotStatus.textContent = "Open the Mini App using the button at the bottom of your bot chat.";
      return;
    }
    screenshotButton.disabled = true;
    screenshotStatus.textContent = "Sending request to the bot…";
    tg.sendData(JSON.stringify({action:"screenshot"}));
  });

  const input = document.getElementById("api-url");
  const status = document.getElementById("connection-status");
  const connect = document.getElementById("connect-btn");
  let apiBase = localStorage.getItem("couchcontrol_api") || new URLSearchParams(location.search).get("api") || "";
  if (apiBase) input.value = apiBase;

  const request = async (path, payload) => {
    if (!apiBase || !tg?.initData) throw new Error("Open the Mini App from Telegram and enter the connection address.");
    const response = await fetch(apiBase + path, {
      method: "POST",
      headers: {"Content-Type":"application/json","X-Telegram-Init-Data":tg.initData},
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error("Connection error (" + response.status + ")");
    return response.json();
  };

  connect.addEventListener("click", async () => {
    const value = input.value.trim().replace(/\/$/, "");
    if (!/^https:\/\/[a-z0-9.-]+$/.test(value)) {
      status.textContent = "Enter the HTTPS address of your Cloudflare Tunnel.";
      return;
    }
    try {
      const response = await fetch(value + "/api/health");
      if (!response.ok) throw new Error("The server did not respond");
      apiBase = value;
      localStorage.setItem("couchcontrol_api", apiBase);
      status.textContent = "Server found. Telegram access will be verified on the first movement.";
    } catch (_error) {
      status.textContent = "Could not reach the PC. Check the address and make sure the tunnel is running.";
    }
  });

  const speedControl = document.getElementById("mouse-speed");
  let moveTimer = null;
  let moveInFlight = false;
  let activeDirection = null;

  const stopMoving = () => {
    if (moveTimer) clearInterval(moveTimer);
    moveTimer = null;
    activeDirection = null;
  };

  const sendDirection = async () => {
    if (!activeDirection || moveInFlight) return;
    moveInFlight = true;
    const step = Number(speedControl.value || 28);
    try {
      await request("/api/mouse/move", {
        dx: activeDirection.dx * step,
        dy: activeDirection.dy * step
      });
    } catch (error) {
      status.textContent = error.message;
      stopMoving();
    } finally {
      moveInFlight = false;
    }
  };

  document.querySelectorAll(".direction-btn").forEach(button => {
    button.addEventListener("pointerdown", event => {
      event.preventDefault();
      stopMoving();
      if (button.dataset.stop === "true") return;
      activeDirection = {dx:Number(button.dataset.dx),dy:Number(button.dataset.dy)};
      button.setPointerCapture?.(event.pointerId);
      if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
      sendDirection();
      moveTimer = setInterval(sendDirection, 110);
    });
    button.addEventListener("pointerup", stopMoving);
    button.addEventListener("pointercancel", stopMoving);
    button.addEventListener("lostpointercapture", stopMoving);
    button.addEventListener("contextmenu", event => event.preventDefault());
  });
  window.addEventListener("pointerup", stopMoving);
  window.addEventListener("blur", stopMoving);

  document.querySelectorAll(".mouse-btn").forEach(button => {
    button.addEventListener("click", async () => {
      try { await request("/api/mouse/click", {button:button.dataset.button}); }
      catch (error) { status.textContent = error.message; }
    });
  });
  document.querySelectorAll(".key,.action-tile").forEach(button => {
    button.addEventListener("click", () => {
      if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
      document.getElementById("demo-hint").textContent = "This feature will be added in a future update.";
    });
  });
})();