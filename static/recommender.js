(function () {
  const root = document.getElementById("root");
  const form = document.getElementById("form-profile");
  const errEl = document.getElementById("form-error");
  const btnSubmit = document.getElementById("btn-submit");
  const panelOutput = document.getElementById("panel-output");
  const metaEl = document.getElementById("output-meta");
  const tiersEl = document.getElementById("output-tiers");
  const btnBack = document.getElementById("btn-back");

  function esc(s) {
    if (s == null) return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }

  function optNum(input) {
    const v = input.value.trim();
    if (v === "") return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  function buildPayload(fd) {
    const housing = (fd.get("housing") || "").toString();
    const payload = {
      credit_score: Number(fd.get("credit_score")),
      annual_income: Number(fd.get("annual_income")),
      location: (fd.get("location") || "").toString().trim() || "US",
      housing: housing,
      is_student: fd.get("is_student") === "on",
    };
    const ch = optNum({ value: fd.get("credit_history_years") || "" });
    const dtiRaw = (fd.get("debt_to_income_ratio") || "").toString().trim();
    const emp = optNum({ value: fd.get("employment_years") || "" });
    const inqRaw = (fd.get("recent_hard_inquiries_12m") || "").toString().trim();
    const spend = optNum({ value: fd.get("estimated_monthly_card_spend") || "" });

    if (ch != null) payload.credit_history_years = ch;
    if (dtiRaw !== "") {
      const dti = Number(dtiRaw);
      if (Number.isFinite(dti)) payload.debt_to_income_ratio = dti;
    }
    if (emp != null) payload.employment_years = emp;
    if (inqRaw !== "") {
      const inq = parseInt(inqRaw, 10);
      if (Number.isFinite(inq)) payload.recent_hard_inquiries_12m = inq;
    }
    if (spend != null) payload.estimated_monthly_card_spend = spend;
    return payload;
  }

  function formatMoney(n) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(n);
  }

  function profileLines(p) {
    const lines = [
      `Score ${p.credit_score} · Income ${formatMoney(p.annual_income)} · ${esc(p.location)} · ${p.housing}`,
      p.is_student ? "Student" : "Not a student",
    ];
    if (p.credit_history_years != null) lines.push(`History ~${p.credit_history_years} yr`);
    if (p.debt_to_income_ratio != null)
      lines.push(`DTI ${(p.debt_to_income_ratio * 100).toFixed(0)}%`);
    if (p.employment_years != null) lines.push(`Job ~${p.employment_years} yr`);
    if (p.recent_hard_inquiries_12m != null) lines.push(`Inquiries ${p.recent_hard_inquiries_12m}`);
    if (p.estimated_monthly_card_spend != null)
      lines.push(`Spend ~${formatMoney(p.estimated_monthly_card_spend)}/mo`);
    return lines.join(" · ");
  }

  function renderList(items, className) {
    if (!items || !items.length) return `<p class="tier__empty">None in this bucket.</p>`;
    return `<ul class="card__list ${className}">${items.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`;
  }

  function renderCard(c, staggerMs) {
    const skipBlock =
      c.avoid_if && c.avoid_if.length
        ? `<p class="card__skip-title">Often skip if</p>${renderList(c.avoid_if, "card__list")}`
        : "";

    const notesBlock =
      c.profile_notes && c.profile_notes.length
        ? `<div class="card__notes"><span class="card__col-title">Your profile</span><ul>${c.profile_notes
            .map((n) => `<li>${esc(n)}</li>`)
            .join("")}</ul></div>`
        : "";

    return `
      <article class="card" style="--delay:${staggerMs}ms">
        <div class="card__top">
          <div>
            <h2 class="card__name">${esc(c.name)}</h2>
            <p class="card__issuer">${esc(c.issuer)}</p>
          </div>
          <div class="card__meta">${esc(c.annual_fee_label)}<br/>fit ${esc(String(c.fit_score))}</div>
        </div>
        <p class="card__band">Typical score band: ${esc(c.score_band)}</p>
        <div class="card__cols">
          <div>
            <p class="card__col-title">Pros</p>
            ${renderList(c.pros, "card__list card__list--pros")}
          </div>
          <div>
            <p class="card__col-title">Cons</p>
            ${renderList(c.cons, "card__list card__list--cons")}
          </div>
        </div>
        ${skipBlock}
        ${notesBlock}
      </article>
    `;
  }

  function renderTier(title, cards, state) {
    let delay = state.d;
    const list = cards || [];
    const body = list.length
      ? list
          .map((c) => {
            const d = delay;
            delay += 42;
            return renderCard(c, d);
          })
          .join("")
      : `<p class="tier__empty">None in this bucket.</p>`;
    state.d = delay + 90;
    return `<section class="tier"><h3 class="tier__label">${esc(title)}</h3>${body}</section>`;
  }

  function showOutput(data) {
    const p = data.profile;
    const m = data.meta;
    const stagger = { d: 50 };

    metaEl.innerHTML = `
      <p class="meta__profile">${profileLines(p)}</p>
      <p class="meta__note">${esc(m.location_note)}</p>
      ${m.housing_hint ? `<p class="meta__note">${esc(m.housing_hint)}</p>` : ""}
      <p class="meta__disclaimer">${esc(m.disclaimer)}</p>
    `;

    const t = data.tiers;
    tiersEl.innerHTML =
      renderTier("Stronger match", t.good, stagger) +
      renderTier("Compare carefully", t.maybe, stagger) +
      renderTier("Skip for now", t.avoid, stagger);

    panelOutput.hidden = false;
    requestAnimationFrame(() => {
      root.dataset.phase = "output";
    });
  }

  function showInput() {
    root.dataset.phase = "input";
    const onEnd = (e) => {
      if (e.target !== panelOutput || e.propertyName !== "opacity") return;
      panelOutput.removeEventListener("transitionend", onEnd);
      if (root.dataset.phase === "input") panelOutput.hidden = true;
    };
    panelOutput.addEventListener("transitionend", onEnd);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errEl.hidden = true;
    errEl.textContent = "";

    const fd = new FormData(form);
    const payload = buildPayload(fd);

    if (!payload.housing) {
      errEl.textContent = "Choose housing (rent, own, or other).";
      errEl.hidden = false;
      return;
    }

    btnSubmit.disabled = true;
    btnSubmit.classList.add("is-loading");

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.error || "Something went wrong.");
      }
      showOutput(data);
    } catch (err) {
      errEl.textContent = err.message || "Request failed.";
      errEl.hidden = false;
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.classList.remove("is-loading");
    }
  });

  btnBack.addEventListener("click", () => {
    showInput();
  });
})();
