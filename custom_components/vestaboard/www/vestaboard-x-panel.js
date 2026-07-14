/**
 * Vestaboard-x sidebar panel: props builder + VBML modal with
 * syntax highlighting, validation, and drag-and-drop prop insertion.
 */
class VestaboardXPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
    this._devices = [];
    this._deviceId = "";
    this._props = this._defaultProps();
    this._vbmlText = this._defaultVbml();
    this._templates = [];
    this._selectedTemplateId = "";
    this._templateName = "Elvira's House of Horrors";
    this._modalOpen = false;
    this._validation = { valid: null, errors: [], warnings: [] };
    this._validateTimer = null;
    this._sendStatus = "";
    this._dragProp = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._devicesLoaded) {
      this._devicesLoaded = true;
      this._loadDevices();
      this._loadTemplates();
    }
  }

  set narrow(value) {
    this._narrow = Boolean(value);
    if (this._rendered) this._render();
  }

  set panel(_panel) {}

  connectedCallback() {
    this._render();
    this._rendered = true;
  }

  _scoreCommaTemplate(entityId) {
    // Full score with thousands separators, e.g. 1,233,532,321
    return `{{ '{:,.0f}'.format(states('${entityId}') | float(0)) }}`;
  }

  _defaultProps() {
    // Matches seeded Elvira template (all games use player/score props)
    const scoreEntity =
      "sensor.2026_leaderboard_elvira_s_house_of_horrors_top_score";
    return [
      {
        name: "player",
        entity_id:
          "sensor.2026_leaderboard_elvira_s_house_of_horrors_top_player",
        template: "", // UI field only; blank templates are omitted on save/resolve
      },
      {
        name: "score",
        entity_id: scoreEntity,
        template: this._scoreCommaTemplate(scoreEntity),
      },
    ];
  }

  _defaultVbml() {
    // Flagship 6x22 — corner dots, title, player, TOP SCORE, full score
    // {63}=red, {70}=black
    return JSON.stringify(
      {
        props: {},
        components: [
          {
            style: {
              justify: "left",
              align: "top",
              height: 1,
              width: 1,
              absolutePosition: { x: 0, y: 0 },
            },
            template: "{70}",
          },
          {
            style: {
              justify: "left",
              align: "top",
              height: 1,
              width: 1,
              absolutePosition: { x: 21, y: 0 },
            },
            template: "{63}",
          },
          {
            style: {
              justify: "center",
              align: "top",
              height: 2,
              width: 22,
              absolutePosition: { x: 0, y: 1 },
            },
            template: "ELVIRA'S HOUSE\nOF HORRORS",
          },
          {
            style: {
              justify: "center",
              align: "top",
              height: 1,
              width: 22,
              absolutePosition: { x: 0, y: 3 },
            },
            template: "{{player}}",
          },
          {
            style: {
              justify: "center",
              align: "top",
              height: 1,
              width: 22,
              absolutePosition: { x: 0, y: 4 },
            },
            template: "TOP SCORE",
          },
          {
            style: {
              justify: "center",
              align: "top",
              height: 1,
              width: 20,
              absolutePosition: { x: 1, y: 5 },
            },
            template: "{{score}}",
          },
          {
            style: {
              justify: "left",
              align: "top",
              height: 1,
              width: 1,
              absolutePosition: { x: 0, y: 5 },
            },
            template: "{63}",
          },
          {
            style: {
              justify: "left",
              align: "top",
              height: 1,
              width: 1,
              absolutePosition: { x: 21, y: 5 },
            },
            template: "{70}",
          },
        ],
      },
      null,
      2
    );
  }

  async _loadDevices() {
    if (!this._hass) return;
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "vestaboard/list_devices",
      });
      this._devices = result.devices || [];
      if (!this._deviceId && this._devices.length) {
        this._deviceId = this._devices[0].id;
      }
      this._render();
    } catch (err) {
      this._sendStatus = `Failed to load devices: ${err.message || err}`;
      this._render();
    }
  }

  async _loadTemplates(selectId) {
    if (!this._hass) return;
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "vestaboard/list_templates",
      });
      this._templates = result.templates || [];
      const preferred =
        selectId ||
        this._selectedTemplateId ||
        (this._templates[0] && this._templates[0].id);
      if (preferred) {
        const match = this._templates.find((t) => t.id === preferred);
        if (match) this._applyTemplate(match, false);
      }
      this._render();
    } catch (err) {
      this._sendStatus = `Failed to load templates: ${err.message || err}`;
      this._render();
    }
  }

  _applyTemplate(template, render = true) {
    this._selectedTemplateId = template.id || "";
    this._templateName = template.name || "";
    this._props = (template.props || []).map((p) => ({
      name: p.name || "",
      entity_id: p.entity_id || "",
      template: p.template || "",
      attribute: p.attribute || "",
    }));
    const vbml = template.vbml || { props: {}, components: [] };
    this._vbmlText =
      typeof vbml === "string" ? vbml : JSON.stringify(vbml, null, 2);
    if (render) this._render();
  }

  _currentPropsPayload() {
    return this._props
      .filter((p) => p.name && (p.entity_id || p.template))
      .map((p) => {
        const item = { name: p.name };
        if (p.entity_id) item.entity_id = p.entity_id;
        if (p.attribute) item.attribute = p.attribute;
        if (p.template) item.template = p.template;
        return item;
      });
  }

  async _saveTemplate(asNew) {
    if (!this._hass) return;
    const name = (this._templateName || "").trim();
    if (!name) {
      this._sendStatus = "Enter a template name before saving.";
      this._render();
      return;
    }
    let vbml;
    try {
      vbml = JSON.parse(this._vbmlText);
    } catch (err) {
      this._sendStatus = `Cannot save — VBML JSON invalid: ${err.message}`;
      this._render();
      return;
    }
    const payload = {
      type: "vestaboard/save_template",
      name,
      props: this._currentPropsPayload(),
      vbml,
    };
    if (!asNew && this._selectedTemplateId) payload.id = this._selectedTemplateId;
    try {
      const result = await this._hass.connection.sendMessagePromise(payload);
      if (!result.ok) {
        this._sendStatus = result.error || "Save failed.";
        this._render();
        return;
      }
      this._sendStatus = `Saved template "${result.template.name}".`;
      await this._loadTemplates(result.template.id);
    } catch (err) {
      this._sendStatus = `Save failed: ${err.message || err}`;
      this._render();
    }
  }

  async _deleteTemplate() {
    if (!this._hass || !this._selectedTemplateId) {
      this._sendStatus = "Select a saved template to delete.";
      this._render();
      return;
    }
    const current = this._templates.find((t) => t.id === this._selectedTemplateId);
    if (
      current &&
      !window.confirm(`Delete template "${current.name}"? This cannot be undone.`)
    ) {
      return;
    }
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "vestaboard/delete_template",
        id: this._selectedTemplateId,
      });
      if (!result.ok) {
        this._sendStatus = result.error || "Delete failed.";
        this._render();
        return;
      }
      this._selectedTemplateId = "";
      this._sendStatus = "Template deleted.";
      await this._loadTemplates();
    } catch (err) {
      this._sendStatus = `Delete failed: ${err.message || err}`;
      this._render();
    }
  }

  _yamlScalar(value) {
    if (value === null || value === undefined) return '""';
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    const text = String(value);
    if (text === "") return '""';
    if (
      /[:#{}[\],&*?|>!%@`]/.test(text) ||
      /^\s|\s$/.test(text) ||
      /\n/.test(text) ||
      text.includes("{{")
    ) {
      return `"${text
        .replace(/\\/g, "\\\\")
        .replace(/"/g, '\\"')
        .replace(/\n/g, "\\n")}"`;
    }
    return text;
  }

  _yamlDump(value, indent = 0) {
    const pad = "  ".repeat(indent);
    if (Array.isArray(value)) {
      if (!value.length) return `${pad}[]`;
      return value
        .map((item) => {
          if (item !== null && typeof item === "object" && !Array.isArray(item)) {
            const keys = Object.keys(item);
            if (!keys.length) return `${pad}- {}`;
            const firstKey = keys[0];
            const firstVal = item[firstKey];
            let block = "";
            if (firstVal !== null && typeof firstVal === "object") {
              block += `${pad}- ${firstKey}:\n${this._yamlDump(firstVal, indent + 2)}\n`;
            } else {
              block += `${pad}- ${firstKey}: ${this._yamlScalar(firstVal)}\n`;
            }
            for (const key of keys.slice(1)) {
              const child = item[key];
              if (child !== null && typeof child === "object") {
                block += `${pad}  ${key}:\n${this._yamlDump(child, indent + 2)}\n`;
              } else {
                block += `${pad}  ${key}: ${this._yamlScalar(child)}\n`;
              }
            }
            return block.replace(/\n$/, "");
          }
          return `${pad}- ${this._yamlScalar(item)}`;
        })
        .join("\n");
    }
    if (value !== null && typeof value === "object") {
      const keys = Object.keys(value);
      if (!keys.length) return `${pad}{}`;
      return keys
        .map((key) => {
          const child = value[key];
          if (child !== null && typeof child === "object") {
            const nested = this._yamlDump(child, indent + 1);
            if (nested.trim() === "[]" || nested.trim() === "{}") {
              return `${pad}${key}: ${nested.trim()}`;
            }
            return `${pad}${key}:\n${nested}`;
          }
          return `${pad}${key}: ${this._yamlScalar(child)}`;
        })
        .join("\n");
    }
    return `${pad}${this._yamlScalar(value)}`;
  }

  _buildAutomationYaml() {
    let vbml;
    try {
      vbml = JSON.parse(this._vbmlText);
      // Keep placeholders in templates; service merges resolved props at runtime
      vbml.props = {};
    } catch (err) {
      throw new Error(`VBML JSON invalid: ${err.message}`);
    }
    const data = {
      device_id: this._deviceId || "YOUR_VESTABOARD_DEVICE_ID",
      props: this._currentPropsPayload(),
      vbml,
    };
    return `action: vestaboard.message\ndata:\n${this._yamlDump(data, 1)}`;
  }

  async _copyAutomation() {
    try {
      const yaml = this._buildAutomationYaml();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(yaml);
      } else {
        const ta = document.createElement("textarea");
        ta.value = yaml;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      this._sendStatus =
        "Copied vestaboard.message YAML to the clipboard — paste into your automation.";
    } catch (err) {
      this._sendStatus = `Copy failed: ${err.message || err}`;
    }
    this._render();
  }

  _newBlankTemplate() {
    this._selectedTemplateId = "";
    this._templateName = "New game template";
    this._props = [
      { name: "player", entity_id: "", template: "" },
      { name: "score", entity_id: "", template: "" },
    ];
    this._vbmlText = JSON.stringify(
      {
        props: {},
        components: [
          {
            style: { justify: "center", align: "center", height: 6, width: 22 },
            template: "GAME TITLE\n\n{{player}}\n\nTOP SCORE {{score}}",
          },
        ],
      },
      null,
      2
    );
    this._sendStatus = "Drafting a new template — edit, then Save as new.";
    this._render();
  }

  _escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  _highlightJson(source) {
    // Simple JSON highlighter + {{prop}} accents
    let out = "";
    let i = 0;
    const s = source;
    const push = (cls, text) => {
      out += `<span class="${cls}">${this._escapeHtml(text)}</span>`;
    };
    while (i < s.length) {
      const ch = s[i];
      if (ch === '"') {
        let j = i + 1;
        while (j < s.length) {
          if (s[j] === "\\") {
            j += 2;
            continue;
          }
          if (s[j] === '"') break;
          j += 1;
        }
        const end = Math.min(j + 1, s.length);
        const str = s.slice(i, end);
        const after = s.slice(end).match(/^\s*:/);
        if (after) {
          push("tok-key", str);
        } else if (/\{\{[^{}]+\}\}/.test(str)) {
          const escaped = this._escapeHtml(str).replace(
            /(\{\{[^{}]+\}\})/g,
            '<span class="tok-prop">$1</span>'
          );
          out += `<span class="tok-string">${escaped}</span>`;
        } else {
          push("tok-string", str);
        }
        i = end;
        continue;
      }
      if ((ch === "-" && /[0-9]/.test(s[i + 1] || "")) || /[0-9]/.test(ch)) {
        let j = i + 1;
        while (j < s.length && /[0-9.eE+\-]/.test(s[j])) j += 1;
        push("tok-number", s.slice(i, j));
        i = j;
        continue;
      }
      if (/[a-zA-Z]/.test(ch)) {
        let j = i + 1;
        while (j < s.length && /[a-zA-Z]/.test(s[j])) j += 1;
        const word = s.slice(i, j);
        push(
          word === "true" || word === "false" || word === "null"
            ? "tok-bool"
            : "tok-plain",
          word
        );
        i = j;
        continue;
      }
      push("tok-plain", ch);
      i += 1;
    }
    return out;
  }

  _scheduleValidate() {
    clearTimeout(this._validateTimer);
    this._validateTimer = setTimeout(() => this._validate(), 350);
  }

  async _validate() {
    if (!this._hass) return;
    const payload = {
      type: "vestaboard/validate_vbml",
      vbml: this._vbmlText,
    };
    if (this._deviceId) payload.device_id = this._deviceId;
    try {
      const result = await this._hass.connection.sendMessagePromise(payload);
      this._validation = {
        valid: result.valid,
        errors: result.errors || [],
        warnings: result.warnings || [],
      };
    } catch (err) {
      this._validation = {
        valid: false,
        errors: [String(err.message || err)],
        warnings: [],
      };
    }
    this._paintEditor();
    this._paintStatus();
  }

  async _syncPropsIntoVbml() {
    if (!this._hass) return;
    const defs = this._props.filter((p) => p.name && (p.entity_id || p.template));
    let resolved = {};
    if (defs.length) {
      try {
        const result = await this._hass.connection.sendMessagePromise({
          type: "vestaboard/resolve_props",
          props: defs,
        });
        if (result.ok) resolved = result.props || {};
        else this._sendStatus = result.error || "Failed to resolve props";
      } catch (err) {
        this._sendStatus = String(err.message || err);
      }
    }
    try {
      const data = JSON.parse(this._vbmlText);
      data.props = { ...(data.props || {}), ...resolved };
      // Ensure keys for named props even if resolve failed partially
      for (const p of this._props) {
        if (p.name && !(p.name in (data.props || {}))) {
          data.props[p.name] = data.props[p.name] || "";
        }
      }
      this._vbmlText = JSON.stringify(data, null, 2);
    } catch (_err) {
      // Keep editor text if JSON currently invalid
    }
  }

  _insertAtCursor(textarea, text) {
    const start = textarea.selectionStart ?? textarea.value.length;
    const end = textarea.selectionEnd ?? start;
    const before = textarea.value.slice(0, start);
    const after = textarea.value.slice(end);
    textarea.value = before + text + after;
    const pos = start + text.length;
    textarea.selectionStart = pos;
    textarea.selectionEnd = pos;
    this._vbmlText = textarea.value;
    textarea.focus();
    this._paintEditor();
    this._scheduleValidate();
  }

  _paintEditor() {
    const pre = this.shadowRoot.querySelector("#highlight");
    const ta = this.shadowRoot.querySelector("#vbml-editor");
    if (!pre || !ta) return;
    pre.innerHTML = this._highlightJson(ta.value) + "\n";
    const shell = this.shadowRoot.querySelector(".editor-shell");
    if (!shell) return;
    shell.classList.remove("is-valid", "is-invalid", "is-unknown");
    if (this._validation.valid === true) shell.classList.add("is-valid");
    else if (this._validation.valid === false) shell.classList.add("is-invalid");
    else shell.classList.add("is-unknown");
  }

  _paintStatus() {
    const el = this.shadowRoot.querySelector("#validation-status");
    if (!el) return;
    const { valid, errors, warnings } = this._validation;
    if (valid === null) {
      el.className = "status unknown";
      el.textContent = "Waiting for validation…";
      return;
    }
    if (valid) {
      el.className = "status valid";
      const warn =
        warnings && warnings.length
          ? ` Warnings: ${warnings.join(" | ")}`
          : "";
      el.textContent = `VBML is syntactically valid.${warn}`;
    } else {
      el.className = "status invalid";
      el.textContent = (errors || ["Invalid VBML"]).join(" | ");
    }
  }

  async _openModal() {
    await this._syncPropsIntoVbml();
    this._modalOpen = true;
    this._render();
    this._paintEditor();
    this._scheduleValidate();
    const ta = this.shadowRoot.querySelector("#vbml-editor");
    if (ta) ta.focus();
  }

  _closeModal(apply) {
    const ta = this.shadowRoot.querySelector("#vbml-editor");
    if (apply && ta) this._vbmlText = ta.value;
    this._modalOpen = false;
    this._render();
  }

  async _send() {
    if (!this._hass || !this._deviceId) {
      this._sendStatus = "Select a Vestaboard device first.";
      this._render();
      return;
    }
    await this._syncPropsIntoVbml();
    await this._validate();
    if (!this._validation.valid) {
      this._sendStatus = "Fix VBML validation errors before sending.";
      this._render();
      return;
    }
    let vbml;
    try {
      vbml = JSON.parse(this._vbmlText);
    } catch (err) {
      this._sendStatus = `Invalid JSON: ${err.message}`;
      this._render();
      return;
    }
    try {
      await this._hass.callService("vestaboard", "message", {
        device_id: this._deviceId,
        vbml,
      });
      this._sendStatus = "Message sent.";
    } catch (err) {
      this._sendStatus = String(err.message || err);
    }
    this._render();
  }

  _addProp() {
    this._props = [
      ...this._props,
      { name: `prop${this._props.length + 1}`, entity_id: "", template: "" },
    ];
    this._render();
  }

  _removeProp(index) {
    this._props = this._props.filter((_, i) => i !== index);
    this._render();
  }

  _bindMainEvents() {
    const root = this.shadowRoot;
    root.querySelector("#device")?.addEventListener("change", (e) => {
      this._deviceId = e.target.value;
    });
    root.querySelector("#template-select")?.addEventListener("change", (e) => {
      const id = e.target.value;
      if (!id) {
        this._selectedTemplateId = "";
        return;
      }
      const match = this._templates.find((t) => t.id === id);
      if (match) this._applyTemplate(match, true);
    });
    root.querySelector("#template-name")?.addEventListener("change", (e) => {
      this._templateName = e.target.value;
    });
    root.querySelector("#template-name")?.addEventListener("input", (e) => {
      this._templateName = e.target.value;
    });
    root.querySelector("#save-template")?.addEventListener("click", () =>
      this._saveTemplate(false)
    );
    root.querySelector("#save-template-as")?.addEventListener("click", () =>
      this._saveTemplate(true)
    );
    root.querySelector("#delete-template")?.addEventListener("click", () =>
      this._deleteTemplate()
    );
    root.querySelector("#new-template")?.addEventListener("click", () =>
      this._newBlankTemplate()
    );
    root.querySelector("#copy-automation")?.addEventListener("click", () =>
      this._copyAutomation()
    );
    root.querySelector("#add-prop")?.addEventListener("click", () => this._addProp());
    root.querySelectorAll("[data-remove-prop]").forEach((btn) => {
      btn.addEventListener("click", () =>
        this._removeProp(Number(btn.getAttribute("data-remove-prop")))
      );
    });
    root.querySelectorAll("[data-prop-field]").forEach((input) => {
      input.addEventListener("change", (e) => {
        const index = Number(input.getAttribute("data-prop-index"));
        const field = input.getAttribute("data-prop-field");
        this._props[index] = { ...this._props[index], [field]: e.target.value };
      });
    });
    root.querySelector("#open-vbml")?.addEventListener("click", () => this._openModal());
    root.querySelector("#send")?.addEventListener("click", () => this._send());
  }

  _bindModalEvents() {
    const root = this.shadowRoot;
    const ta = root.querySelector("#vbml-editor");
    const pre = root.querySelector("#highlight");
    root.querySelectorAll("#apply-modal").forEach((btn) =>
      btn.addEventListener("click", () => this._closeModal(true))
    );
    root.querySelector("#cancel-modal")?.addEventListener("click", () =>
      this._closeModal(false)
    );
    root.querySelector("#backdrop")?.addEventListener("click", () =>
      this._closeModal(true)
    );
    root.querySelector("#validate-now")?.addEventListener("click", () =>
      this._validate()
    );
    root.querySelector("#format-json")?.addEventListener("click", () => {
      try {
        this._vbmlText = JSON.stringify(JSON.parse(ta.value), null, 2);
        ta.value = this._vbmlText;
        this._paintEditor();
        this._scheduleValidate();
      } catch (err) {
        this._validation = {
          valid: false,
          errors: [`Cannot format: ${err.message}`],
          warnings: [],
        };
        this._paintStatus();
      }
    });

    if (ta && pre) {
      ta.addEventListener("input", () => {
        this._vbmlText = ta.value;
        this._paintEditor();
        this._scheduleValidate();
      });
      ta.addEventListener("scroll", () => {
        pre.scrollTop = ta.scrollTop;
        pre.scrollLeft = ta.scrollLeft;
      });
      ta.addEventListener("dragover", (e) => {
        e.preventDefault();
        ta.classList.add("drop-hover");
      });
      ta.addEventListener("dragleave", () => ta.classList.remove("drop-hover"));
      ta.addEventListener("drop", (e) => {
        e.preventDefault();
        ta.classList.remove("drop-hover");
        const name =
          e.dataTransfer.getData("text/prop-name") ||
          e.dataTransfer.getData("text/plain");
        if (!name) return;
        // Approximate caret from drop coordinates when possible
        if (document.caretRangeFromPoint) {
          const range = document.caretRangeFromPoint(e.clientX, e.clientY);
          // caretRangeFromPoint may not work inside shadow textarea; fallback to selection
        }
        this._insertAtCursor(ta, `{{${name}}}`);
      });
    }

    root.querySelectorAll(".prop-chip").forEach((chip) => {
      chip.addEventListener("dragstart", (e) => {
        const name = chip.getAttribute("data-name");
        this._dragProp = name;
        e.dataTransfer.setData("text/prop-name", name);
        e.dataTransfer.setData("text/plain", name);
        e.dataTransfer.effectAllowed = "copy";
      });
      chip.addEventListener("dblclick", () => {
        if (ta) this._insertAtCursor(ta, `{{${chip.getAttribute("data-name")}}}`);
      });
      chip.addEventListener("click", () => {
        if (ta) this._insertAtCursor(ta, `{{${chip.getAttribute("data-name")}}}`);
      });
    });
  }

  _styles() {
    return `
      :host {
        display: block;
        padding: 16px;
        color: var(--primary-text-color);
        background: var(--primary-background-color, var(--hass-background, #111));
        min-height: 100vh;
        box-sizing: border-box;
        font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
      }
      h1 { margin: 0 0 8px; font-size: 1.6rem; }
      p.lead { opacity: 0.8; margin-top: 0; }
      .card {
        background: var(--card-background-color, #1c1c1c);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border: 1px solid var(--divider-color, #333);
      }
      label { display: block; font-weight: 600; margin: 8px 0 4px; }
      select, input, button, textarea {
        font: inherit;
      }
      select, input[type="text"] {
        width: 100%;
        box-sizing: border-box;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--divider-color, #444);
        background: var(--input-fill-color, transparent);
        color: var(--primary-text-color);
      }
      .row { display: grid; grid-template-columns: 1fr 1.4fr 1.4fr auto; gap: 8px; align-items: end; margin-bottom: 8px; }
      .template-grid {
        display: grid;
        grid-template-columns: 1.2fr 1fr;
        gap: 12px;
        align-items: end;
      }
      @media (max-width: 800px) {
        .row, .template-grid { grid-template-columns: 1fr; }
      }
      .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
      button {
        cursor: pointer;
        border: none;
        border-radius: 8px;
        padding: 10px 14px;
        background: var(--primary-color, #03a9f4);
        color: var(--text-primary-color, #fff);
      }
      button.secondary {
        background: var(--secondary-background-color, #333);
        color: var(--primary-text-color);
      }
      button.danger { background: var(--error-color, #db4437); }
      .status-line { margin-top: 10px; opacity: 0.9; }
      .backdrop {
        position: fixed; inset: 0; background: rgba(0,0,0,0.55);
        z-index: 10;
      }
      .modal {
        position: fixed; z-index: 11;
        left: 50%; top: 50%; transform: translate(-50%, -50%);
        width: min(1100px, calc(100vw - 24px));
        height: min(820px, calc(100vh - 24px));
        background: var(--card-background-color, #1c1c1c);
        color: var(--primary-text-color);
        border-radius: 14px;
        border: 1px solid var(--divider-color, #444);
        display: grid;
        grid-template-rows: auto 1fr auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.45);
      }
      .modal-header, .modal-footer {
        padding: 14px 16px;
        border-bottom: 1px solid var(--divider-color, #333);
        display: flex; align-items: center; justify-content: space-between; gap: 8px;
      }
      .modal-footer { border-bottom: none; border-top: 1px solid var(--divider-color, #333); }
      .modal-body {
        display: grid;
        grid-template-columns: 240px 1fr;
        min-height: 0;
      }
      @media (max-width: 800px) {
        .modal-body { grid-template-columns: 1fr; }
      }
      .props-pane {
        border-right: 1px solid var(--divider-color, #333);
        padding: 12px;
        overflow: auto;
      }
      .props-pane h3 { margin: 0 0 8px; font-size: 1rem; }
      .hint { font-size: 0.85rem; opacity: 0.75; margin-bottom: 10px; }
      .prop-chip {
        display: block;
        width: 100%;
        text-align: left;
        margin: 0 0 8px;
        background: var(--secondary-background-color, #2a2a2a);
        color: var(--primary-text-color);
        border: 1px dashed var(--primary-color, #03a9f4);
        cursor: grab;
      }
      .prop-chip small { display: block; opacity: 0.7; font-weight: 400; }
      .editor-pane { padding: 12px; display: grid; grid-template-rows: auto 1fr auto; min-height: 0; gap: 8px; }
      .editor-shell {
        position: relative;
        min-height: 0;
        border-radius: 10px;
        border: 2px solid var(--divider-color, #555);
        overflow: hidden;
        background: #0f1115;
      }
      .editor-shell.is-valid { border-color: var(--success-color, #43a047); }
      .editor-shell.is-invalid { border-color: var(--error-color, #db4437); }
      .editor-shell.is-unknown { border-color: var(--warning-color, #f4b400); }
      #highlight, #vbml-editor {
        position: absolute; inset: 0;
        margin: 0;
        padding: 12px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 13px;
        line-height: 1.45;
        white-space: pre;
        overflow: auto;
        tab-size: 2;
        box-sizing: border-box;
      }
      #highlight {
        color: #c9d1d9;
        pointer-events: none;
      }
      #vbml-editor {
        position: absolute;
        background: transparent;
        color: transparent;
        caret-color: #fff;
        border: none;
        resize: none;
        width: 100%;
        height: 100%;
      }
      #vbml-editor.drop-hover { outline: 2px dashed var(--primary-color, #03a9f4); outline-offset: -6px; }
      .tok-key { color: #79c0ff; }
      .tok-string { color: #a5d6ff; }
      .tok-prop { color: #ffa657; font-weight: 700; background: rgba(255,166,87,0.12); }
      .tok-number { color: #7ee787; }
      .tok-bool { color: #d2a8ff; }
      .tok-plain { color: #c9d1d9; }
      .status { padding: 8px 10px; border-radius: 8px; font-size: 0.92rem; }
      .status.valid { background: rgba(67,160,71,0.18); color: #b7efc5; }
      .status.invalid { background: rgba(219,68,55,0.18); color: #ffc9c5; }
      .status.unknown { background: rgba(244,180,0,0.15); color: #ffe08a; }
    `;
  }

  _render() {
    const deviceOptions = this._devices
      .map(
        (d) =>
          `<option value="${this._escapeHtml(d.id)}" ${
            d.id === this._deviceId ? "selected" : ""
          }>${this._escapeHtml(d.name)}</option>`
      )
      .join("");

    const propRows = this._props.length
      ? this._props
          .map(
            (p, index) => `
        <div class="row">
          <div>
            <label>Name</label>
            <input type="text" data-prop-index="${index}" data-prop-field="name" value="${this._escapeHtml(p.name || "")}" />
          </div>
          <div>
            <label>Entity ID</label>
            <input type="text" data-prop-index="${index}" data-prop-field="entity_id" value="${this._escapeHtml(p.entity_id || "")}" placeholder="sensor.example" />
          </div>
          <div>
            <label>Template (optional)</label>
            <input type="text" data-prop-index="${index}" data-prop-field="template" value="${this._escapeHtml(p.template || "")}" placeholder="{{ states('sensor.example') }}" />
          </div>
          <div>
            <label>&nbsp;</label>
            <button class="danger" type="button" data-remove-prop="${index}">Remove</button>
          </div>
        </div>`
          )
          .join("")
      : `<p class="hint">No props yet. Add a Home Assistant sensor/entity, then open the VBML editor and drag props into templates.</p>`;

    const chips = this._props
      .filter((p) => p.name)
      .map(
        (p) => `
        <button class="prop-chip" type="button" draggable="true" data-name="${this._escapeHtml(p.name)}">
          {{${this._escapeHtml(p.name)}}}
          <small>${this._escapeHtml(p.entity_id || p.template || "manual")}</small>
        </button>`
      )
      .join("");

    const modal = this._modalOpen
      ? `
      <div class="backdrop" id="backdrop"></div>
      <div class="modal" role="dialog" aria-modal="true" aria-label="VBML editor">
        <div class="modal-header">
          <div>
            <strong>VBML editor</strong>
            <div class="hint">Drag props into the markup or click a chip to insert {{prop}}. Color coding highlights JSON and prop placeholders.</div>
          </div>
          <button class="secondary" type="button" id="apply-modal">Done</button>
        </div>
        <div class="modal-body">
          <aside class="props-pane">
            <h3>Props</h3>
            <div class="hint">Drag into the editor</div>
            ${chips || "<p class='hint'>Add props on the main page first.</p>"}
          </aside>
          <div class="editor-pane">
            <div class="actions">
              <button type="button" id="validate-now">Validate</button>
              <button class="secondary" type="button" id="format-json">Format JSON</button>
            </div>
            <div class="editor-shell is-unknown">
              <pre id="highlight" aria-hidden="true"></pre>
              <textarea id="vbml-editor" spellcheck="false">${this._escapeHtml(this._vbmlText)}</textarea>
            </div>
            <div id="validation-status" class="status unknown">Waiting for validation…</div>
          </div>
        </div>
        <div class="modal-footer">
          <span class="hint">Border turns green when VBML is valid, red when invalid.</span>
          <div class="actions">
            <button class="secondary" type="button" id="cancel-modal">Cancel</button>
            <button type="button" id="apply-modal">Apply & close</button>
          </div>
        </div>
      </div>`
      : "";

    const templateOptions = [
      `<option value="">— unsaved draft —</option>`,
      ...this._templates.map(
        (t) =>
          `<option value="${this._escapeHtml(t.id)}" ${
            t.id === this._selectedTemplateId ? "selected" : ""
          }>${this._escapeHtml(t.name)}</option>`
      ),
    ].join("");

    this.shadowRoot.innerHTML = `
      <style>${this._styles()}</style>
      <h1>Vestaboard-x</h1>
      <p class="lead">Saved templates include the rainbow <strong>Location Announcement</strong> and each Stern game board. Use <code>vestaboard.send_template</code> in automations, or copy YAML for a custom <code>vestaboard.message</code>.</p>
      <div class="card">
        <label for="device">Device</label>
        <select id="device">
          <option value="">Select a Vestaboard…</option>
          ${deviceOptions}
        </select>
      </div>
      <div class="card">
        <h2 style="margin:0 0 12px;font-size:1.1rem;">Saved templates</h2>
        <div class="template-grid">
          <div>
            <label for="template-select">Load template</label>
            <select id="template-select">${templateOptions}</select>
          </div>
          <div>
            <label for="template-name">Template name</label>
            <input id="template-name" type="text" value="${this._escapeHtml(
              this._templateName || ""
            )}" placeholder="e.g. Godzilla" />
          </div>
        </div>
        <div class="actions">
          <button type="button" id="save-template">Save</button>
          <button class="secondary" type="button" id="save-template-as">Save as new</button>
          <button class="secondary" type="button" id="new-template">New draft</button>
          <button class="danger" type="button" id="delete-template">Delete</button>
          <button type="button" id="copy-automation">Copy for automation</button>
        </div>
        <p class="hint" style="margin-top:10px;">
          Preferred: Automations → <code>vestaboard.send_template</code> and pick a template from the dropdown
          (no paste). <strong>Location Announcement</strong> is the rainbow
          <code>NOW DISPLAYING HIGH SCORES FOR</code> board. Duplicate a game with
          <strong>Save as new</strong>, then swap entities and title text.
        </p>
      </div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <h2 style="margin:0;font-size:1.1rem;">Props</h2>
          <button type="button" id="add-prop">Add prop</button>
        </div>
        ${propRows}
      </div>
      <div class="card">
        <div class="actions">
          <button type="button" id="open-vbml">Open VBML editor</button>
          <button type="button" id="send">Send to board</button>
        </div>
        <div class="status-line">${this._escapeHtml(this._sendStatus || "")}</div>
      </div>
      ${modal}
    `;

    this._bindMainEvents();
    if (this._modalOpen) {
      this._bindModalEvents();
      this._paintEditor();
      this._paintStatus();
    }
  }
}

customElements.define("vestaboard-x-panel", VestaboardXPanel);
