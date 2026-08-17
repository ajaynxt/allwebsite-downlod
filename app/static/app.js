"use strict";

const elements = {
  form: document.querySelector("#link-form"),
  url: document.querySelector("#media-url"),
  analyze: document.querySelector("#analyze-button"),
  formError: document.querySelector("#form-error"),
  result: document.querySelector("#result"),
  thumbnail: document.querySelector("#media-thumbnail"),
  thumbnailFallback: document.querySelector("#thumbnail-fallback"),
  source: document.querySelector("#source-badge"),
  duration: document.querySelector("#duration-badge"),
  title: document.querySelector("#result-title"),
  creator: document.querySelector("#media-creator"),
  videoTab: document.querySelector("#video-tab"),
  audioTab: document.querySelector("#audio-tab"),
  formats: document.querySelector("#format-options"),
  rights: document.querySelector("#rights-confirmed"),
  download: document.querySelector("#download-button"),
  downloadError: document.querySelector("#download-error"),
  jobSection: document.querySelector("#job-section"),
  jobMessage: document.querySelector("#job-message"),
  jobPercent: document.querySelector("#job-percent"),
  jobProgress: document.querySelector("#job-progress"),
  ready: document.querySelector("#ready-button"),
};

const state = {
  info: null,
  kind: "video",
  selected: null,
  pollToken: 0,
};

function showError(element, message) {
  element.textContent = message;
  element.hidden = !message;
}

function setAnalyzeBusy(busy) {
  elements.analyze.disabled = busy;
  elements.analyze.querySelector("span").textContent = busy ? "Reading link…" : "Read link";
}

function normalizeUrl(raw) {
  const value = raw.trim();
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("Complete http/https link paste karein.");
  }
  if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password) {
    throw new Error("Valid public http/https link paste karein.");
  }
  return parsed.toString();
}

