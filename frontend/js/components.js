/* Reusable Vanilla JS UI Components & Modals for OpenUPSC */
window.UI = (function () {
  function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function safeUrl(url) {
    const trimmed = String(url || '').trim();
    if (/^https?:\/\//i.test(trimmed)) return trimmed;
    return '#';
  }

  function extractPlaylistId(url) {
    const m = String(url || '').match(/[?&]list=([A-Za-z0-9_-]+)/);
    return m ? m[1] : null;
  }

  function formatMinutes(totalMins) {
    const m = Math.max(0, Math.round(totalMins || 0));
    const hrs = Math.floor(m / 60);
    const rem = m % 60;
    if (hrs === 0) return `${rem}m`;
    return `${hrs}h ${rem}m`;
  }

  function timeGreeting() {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  }

  function plural(n, singular, pluralWord) {
    return `${n} ${n === 1 ? singular : pluralWord}`;
  }

  function toast(message, type = 'default') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 200);
    }, 2800);
  }

  function seniorBox(advice, title = 'Senior Tip') {
    return `
      <div class="senior-box">
        <strong class="font-mono text-xs" style="text-transform:uppercase;letter-spacing:0.06em">${esc(title)}:</strong>
        <span style="margin-left:4px">“${esc(advice)}”</span>
      </div>
    `;
  }

  function resourceCard(res) {
    const pct = Number(AppState.progressMap[res.id] || 0);
    const isBookmarked = AppState.bookmarkedIds.includes(res.id);
    const isDone = pct === 100;
    const href = safeUrl(res.url);
    const playlistId = res.youtubePlaylistId || extractPlaylistId(res.url);
    const isVideo = res.type === 'YouTube' || !!playlistId;

    const progressSteps = [0, 25, 50, 75, 100];
    if (!progressSteps.includes(pct)) progressSteps.push(pct);
    progressSteps.sort((a, b) => a - b);

    const typeBadge =
      isVideo
        ? `<span class="badge badge-rose">▶ Video Playlist</span>`
        : res.type === 'PYQ'
        ? `<span class="badge badge-blue">Exam Papers</span>`
        : res.type === 'PDF'
        ? `<span class="badge badge-emerald">Official PDF</span>`
        : `<span class="badge badge-neutral">${esc(res.type || 'Guide')}</span>`;

    return `
      <article class="card resource-card card-interactive ${isDone ? 'card-completed' : ''}" data-resource-card="${esc(res.id)}">
        <div class="flex-col gap-2">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-1 flex-wrap">
              ${typeBadge}
              <span class="badge badge-outline">${esc(res.subject)}</span>
            </div>
            <button type="button" class="btn-icon" data-action="toggle-bookmark" data-id="${esc(res.id)}" title="${
              isBookmarked ? 'Remove from Saved' : 'Save Resource'
            }">
              ${isBookmarked ? Icons('bookmarkFill', 15) : Icons('bookmark', 15)}
            </button>
          </div>

          <div>
            <h3 class="resource-title">${esc(res.title)}</h3>
            <p class="resource-meta">
              ${esc(res.provider)} · ${esc(res.language || 'English')} ${res.estimatedHours > 0 ? `· ~${res.estimatedHours}h` : ''}
            </p>
          </div>

          <p class="resource-desc">${esc(res.description)}</p>
          ${res.seniorTip ? `<div class="resource-tip">${esc(res.seniorTip)}</div>` : ''}
        </div>

        <div class="resource-footer">
          <div class="flex items-center justify-between gap-2">
            <select class="progress-select ${isDone ? 'done' : ''}" data-action="update-progress" data-id="${esc(res.id)}" aria-label="Progress">
              ${progressSteps
                .map((v) => `<option value="${v}" ${pct === v ? 'selected' : ''}>${v === 100 ? '✓ Done' : v + '% Done'}</option>`)
                .join('')}
            </select>
            <div class="flex items-center gap-1">
              <button type="button" class="btn btn-ghost btn-sm"
                data-action="open-notes"
                data-id="${esc(res.id)}"
                data-title="${esc(res.title)}"
                data-category="${esc(res.subject)}">
                ${Icons('edit', 13)} <span>Note</span>
              </button>
              <a href="/study?subject=${encodeURIComponent(res.subject)}&topic=${encodeURIComponent(res.title)}&duration=50" data-link class="btn btn-ghost btn-sm" title="Start Focus Timer">
                ${Icons('clock', 13)}
              </a>
            </div>
          </div>

          <div class="flex items-center gap-2">
            ${
              playlistId
                ? `<button type="button" class="btn btn-video btn-sm w-full"
                     data-action="watch-video"
                     data-playlist="${esc(playlistId)}"
                     data-url="${esc(href)}"
                     data-title="${esc(res.title)}"
                     data-provider="${esc(res.provider)}"
                     data-id="${esc(res.id)}"
                     data-subject="${esc(res.subject)}">
                     ${Icons('play', 12)} <span>Watch Here</span>
                   </button>
                   <a href="${esc(href)}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm" title="Open on YouTube">
                     ${Icons('arrowUpRight', 13)}
                   </a>`
                : `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm w-full">
                     <span>${res.type === 'PDF' ? 'Open Official PDF' : res.type === 'PYQ' ? 'Open Exam Papers' : 'Open Resource'}</span>
                     ${Icons('arrowUpRight', 13)}
                   </a>`
            }
          </div>
        </div>
      </article>
    `;
  }

  function openVideoModal({ playlistId, url, title, provider, itemId, subject }) {
    const modal = document.getElementById('video-modal');
    const safeHref = safeUrl(url);
    const embedSrc = `https://www.youtube.com/embed/videoseries?list=${encodeURIComponent(playlistId)}&rel=0`;
    const pct = itemId ? Number(AppState.progressMap[itemId] || 0) : 0;

    modal.innerHTML = `
      <div class="modal-card video-lg">
        <div class="modal-header">
          <div style="min-width:0">
            <span class="eyebrow">${esc(provider || 'YouTube')} · ${esc(subject || 'UPSC Lecture')}</span>
            <h3 class="mt-1" style="font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(title)}</h3>
          </div>
          <button type="button" class="btn-icon" data-close-modal="video-modal" aria-label="Close Video">${Icons('x', 18)}</button>
        </div>
        <div class="modal-body">
          <div class="video-frame-wrap">
            <iframe src="${embedSrc}" title="${esc(title)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
          </div>
          <p class="text-xs text-muted">Tip: Click the playlist icon in the top-right corner of the player to browse all lectures in this series, or switch speed to 1.25x–1.5x.</p>
        </div>
        <div class="modal-footer">
          <div class="flex items-center gap-2 flex-wrap">
            ${
              itemId
                ? `<select class="progress-select ${pct === 100 ? 'done' : ''}" data-action="update-progress" data-id="${esc(itemId)}">
                     ${[0, 25, 50, 75, 100].map((v) => `<option value="${v}" ${pct === v ? 'selected' : ''}>${v === 100 ? '✓ Completed' : v + '% Done'}</option>`).join('')}
                   </select>
                   <button type="button" class="btn btn-secondary btn-sm"
                     data-action="open-notes"
                     data-id="${esc(itemId)}"
                     data-title="${esc(title)}"
                     data-category="${esc(subject || 'Video Note')}">
                     ${Icons('edit', 13)} <span>Take Notes</span>
                   </button>`
                : ''
            }
          </div>
          <div class="flex items-center gap-2">
            <a href="${esc(safeHref)}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">
              <span>Open on YouTube</span> ${Icons('arrowUpRight', 13)}
            </a>
            <button type="button" class="btn btn-primary btn-sm" data-close-modal="video-modal">Done</button>
          </div>
        </div>
      </div>
    `;
    modal.classList.remove('hidden');
  }

  function openNotesModal(itemId, itemTitle, itemCategory = 'UPSC Note') {
    const modal = document.getElementById('notes-modal');
    const existing = AppState.notes[itemId] || '';

    modal.innerHTML = `
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <span class="eyebrow">${esc(itemCategory)} · PERSONAL NOTE</span>
            <h3 class="mt-1" style="font-size:16px">${esc(itemTitle)}</h3>
          </div>
          <button type="button" class="btn-icon" data-close-modal="notes-modal">${Icons('x', 18)}</button>
        </div>
        <div class="modal-body">
          <textarea id="notes-textarea" class="textarea" rows="9" placeholder="Write crisp UPSC key points, articles, committees, dates, or revision notes...">${esc(existing)}</textarea>
          <p class="text-xs text-muted">Saved to SQLite and accessible inside Streamlit Studio → Notes Explorer.</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary btn-pill" data-close-modal="notes-modal">Cancel</button>
          <button type="button" class="btn btn-primary btn-pill" id="save-note-btn">Save Note</button>
        </div>
      </div>
    `;
    modal.classList.remove('hidden');

    const textarea = document.getElementById('notes-textarea');
    textarea.focus();

    document.getElementById('save-note-btn').onclick = async () => {
      try {
        await API.saveNote(itemId, textarea.value, itemTitle, itemCategory);
        toast('Note saved.', 'success');
        closeModal('notes-modal');
      } catch (err) {
        toast(err.message, 'error');
      }
    };
  }

  let searchSeq = 0;

  function openSearchModal(initialQuery = '') {
    const modal = document.getElementById('search-modal');
    modal.innerHTML = `
      <div class="modal-card">
        <div class="modal-header">
          <div class="search-box w-full">
            <span class="search-icon">${Icons('search', 16)}</span>
            <input type="text" id="global-search-input" class="input" value="${esc(initialQuery)}" placeholder="Search any UPSC subject, video playlist, NCERT chapter, or PYQ..." autocomplete="off" />
          </div>
          <button type="button" class="btn-icon" data-close-modal="search-modal">${Icons('x', 18)}</button>
        </div>
        <div class="modal-body" id="global-search-results">
          <p class="text-xs text-muted">Try <strong>Laxmikanth</strong>, <strong>Mrunal</strong>, <strong>CSAT</strong>, <strong>Harappa</strong>, <strong>Article 21</strong>, or <strong>Papers</strong>.</p>
        </div>
      </div>
    `;
    modal.classList.remove('hidden');

    const input = document.getElementById('global-search-input');
    const resultsEl = document.getElementById('global-search-results');
    input.focus();

    let debounceTimer = null;
    async function runSearch(q) {
      const seq = ++searchSeq;
      if (!q) {
        resultsEl.innerHTML = '<p class="text-xs text-muted">Type any UPSC topic, educator, NCERT class, or question paper...</p>';
        return;
      }
      try {
        const data = await API.search(q);
        if (seq !== searchSeq) return; // Discard stale out-of-order response
        if (!data.results.length) {
          resultsEl.innerHTML = `<p class="text-xs text-muted">No matches found for “${esc(q)}”.</p>`;
          return;
        }
        resultsEl.innerHTML = data.results
          .map(
            (r) => `
            <a href="${esc(r.href)}" data-link class="search-result-item" data-close-modal="search-modal">
              <div>
                <span class="badge badge-neutral">${esc(r.kind)}</span>
                <div class="font-bold text-sm mt-1">${esc(r.title)}</div>
                <div class="text-xs text-muted">${esc(r.subtitle)}</div>
              </div>
              ${Icons('chevronRight', 15)}
            </a>`
          )
          .join('');
      } catch (err) {
        if (seq === searchSeq) {
          resultsEl.innerHTML = `<p class="text-xs text-muted">Search error: ${esc(err.message)}</p>`;
        }
      }
    }

    input.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => runSearch(input.value.trim()), 160);
    });

    if (initialQuery) runSearch(initialQuery.trim());
  }

  function openCustomModal(html) {
    const modal = document.getElementById('custom-modal');
    modal.innerHTML = `<div class="modal-card">${html}</div>`;
    modal.classList.remove('hidden');
    return modal;
  }

  function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.add('hidden');
    // Immediately stop video playback when closing video modal
    if (id === 'video-modal') {
      el.innerHTML = '';
    }
  }

  return {
    esc,
    safeUrl,
    extractPlaylistId,
    formatMinutes,
    timeGreeting,
    plural,
    toast,
    seniorBox,
    resourceCard,
    openVideoModal,
    openNotesModal,
    openSearchModal,
    openCustomModal,
    closeModal,
  };
})();
