/**
 * AI Cyber Value Creator — Hermes Dashboard Plugin
 *
 * The roadmap page: Create Value foundation (ICP → Problems → Solutions →
 * Offer → Elevator Pitch), the shared Company Context panel, the four-phase
 * flywheel (Attract / Nurture / Convert / Deliver) with the clockwise arrow
 * hub, and the Laps / Phases / Sequence views. Faithful port of the paperclip
 * plugin's roadmap page onto the hermes dashboard SDK.
 *
 * Plain IIFE, no build step. Uses window.__HERMES_PLUGIN_SDK__ for React and
 * calls the plugin backend at /api/plugins/ai-cyber-value-creator/. Step tasks
 * are hermes kanban tasks; deep links go to the Kanban tab and the worker
 * session's chat thread.
 */
(function () {
  "use strict";

  var SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK || !window.__HERMES_PLUGINS__) return;

  // -------------------------------------------------------------------------
  // Flywheel phase groups — collapsible ATTRACT/NURTURE/CONVERT/DELIVER
  // section headers at the bottom of the branded sidebar block. YouTube
  // Insights nests under ATTRACT (pure CSS ordering + :has, no React DOM
  // moves); empty phases show a "coming soon" placeholder until their
  // plugins ship. Injected with an ensure-loop (React re-renders can drop
  // appended children — same self-healing pattern as the header pills).
  // -------------------------------------------------------------------------
  (function phaseGroups() {
    // Planned tools per phase (two-word names from the coverage plan); each
    // renders as a stacked menu item with a right-aligned "soon" pill until
    // its plugin ships (then the real link replaces it here).
    // Tools listed in roadmap-step order per pillar (A1→A3, N1→N3, C1→C3,
    // D1→D3). Offer Forge is Foundation F4 but lives at the top of CONVERT
    // as its commercial front door. NURTURE's pre-stack renders above the
    // real YouTube Insights link (N2); its items stack below it.
    var PHASES = [
      { id: "attract", label: "ATTRACT",
        items: ["Referral Ledger", "Tribe Builder"] },   // Shorts Lab shipped — real /shorts link below the stack
      { id: "nurture", label: "NURTURE",
        pre: ["Community Engine"],
        items: ["Funnel Automations"] },
      { id: "convert", label: "CONVERT",
        items: ["Sales Forge", "Waitlist Gate", "Campaign Scheduler"] },
      { id: "deliver", label: "DELIVER",
        pre: ["Journey Choreographer"],
        items: ["Testimonial Collector"] },
    ];
    function ensure() {
      try {
        if (document.getElementById("acvc-pg-attract-head")) return;
        var G = document.querySelector('div[aria-labelledby="hermes-sidebar-plugin-nav-heading"]');
        if (!G) return;
        var ul = G.querySelector("ul");
        if (!ul) return;
        PHASES.forEach(function (p) {
          var id = p.id, label = p.label;
          var open = true;
          try { open = localStorage.getItem("acvc-pg-" + id) !== "0"; } catch (e) {}

          function itemStack(domId, tools) {
            var li = document.createElement("li");
            li.id = domId;
            li.className = "acvc-pg-holder acvc-pg-items" + (open ? " acvc-pg-open" : "");
            tools.forEach(function (name) {
              var row = document.createElement("div");
              row.className = "acvc-pg-item";
              row.title = name + " — planned, not yet available";
              var nm = document.createElement("span");
              nm.textContent = name;
              var tag = document.createElement("span");
              tag.className = "acvc-pg-soon";
              tag.textContent = "soon";
              row.appendChild(nm);
              row.appendChild(tag);
              li.appendChild(row);
            });
            return li;
          }

          var headLi = document.createElement("li");
          headLi.id = "acvc-pg-" + id + "-head";
          headLi.className = "acvc-pg-holder" + (open ? " acvc-pg-open" : "");
          var head = document.createElement("button");
          head.type = "button";
          head.className = "acvc-pg-head";
          head.title = "Flywheel phase";
          head.innerHTML = '<span class="acvc-pg-chev">▶</span>' + label;
          headLi.appendChild(head);

          var stacks = [];
          if (p.pre && p.pre.length)
            stacks.push(itemStack("acvc-pg-" + id + "-pre", p.pre));
          stacks.push(itemStack("acvc-pg-" + id + "-items", p.items));

          head.onclick = function () {
            var nowOpen = !headLi.classList.contains("acvc-pg-open");
            headLi.classList.toggle("acvc-pg-open", nowOpen);
            stacks.forEach(function (li) {
              li.classList.toggle("acvc-pg-open", nowOpen);
            });
            try { localStorage.setItem("acvc-pg-" + id, nowOpen ? "1" : "0"); } catch (e) {}
          };

          ul.appendChild(headLi);
          stacks.forEach(function (li) { ul.appendChild(li); });
        });
      } catch (e) { /* cosmetic */ }
    }
    setInterval(ensure, 1500);
    ensure();
  })();

  // First-login onboarding redirect: exactly once per browser, EVERY first
  // login lands on the Roadmap — its Getting Started card walks the mentee
  // through keys and everything else. Only the generic landing routes
  // redirect; deep links stay untouched. Synchronous, so it wins the race
  // with the SPA router.
  try {
    if (!localStorage.getItem("acvc-first-login-redirect")) {
      localStorage.setItem("acvc-first-login-redirect", "1");
      var p0 = window.location.pathname;
      if (p0 === "/" || p0 === "/chat" || p0 === "/sessions") {
        window.location.assign("/roadmap");
      }
    }
  } catch (e) { /* storage unavailable — skip the nicety */ }

  // Sidebar: surface the Plugins section ABOVE the core nav — the plugin
  // tabs are the product for mentees. Pure CSS reorder (order:-1) against
  // the sidebar's stable aria hooks, so React re-renders can't undo it and
  // no hermes code changes.
  try {
    if (!document.getElementById("acvc-sidebar-order")) {
      var acvcNavStyle = document.createElement("style");
      acvcNavStyle.id = "acvc-sidebar-order";
      var G = 'div[aria-labelledby="hermes-sidebar-plugin-nav-heading"]';
      acvcNavStyle.textContent =
        'nav:has(> ' + G + '){display:flex;flex-direction:column;}' +
        'nav > ' + G + '{order:-1;border-top:0;' +
        'border-bottom:1px solid color-mix(in srgb, currentColor 10%, transparent);}' +
        // Branded split: our tabs first under "AI CYBER VALUE CREATOR"
        // (Your Level, then Roadmap, then YouTube), everything else under
        // "HERMES PLUGINS". Pure CSS (order + ::before labels) against
        // stable hrefs, so React re-renders can't undo it. The section
        // label sits on /level when that plugin is installed and falls
        // back to /roadmap when it isn't.
        '#hermes-sidebar-plugin-nav-heading{display:none;}' +
        G + ' > ul{display:flex;flex-direction:column;}' +
        G + ' li{order:1;}' +
        G + ' li:has(> a[href="/brief"]){order:-20;}' +
        G + ' li:has(> a[href="/level"]){order:-19;}' +
        G + ' li:has(> a[href="/roadmap"]){order:-18;}' +
        // NURTURE holds YouTube Insights; its soon-items stack below the link
        G + ' li:has(> a[href="/youtube"]){order:-10;margin-left:14px;}' +
        '#acvc-pg-attract-head{order:-15;}#acvc-pg-attract-items{order:-14;}' +
        G + ' li:has(> a[href="/shorts"]){order:-13;margin-left:14px;}' +
        '#acvc-pg-nurture-head{order:-12;}#acvc-pg-nurture-pre{order:-11;}' +
        '#acvc-pg-nurture-items{order:-9;}' +
        '#acvc-pg-convert-head{order:-7;}#acvc-pg-convert-items{order:-6;}' +
        '#acvc-pg-deliver-head{order:-5;}#acvc-pg-deliver-pre{order:-4;}' +
        G + ' li:has(> a[href="/delivery"]){order:-3;margin-left:14px;}' +
        '#acvc-pg-deliver-items{order:-2;}' +
        G + ':has(#acvc-pg-deliver-head:not(.acvc-pg-open)) li:has(> a[href="/delivery"]){display:none;}' +
        '.acvc-pg-holder{list-style:none;margin:0;padding:0;}' +
        // collapsing NURTURE hides its nested real link (pure CSS via :has)
        G + ':has(#acvc-pg-nurture-head:not(.acvc-pg-open)) li:has(> a[href="/youtube"]){display:none;}' +
        '.acvc-pg-items{display:none;}' +
        '.acvc-pg-items.acvc-pg-open{display:block;}' +
        G + ':has(> span[class~="lg:hidden"]) .acvc-pg-holder{display:none;}' +
        '.acvc-pg-head{display:flex;align-items:center;gap:6px;width:100%;' +
        'background:none;border:none;cursor:pointer;text-align:left;' +
        'padding:8px 20px 3px;font-size:11px;letter-spacing:0.12em;font-weight:600;' +
        'color:var(--color-muted-foreground,#9aa0b4);font-family:inherit;}' +
        '.acvc-pg-head:hover{color:currentColor;}' +
        '.acvc-pg-chev{display:inline-block;font-size:9px;transition:transform 0.12s ease;}' +
        '.acvc-pg-open .acvc-pg-chev{transform:rotate(90deg);}' +
        '.acvc-pg-item{display:flex;align-items:center;justify-content:space-between;' +
        'gap:8px;padding:3px 20px 3px 33px;font-size:12.5px;' +
        'color:var(--color-muted-foreground,#9aa0b4);cursor:default;opacity:0.5;}' +
        '.acvc-pg-item span:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}' +
        '.acvc-pg-soon{flex-shrink:0;font-size:9px;letter-spacing:0.08em;' +
        'text-transform:uppercase;font-weight:700;padding:1px 7px;border-radius:999px;' +
        'border:1px solid color-mix(in srgb, currentColor 35%, transparent);}' +
        G + ' li:has(> a[href="/level"])::before{content:"AI CYBER VALUE CREATOR";}' +
        G + ':not(:has(a[href="/level"])) li:has(> a[href="/roadmap"])::before{content:"AI CYBER VALUE CREATOR";}' +
        G + ' li:has(> a[href="/kanban"])::before{content:"HERMES PLUGINS";}' +
        G + ' li:has(> a[href="/level"])::before,' +
        G + ' li:has(> a[href="/roadmap"])::before,' + G + ' li:has(> a[href="/kanban"])::before{' +
        'display:block;padding:10px 20px 4px;font-size:11px;letter-spacing:0.12em;' +
        'font-weight:600;color:var(--color-muted-foreground,#9aa0b4);}' +
        // Collapsed sidebar (heading carries lg:hidden): no room for labels.
        G + ':has(> span[class~="lg:hidden"]) li::before{display:none;}';
      document.head.appendChild(acvcNavStyle);
    }
  } catch (e) { /* styling nicety only */ }

  // Distribution default theme: cyberpunk — applied ONLY when the mentee
  // has never picked a theme (host key absent). A chosen theme always wins.
  try {
    if (window.localStorage.getItem("hermes-dashboard-theme") === null) {
      window.localStorage.setItem("hermes-dashboard-theme", "cyberpunk");
    }
    // …and the system sans font (the font selector in the sidebar footer) —
    // cyberpunk colors, readable type. A saved choice always wins.
    if (window.localStorage.getItem("hermes-dashboard-font") === null) {
      window.localStorage.setItem("hermes-dashboard-font", "system-sans");
    }
  } catch (e) { /* private mode etc. */ }

  // -------------------------------------------------------------------------
  // Update-available button — injected on the right side of the top header
  // bar when a newer image than the running one has been published. Links
  // (new tab) to the Railway service page where Redeploy pulls :stable.
  // -------------------------------------------------------------------------
  (function updateButton() {
    var info = null;
    function ensure() {
      try {
        // Railway-only: the button and its redeploy guidance are meaningless
        // on other hosts (railwayUrl exists only when Railway injected its
        // project/service ids). Others never see this.
        if (!info || !info.updateAvailable || !info.railwayUrl) return;
        if (document.getElementById("acvc-update-btn")) return;
        var headers = [].slice.call(document.querySelectorAll("header"));
        var bar = headers.filter(function (x) {
          return !/lg:hidden/.test(String(x.className));
        })[0] || headers[0];
        if (!bar) return;
        var a = document.createElement("a");
        a.id = "acvc-update-btn";
        a.href = "#";
        a.title = "Version " + info.latest + " is available (you run " +
          info.current + "). Click for update instructions.";
        a.onclick = function (e) { e.preventDefault(); showModal(); };
        a.textContent = "⬆ Update available";
        a.style.cssText =
          "margin-left:auto;margin-right:18px;flex-shrink:0;font-size:12px;font-weight:700;" +
          "letter-spacing:0.04em;padding:4px 12px;border-radius:999px;" +
          "text-decoration:none;color:#04211c;cursor:pointer;" +
          "background:linear-gradient(120deg,#34d399,#a7f3d0);" +
          "box-shadow:0 0 12px rgba(52,211,153,0.5);" +
          "animation:acvc-update-pulse 2.6s ease-in-out infinite;";
        bar.style.display = "flex";
        bar.style.alignItems = "center";
        bar.appendChild(a);
      } catch (e) { /* cosmetic */ }
    }
    function behindText() {
      // Versions are America/New_York wall-clock stamps: YYYY.MMDD.HHMM.
      function parse(v) {
        var m = /^(\d{4})\.(\d{2})(\d{2})\.(\d{2})(\d{2})$/.exec(v || "");
        if (!m) return null;
        return Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
      }
      var a = parse(info.current), b = parse(info.latest);
      if (a == null || b == null || b <= a) return "";
      var mins = Math.floor((b - a) / 60000);
      var hours = Math.floor(mins / 60);
      var days = Math.floor(hours / 24);
      var parts = [];
      if (days) {
        parts.push(days + (days === 1 ? " day" : " days"));
        var hr = hours % 24;
        if (hr) parts.push(hr + (hr === 1 ? " hour" : " hours"));
      } else if (hours) {
        parts.push(hours + (hours === 1 ? " hour" : " hours"));
        var mr = mins % 60;
        if (mr) parts.push(mr + (mr === 1 ? " minute" : " minutes"));
      } else {
        parts.push(mins + (mins === 1 ? " minute" : " minutes"));
      }
      return " Your deployment is " + parts.join(" and ") + " behind.";
    }

    function reportHref() {
      var subject = "hermes-plugins update issue (" +
        (info.current || "?") + " -> " + (info.latest || "?") + ")";
      var body = "What happened after the update:\n\n\n---\n" +
        "Running: " + (info.current || "?") + "\n" +
        "Latest: " + (info.latest || "?") + "\n" +
        "Rolled back: yes/no\n";
      return "mailto:allen@allenharper.com?subject=" +
        encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
    }

    function showModal() {
      if (document.getElementById("acvc-update-modal")) return;
      var overlay = document.createElement("div");
      overlay.id = "acvc-update-modal";
      overlay.className = "acvc-update-overlay";
      function close() { overlay.remove(); }
      overlay.onclick = function (e) { if (e.target === overlay) close(); };

      var box = document.createElement("div");
      box.className = "acvc-update-box";
      box.innerHTML =
        '<div class="acvc-update-title">⬆ Update your deployment</div>' +
        '<div class="acvc-update-sub">Version <b>' + (info.latest || "?") +
        "</b> is published — you're running <b>" + (info.current || "?") +
        "</b>." + behindText() +
        " Redeploying pulls the update; your data and settings are on " +
        "the volume and are kept.</div>" +
        '<img class="acvc-update-img" alt="Railway deployments page: the three-dot menu on the ACTIVE deployment, with Redeploy highlighted" ' +
        'src="/dashboard-plugins/ai-cyber-value-creator/dist/railway-redeploy.png">' +
        '<ol class="acvc-update-steps">' +
        "<li>On your Railway service page, find the <b>ACTIVE</b> deployment " +
        "and click its <b>⋮</b> (three-dot) button.</li>" +
        "<li>Select <b>Redeploy</b> — Railway pulls the newest image.</li>" +
        "<li>Wait for the green <b>Deployment successful</b> status, then " +
        "open your URL again (or just refresh this page).</li>" +
        "</ol>" +
        '<div class="acvc-update-rollback">' +
        "<b>Trouble after the update?</b> Roll back: on the same page, under " +
        "<b>HISTORY</b>, click the <b>⋮</b> on the most recent previous " +
        "deployment and choose <b>Rollback</b>. Railway restores exactly the " +
        "version that was running before — your data and settings stay as " +
        "they are — and you can try the update again any time. Then " +
        '<a class="acvc-update-report" href="' + reportHref() + '">' +
        "report the issue to your mentor ↗</a> so it gets fixed.</div>";

      var row = document.createElement("div");
      row.className = "acvc-update-actions";
      var cancel = document.createElement("button");
      cancel.className = "acvc-update-cancel";
      cancel.textContent = "Cancel";
      cancel.onclick = close;
      row.appendChild(cancel);
      var go = document.createElement("a");
      go.className = "acvc-update-go";
      go.href = info.railwayUrl;
      go.target = "_blank";
      go.rel = "noreferrer";
      go.textContent = "Open Railway ↗";
      go.onclick = function () { close(); };
      row.appendChild(go);
      box.appendChild(row);
      overlay.appendChild(box);
      document.body.appendChild(overlay);
    }

    function poll() {
      SDK.fetchJSON("/api/plugins/ai-cyber-value-creator/update-check")
        .then(function (d) {
          info = d;
          var old = document.getElementById("acvc-update-btn");
          if (old && (!d || !d.updateAvailable || !d.railwayUrl)) old.remove();
          ensure();
        })
        .catch(function () { /* try again next poll */ });
    }
    poll();
    setInterval(poll, 30 * 60 * 1000);           // fresh check every 30 min
    setInterval(ensure, 2000);                   // survive React re-renders
  })();

  // -------------------------------------------------------------------------
  // Weekly feedback pill — left of the update pill when both show. Green
  // when submitted within 7 days, yellow (pulsing) past a week or never,
  // red (pulsing) past two weeks. Opens the stoplight check-in modal.
  // Appears only when the mentor's Feedback Hub is configured.
  // -------------------------------------------------------------------------
  function acvcBurstConfetti() {
    var layer = document.getElementById("acvc-confetti-layer");
    if (!layer) {
      layer = document.createElement("div");
      layer.id = "acvc-confetti-layer";
      layer.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:120;";
      document.body.appendChild(layer);
    }
    var colors = ["#ffd700", "#ff6b35", "#4ecdc4", "#5b8cff", "#b56bff", "#2ecc71"];
    for (var i = 0; i < 80; i++) {
      var p = document.createElement("div");
      p.className = "acvc-confetti";
      p.style.background = colors[i % colors.length];
      p.style.left = 50 + (Math.random() - 0.5) * 30 + "%";
      p.style.setProperty("--dx", (Math.random() - 0.5) * 90 + "vw");
      p.style.setProperty("--dy", -(20 + Math.random() * 60) + "vh");
      p.style.setProperty("--rot", Math.random() * 1080 + "deg");
      p.style.animationDelay = Math.random() * 0.3 + "s";
      layer.appendChild(p);
      (function (el) { setTimeout(function () { el.remove(); }, 3800); })(p);
    }
  }

  (function feedbackPill() {
    var fstat = null;
    var COLORS = {
      green: "linear-gradient(120deg,#34d399,#a7f3d0)",   // same as update pill
      yellow: "linear-gradient(120deg,#f59e0b,#fde68a)",
      red: "linear-gradient(120deg,#ef4444,#fca5a5)",
    };
    function ensure() {
      try {
        if (!fstat || !fstat.configured) return;
        var btn = document.getElementById("acvc-feedback-btn");
        if (!btn) {
          var headers = [].slice.call(document.querySelectorAll("header"));
          var bar = headers.filter(function (x) {
            return !/lg:hidden/.test(String(x.className));
          })[0] || headers[0];
          if (!bar) return;
          btn = document.createElement("a");
          btn.id = "acvc-feedback-btn";
          btn.href = "#";
          btn.textContent = "📝 Weekly feedback";
          btn.onclick = function (e) { e.preventDefault(); showFeedbackModal(); };
          bar.style.display = "flex";
          bar.style.alignItems = "center";
          bar.appendChild(btn);
        }
        var f = fstat.freshness || "yellow";
        // Fresh (green) = the standing "Daily feedback" invitation, calm and
        // the same shade as the update pill. Once the last check-in is more
        // than 24h old the green pill pulses visibly (today's check-in is
        // due). Past a week it becomes the pulsing yellow "Weekly feedback"
        // nag; past two, pulsing red.
        var dailyDue = f === "green" && fstat.lastSubmittedAt &&
          (Date.now() / 1000 - fstat.lastSubmittedAt) > 24 * 3600;
        btn.textContent = f === "green" ? "📝 Daily feedback" : "📝 Weekly feedback";
        btn.style.cssText =
          "margin-left:auto;margin-right:18px;flex-shrink:0;font-size:12px;" +
          "font-weight:700;letter-spacing:0.04em;padding:4px 12px;" +
          "border-radius:999px;text-decoration:none;color:#04211c;" +
          "cursor:pointer;order:97;" +
          "background:" + COLORS[f] + ";" +
          (f === "yellow"
            ? "animation:acvc-feedback-pulse-yellow 1.5s ease-in-out infinite;"
            : f === "red"
              ? "animation:acvc-feedback-pulse-red 1.3s ease-in-out infinite;"
              : dailyDue
                ? "animation:acvc-feedback-pulse-daily 1.5s ease-in-out infinite;"
                : "");
        btn.title = fstat.lastSubmittedAt
          ? "Last check-in: " + new Date(fstat.lastSubmittedAt * 1000).toLocaleString()
          : "No check-in yet — your mentor is waiting to hear from you";
        // sit LEFT of the update pill when it exists (kill its auto margin
        // every tick — its own ensure() may recreate it)
        var up = document.getElementById("acvc-update-btn");
        if (up) { up.style.order = "98"; up.style.marginLeft = "8px"; }
      } catch (e) { /* cosmetic */ }
    }
    function poll() {
      SDK.fetchJSON("/api/plugins/ai-cyber-value-creator/feedback/status")
        .then(function (d) {
          fstat = d;
          var old = document.getElementById("acvc-feedback-btn");
          if (old && (!d || !d.configured)) old.remove();
          ensure();
        })
        .catch(function () {});
    }

    function light(color, face, label) {
      return '<button type="button" class="acvc-fb-light acvc-fb-' + color +
        '" data-c="' + color + '" title="' + label + '">' +
        '<span class="acvc-fb-face">' + face + "</span></button>";
    }

    function showFeedbackModal() {
      if (document.getElementById("acvc-fb-modal")) return;
      var overlay = document.createElement("div");
      overlay.id = "acvc-fb-modal";
      overlay.className = "acvc-update-overlay";
      function close() { overlay.remove(); }
      overlay.onclick = function (e) { if (e.target === overlay) close(); };

      var daily = fstat && fstat.freshness === "green";
      var ident = (fstat && fstat.identity) || { name: "", email: "" };
      var hasIdent = !!(ident.name && ident.email);
      var prefillEmail = ident.email || (fstat && fstat.loginEmail) || "";
      var box = document.createElement("div");
      box.className = "acvc-update-box";
      box.innerHTML =
        '<div class="acvc-update-title">' +
        (daily ? "How are you doing today?" : "How are you doing this week?") +
        "</div>" +
        '<div class="acvc-fb-ident' + (hasIdent ? " acvc-fb-ident-locked" : "") + '">' +
        '  <div class="acvc-fb-ident-fields">' +
        '    <div><label>Full name</label>' +
        '    <input type="text" id="acvc-fb-name" placeholder="Your full name" value="' +
        String(ident.name || "").replace(/"/g, "&quot;") + '"' +
        (hasIdent ? " disabled" : "") + "></div>" +
        '    <div><label>Email (from your sign-in — change it if you prefer another)</label>' +
        '    <input type="email" id="acvc-fb-email" placeholder="you@example.com" value="' +
        String(prefillEmail).replace(/"/g, "&quot;") + '"' +
        (hasIdent ? " disabled" : "") + "></div>" +
        "  </div>" +
        (hasIdent
          ? '<button type="button" class="acvc-fb-edit" id="acvc-fb-edit">Edit</button>'
          : "") +
        "</div>" +
        '<div class="acvc-fb-row">' +
        '  <div class="acvc-fb-lightcol">' +
        '  <label class="acvc-fb-feel">How are you feeling?</label>' +
        '  <div class="acvc-fb-stoplight">' +
        light("red", "🙁", "Rough week — I need help") +
        light("yellow", "😐", "OK week — some friction") +
        light("green", "🙂", "Good week — on track") +
        "  </div></div>" +
        '  <div class="acvc-fb-notecol">' +
        '    <label>Quick note next to your pick</label>' +
        '    <textarea id="acvc-fb-note" rows="3" placeholder="One or two lines that explain why you are feeling this way. Be honest — we need the feedback to help you."></textarea>' +
        "  </div>" +
        "</div>" +
        "<label>" + (daily ? "What did you get done since your last check-in?"
                            : "What did you get done this week?") + "</label>" +
        '<textarea id="acvc-fb-activities" rows="2" placeholder="Summary of the activities you performed…"></textarea>' +
        "<label>What is your very next step?</label>" +
        '<textarea id="acvc-fb-next" rows="2" placeholder="The one concrete thing you\'ll do next…"></textarea>' +
        '<label>Anything you\'re stuck on and need assistance with? <span style="font-weight:400">(optional — leave blank if you\'re not stuck)</span></label>' +
        '<textarea id="acvc-fb-stuck" rows="2" placeholder="Blockers, questions, things you want your mentor to see — or leave blank…"></textarea>' +
        '<label class="acvc-fb-ack"><input type="checkbox" id="acvc-fb-ack"> ' +
        "I agree that my current level and roadmap completion status will be " +
        "submitted as part of this feedback to Dr. Allen Harper, " +
        "AI Cyber Value Creator. <b>(required)</b></label>" +
        '<div class="acvc-fb-err" id="acvc-fb-err"></div>';

      var row = document.createElement("div");
      row.className = "acvc-update-actions";
      var cancel = document.createElement("button");
      cancel.className = "acvc-update-cancel";
      cancel.textContent = "Cancel";
      cancel.onclick = close;
      var send = document.createElement("button");
      send.className = "acvc-update-go";
      send.style.border = "none";
      send.style.cursor = "pointer";
      send.textContent = "Submit feedback";
      row.appendChild(cancel);
      row.appendChild(send);
      box.appendChild(row);
      overlay.appendChild(box);
      document.body.appendChild(overlay);

      var picked = "";
      [].forEach.call(box.querySelectorAll(".acvc-fb-light"), function (b) {
        b.onclick = function () {
          picked = b.getAttribute("data-c");
          [].forEach.call(box.querySelectorAll(".acvc-fb-light"), function (x) {
            x.classList.toggle("acvc-fb-on", x === b);
          });
        };
      });
      var editBtn = box.querySelector("#acvc-fb-edit");
      if (editBtn) {
        editBtn.onclick = function () {
          box.querySelector("#acvc-fb-name").disabled = false;
          box.querySelector("#acvc-fb-email").disabled = false;
          box.querySelector(".acvc-fb-ident").classList.remove("acvc-fb-ident-locked");
          editBtn.remove();
          box.querySelector("#acvc-fb-name").focus();
        };
      }

      function refreshSend() {
        // Required: identity, a light, note/activities/next-step, and the
        // acknowledgement. Stuck is optional — blank means "not stuck".
        var filled = ["acvc-fb-note", "acvc-fb-activities", "acvc-fb-next"]
          .every(function (id) {
            return box.querySelector("#" + id).value.trim().length > 0;
          });
        var nameOk = box.querySelector("#acvc-fb-name").value.trim().length > 0;
        var emailV = box.querySelector("#acvc-fb-email").value.trim();
        var emailOk = emailV.length > 2 && emailV.indexOf("@") !== -1;
        var ok = picked && filled && nameOk && emailOk &&
          box.querySelector("#acvc-fb-ack").checked;
        send.disabled = !ok;
        send.style.opacity = ok ? "1" : "0.45";
      }
      box.querySelector("#acvc-fb-ack").onchange = refreshSend;
      box.addEventListener("click", refreshSend);
      box.addEventListener("input", refreshSend);
      refreshSend();

      send.onclick = function () {
        if (send.disabled) return;
        send.textContent = "Sending…";
        send.disabled = true;
        SDK.fetchJSON("/api/plugins/ai-cyber-value-creator/feedback/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sentiment: picked,
            note: box.querySelector("#acvc-fb-note").value,
            activities: box.querySelector("#acvc-fb-activities").value,
            stuck: box.querySelector("#acvc-fb-stuck").value,
            nextStep: box.querySelector("#acvc-fb-next").value,
            statusAck: box.querySelector("#acvc-fb-ack").checked,
            name: box.querySelector("#acvc-fb-name").value,
            email: box.querySelector("#acvc-fb-email").value,
          }),
        }).then(function (r) {
          if (r && r.status) fstat = r.status;
          ensure();
          close();
          acvcBurstConfetti();
        }).catch(function (e) {
          box.querySelector("#acvc-fb-err").textContent =
            String((e && e.message) || e);
          send.textContent = "Submit feedback";
          send.disabled = false;
        });
      };
    }

    poll();
    setInterval(poll, 10 * 60 * 1000);
    setInterval(ensure, 2000);
  })();

  // -------------------------------------------------------------------------
  // Ambient background engine — the SAME treatment as the levels page
  // (theme-tinted fixed layer + drifting dust + wandering lights), applied
  // to the Roadmap and YouTube Insights pages. Vanilla JS (React-free) so it
  // survives SPA navigation; honors the shared FX toggle (vcl-effects-off).
  // -------------------------------------------------------------------------
  (function ambientBackground() {
    var ROUTES = { "/roadmap": 1, "/youtube": 1, "/brief": 1, "/delivery": 1,
                   "/shorts": 1 };
    var canvas = null, tintEl = null, raf = 0, stars = null;
    var pointer = { x: 0, y: 0 }, eased = { x: 0, y: 0 };
    var theme = { r: 20, g: 184, b: 166 }, fore = { r: 230, g: 230, b: 240 };
    var lightTheme = false, moteBase = 255, dpr = 1;
    var probeCanvas = null;

    function parseColor(col, fallback) {
      if (!probeCanvas) { probeCanvas = document.createElement("canvas"); probeCanvas.width = probeCanvas.height = 1; }
      var x = probeCanvas.getContext("2d", { willReadFrequently: true });
      x.fillStyle = fallback; x.fillStyle = col;
      x.clearRect(0, 0, 1, 1); x.fillRect(0, 0, 1, 1);
      var d = x.getImageData(0, 0, 1, 1).data;
      return { r: d[0], g: d[1], b: d[2] };
    }
    function resolveVar(name, fallback) {
      var probe = document.createElement("span");
      probe.style.color = "var(" + name + ", " + fallback + ")";
      probe.style.display = "none";
      document.body.appendChild(probe);
      var col = getComputedStyle(probe).color;
      probe.remove();
      return parseColor(col, fallback);
    }
    function refreshPalette() {
      theme = resolveVar("--color-primary", "#14b8a6");
      fore = parseColor(getComputedStyle(document.body).color, "#e6e6f0");
      var card = resolveVar("--color-card", "#16162a");
      var lum = 0.2126 * card.r + 0.7152 * card.g + 0.0722 * card.b;
      lightTheme = lum > 140;
      moteBase = lightTheme ? 0 : 255;
    }
    function effectsOff() {
      try { return localStorage.getItem("vcl-effects-off") === "1"; }
      catch (e) { return false; }
    }
    function resize() {
      if (!canvas) return;
      dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
    }
    function onMove(e) {
      pointer.x = (e.clientX / window.innerWidth - 0.5) * 2;
      pointer.y = (e.clientY / window.innerHeight - 0.5) * 2;
    }
    function frame(t) {
      if (!canvas) return;
      var ctx = canvas.getContext("2d");
      var w = canvas.width, hgt = canvas.height;
      if (effectsOff()) { ctx.clearRect(0, 0, w, hgt); raf = requestAnimationFrame(frame); return; }
      eased.x += (pointer.x - eased.x) * 0.03;
      eased.y += (pointer.y - eased.y) * 0.03;
      ctx.clearRect(0, 0, w, hgt);
      var lx = (0.5 + 0.34 * Math.sin(t * 0.000041)) * w;
      var ly = (0.42 + 0.30 * Math.sin(t * 0.000029 + 1.7)) * hgt;
      var lr = Math.max(w, hgt) * 0.42;
      var glow = ctx.createRadialGradient(lx, ly, 0, lx, ly, lr);
      glow.addColorStop(0, "rgba(" + theme.r + "," + theme.g + "," + theme.b + ",0.34)");
      glow.addColorStop(0.55, "rgba(" + theme.r + "," + theme.g + "," + theme.b + ",0.13)");
      glow.addColorStop(1, "rgba(" + theme.r + "," + theme.g + "," + theme.b + ",0)");
      ctx.fillStyle = glow; ctx.fillRect(0, 0, w, hgt);
      var l2x = (0.5 - 0.38 * Math.sin(t * 0.000033 + 0.6)) * w;
      var l2y = (0.55 + 0.28 * Math.cos(t * 0.000047)) * hgt;
      var g2 = ctx.createRadialGradient(l2x, l2y, 0, l2x, l2y, lr * 0.7);
      g2.addColorStop(0, "rgba(" + fore.r + "," + fore.g + "," + fore.b + "," + (lightTheme ? 0.09 : 0.13) + ")");
      g2.addColorStop(1, "rgba(" + fore.r + "," + fore.g + "," + fore.b + ",0)");
      ctx.fillStyle = g2; ctx.fillRect(0, 0, w, hgt);
      for (var i = 0; i < stars.length; i++) {
        var st = stars[i];
        st.x += 0.000012 * (0.3 + st.depth);
        st.y -= 0.0000048 * (0.3 + st.depth);
        if (st.x > 1.02) st.x = -0.02;
        if (st.y < -0.02) st.y = 1.02;
        var px = (st.x + eased.x * 0.012 * st.depth) * w;
        var py = (st.y + eased.y * 0.012 * st.depth) * hgt;
        var a = (0.10 + 0.16 * st.depth) *
          (0.7 + 0.3 * Math.sin(t * 0.00045 * st.twinkle + st.phase));
        var base = st.themed ? theme : fore;
        var cr = Math.round(base.r * 0.45 + moteBase * 0.55);
        var cg = Math.round(base.g * 0.45 + moteBase * 0.55);
        var cb = Math.round(base.b * 0.45 + moteBase * 0.55);
        ctx.beginPath();
        ctx.fillStyle = "rgba(" + cr + "," + cg + "," + cb + "," + a + ")";
        ctx.arc(px, py, (0.5 + st.depth * 0.9) * dpr, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(frame);
    }
    function mount() {
      if (canvas) return;
      stars = [];
      for (var i = 0; i < 140; i++) {
        stars.push({ x: Math.random(), y: Math.random(),
          depth: 0.35 + Math.random() * 0.65,
          phase: Math.random() * Math.PI * 2,
          twinkle: 0.4 + Math.random() * 0.8,
          themed: Math.random() < 0.45 });
      }
      tintEl = document.createElement("div");
      tintEl.className = "acvc-ambient-tint";
      canvas = document.createElement("canvas");
      canvas.className = "acvc-ambient-canvas";
      canvas.style.opacity = "0.95";
      document.body.appendChild(tintEl);
      document.body.appendChild(canvas);
      refreshPalette(); resize();
      window.addEventListener("resize", resize);
      window.addEventListener("mousemove", onMove);
      raf = requestAnimationFrame(frame);
    }
    function unmount() {
      if (!canvas) return;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      canvas.remove(); tintEl.remove();
      canvas = null; tintEl = null;
    }
    function check() {
      if (ROUTES[window.location.pathname]) mount(); else unmount();
    }
    try {
      new MutationObserver(function () { refreshPalette(); })
        .observe(document.documentElement, { attributes: true, attributeFilter: ["class", "style", "data-theme"] });
    } catch (e) {}
    setInterval(refreshPalette, 3000);
    window.addEventListener("popstate", check);
    setInterval(check, 800);
    check();
  })();

  var React = SDK.React;
  var h = React.createElement;
  var hooks = SDK.hooks;
  var useState = hooks.useState;
  var useEffect = hooks.useEffect;
  var useCallback = hooks.useCallback;
  var useRef = hooks.useRef;

  var API = "/api/plugins/ai-cyber-value-creator";

  function api(path, options) {
    // Delegate to the host SDK's fetchJSON so auth is handled correctly in
    // both loopback-token and gated-cookie modes.
    return SDK.fetchJSON(API + path, options);
  }

  function postJSON(path, body) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  // -------------------------------------------------------------------------
  // Theme tokens — host CSS variables with fallbacks (match the original).
  // -------------------------------------------------------------------------
  // The page paints NO background of its own — the host's themed bg shows
  // through and the ambient layer (below) adds the tint + FX, exactly like
  // the levels page.
  var PAGE_BG = "transparent";
  var CARD_BG = "var(--color-card, #1a1a2e)";
  var INSET_BG = "var(--color-secondary, #13131f)";
  var FIELD_BG = "var(--color-input, #0f0f1c)";
  var BORDER = "var(--color-border, #2b2b44)";
  var TEXT = "currentColor";   // hermes themes define no --color-foreground
  var MUTED = "var(--color-muted-foreground, #9aa0b4)";
  var ACCENT_FG = "var(--color-primary-foreground, #0e0e1a)";
  var PURPLE = "#8b5cf6";

  function hexToRgba(hex, alpha) {
    var x = hex.replace("#", "");
    var r = parseInt(x.slice(0, 2), 16);
    var g = parseInt(x.slice(2, 4), 16);
    var b = parseInt(x.slice(4, 6), 16);
    return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
  }

  // Global work order: lap-major, phase order within each lap.
  function stepNumber(phaseIndex, taskIndex, numPhases) {
    return taskIndex * numPhases + phaseIndex + 1;
  }

  // Regroup the phases into laps: lap k holds the kth task of every phase.
  function buildLaps(phases) {
    var numPhases = phases.length;
    var maxLen = phases.reduce(function (m, p) { return Math.max(m, p.tasks.length); }, 0);
    var laps = [];
    for (var i = 0; i < maxLen; i++) {
      var rows = [];
      phases.forEach(function (phase, pIdx) {
        var task = phase.tasks[i];
        if (!task) return;
        rows.push({ step: stepNumber(pIdx, i, numPhases), lap: i + 1, phase: phase, task: task });
      });
      laps.push({
        index: i + 1,
        rows: rows,
        doneCount: rows.filter(function (r) { return r.task.status === "done"; }).length,
        totalCount: rows.length,
      });
    }
    return laps;
  }

  var VIEW_TABS = [
    { id: "laps", label: "Laps", hint: "One trip around the wheel per lap — step N of every phase." },
    { id: "phases", label: "Phases", hint: "The four phases, each with its three steps (laps 1→3)." },
    { id: "sequence", label: "Sequence", hint: "The flat 1→12 work order with lap dividers." },
  ];

  // -------------------------------------------------------------------------
  // Minimal markdown renderer (headers, bold/italic/code, lists, GFM tables,
  // links, paragraphs) — enough for the Company Context field bodies.
  // -------------------------------------------------------------------------
  function mdInline(text, keyBase) {
    var out = [];
    var rest = String(text);
    var key = 0;
    var re = /(\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\*([^*]+)\*)/;
    while (rest.length) {
      var m = re.exec(rest);
      if (!m) { out.push(rest); break; }
      if (m.index > 0) out.push(rest.slice(0, m.index));
      var k = keyBase + "-" + key++;
      if (m[2] != null) out.push(h("strong", { key: k }, m[2]));
      else if (m[3] != null) out.push(h("code", { key: k }, m[3]));
      else if (m[4] != null)
        out.push(h("a", { key: k, href: m[5], target: "_blank", rel: "noreferrer" }, m[4]));
      else if (m[6] != null) out.push(h("em", { key: k }, m[6]));
      rest = rest.slice(m.index + m[1].length);
    }
    return out;
  }

  function splitTableRow(line) {
    var t = line.trim().replace(/^\|/, "").replace(/\|$/, "");
    return t.split("|").map(function (c) { return c.trim(); });
  }

  function isTableDivider(line) {
    return /^\s*\|?\s*:?-{2,}.*\|/.test(line) && /^[\s|:-]+$/.test(line);
  }

  function renderMarkdown(md) {
    var lines = String(md || "").split(/\r?\n/);
    var blocks = [];
    var i = 0;
    var key = 0;
    while (i < lines.length) {
      var line = lines[i];
      if (!line.trim()) { i++; continue; }
      var hm = /^(#{1,6})\s+(.*)$/.exec(line);
      if (hm) {
        var lvl = Math.min(6, hm[1].length + 2); // demote: fields live inside a panel
        blocks.push(h("h" + lvl, { key: "k" + key++ }, mdInline(hm[2], "h" + key)));
        i++;
        continue;
      }
      if (/^```/.test(line)) {
        var code = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i])) { code.push(lines[i]); i++; }
        i++;
        blocks.push(h("pre", { key: "k" + key++ }, h("code", null, code.join("\n"))));
        continue;
      }
      if (line.indexOf("|") >= 0 && i + 1 < lines.length && isTableDivider(lines[i + 1])) {
        var headCells = splitTableRow(line);
        i += 2;
        var rows = [];
        while (i < lines.length && lines[i].indexOf("|") >= 0 && lines[i].trim()) {
          rows.push(splitTableRow(lines[i]));
          i++;
        }
        blocks.push(
          h("table", { key: "k" + key++ },
            h("thead", null, h("tr", null, headCells.map(function (c, ci) {
              return h("th", { key: ci }, mdInline(c, "th" + ci));
            }))),
            h("tbody", null, rows.map(function (r, ri) {
              return h("tr", { key: ri }, r.map(function (c, ci) {
                return h("td", { key: ci }, mdInline(c, "td" + ri + "-" + ci));
              }));
            }))
          )
        );
        continue;
      }
      if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
        var ordered = /^\s*\d+\./.test(line);
        var items = [];
        while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) {
          items.push(lines[i].replace(/^\s*([-*]|\d+\.)\s+/, ""));
          i++;
        }
        blocks.push(
          h(ordered ? "ol" : "ul", { key: "k" + key++ }, items.map(function (it, ii) {
            return h("li", { key: ii }, mdInline(it, "li" + ii));
          }))
        );
        continue;
      }
      var para = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,6})\s|^```|^\s*([-*]|\d+\.)\s+/.test(lines[i]) &&
             !(lines[i].indexOf("|") >= 0 && i + 1 < lines.length && isTableDivider(lines[i + 1]))) {
        para.push(lines[i]);
        i++;
      }
      blocks.push(h("p", { key: "k" + key++ }, mdInline(para.join(" "), "p" + key)));
    }
    return h("div", { className: "acvc-md" }, blocks);
  }

  // -------------------------------------------------------------------------
  // localStorage-persisted collapsible state
  // -------------------------------------------------------------------------
  function useCollapsible(storageKey, defaultOpen) {
    var st = useState(function () {
      try {
        var v = window.localStorage.getItem(storageKey);
        return v === null ? (defaultOpen !== false) : v === "1";
      } catch (e) { return defaultOpen !== false; }
    });
    var open = st[0], setOpen = st[1];
    var toggle = function () {
      setOpen(function (prev) {
        var next = !prev;
        try { window.localStorage.setItem(storageKey, next ? "1" : "0"); } catch (e) {}
        return next;
      });
    };
    return [open, toggle];
  }

  function Chevron(props) {
    var color = props.color || MUTED;
    var size = props.size || 22;
    return h("span", {
      "aria-hidden": true,
      title: props.open ? "Collapse" : "Expand",
      style: {
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        width: size, height: size, borderRadius: 6,
        background: /^#/.test(color) ? hexToRgba(color, 0.14) : "transparent",
        transition: "transform 0.15s ease",
        transform: props.open ? "rotate(0deg)" : "rotate(-90deg)",
        flexShrink: 0, userSelect: "none",
      },
    }, h("svg", {
      width: Math.round(size * 0.62), height: Math.round(size * 0.62),
      viewBox: "0 0 24 24", fill: "none", stroke: color, strokeWidth: 3.5,
      strokeLinecap: "round", strokeLinejoin: "round",
    }, h("polyline", { points: "6 9 12 15 18 9" })));
  }

  // -------------------------------------------------------------------------
  // Shared bits
  // -------------------------------------------------------------------------
  function ProgressBar(props) {
    return h("div", { className: "acvc-progress-track" },
      h("div", {
        className: "acvc-progress-fill",
        style: { width: props.pct + "%", background: props.color },
      }));
  }

  function PhaseBadgeCircle(props) {
    return h("div", {
      style: {
        width: 34, height: 34, borderRadius: "50%", background: props.color,
        color: ACCENT_FG, display: "flex", alignItems: "center",
        justifyContent: "center", fontWeight: 800, fontSize: 16, flexShrink: 0,
      },
    }, props.children);
  }

  function StatusDot(props) {
    var base = {
      width: 18, height: 18, borderRadius: "50%", flexShrink: 0, marginTop: 2,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: 12, fontWeight: 800,
    };
    if (props.status === "done")
      return h("span", { style: Object.assign({}, base, { background: props.color, color: ACCENT_FG }) }, "✓");
    if (props.status === "in-progress")
      return h("span", { style: Object.assign({}, base, { border: "2px solid " + props.color, color: props.color }) }, "◐");
    return h("span", { style: Object.assign({}, base, { border: "2px solid " + BORDER }) });
  }

  function StatusBadge(props) {
    var status = props.status;
    var inProgress = status === "in-progress";
    var label = status === "done" ? "Done" : inProgress ? "In progress" : "To do";
    var bg = status === "done" ? hexToRgba(props.color, 0.18)
      : inProgress ? "rgba(245, 158, 11, 0.15)" : "rgba(154, 160, 180, 0.12)";
    var fg = status === "done" ? props.color : inProgress ? "#f59e0b" : MUTED;
    return h("span", {
      style: {
        flexShrink: 0, fontSize: 11, fontWeight: 700, padding: "3px 10px",
        borderRadius: 999, background: bg, color: fg, whiteSpace: "nowrap", marginTop: 1,
      },
    }, label);
  }

  function GateFooter(props) {
    return h("div", { className: "acvc-gate-footer" },
      h("span", { style: { color: props.color, fontWeight: 700 } }, "↳"),
      " Pass through ",
      h("span", { style: { color: TEXT, fontWeight: 700 } }, props.gate),
      props.isLast ? " — then the wheel loops back to Attract." : " on the way to the next phase.");
  }

  // -------------------------------------------------------------------------
  // Per-step coach control: the in-page working session (host-owned LLM via
  // /coach endpoints) replaces kanban tasks + worker chat threads. Expand a
  // step to see its guidance and work it in a scrollable chat right here.
  // -------------------------------------------------------------------------
  function TaskControl(props) {
    var task = props.task;
    var A = props.taskActions;
    var cs = (A.coach && A.coach[task.id]) || { status: "open", messages: [] };
    var busy = A.busyTaskId === task.id;
    var expanded = A.expandedTask === task.id;
    var armedSt = useState(false); var resetArmed = armedSt[0], setResetArmed = armedSt[1];
    var els = [];

    if (cs.status === "open" && A.levelGate) {
      return h("a", {
        href: "/level",
        onClick: function (e) { e.preventDefault(); window.location.assign("/level"); },
        title: "Establish your level first — take the assessment on the Your Level page",
        className: "acvc-link",
        style: { color: MUTED, fontSize: 12 },
      }, "🔒 establish your level first");
    }
    if (cs.status === "open" && cs.lockedBy) {
      return h("span", {
        className: "acvc-link",
        title: "Finish the previous foundation step first: " + cs.lockedBy,
        style: { color: MUTED, fontSize: 12, cursor: "not-allowed" },
      }, "🔒 " + cs.lockedBy.slice(0, 22) + " first");
    }
    var label;
    if (cs.status === "complete") label = expanded ? "hide ▴" : "review ▾";
    else if (cs.status === "active") label = expanded ? "hide ▴" : "continue ▾";
    else label = expanded ? "hide ▴" : "▸ Coach";
    els.push(h("button", {
      key: "coach",
      onClick: function () {
        if (busy) return;
        if (!expanded && cs.status === "open") A.onStart(task.id);
        A.onToggle(task.id);
      },
      disabled: busy,
      title: cs.status === "open"
        ? "Work this step with the Coach — a live session right here on the page"
        : "Open this step's working session",
      className: "acvc-task-btn",
      style: { cursor: busy ? "wait" : "pointer", color: busy ? MUTED : "#6366f1", borderColor: busy ? BORDER : "#4f46e5" },
    }, busy && cs.status === "open" ? "Starting…" : label));

    if (cs.status !== "open" || (cs.messages && cs.messages.length)) {
      els.push(h("a", {
        key: "reset",
        href: "#",
        onClick: function (e) {
          e.preventDefault();
          if (busy) return;
          if (!resetArmed) {
            setResetArmed(true);
            setTimeout(function () { setResetArmed(false); }, 5000);
            return;
          }
          setResetArmed(false);
          A.onReset(task.id);
        },
        title: resetArmed
          ? "Click again to confirm: clears this step's conversation and captured answers — fresh start"
          : "Reset this step — clears its conversation and captured answers",
        className: "acvc-link acvc-reset-link",
        style: resetArmed ? { color: "#f59e0b", fontWeight: 700 } : { color: MUTED },
      }, busy ? "…" : (resetArmed ? "confirm reset?" : "reset ↺")));
    }
    return h("span", { style: { display: "flex", gap: 8, alignItems: "center" } }, els);
  }

  // The expandable working panel under a step row: guidance bullets + the
  // persisted, scrollable coach conversation.
  function CoachPanel(props) {
    var task = props.task;
    var A = props.taskActions;
    var cs = (A.coach && A.coach[task.id]) || { status: "open", messages: [], guidance: [] };
    var busy = A.busyTaskId === task.id;
    var draftSt = useState("");
    var draft = draftSt[0], setDraft = draftSt[1];
    var endRef = useRef(null);
    var inputRef = useRef(null);
    useEffect(function () {
      if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
      // When the Coach's next question lands (or the panel opens on an
      // active session), put the cursor straight back in the input.
      if (!busy && inputRef.current && cs.status === "active") {
        inputRef.current.focus();
      }
    }, [(cs.messages || []).length, busy]);

    var pendingSt = useState(null);   // optimistic echo until the server copy lands
    var pending = pendingSt[0], setPending = pendingSt[1];

    function send() {
      var t = draft.trim();
      if (!t || busy) return;
      setDraft("");
      setPending({ text: t, atLen: (cs.messages || []).length });
      A.onAnswer(task.id, t);
    }
    var showPending = pending && (cs.messages || []).length === pending.atLen;

    return h("div", { className: "acvc-coach-panel", style: { borderColor: hexToRgba(props.accent || "#6366f1", 0.35) } },
      cs.guidance && cs.guidance.length
        ? h("div", { className: "acvc-coach-guidance" },
            h("div", { className: "acvc-coach-guidance-label" }, "📋 How this step works"),
            cs.guidance.map(function (g, i) {
              return h("div", { key: i, className: "acvc-coach-guidance-row" }, "• " + g);
            }))
        : null,
      cs.messages && cs.messages.length
        ? h("div", { className: "acvc-coach-log" },
            cs.messages.map(function (m, i) {
              return h("div", {
                key: i,
                className: "acvc-coach-msg " + (m.role === "coach" ? "acvc-coach-msg-coach" : "acvc-coach-msg-user"),
              }, m.text);
            }),
            showPending ? h("div", { className: "acvc-coach-msg acvc-coach-msg-user" }, pending.text) : null,
            busy ? h("div", { className: "acvc-coach-msg acvc-coach-msg-coach acvc-coach-thinking" },
              h("span", null, "●"), h("span", null, "●"), h("span", null, "●")) : null,
            h("div", { ref: endRef }))
        : (busy ? h("div", { className: "acvc-coach-log" },
            h("div", { className: "acvc-coach-msg acvc-coach-msg-coach acvc-coach-thinking" },
              h("span", null, "●"), h("span", null, "●"), h("span", null, "●"))) : null),
      cs.status === "complete"
        ? h("div", { className: "acvc-coach-done" },
            "✅ Complete", cs.summary ? " — " + cs.summary : "")
        : h("div", { className: "acvc-coach-input" },
            h("textarea", {
              ref: inputRef,
              className: "acvc-coach-textarea",
              rows: 2,
              placeholder: "Work the step — answer the Coach… (Enter sends, Shift+Enter for a new line)",
              value: draft,
              disabled: busy || cs.status === "open",
              onChange: function (e) { setDraft(e.target.value); },
              onKeyDown: function (e) {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
              },
            }),
            h("button", {
              className: "acvc-task-btn",
              onClick: send,
              disabled: busy || !draft.trim() || cs.status === "open",
              style: { color: "#6366f1", borderColor: "#4f46e5" },
            }, busy ? "…" : "Send")));
  }

  // -------------------------------------------------------------------------
  // Task row (shared by all views)
  // -------------------------------------------------------------------------
  function TaskRow(props) {
    var task = props.task;
    var done = task.status === "done";
    return h(React.Fragment, null, h("div", { className: "acvc-task-row" },
      h("div", {
        className: "acvc-task-main",
        style: { cursor: "default" },
      },
        props.numberLabel != null
          ? h("span", { className: "acvc-task-num" }, props.numberLabel)
          : null,
        h(StatusDot, { status: task.status, color: props.accent }),
        h("span", { style: { flex: 1 } },
          h("span", { style: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" } },
            props.phaseChip
              ? h("span", {
                  className: "acvc-chip",
                  style: {
                    color: props.phaseChip.color,
                    background: hexToRgba(props.phaseChip.color, 0.14),
                    border: "1px solid " + hexToRgba(props.phaseChip.color, 0.4),
                  },
                }, props.phaseChip.name)
              : null,
            h("span", {
              style: {
                fontSize: 15, fontWeight: 600,
                color: done ? MUTED : TEXT,
                textDecoration: done ? "line-through" : "none",
              },
            }, task.title)
          ),
          h("span", { style: { display: "block", fontSize: 13, color: MUTED, marginTop: 3 } }, task.blurb)
        )
      ),
      h("span", { style: { display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0 } },
        h(StatusBadge, { status: task.status, color: props.accent }),
        props.badge ? h("span", { style: { fontSize: 10.5, color: MUTED } }, props.badge) : null,
        h(TaskControl, { task: task, taskActions: props.taskActions })
      )
    ),
    props.taskActions && props.taskActions.expandedTask === task.id
      ? h(CoachPanel, { task: task, taskActions: props.taskActions, accent: props.accent })
      : null);
  }

  // -------------------------------------------------------------------------
  // Your Level — status + badge from the value-creator-level plugin; the
  // whole roadmap is gated on an established badge.
  // -------------------------------------------------------------------------
  // Exact replica of the value-creator-level badge medallion (ring, dark
  // face, shine, hover tilt) so the roadmap shows the SAME badge.
  var LEVEL_BADGE_COLORS = {
    1: ["#ff6b35", "#ffd166"],
    2: ["#4ecdc4", "#a8e6cf"],
    3: ["#5b8cff", "#9d6bff"],
    4: ["#b56bff", "#ff6bd6"],
    5: ["#ffd700", "#fff3b0"],
  };

  function LevelBadge(props) {
    var badge = props.badge;   // {level, name, emoji} or null
    var size = props.size || 56;
    var ref = useRef(null);
    var colors = badge ? (LEVEL_BADGE_COLORS[badge.level] || ["#888", "#bbb"]) : ["#3a3a4c", "#55556b"];
    function onMove(e) {
      var el = ref.current;
      if (!el || !badge) return;
      var r = el.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      el.style.transform = "perspective(600px) rotateY(" + x * 34 + "deg) rotateX(" + (-y * 34) + "deg) scale(1.06)";
    }
    function onLeave() { if (ref.current) ref.current.style.transform = ""; }
    return h("div", {
      ref: ref,
      className: "acvc-lvl-badge" + (badge ? " acvc-lvl-badge-earned" : " acvc-lvl-badge-locked"),
      style: { width: size + "px", height: size + "px", "--c1": colors[0], "--c2": colors[1] },
      onMouseMove: onMove,
      onMouseLeave: onLeave,
      title: badge ? ("Level " + badge.level + " — " + badge.name) : "No badge yet",
    },
      h("div", { className: "acvc-lvl-badge-ring" }),
      h("div", { className: "acvc-lvl-badge-face" },
        h("div", { style: { fontSize: size * 0.34 + "px", lineHeight: 1 } }, badge ? badge.emoji : "🔒"),
        h("div", { className: "acvc-lvl-badge-lvl" }, badge ? "LVL " + badge.level : "—")),
      badge ? h("div", { className: "acvc-lvl-badge-shine" }) : null);
  }

  function LevelSection(props) {
    var lv = props.levelStatus || { level: 0, badge: null };
    var color = "#eab308";
    var c = useCollapsible("acvc-level-open");
    var open = c[0], toggleOpen = c[1];
    var hasBadge = !!lv.badge;
    var established = lv.level > 0;   // roadmap unlocks at level 1+
    return h("div", {
      className: "acvc-card",
      style: {
        border: "1px solid " + hexToRgba(color, 0.5),
        borderLeft: "4px solid " + color,
        marginBottom: 24,
      },
    },
      h("div", {
        onClick: toggleOpen,
        title: open ? "Collapse" : "Expand",
        className: "acvc-card-head",
        style: { background: hexToRgba(color, 0.1) },
      },
        h(Chevron, { open: open, color: color }),
        h(LevelBadge, { badge: lv.badge, size: 56 }),
        h("div", { style: { flex: 1 } },
          h("div", { style: { display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" } },
            h("span", { style: { fontSize: 22, fontWeight: 800, color: color } }, "Your Level"),
            hasBadge
              ? h("span", { style: { fontSize: 13, color: MUTED } },
                  "Level " + lv.level + " — " + (lv.badge ? lv.badge.name : ""))
              : h("span", { style: { fontSize: 13, color: MUTED } }, "Unranked")),
          h("div", { style: { fontSize: 12.5, color: established ? "#16a34a" : "#f59e0b", marginTop: 3 } },
            established
              ? "✓ Badge established — the roadmap below is unlocked."
              : hasBadge
                ? "💡 Curious — the roadmap needs an idea. Reach Level 1 to unlock it; your prescription shows the way."
                : "Take the assessment to establish your builder level — the roadmap unlocks at Level 1.")
        ),
        h("div", { style: { textAlign: "right", minWidth: 130 } },
          h("a", {
            href: "/level",
            onClick: function (e) { e.preventDefault(); e.stopPropagation(); window.location.assign("/level"); },
            className: "acvc-link",
            style: { color: color, fontWeight: 700 },
          }, established ? "Your Level ↗" : hasBadge ? "Your prescription ↗" : "Take the assessment ↗"))
      ),
      open
        ? h("div", { style: { padding: "12px 18px", fontSize: 13, color: MUTED, lineHeight: 1.55 } },
            established && lv.current
              ? h("div", { style: { marginBottom: 8 } },
                  h("b", { style: { color: TEXT } },
                    "You are — Level " + lv.level + " (" + lv.current.name + "): "),
                  lv.current.summary,
                  lv.rationale ? " The Examiner's verdict on you: " + lv.rationale : "")
              : null,
            established && lv.next
              ? h("div", { style: { marginBottom: 8 } },
                  h("b", { style: { color: TEXT } },
                    "Next up — Level " + lv.next.level + " (" + lv.next.name + "): "),
                  lv.next.summary)
              : null,
            established && lv.checklist
              ? h("div", null,
                  h("b", { style: { color: TEXT } }, "Road to Level " + lv.checklist.targetLevel + ": "),
                  lv.checklist.done + "/" + lv.checklist.total + " prescription steps verified.")
              : null,
            !established
              ? "The 5-level \"Levels of AI Building\" assessment places you honestly — level, badge, and a 10-step prescription. Everything on this roadmap builds on knowing where you actually stand."
              : null)
        : null
    );
  }

  // -------------------------------------------------------------------------
  // Foundation — Create Value
  // -------------------------------------------------------------------------
  function FoundationSection(props) {
    var phase = props.phase;
    var pct = phase.totalCount > 0 ? Math.round((phase.doneCount / phase.totalCount) * 100) : 0;
    var c = useCollapsible("acvc-foundation-open");
    var open = c[0], toggleOpen = c[1];
    return h("div", {
      className: "acvc-card",
      style: {
        border: "1px solid " + hexToRgba(phase.color, 0.5),
        borderLeft: "4px solid " + phase.color,
        marginBottom: 24,
      },
    },
      h("div", {
        onClick: toggleOpen,
        title: open ? "Collapse" : "Expand",
        className: "acvc-card-head",
        style: { background: hexToRgba(phase.color, 0.1) },
      },
        h(Chevron, { open: open, color: phase.color }),
        h(PhaseBadgeCircle, { color: phase.color }, "★"),
        h("div", { style: { flex: 1 } },
          h("div", { style: { display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" } },
            h("span", { style: { fontSize: 22, fontWeight: 800, color: phase.color } }, phase.name + " — Foundational"),
            h("span", { style: { fontSize: 13, color: MUTED } }, "Goal: " + phase.goal)
          ),
          h("div", { style: { fontSize: 12.5, color: props.done ? "#16a34a" : MUTED, marginTop: 3 } },
            props.done
              ? "✓ Foundation complete — you're ready to work the flywheel laps below."
              : "Complete these steps before entering the laps — they're the foundation for everything downstream.")
        ),
        h("div", { style: { textAlign: "right", minWidth: 130 } },
          h("div", { style: { fontSize: 12, color: MUTED, marginBottom: 4 } },
            phase.doneCount + "/" + phase.totalCount + " complete"),
          h(ProgressBar, { pct: pct, color: phase.color })
        )
      ),
      open
        ? h("div", null, phase.tasks.map(function (task, ti) {
            return h(TaskRow, {
              key: task.id, task: task, accent: phase.color,
              numberLabel: (ti + 1) + ".",
              taskActions: props.taskActions,
            });
          }))
        : null
    );
  }

  // -------------------------------------------------------------------------
  // Company Context panel
  // -------------------------------------------------------------------------
  var FIELD_TASK_ID = {
    icp: "create-value-icp",
    problems: "create-value-problems",
    solutions: "create-value-solutions",
    offer: "create-value-offers",
  };
  var PITCH_TASK_ID = "create-value-pitch";
  var CTX_ACCENT = "#14b8a6";

  function taskLinkEl(taskById, taskId, label) {
    var t = taskById[taskId];
    if (!t || !t.kanban || !t.kanban.taskId) return null;
    var els = [];
    if (t.kanban.sessionId) {
      var href = "/chat?resume=" + encodeURIComponent(t.kanban.sessionId);
      els.push(h("a", {
        key: "thread",
        href: href,
        onClick: function (e) { e.preventDefault(); window.location.assign(href); },
        className: "acvc-link",
        title: 'Open the conversation thread for "' + label + '"',
      }, "chat ↗"));
    }
    var kbHref = "/kanban#task=" + encodeURIComponent(t.kanban.taskId);
    els.push(h("a", {
      key: "kb",
      href: kbHref,
      onClick: function (e) { e.preventDefault(); window.location.assign(kbHref); },
      className: "acvc-link",
      title: 'Open the kanban task for "' + label + '"',
    }, "task ↗"));
    return els;
  }

  function CompanyContextPanel(props) {
    var ctxData = props.contextData || {};
    var ctx = ctxData.context || {};
    var fields = ctxData.fields || [];
    var pitch = ctxData.pitch || null;
    var pitchVal = pitch ? ctx[pitch.key] : null;
    var editingSt = useState(false);
    var editing = editingSt[0], setEditing = editingSt[1];
    var draftSt = useState({});
    var draft = draftSt[0], setDraft = draftSt[1];
    var busySt = useState(false);
    var busy = busySt[0], setBusy = busySt[1];
    var genSt = useState(false);
    var genBusy = genSt[0], setGenBusy = genSt[1];
    var genErrSt = useState(null);
    var genErr = genErrSt[0], setGenErr = genErrSt[1];
    var c = useCollapsible("acvc-context-open", false);
    var open = c[0], toggleOpen = c[1];
    var collapsedSt = useState(function () {
      try { return JSON.parse(window.localStorage.getItem("acvc-context-sections") || "{}"); }
      catch (e) { return {}; }
    });
    var collapsed = collapsedSt[0], setCollapsed = collapsedSt[1];
    var isSectionOpen = function (key) { return collapsed[key] !== true; };
    var toggleSection = function (key) {
      setCollapsed(function (prev) {
        var next = Object.assign({}, prev);
        next[key] = !prev[key];
        try { window.localStorage.setItem("acvc-context-sections", JSON.stringify(next)); } catch (e) {}
        return next;
      });
    };
    var taskById = props.taskById || {};
    var pitchTask = taskById[PITCH_TASK_ID];
    var pitchStarted = !!(pitchTask && pitchTask.kanban && pitchTask.kanban.taskId);

    function startEdit() {
      var d = {};
      fields.forEach(function (f) { d[f.key] = ctx[f.key] || ""; });
      if (pitch) d[pitch.key] = pitchVal || "";
      setDraft(d);
      setEditing(true);
    }

    function runPitchTask() {
      setGenBusy(true);
      setGenErr(null);
      postJSON("/start-step", { taskId: PITCH_TASK_ID })
        .then(function () { return props.refresh(); })
        .catch(function (e) { setGenErr(String((e && e.message) || e)); })
        .finally(function () { setGenBusy(false); });
    }

    // Auto-start the pitch task ONCE when the four fields are set and the task
    // hasn't been started (same gate as the original, keyed in localStorage).
    var autoRef = useRef(false);
    useEffect(function () {
      if (!pitch || !pitch.ready || pitchStarted || (pitchVal && pitchVal.trim()) || genBusy || autoRef.current) return;
      try {
        if (window.localStorage.getItem("acvc-pitch-autostart") === "1") return;
        window.localStorage.setItem("acvc-pitch-autostart", "1");
      } catch (e) { return; }
      autoRef.current = true;
      runPitchTask();
    }, [pitch && pitch.ready, pitchStarted, pitchVal, genBusy]);

    function save() {
      setBusy(true);
      postJSON("/context", draft)
        .then(function () { return props.refresh(); })
        .then(function () { setEditing(false); })
        .finally(function () { setBusy(false); });
    }

    return h("div", {
      className: "acvc-card acvc-ctx",
      style: {
        border: "1px solid " + hexToRgba(CTX_ACCENT, 0.4),
        borderLeft: "4px solid " + CTX_ACCENT,
        marginBottom: 24,
      },
    },
      h("div", {
        onClick: toggleOpen,
        title: open ? "Collapse" : "Expand",
        className: "acvc-card-head",
        style: { background: hexToRgba(CTX_ACCENT, 0.1), flexWrap: "wrap" },
      },
        h(Chevron, { open: open, color: CTX_ACCENT }),
        h("div", { style: { flex: 1, minWidth: 220 } },
          h("div", { style: { fontSize: 16, fontWeight: 800, color: CTX_ACCENT } }, "Company Context"),
          h("div", { style: { fontSize: 12.5, color: MUTED, marginTop: 2 } },
            "Who we serve & what we deliver — ",
            h("b", null, "shared with every session"),
            ". Step tasks update it as they run the foundation; edit it here anytime.")
        ),
        h("div", { style: { display: "flex", gap: 8, alignItems: "center" } },
          ctx.updatedAt && !editing
            ? h("span", { style: { fontSize: 11, color: MUTED } },
                "updated " + new Date(ctx.updatedAt).toLocaleDateString())
            : null,
          editing
            ? [
                h("button", {
                  key: "save",
                  onClick: function (e) { e.stopPropagation(); save(); },
                  disabled: busy,
                  className: "acvc-btn-primary",
                  style: { opacity: busy ? 0.7 : 1 },
                }, busy ? "Saving…" : "Save & sync"),
                h("button", {
                  key: "cancel",
                  onClick: function (e) { e.stopPropagation(); setEditing(false); },
                  disabled: busy,
                  className: "acvc-btn-ghost",
                }, "Cancel"),
              ]
            : h("button", {
                onClick: function (e) {
                  e.stopPropagation();
                  if (!open) toggleOpen();
                  startEdit();
                },
                className: "acvc-btn-ghost",
              }, "Edit")
        )
      ),
      open
        ? h("div", { style: { padding: "12px 20px", display: "flex", flexDirection: "column", gap: 14 } },
            fields.map(function (f) {
              var isOffer = f.key === "offer";
              var rawVal = ctx[f.key];
              var val = isOffer ? (ctxData.offerSummary || rawVal) : rawVal;
              var sectionOpen = editing || isSectionOpen(f.key);
              return h("div", { key: f.key, className: "acvc-field" },
                h("div", {
                  onClick: function () { toggleSection(f.key); },
                  title: sectionOpen ? "Collapse" : "Expand",
                  className: "acvc-field-head",
                },
                  h(Chevron, { open: sectionOpen, color: MUTED }),
                  h("div", { style: { flex: 1, fontSize: 12, fontWeight: 700, color: TEXT } },
                    f.label, " ",
                    h("span", { style: { color: MUTED, fontWeight: 400 } }, "· " + f.hint)),
                  taskLinkEl(props.taskById, FIELD_TASK_ID[f.key], f.label)
                ),
                sectionOpen
                  ? h("div", { style: { padding: "0 10px 10px 30px" } },
                      editing
                        ? h("textarea", {
                            value: draft[f.key] || "",
                            onChange: function (e) {
                              var v = e.target.value;
                              setDraft(function (d) {
                                var nd = Object.assign({}, d); nd[f.key] = v; return nd;
                              });
                            },
                            rows: 3,
                            className: "acvc-textarea",
                          })
                        : val && val.trim()
                          ? renderMarkdown(val.trim())
                          : h("div", { style: { fontSize: 13, color: MUTED } },
                              "Not yet defined — discovered in the Create Value foundation.")
                    )
                  : null
              );
            }),
            pitch
              ? (function () {
                  var pitchOpen = editing || isSectionOpen("pitch");
                  return h("div", { className: "acvc-field" },
                    h("div", {
                      onClick: function () { toggleSection("pitch"); },
                      title: pitchOpen ? "Collapse" : "Expand",
                      className: "acvc-field-head",
                      style: { flexWrap: "wrap" },
                    },
                      h(Chevron, { open: pitchOpen, color: CTX_ACCENT }),
                      h("div", { style: { flex: 1, minWidth: 180, fontSize: 12, fontWeight: 700, color: CTX_ACCENT } },
                        pitch.label, " ",
                        h("span", { style: { color: MUTED, fontWeight: 400 } }, "· " + pitch.hint)),
                      taskLinkEl(props.taskById, PITCH_TASK_ID, pitch.label),
                      !editing
                        ? h("button", {
                            onClick: function (e) { e.stopPropagation(); runPitchTask(); },
                            disabled: genBusy || !pitch.ready,
                            title: pitch.ready
                              ? (pitchStarted
                                  ? "Restart the elevator-pitch task — it rewrites the pitch from the full context"
                                  : "Run the elevator-pitch task (written from the full context)")
                              : "Complete ICP, Problems, Solutions, and Offer first",
                            className: "acvc-btn-ghost",
                            style: {
                              fontSize: 12, padding: "4px 10px",
                              opacity: genBusy || !pitch.ready ? 0.55 : 1,
                              cursor: genBusy || !pitch.ready ? "not-allowed" : "pointer",
                            },
                          }, genBusy ? "Starting…" : pitchStarted ? "↻ Regenerate" : "✨ Generate")
                        : null
                    ),
                    pitchOpen
                      ? h("div", { style: { padding: "0 10px 10px 30px" } },
                          editing
                            ? h("textarea", {
                                value: draft[pitch.key] || "",
                                onChange: function (e) {
                                  var v = e.target.value;
                                  setDraft(function (d) {
                                    var nd = Object.assign({}, d); nd[pitch.key] = v; return nd;
                                  });
                                },
                                rows: 2,
                                placeholder: "I help [brief ICP name] with [problem] [achieve outcome] within [timeframe].",
                                className: "acvc-textarea",
                                style: { marginTop: 6 },
                              })
                            : pitchVal && pitchVal.trim()
                              ? h("div", {
                                  style: { fontSize: 15, fontWeight: 600, color: TEXT, marginTop: 6, fontStyle: "italic" },
                                }, "“" + pitchVal.trim() + "”")
                              : h("div", { style: { fontSize: 13, color: MUTED, marginTop: 6 } },
                                  pitch.ready
                                    ? "Run the elevator-pitch task — it writes the pitch from the full context (auto-runs after the offer; or click Generate)."
                                    : "Finishes the foundation: complete ICP, Problems, Solutions, and the Offer, then it runs."),
                          genErr ? h("div", { style: { fontSize: 12, color: "#f87171", marginTop: 6 } }, genErr) : null
                        )
                      : null
                  );
                })()
              : null
          )
        : null
    );
  }

  // -------------------------------------------------------------------------
  // Flywheel — 2×2 quadrant wheel with the clockwise-arrow hub
  // -------------------------------------------------------------------------
  function ExpandIcon() {
    return h("svg", {
      width: 13, height: 13, viewBox: "0 0 24 24", fill: "none",
      stroke: "currentColor", strokeWidth: 2.2, strokeLinecap: "round", strokeLinejoin: "round",
    },
      h("path", { d: "M15 3h6v6" }),
      h("path", { d: "M10 14 21 3" }),
      h("path", { d: "M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5" }));
  }

  function ProcessDiagramModal(props) {
    var urlSt = useState(null);
    var url = urlSt[0], setUrl = urlSt[1];
    useEffect(function () {
      var onKey = function (e) { if (e.key === "Escape") props.onClose(); };
      window.addEventListener("keydown", onKey);
      return function () { window.removeEventListener("keydown", onKey); };
    }, []);
    useEffect(function () {
      var revoke = null;
      SDK.authedFetch(API + "/process-diagram")
        .then(function (r) { return r.ok ? r.blob() : null; })
        .then(function (b) {
          if (b) { revoke = URL.createObjectURL(b); setUrl(revoke); }
        })
        .catch(function () {});
      return function () { if (revoke) URL.revokeObjectURL(revoke); };
    }, []);
    return h("div", {
      onClick: props.onClose,
      role: "dialog", "aria-modal": true,
      "aria-label": "AI Cyber Value Creator process diagram",
      className: "acvc-modal-backdrop",
    },
      h("div", { onClick: function (e) { e.stopPropagation(); }, className: "acvc-modal" },
        h("div", { style: { display: "flex", alignItems: "center", gap: 10 } },
          h("div", { style: { flex: 1, fontSize: 14, fontWeight: 800, color: TEXT } },
            "AI Cyber Value Creator — Process"),
          h("button", { onClick: props.onClose, title: "Close", className: "acvc-modal-close" }, "×")),
        url
          ? h("img", {
              src: url,
              alt: "AI Cyber Value Creator process diagram — Attract, Nurture, Convert, Deliver flywheel",
              style: {
                display: "block", maxWidth: "100%", maxHeight: "84vh",
                objectFit: "contain", borderRadius: 8, background: "#fff",
              },
            })
          : h("div", { style: { padding: 40, color: MUTED } }, "Loading diagram…")
      )
    );
  }

  function Flywheel(props) {
    var st = useState(false);
    var diagramOpen = st[0], setDiagramOpen = st[1];
    var byId = {};
    props.phases.forEach(function (p) { byId[p.id] = p; });
    // Clockwise into quadrants: Attract TL, Nurture TR, Convert BR, Deliver BL.
    var grid = [
      { p: byId.attract, align: "left" },
      { p: byId.nurture, align: "right" },
      { p: byId.deliver, align: "left" },
      { p: byId.convert, align: "right" },
    ];
    return h("div", { className: "acvc-flywheel" },
      grid.map(function (cell, idx) {
        var p = cell.p;
        if (!p) return h("div", { key: idx });
        return h("a", {
          key: p.id,
          href: "#phase-" + p.id,
          onClick: function (e) { e.preventDefault(); props.onPhase(p.id); },
          className: "acvc-quadrant",
          style: {
            color: TEXT,
            background: hexToRgba(p.color, 0.12),
            border: "1px solid " + hexToRgba(p.color, 0.5),
            textAlign: cell.align === "right" ? "right" : "left",
          },
        },
          h("div", {
            style: {
              display: "flex", alignItems: "center", gap: 8,
              justifyContent: cell.align === "right" ? "flex-end" : "flex-start",
            },
          },
            h("span", {
              style: {
                width: 10, height: 10, borderRadius: "50%", background: p.color,
                order: cell.align === "right" ? 2 : 0,
              },
            }),
            h("span", { style: { fontWeight: 800, fontSize: 20, color: p.color } }, p.name)),
          h("div", { style: { fontSize: 12, color: MUTED } }, p.goal),
          h("div", { style: { marginTop: "auto", fontSize: 12, color: MUTED } },
            p.doneCount + "/" + p.totalCount + " done · gate → ",
            h("b", { style: { color: TEXT } }, p.gateToNext))
        );
      }),
      // Center hub with the ~340° clockwise arrow (gap straddles Attract).
      h("div", { className: "acvc-hub-wrap" },
        h("svg", {
          viewBox: "0 0 100 100", width: 210, height: 210,
          style: { position: "absolute", inset: 0, pointerEvents: "none", overflow: "visible" },
          "aria-hidden": true,
        },
          h("defs", null,
            h("marker", {
              id: "acvc-flywheel-arrow", viewBox: "0 0 10 10", refX: "7", refY: "5",
              markerWidth: "5", markerHeight: "5", orient: "auto",
            }, h("path", { d: "M0,0 L10,5 L0,10 z", fill: PURPLE }))),
          h("path", {
            d: "M24.8,14.0 A44,44 0 1 1 14.0,24.8",
            fill: "none", stroke: PURPLE, strokeWidth: 2.25,
            strokeLinecap: "round", markerEnd: "url(#acvc-flywheel-arrow)",
          })),
        h("div", {
          onClick: function () { setDiagramOpen(true); },
          role: "button", tabIndex: 0,
          onKeyDown: function (e) {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setDiagramOpen(true); }
          },
          title: "View the AI Cyber Value Creator process diagram",
          className: "acvc-hub",
        },
          h("span", { style: { fontSize: 18, fontWeight: 800, lineHeight: 1.2, padding: "0 12px" } },
            "AI Cyber", h("br"), "Value Creator"),
          h("span", {
            "aria-hidden": true,
            style: {
              marginTop: 6, display: "inline-flex", alignItems: "center", gap: 4,
              color: PURPLE, fontSize: 11, fontWeight: 700,
            },
          }, h(ExpandIcon), " View process"))
      ),
      diagramOpen ? h(ProcessDiagramModal, { onClose: function () { setDiagramOpen(false); } }) : null
    );
  }

  // -------------------------------------------------------------------------
  // View toggle + cards
  // -------------------------------------------------------------------------
  function ViewToggle(props) {
    return h("div", { className: "acvc-view-toggle" },
      VIEW_TABS.map(function (tab) {
        var active = tab.id === props.view;
        return h("button", {
          key: tab.id,
          onClick: function () { props.onChange(tab.id); },
          className: "acvc-view-tab",
          style: {
            color: active ? ACCENT_FG : MUTED,
            background: active ? PURPLE : "transparent",
          },
        }, tab.label);
      }));
  }

  function PhaseCard(props) {
    var phase = props.phase;
    var pct = phase.totalCount > 0 ? Math.round((phase.doneCount / phase.totalCount) * 100) : 0;
    var c = useCollapsible("acvc-phase-" + phase.id);
    var open = c[0], toggleOpen = c[1];
    return h("div", {
      id: "phase-" + phase.id,
      className: "acvc-card",
      style: { border: "1px solid " + BORDER, borderLeft: "4px solid " + phase.color },
    },
      h("div", {
        onClick: toggleOpen,
        title: open ? "Collapse" : "Expand",
        className: "acvc-card-head",
        style: { background: hexToRgba(phase.color, 0.08) },
      },
        h(Chevron, { open: open, color: phase.color }),
        h(PhaseBadgeCircle, { color: phase.color }, String(props.index + 1)),
        h("div", { style: { flex: 1 } },
          h("div", { style: { display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" } },
            h("span", { style: { fontSize: 22, fontWeight: 800, color: phase.color } }, phase.name),
            h("span", { style: { fontSize: 13, color: MUTED } }, "Goal: " + phase.goal))),
        h("div", { style: { textAlign: "right", minWidth: 130 } },
          h("div", { style: { fontSize: 12, color: MUTED, marginBottom: 4 } },
            phase.doneCount + "/" + phase.totalCount + " complete"),
          h(ProgressBar, { pct: pct, color: phase.color }))
      ),
      open
        ? [
            h("div", { key: "tasks" }, phase.tasks.map(function (task, ti) {
              return h(TaskRow, {
                key: task.id, task: task, accent: phase.color,
                numberLabel: (ti + 1) + ".",
                badge: "Step " + stepNumber(props.index, ti, props.numPhases) + " · Lap " + (ti + 1),
                taskActions: props.taskActions,
              });
            })),
            h(GateFooter, { key: "gate", color: phase.color, gate: phase.gateToNext, isLast: props.isLast }),
          ]
        : null
    );
  }

  function LapCard(props) {
    var lap = props.lap;
    var pct = lap.totalCount > 0 ? Math.round((lap.doneCount / lap.totalCount) * 100) : 0;
    var ordinal = ["first", "second", "third", "fourth", "fifth"][lap.index - 1] || lap.index + "th";
    var c = useCollapsible("acvc-lap-" + lap.index);
    var open = c[0], toggleOpen = c[1];
    return h("div", {
      className: "acvc-card",
      style: { border: "1px solid " + BORDER, borderLeft: "4px solid " + PURPLE },
    },
      h("div", {
        onClick: toggleOpen,
        title: open ? "Collapse" : "Expand",
        className: "acvc-card-head",
        style: { background: "rgba(139, 92, 246, 0.08)" },
      },
        h(Chevron, { open: open, color: PURPLE }),
        h(PhaseBadgeCircle, { color: PURPLE }, String(lap.index)),
        h("div", { style: { flex: 1 } },
          h("div", { style: { display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" } },
            h("span", { style: { fontSize: 22, fontWeight: 800, color: PURPLE } }, "Lap " + lap.index),
            h("span", { style: { fontSize: 13, color: MUTED } },
              ordinal + " trip around the wheel · one step in every phase"))),
        h("div", { style: { textAlign: "right", minWidth: 130 } },
          h("div", { style: { fontSize: 12, color: MUTED, marginBottom: 4 } },
            lap.doneCount + "/" + lap.totalCount + " complete"),
          h(ProgressBar, { pct: pct, color: PURPLE }))
      ),
      open
        ? [
            h("div", { key: "rows" }, lap.rows.map(function (row) {
              return h(TaskRow, {
                key: row.task.id, task: row.task, accent: row.phase.color,
                numberLabel: String(row.step),
                phaseChip: { name: row.phase.name, color: row.phase.color },
                taskActions: props.taskActions,
              });
            })),
            h("div", { key: "note", className: "acvc-gate-footer" },
              lap.index < props.totalLaps
                ? "When every phase has its step done, start the next lap."
                : "Final lap — completing it means you now are an AI Cyber Value Creator. Congrats!"),
          ]
        : null
    );
  }

  function SequenceLapSection(props) {
    var lap = props.lap;
    var c = useCollapsible("acvc-seq-" + lap.index);
    var open = c[0], toggleOpen = c[1];
    return h("div", null,
      h("div", {
        onClick: toggleOpen,
        title: open ? "Collapse" : "Expand",
        className: "acvc-seq-head",
      },
        h(Chevron, { open: open, color: PURPLE, size: 18 }),
        h("span", { className: "acvc-seq-label" }, "Lap " + lap.index),
        h("span", { style: { fontSize: 11, color: MUTED } }, lap.doneCount + "/" + lap.totalCount)),
      open
        ? lap.rows.map(function (row) {
            return h(TaskRow, {
              key: row.task.id, task: row.task, accent: row.phase.color,
              numberLabel: String(row.step),
              phaseChip: { name: row.phase.name, color: row.phase.color },
              taskActions: props.taskActions,
            });
          })
        : null
    );
  }

  function SequenceView(props) {
    return h("div", { className: "acvc-card", style: { border: "1px solid " + BORDER } },
      props.laps.map(function (lap) {
        return h(SequenceLapSection, {
          key: lap.index, lap: lap,
          taskActions: props.taskActions,
        });
      }));
  }

  // -------------------------------------------------------------------------
  // Page
  // -------------------------------------------------------------------------
  function scrollToPhase(phaseId) {
    window.setTimeout(function () {
      var el = document.getElementById("phase-" + phaseId);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 60);
  }

  // Getting Started onboarding card — shows until Grok is connected and the
  // transcript key is set; deep-links to the dashboard's Environment page
  // where the xai-oauth device-code card and env editor live. Dismissible per
  // browser; reappears if setup regresses.
  function GettingStartedCard() {
    var st = useState(null);
    var status = st[0], setStatus = st[1];
    var dis = useState(function () {
      try { return localStorage.getItem("acvc-gs-dismissed") === "1"; } catch (e) { return false; }
    });
    var dismissed = dis[0], setDismissed = dis[1];

    useEffect(function () {
      api("/setup-status").then(function (s) {
        setStatus(s);
        try {
          if (s && (s.llmConnected || s.grokConnected) &&
              !localStorage.getItem("acvc-cron-pinned")) {
            postJSON("/pin-cron", {}).then(function () {
              localStorage.setItem("acvc-cron-pinned", "1");
            }).catch(function () { /* retried next visit */ });
          }
        } catch (e) {}
      }).catch(function () { setStatus(null); });
    }, []);

    if (!status || (status.allDone && true) || dismissed) return null;

    var GS_LINK = {
      color: "var(--color-primary, #14b8a6)",
      textDecoration: "underline",
      textUnderlineOffset: 3,
      fontWeight: 700,
    };

    function StepRow(props) {
      var done = props.done;
      return h("div", { style: { display: "flex", alignItems: "flex-start", gap: 10, padding: "8px 0" } },
        h("span", {
          style: {
            width: 20, height: 20, borderRadius: "50%", flexShrink: 0, marginTop: 1,
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            fontSize: 13, fontWeight: 700,
            background: done ? "var(--color-primary, #14b8a6)" : "transparent",
            border: done ? "none" : "2px solid var(--color-border, #333)",
            color: done ? "var(--color-primary-foreground, #04211c)" : MUTED,
          },
        }, done ? "✓" : props.num),
        h("div", null,
          h("div", { style: { fontWeight: 600, textDecoration: done ? "line-through" : "none", opacity: done ? 0.6 : 1 } }, props.title),
          !done && props.children));
    }

    return h("div", {
      className: "acvc-card",
      style: { marginBottom: 22, padding: "18px 20px", borderLeft: "3px solid var(--color-primary, #14b8a6)" },
    },
      h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 } },
        h("div", { style: { fontSize: 16, fontWeight: 800 } }, "🚀 Getting Started"),
        h("button", {
          className: "acvc-btn-ghost",
          onClick: function () { try { localStorage.setItem("acvc-gs-dismissed", "1"); } catch (e) {} setDismissed(true); },
          title: "Hide this checklist",
        }, "Dismiss")),
      h("div", { style: { color: MUTED, fontSize: 13, marginBottom: 6 } },
        "A few quick connections and your AI business system is fully armed."),
      h(StepRow, { num: "1", done: !!(status.llmConnected || status.grokConnected), title: "Connect an AI model provider (powers your agent)" },
        h("div", { style: { color: MUTED, fontSize: 13 } },
          "Open the ", h("a", { href: "/env", style: GS_LINK }, "Keys page"),
          " — the OAuth and Providers tabs have Get-key links and in-browser sign-ins for every provider (Anthropic/Claude, OpenAI, xAI Grok, Nous, and more). Connect ANY one you already use. Then open the ",
          h("a", { href: "/models", style: GS_LINK }, "Models page"),
          " and select your provider (LLM) and its model — two clicks, and your agent is live. (xAI users: pick Grok 4.5.)")),
      h(StepRow, { num: "2", done: !!status.transcriptKeySet, title: "Add a transcript API key (optional — for YouTube Insights)" },
        h("div", { style: { color: MUTED, fontSize: 13 } },
          "Only needed if you want competitor YouTube intelligence. Create a key at ",
          h("a", { href: "https://transcriptapi.com", target: "_blank", rel: "noreferrer", style: GS_LINK }, "transcriptapi.com"),
          ", then set TRANSCRIPT_API_KEY on the ",
          h("a", { href: "/env", style: GS_LINK }, "Keys page"),
          " — it's waiting for you under Custom Keys.")),
      h(StepRow, { num: "3", done: !!status.imageGenReady, title: "Enable image generation (thumbnails & beat visuals)" },
        h("div", { style: { color: MUTED, fontSize: 13 } },
          "Already covered if you connected xAI Grok in step 1 — images use Grok automatically. ",
          "Using a different AI provider (Claude, OpenAI, …)? Create a free Google Gemini key at ",
          h("a", { href: "https://aistudio.google.com/apikey", target: "_blank", rel: "noreferrer", style: GS_LINK }, "aistudio.google.com/apikey"),
          " and set GEMINI_API_KEY on the ",
          h("a", { href: "/env", style: GS_LINK }, "Keys page"),
          " under Custom Keys — it's only used when xAI isn't connected.")));
  }

  function ValueCreatorPage() {
    var dataSt = useState(null);
    var data = dataSt[0], setData = dataSt[1];
    var errSt = useState(null);
    var error = errSt[0], setError = errSt[1];
    var busyCreateSt = useState(null);
    var busyTaskCreate = busyCreateSt[0], setBusyTaskCreate = busyCreateSt[1];
    var coachSt = useState({});
    var coach = coachSt[0], setCoach = coachSt[1];
    var expandedSt = useState(null);
    var expandedTask = expandedSt[0], setExpandedTask = expandedSt[1];
    var viewSt = useState("laps");
    var view = viewSt[0], setView = viewSt[1];
    var pendingPhaseRef = useRef(null);

    var levelSt = useState(null);
    var levelStatus = levelSt[0], setLevelStatus = levelSt[1];
    var levelGateSt = useState(false);
    var levelGate = levelGateSt[0], setLevelGate = levelGateSt[1];
    var refresh = useCallback(function () {
      api("/coach")
        .then(function (d) {
          if (d && d.steps) setCoach(d.steps);
          if (d) { setLevelStatus(d.levelStatus || null); setLevelGate(!!d.levelGate); }
        })
        .catch(function () { /* coach state is additive */ });
      return api("/roadmap")
        .then(function (d) { setData(d); setError(null); })
        .catch(function (e) { setError(String((e && e.message) || e)); });
    }, []);

    useEffect(function () {
      refresh();
      // Kanban tasks progress in the background — refresh on a slow poll so
      // Done lands automatically when a step's task completes.
      var iv = window.setInterval(refresh, 15000);
      return function () { window.clearInterval(iv); };
    }, [refresh]);

    var onPhaseSelect = function (phaseId) {
      if (view === "phases") {
        scrollToPhase(phaseId);
      } else {
        pendingPhaseRef.current = phaseId;
        setView("phases");
      }
    };
    useEffect(function () {
      if (view === "phases" && pendingPhaseRef.current) {
        scrollToPhase(pendingPhaseRef.current);
        pendingPhaseRef.current = null;
      }
    }, [view]);

    function coachStart(taskId) {
      setBusyTaskCreate(taskId);
      postJSON("/coach/start", { taskId: taskId })
        .catch(function (e) { setError(String((e && e.message) || e)); })
        .then(refresh)
        .finally(function () { setBusyTaskCreate(null); });
    }

    function coachAnswer(taskId, text) {
      setBusyTaskCreate(taskId);
      postJSON("/coach/answer", { taskId: taskId, text: text })
        .catch(function (e) { setError(String((e && e.message) || e)); })
        .then(refresh)
        .finally(function () { setBusyTaskCreate(null); });
    }

    function coachReset(taskId) {
      setBusyTaskCreate(taskId);
      postJSON("/coach/reset", { taskId: taskId })
        .catch(function (e) { setError(String((e && e.message) || e)); })
        .then(refresh)
        .finally(function () {
          setBusyTaskCreate(null);
          setExpandedTask(null);   // collapse the panel — fresh start
        });
    }

    function handleReset() {
      if (!window.confirm("Reset all roadmap progress? (Kanban tasks already created are kept — only the roadmap's progress and step links are cleared.)")) return;
      postJSON("/reset-progress", {}).then(refresh);
    }

    if (error && !data) {
      return h("div", { style: { padding: 24, color: "#f87171" } }, "Error: " + error);
    }
    if (!data) {
      return h("div", { style: { padding: 24, color: MUTED } }, "Loading roadmap…");
    }

    var phases = data.phases || [];
    var foundationPhase = null;
    var wheelPhases = [];
    phases.forEach(function (p) {
      if (p.foundation) foundationPhase = p;
      else wheelPhases.push(p);
    });
    var foundationDone = !foundationPhase || foundationPhase.tasks.every(function (t) { return t.status === "done"; });
    var totalTasks = data.totalTasks || 0;
    var doneTasks = data.doneTasks || 0;
    var pct = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0;
    var laps = buildLaps(wheelPhases);
    var activeHint = (VIEW_TABS.find(function (t) { return t.id === view; }) || {}).hint || "";

    var taskById = {};
    phases.forEach(function (p) { p.tasks.forEach(function (t) { taskById[t.id] = t; }); });

    var taskActions = {
      busyTaskId: busyTaskCreate,
      levelGate: levelGate,
      coach: coach,
      expandedTask: expandedTask,
      onToggle: function (taskId) {
        setExpandedTask(expandedTask === taskId ? null : taskId);
      },
      onStart: coachStart,
      onAnswer: coachAnswer,
      onReset: coachReset,
      refresh: refresh,
    };

    return h("div", { className: "acvc-page", style: { background: PAGE_BG, minHeight: "100%", color: TEXT } },
      h("div", { style: { padding: "28px 24px 48px", maxWidth: 1100, margin: "0 auto" } },

        h(GettingStartedCard, null),

        // Header
        h("div", {
          style: {
            display: "flex", alignItems: "flex-end", justifyContent: "space-between",
            flexWrap: "wrap", gap: 16, marginBottom: 24,
          },
        },
          h("div", null,
            h("div", { style: { fontSize: 13, letterSpacing: 1.5, color: MUTED, textTransform: "uppercase" } },
              "AI Cyber Value Creator"),
            h("h1", { style: { fontSize: 30, margin: "4px 0 6px", fontWeight: 800 } },
              (data.centerLabel || "AI Cyber Value Creator") + " Roadmap"),
            h("div", { style: { color: MUTED, fontSize: 14, maxWidth: 640 } },
              "First lay the ", h("b", null, "foundation"),
              " — Create Value (ICP → Problems → Solutions → Offer). Then work the four-phase value flywheel in ",
              h("b", null, "laps"),
              " — one trip around hits step 1 of all four phases, the next trip hits step 2, and so on.")),
          h("div", { style: { textAlign: "right", minWidth: 200 } },
            h("div", { style: { fontSize: 34, fontWeight: 800 } }, pct + "%"),
            h("div", { style: { color: MUTED, fontSize: 13 } }, doneTasks + " / " + totalTasks + " sub-tasks complete"),
            h(ProgressBar, { pct: pct, color: PURPLE }))
        ),

        // Your Level — gates the roadmap (only when that plugin is installed)
        levelStatus && levelStatus.installed
          ? h(LevelSection, { levelStatus: levelStatus })
          : null,

        // Foundation
        foundationPhase
          ? h(FoundationSection, {
              phase: foundationPhase, done: foundationDone,
              taskActions: taskActions,
            })
          : null,

        // Company Context
        h(CompanyContextPanel, { contextData: data.context, taskById: taskById, refresh: refresh }),

        // Flywheel
        h(Flywheel, { phases: wheelPhases, onPhase: onPhaseSelect }),

        // View toggle
        h("div", { style: { marginTop: 28, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" } },
          h(ViewToggle, { view: view, onChange: setView }),
          h("span", { style: { color: MUTED, fontSize: 13 } }, activeHint)),

        // Selected view
        h("div", { style: { marginTop: 18 } },
          view === "phases"
            ? h("div", { style: { display: "flex", flexDirection: "column", gap: 18 } },
                wheelPhases.map(function (phase, i) {
                  return h(PhaseCard, {
                    key: phase.id, index: i, numPhases: wheelPhases.length, phase: phase,
                    taskActions: taskActions,
                    isLast: i === wheelPhases.length - 1,
                  });
                }))
            : null,
          view === "laps"
            ? h("div", { style: { display: "flex", flexDirection: "column", gap: 18 } },
                laps.map(function (lap) {
                  return h(LapCard, {
                    key: lap.index, lap: lap, totalLaps: laps.length,
                    taskActions: taskActions,
                  });
                }))
            : null,
          view === "sequence"
            ? h(SequenceView, { laps: laps, taskActions: taskActions })
            : null
        ),

        // Footer
        h("div", {
          style: {
            marginTop: 32, display: "flex", alignItems: "center",
            justifyContent: "space-between", color: MUTED, fontSize: 12,
          },
        },
          h("span", null, "Tip: expand any step with \"▸ Coach\" — guidance plus a live working session, right here. Steps complete (and reset) through the Coach, not by clicking."),
          h("button", { onClick: handleReset, className: "acvc-btn-ghost" }, "Reset progress")),

        data.build
          ? h("div", { className: "acvc-version", style: { marginTop: 14, textAlign: "center", fontSize: 11, color: MUTED } },
              "AI Cyber Value Creator v" + data.build)
          : null
      )
    );
  }

  window.__HERMES_PLUGINS__.register("ai-cyber-value-creator", ValueCreatorPage);
})();
