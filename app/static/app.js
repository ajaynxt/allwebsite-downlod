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
  serviceQuery: document.querySelector("#service-query"),
  serviceSuggestions: document.querySelector("#service-suggestions"),
  serviceSelected: document.querySelector("#service-selected"),
};

const state = {
  info: null,
  kind: "video",
  selected: null,
  downloadToken: 0,
};

const apiBaseUrl = (document.querySelector('meta[name="api-base-url"]')?.content || "")
  .trim()
  .replace(/\/$/, "");

function resolveApiUrl(url) {
  if (!url || /^https?:\/\//i.test(url) || !apiBaseUrl) return url;
  return url.startsWith("/") ? `${apiBaseUrl}${url}` : `${apiBaseUrl}/${url}`;
}

function track(eventName, parameters = {}) {
  window.dispatchEvent(new CustomEvent("atoz:analytics", { detail: { eventName, parameters } }));
  if (typeof window.gtag === "function") window.gtag("event", eventName, parameters);
}

const platformServices = [
  { key: "instagram", label: "Instagram Reel Downloader", type: "Reel or post", aliases: ["insta reel download", "instagram reels", "instgram reel", "insta video", "ig reel", "reel download"], placeholder: "https://www.instagram.com/reel/…" },
  { key: "pinterest", label: "Pinterest Video Downloader", type: "Video Pin", aliases: ["pinterest download", "pintrest download", "pininterest video", "pinterst", "pin video", "pinterest pin"], placeholder: "https://www.pinterest.com/pin/…" },
  { key: "youtube", label: "YouTube Video Downloader", type: "Video or audio", aliases: ["youtube download", "youtub download", "yt download", "yt video", "youtube video", "youtube shorts", "yt shorts"], placeholder: "https://www.youtube.com/watch?v=…" },
  { key: "youtube-audio", label: "YouTube Audio Downloader", type: "MP3 or M4A", aliases: ["yt audio", "youtube audio", "youtube mp3", "yt mp3", "youtub song"], placeholder: "Paste a permitted YouTube video link" },
  { key: "facebook", label: "Facebook Video Downloader", type: "Video or Reel", aliases: ["facebook download", "facebok video", "fb video", "fb reel", "facebook reels"], placeholder: "https://www.facebook.com/reel/…" },
  { key: "tiktok", label: "TikTok Video Downloader", type: "Public video", aliases: ["tiktok download", "tik tok video", "tictok", "ticktok video", "tt video"], placeholder: "https://www.tiktok.com/@user/video/…" },
  { key: "twitter", label: "X / Twitter Video Downloader", type: "Post video", aliases: ["twitter video", "x video download", "tweeter video", "tweet download", "twitter download"], placeholder: "https://x.com/user/status/…" },
  { key: "reddit", label: "Reddit Video Downloader", type: "Post video", aliases: ["reddit download", "redit video", "reddit mp4", "reddit post video"], placeholder: "https://www.reddit.com/r/…" },
  { key: "vimeo", label: "Vimeo Video Downloader", type: "Public video", aliases: ["vimeo download", "vimo video", "vimeo video"], placeholder: "https://vimeo.com/…" },
  { key: "soundcloud", label: "SoundCloud Audio Downloader", type: "Public audio", aliases: ["soundcloud download", "sound cloud audio", "soundclod song", "sc audio"], placeholder: "https://soundcloud.com/…" },
  { key: "linkedin", label: "LinkedIn Video Downloader", type: "Public post", aliases: ["linkedin video", "linked in download", "linkdin video", "linkedin post"], placeholder: "Paste a public LinkedIn post link" },
  { key: "snapchat", label: "Snapchat Spotlight Downloader", type: "Spotlight", aliases: ["snapchat video", "snap spotlite", "snapchat spotlight", "snap download"], placeholder: "Paste a public Snapchat Spotlight link" },
  { key: "dailymotion", label: "Dailymotion Video Downloader", type: "Public video", aliases: ["dailymotion download", "daily motion video", "dalymotion"], placeholder: "https://www.dailymotion.com/video/…" },
  { key: "twitch", label: "Twitch Clip Downloader", type: "Public clip", aliases: ["twitch clip", "twicht download", "twitch video clip"], placeholder: "Paste a public Twitch clip link" },
  { key: "bandcamp", label: "Bandcamp Audio Downloader", type: "Public audio", aliases: ["bandcamp download", "band camp song", "bandcamp audio"], placeholder: "https://artist.bandcamp.com/track/…" },
  { key: "generic", label: "Public Website Media Downloader", type: "Direct or embedded media", aliases: ["website video", "site download", "web media", "all social media", "any link downloader", "social media download"], placeholder: "Paste a public media page or direct file link" },
];

function normalizeKeyword(value) {
  return value.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, " ").trim();
}

