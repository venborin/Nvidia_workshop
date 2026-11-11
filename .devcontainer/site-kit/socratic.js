/* socratic.js: Socratic check questions for a page of the workshop site.

   In a page, write each question in a block with an id from the answer key:

     <div class="socratic" data-question="q1">
       <p>Why does a buffer resist a change in pH?</p>
     </div>

   and before </body>:   <script src="socratic.js" defer></script>
   (from a page in a subfolder: <script src="../socratic.js" defer></script>)

   The answer key lives in site/.tutor/questions.json, which is never served or
   published. When a student answers, the site's own server asks the workshop
   model to judge the answer against the key and reply with one guiding
   question; the key and the model key never reach the browser. On the
   permanent GitHub Pages copy there is no server, so each block shows the
   question and says checking works on the live site. Replies are plain text. */
(function () {
  "use strict";
  var here = document.currentScript && document.currentScript.src;
  if (!here) return;
  var STATUS = new URL("api/status", here).href;
  var CHECK = new URL("api/socratic", here).href;

  var css = [
    ".socratic{border:1px solid #c9d6d4;border-left:4px solid #0d6a65;border-radius:10px;padding:14px 16px;margin:20px 0;",
    "background:#f6faf9;color:#15242a;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}",
    ".socratic-label{font:700 12px/1 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#0d6a65;margin-bottom:6px}",
    ".socratic-thread{display:flex;flex-direction:column;gap:8px;margin:10px 0}",
    ".socratic-msg{white-space:pre-wrap;padding:8px 10px;border-radius:8px}",
    ".socratic-msg.student{background:#dcecea;align-self:flex-end;max-width:90%}",
    ".socratic-msg.tutor{background:#fff;border:1px solid #e3ebea;max-width:95%}",
    ".socratic-msg.note{color:#55676e;font-size:14px}",
    ".socratic-verdict{display:inline-block;font:700 12px/1 system-ui,sans-serif;padding:4px 8px;border-radius:999px;margin-right:6px;vertical-align:1px}",
    ".socratic-verdict.correct{background:#d7f0dc;color:#1d5b2a}",
    ".socratic-verdict.partly{background:#fdf0c8;color:#6b4e00}",
    ".socratic-verdict.notyet{background:#f6e0dc;color:#7a2a1d}",
    ".socratic-form{display:flex;gap:8px;flex-wrap:wrap}",
    ".socratic-form textarea{flex:1 1 240px;min-height:56px;resize:vertical;font:inherit;padding:8px;border:1px solid #c9d6d4;border-radius:8px;background:#fff;color:inherit}",
    ".socratic-form button{font:600 15px system-ui,sans-serif;padding:8px 14px;border:0;border-radius:8px;background:#0d6a65;color:#fff;cursor:pointer;align-self:flex-end}",
    ".socratic-form button[disabled]{opacity:.5;cursor:default}",
    ".socratic textarea:focus-visible,.socratic button:focus-visible{outline:3px solid #f2b705;outline-offset:2px}",
    "@media (prefers-color-scheme:dark){.socratic{background:#152328;color:#e3ecec;border-color:#27383e;border-left-color:#62c4ba}",
    ".socratic-label{color:#62c4ba}.socratic-msg.student{background:#17353a}.socratic-msg.tutor{background:#0f191d;border-color:#27383e}",
    ".socratic-msg.note{color:#94a7ac}.socratic-form textarea{background:#0f191d;border-color:#27383e}}"
  ].join("");
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var LABEL = { correct: "Correct", partly: "Partly", "not yet": "Not yet" };

  function setup(block, live, offlineText) {
    var id = block.getAttribute("data-question") || "";
    var questionText = (block.innerText || block.textContent || "").trim().slice(0, 1500);
    var history = [];
    var label = document.createElement("div");
    label.className = "socratic-label";
    label.textContent = "Check your understanding";
    block.insertBefore(label, block.firstChild);
    var thread = document.createElement("div");
    thread.className = "socratic-thread";
    thread.setAttribute("aria-live", "polite");
    var form = document.createElement("form");
    form.className = "socratic-form";
    var box = document.createElement("textarea");
    box.id = "socratic-" + id;
    box.placeholder = "Your answer, in your own words";
    box.setAttribute("aria-label", "Your answer");
    var send = document.createElement("button");
    send.type = "submit";
    send.textContent = "Check my answer";
    form.appendChild(box);
    form.appendChild(send);
    block.appendChild(thread);
    block.appendChild(form);

    function add(kind, text, verdict) {
      var p = document.createElement("div");
      p.className = "socratic-msg " + kind;
      if (verdict) {
        var v = document.createElement("span");
        v.className = "socratic-verdict " + verdict.replace(" ", "");
        v.textContent = LABEL[verdict] || verdict;
        p.appendChild(v);
      }
      p.appendChild(document.createTextNode(text));
      thread.appendChild(p);
      return p;
    }

    if (!live) {
      box.disabled = true;
      send.disabled = true;
      add("note", offlineText);
      return;
    }
    box.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); form.requestSubmit(); }
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var a = box.value.trim();
      if (!a) return;
      box.value = "";
      add("student", a);
      send.disabled = true;
      var wait = add("note", "Checking...");
      fetch(CHECK, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: id, question: questionText, history: history.slice(-12), answer: a.slice(0, 1500),
                               page: ((document.querySelector("main") || document.body).innerText || "").slice(0, 3000) })
      }).then(function (r) {
        return r.json().catch(function () { return { error: "The tutor gave no reply." }; });
      }).then(function (d) {
        wait.remove();
        if (d && d.reply) {
          add("tutor", d.reply, d.verdict);
          history.push({ role: "student", content: a.slice(0, 1000) });
          history.push({ role: "tutor", content: d.reply.slice(0, 1000) });
          box.placeholder = d.verdict === "correct" ? "Answer the follow-up, or move on" : "Try again, with the question in mind";
        } else {
          add("note", (d && d.error) || "The tutor gave no reply.");
        }
      }).catch(function () {
        wait.remove();
        add("note", "The tutor could not be reached. Try again in a moment.");
      }).then(function () { send.disabled = false; box.focus(); });
    });
  }

  function start() {
    var blocks = Array.prototype.slice.call(document.querySelectorAll(".socratic[data-question]"));
    if (!blocks.length) return;
    fetch(STATUS, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("no server");
      return r.json();
    }).then(function (d) {
      var live = !!(d && d.available);
      var why = d && d.reason === "resting until tomorrow"
        ? "The tutor has checked all the answers it can for today."
        : "The tutor is not connected yet.";
      blocks.forEach(function (b) { setup(b, live, why); });
    }).catch(function () {
      blocks.forEach(function (b) { setup(b, false, "Answers are checked on the live site, while its Codespace is running."); });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