async function requestJson(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      signal: controller.signal,
    });
    let data = {};
    try {
      data = await response.json();
    } catch {
      data = {};
    }
    if (!response.ok) {
      throw new Error(data.detail || "Request complete nahi hua. Dobara try karein.");
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Server response timed out. Dobara try karein.");
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

function formatDuration(totalSeconds) {
  if (!Number.isFinite(totalSeconds)) return "";
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remaining = seconds % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`
    : `${minutes}:${String(remaining).padStart(2, "0")}`;
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return ` · ~${value >= 10 ? value.toFixed(0) : value.toFixed(1)} ${units[index]}`;
}

function setThumbnail(url, title) {
  elements.thumbnail.hidden = true;
  elements.thumbnailFallback.hidden = false;
  elements.thumbnail.removeAttribute("src");
  elements.thumbnail.alt = title ? `Thumbnail for ${title}` : "Media thumbnail";
  if (!url) return;
  elements.thumbnail.addEventListener(
    "load",
    () => {
      elements.thumbnail.hidden = false;
      elements.thumbnailFallback.hidden = true;
    },
    { once: true }
  );
  elements.thumbnail.addEventListener(
    "error",
    () => {
      elements.thumbnail.hidden = true;
      elements.thumbnailFallback.hidden = false;
    },
    { once: true }
  );
  elements.thumbnail.src = url;
}

function chooseOption(option) {
  state.selected = option;
  for (const button of elements.formats.querySelectorAll(".format-option")) {
    const selected = Number(button.dataset.optionIndex) === option._index;
    button.setAttribute("aria-checked", String(selected));
  }
}

function renderFormats() {
  elements.formats.replaceChildren();
  const available = state.info.formats
    .map((option, index) => ({ ...option, _index: index }))
    .filter((option) => option.kind === state.kind);

  if (!available.length) {
    const empty = document.createElement("p");
    empty.textContent = "Is output type ke formats available nahi hain.";
    elements.formats.append(empty);
    state.selected = null;
    return;
  }

  state.selected = available[0];
  for (const option of available) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "format-option";
    button.dataset.optionIndex = String(option._index);
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(option._index === state.selected._index));

    const copy = document.createElement("span");
    const label = document.createElement("strong");
    label.textContent = option.label;
    const detail = document.createElement("small");
    detail.textContent = `${option.detail}${formatBytes(option.estimated_bytes)}`;
    copy.append(label, detail);

    const check = document.createElement("span");
    check.className = "option-check";
    check.setAttribute("aria-hidden", "true");
    button.append(copy, check);
    button.addEventListener("click", () => chooseOption(option));
    elements.formats.append(button);
  }
}

function selectKind(kind) {
  state.kind = kind;
  elements.videoTab.setAttribute("aria-selected", String(kind === "video"));
  elements.audioTab.setAttribute("aria-selected", String(kind === "audio"));
  renderFormats();
}

function renderMedia(info) {
  state.info = info;
  elements.source.textContent = info.platform || "Website";
  elements.title.textContent = info.title;
  elements.creator.textContent = info.creator || "Public media";
  const duration = formatDuration(info.duration_seconds);
  elements.duration.textContent = duration;
  elements.duration.hidden = !duration;
  setThumbnail(info.thumbnail, info.title);
  elements.rights.checked = false;
  elements.ready.hidden = true;
  elements.jobSection.hidden = true;
  showError(elements.downloadError, "");
  selectKind("video");
  elements.result.hidden = false;
  elements.result.scrollIntoView({ behavior: "smooth", block: "start" });
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError(elements.formError, "");
  state.pollToken += 1;
  try {
    const url = normalizeUrl(elements.url.value);
    setAnalyzeBusy(true);
    const info = await requestJson(
      "/api/analyze",
      { method: "POST", body: JSON.stringify({ url }) },
      95000
    );
    renderMedia(info);
  } catch (error) {
    showError(elements.formError, error.message || "Link read nahi ho saka.");
    elements.url.focus();
  } finally {
    setAnalyzeBusy(false);
  }
});

elements.videoTab.addEventListener("click", () => selectKind("video"));
elements.audioTab.addEventListener("click", () => selectKind("audio"));

function updateJob(status) {
  const progress = Math.max(0, Math.min(100, Number(status.progress) || 0));
  elements.jobMessage.textContent = status.message;
  elements.jobPercent.textContent = `${progress}%`;
  elements.jobProgress.value = progress;
  elements.jobProgress.textContent = `${progress}%`;
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function pollJob(statusUrl, token) {
  for (let attempt = 0; attempt < 1800; attempt += 1) {
    if (token !== state.pollToken) return;
    const status = await requestJson(statusUrl, { method: "GET", headers: {} }, 20000);
    updateJob(status);
    if (status.status === "ready") {
      elements.ready.href = status.file_url;
      elements.ready.setAttribute("download", status.filename || "media");
      elements.ready.hidden = false;
      elements.download.disabled = false;
      elements.download.querySelector("span").textContent = "Download another";
      return;
    }
    if (status.status === "failed") {
      throw new Error(status.message || "Download complete nahi hua.");
    }
    await wait(attempt < 30 ? 1000 : 2500);
  }
  throw new Error("Download session timed out. Please try again.");
}

elements.download.addEventListener("click", async () => {
  showError(elements.downloadError, "");
  if (!state.info || !state.selected) {
    showError(elements.downloadError, "Pehle link read karke quality select karein.");
    return;
  }
  if (!elements.rights.checked) {
    showError(elements.downloadError, "Content ownership/permission checkbox confirm karein.");
    elements.rights.focus();
    return;
  }

  const token = state.pollToken + 1;
  state.pollToken = token;
  elements.download.disabled = true;
  elements.download.querySelector("span").textContent = "Starting…";
  elements.ready.hidden = true;
  updateJob({ progress: 0, message: "Queue mein add ho raha hai" });
  elements.jobSection.hidden = false;
  elements.jobSection.scrollIntoView({ behavior: "smooth", block: "center" });

  try {
    const mode = state.selected.kind === "video" ? "video" : state.selected.extension;
    const created = await requestJson(
      "/api/download",
      {
        method: "POST",
        body: JSON.stringify({
          url: state.info.webpage_url,
          mode,
          format_id: state.selected.id,
          rights_confirmed: true,
        }),
      },
      30000
    );
    await pollJob(created.status_url, token);
  } catch (error) {
    showError(elements.downloadError, error.message || "Download complete nahi hua.");
    elements.jobMessage.textContent = "Download failed";
    elements.jobPercent.textContent = "—";
    elements.download.disabled = false;
    elements.download.querySelector("span").textContent = "Try download again";
  }
});