function editDistance(left, right) {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let row = 1; row <= left.length; row += 1) {
    let diagonal = previous[0];
    previous[0] = row;
    for (let column = 1; column <= right.length; column += 1) {
      const above = previous[column];
      previous[column] = Math.min(
        previous[column] + 1,
        previous[column - 1] + 1,
        diagonal + (left[row - 1] === right[column - 1] ? 0 : 1)
      );
      diagonal = above;
    }
  }
  return previous[right.length];
}

function serviceScore(query, service) {
  const candidates = [service.label, ...service.aliases].map(normalizeKeyword);
  return Math.min(...candidates.map((candidate) => {
    if (candidate === query) return 0;
    if (candidate.includes(query)) return 0.04 + candidate.indexOf(query) / 100;
    if (query.includes(candidate)) return 0.08;
    return editDistance(query, candidate) / Math.max(query.length, candidate.length, 1);
  }));
}

function matchingServices(rawQuery) {
  const query = normalizeKeyword(rawQuery);
  if (!query) return [];
  return platformServices
    .map((service) => ({ service, score: serviceScore(query, service) }))
    .filter(({ score }) => score <= (query.length < 4 ? 0.34 : 0.5))
    .sort((left, right) => left.score - right.score || left.service.label.localeCompare(right.service.label))
    .slice(0, 6);
}

function selectService(service) {
  elements.serviceQuery.value = service.label;
  elements.serviceQuery.setAttribute("aria-expanded", "false");
  elements.serviceSuggestions.hidden = true;
  elements.serviceSelected.textContent = `${service.label} selected — ab neeche apna permitted ${service.type.toLowerCase()} link paste karein.`;
  elements.serviceSelected.hidden = false;
  elements.url.placeholder = service.placeholder;
  elements.url.focus();
  track("platform_suggestion_selected", { platform: service.key });
}

function renderServiceSuggestions(rawQuery) {
  const matches = matchingServices(rawQuery);
  elements.serviceSuggestions.replaceChildren();
  if (!rawQuery.trim()) {
    elements.serviceSuggestions.hidden = true;
    elements.serviceQuery.setAttribute("aria-expanded", "false");
    return;
  }
  if (!matches.length) {
    const message = document.createElement("p");
    message.className = "service-empty";
    message.textContent = "Nearest match nahi mila. Public media link seedha neeche paste kar sakte hain.";
    elements.serviceSuggestions.append(message);
  } else {
    for (const { service, score } of matches) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "service-suggestion";
      button.setAttribute("role", "option");
      const copy = document.createElement("span");
      const title = document.createElement("strong");
      title.textContent = service.label;
      const detail = document.createElement("small");
      detail.textContent = service.type;
      copy.append(title, detail);
      const match = document.createElement("mark");
      match.textContent = score < 0.01 ? "EXACT" : score < 0.18 ? "BEST MATCH" : "SUGGESTED";
      button.append(copy, match);
      button.addEventListener("click", () => selectService(service));
      elements.serviceSuggestions.append(button);
    }
  }
  elements.serviceSuggestions.hidden = false;
  elements.serviceQuery.setAttribute("aria-expanded", "true");
}

elements.serviceQuery.addEventListener("input", () => renderServiceSuggestions(elements.serviceQuery.value));
elements.serviceQuery.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    const first = matchingServices(elements.serviceQuery.value)[0];
    if (first) {
      event.preventDefault();
      selectService(first.service);
    }
  }
  if (event.key === "Escape") {
    elements.serviceSuggestions.hidden = true;
    elements.serviceQuery.setAttribute("aria-expanded", "false");
  }
});

for (const button of document.querySelectorAll("[data-service-key]")) {
  button.addEventListener("click", () => {
    const service = platformServices.find((item) => item.key === button.dataset.serviceKey);
    if (service) selectService(service);
  });
}

document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".service-finder")) {
    elements.serviceSuggestions.hidden = true;
    elements.serviceQuery.setAttribute("aria-expanded", "false");
  }
});

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
    const response = await fetch(resolveApiUrl(url), {
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
  elements.jobSection.hidden = true;
  showError(elements.downloadError, "");
  selectKind("video");
  elements.result.hidden = false;
  elements.result.scrollIntoView({ behavior: "smooth", block: "start" });
  track("link_analyzed", { platform: info.platform || "unknown" });
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError(elements.formError, "");
  state.downloadToken += 1;
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

function updateDownloadStatus(message, progress = null) {
  elements.jobMessage.textContent = message;
  if (Number.isFinite(progress)) {
    const safeProgress = Math.max(0, Math.min(100, progress));
    elements.jobPercent.textContent = `${Math.round(safeProgress)}%`;
    elements.jobProgress.value = safeProgress;
    elements.jobProgress.textContent = `${Math.round(safeProgress)}%`;
    return;
  }
  elements.jobPercent.textContent = "DIRECT";
  elements.jobProgress.removeAttribute("value");
  elements.jobProgress.textContent = "Preparing direct download";
}

function responseFilename(response, fallback) {
  const disposition = response.headers.get("Content-Disposition") || "";
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  if (encoded) {
    try {
      return decodeURIComponent(encoded);
    } catch {
      return fallback;
    }
  }
  return disposition.match(/filename="?([^";]+)"?/i)?.[1] || fallback;
}

async function receiveDirectDownload(payload, token) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 1_800_000);
  try {
    const response = await fetch(resolveApiUrl("/api/download"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) {
      let data = {};
      try {
        data = await response.json();
      } catch {
        data = {};
      }
      throw new Error(data.detail || "Download complete nahi hua.");
    }

    const total = Number(response.headers.get("Content-Length")) || 0;
    const reader = response.body?.getReader();
    const chunks = [];
    let received = 0;
    if (reader) {
      while (true) {
        if (token !== state.downloadToken) {
          await reader.cancel();
          throw new Error("Download cancelled because a new link was opened.");
        }
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        received += value.byteLength;
        const progress = total ? (received / total) * 100 : null;
        updateDownloadStatus("File seedha aapke device par aa rahi hai", progress);
      }
    } else {
      chunks.push(new Uint8Array(await response.arrayBuffer()));
    }

    const fallback = `ajaynxt-download.${payload.mode === "video" ? "mp4" : payload.mode}`;
    const filename = responseFilename(response, fallback);
    const blob = new Blob(chunks, { type: response.headers.get("Content-Type") || "application/octet-stream" });
    const blobUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = filename;
    anchor.hidden = true;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Direct download timed out. Chhoti file ya lower quality try karein.");
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
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

  const token = state.downloadToken + 1;
  state.downloadToken = token;
  elements.download.disabled = true;
  elements.download.querySelector("span").textContent = "Preparing…";
  updateDownloadStatus("Temporary processing start ho rahi hai");
  elements.jobSection.hidden = false;
  elements.jobSection.scrollIntoView({ behavior: "smooth", block: "center" });

  try {
    const mode = state.selected.kind === "video" ? "video" : state.selected.extension;
    await receiveDirectDownload({
      url: state.info.webpage_url,
      mode,
      format_id: state.selected.id,
      rights_confirmed: true,
    }, token);
    updateDownloadStatus("Browser download start ho gaya — server copy delete ho gayi", 100);
    elements.download.disabled = false;
    elements.download.querySelector("span").textContent = "Download another";
    track("direct_download_sent", { platform: state.info?.platform || "unknown", mode });
  } catch (error) {
    showError(elements.downloadError, error.message || "Download complete nahi hua.");
    elements.jobMessage.textContent = "Download failed";
    elements.jobPercent.textContent = "—";
    elements.download.disabled = false;
    elements.download.querySelector("span").textContent = "Try download again";
  }
});

for (const button of document.querySelectorAll("[data-copy-upi]")) {
  button.addEventListener("click", async () => {
    const upiId = button.dataset.copyUpi || "";
    try {
      await navigator.clipboard.writeText(upiId);
      const label = button.querySelector("small");
      if (label) label.textContent = "Copied";
      track("upi_id_copied");
    } catch {
      window.prompt("Copy UPI ID", upiId);
    }
  });
}
