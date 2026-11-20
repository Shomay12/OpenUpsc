/* OpenUPSC Singleton Wall-Clock Timer Engine, Simple Shell & History Router */

// =========================================================================
// GLOBAL SINGLETON TIMER CONTROLLER (Zero background drift, never clobbers pages)
// =========================================================================
window.TimerController = (function () {
  let endTimeMs = null;

  function formatClock(secs) {
    const safe = Math.max(0, Math.floor(secs || 0));
    const m = Math.floor(safe / 60);
    const s = safe % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function syncDom() {
    const t = AppState.timer;
    const text = formatClock(t.secondsLeft);

    const clock = document.getElementById('timer-clock');
    if (clock) clock.textContent = text;

    const bar = document.getElementById('timer-bar');
    if (bar) {
      const total = t.targetMinutes * 60;
      bar.style.width = `${total > 0 ? Math.min(100, ((total - t.secondsLeft) / total) * 100) : 0}%`;
    }

    const headerPill = document.getElementById('header-live-timer');
    if (headerPill) {
      if (t.isRunning && window.location.pathname !== '/study') {
        headerPill.classList.remove('hidden');
        headerPill.textContent = `⏱ ${text} · ${t.subject}`;
      } else {
        headerPill.classList.add('hidden');
      }
    }
  }

  function pause() {
    const t = AppState.timer;
    if (t.intervalId) {
      clearInterval(t.intervalId);
      t.intervalId = null;
    }
    if (t.isRunning && endTimeMs) {
      t.secondsLeft = Math.max(0, Math.ceil((endTimeMs - Date.now()) / 1000));
    }
    endTimeMs = null;
    t.isRunning = false;
    syncDom();
  }

  function start() {
    const t = AppState.timer;
    if (t.isRunning) return;
    if (t.secondsLeft <= 0) t.secondsLeft = t.targetMinutes * 60;
    if (!t.startedAt) t.startedAt = new Date().toISOString();

    t.isRunning = true;
    endTimeMs = Date.now() + t.secondsLeft * 1000;

    t.intervalId = setInterval(async () => {
      const remaining = Math.max(0, Math.ceil((endTimeMs - Date.now()) / 1000));
      t.secondsLeft = remaining;
      syncDom();

      if (remaining <= 0) {
        pause();
        try {
          await complete(t.targetMinutes);
        } catch (err) {
          UI.toast(`Could not save session: ${err.message}`, 'error');
          if (window.location.pathname === '/study') window.Router.renderCurrentRoute();
        }
      }
    }, 500);

    syncDom();
  }

  function toggle() {
    if (AppState.timer.isRunning) pause();
    else start();
  }

  function reset() {
    pause();
    const t = AppState.timer;
    t.secondsLeft = t.targetMinutes * 60;
    t.startedAt = null;
    syncDom();
  }

  function setPreset(minutes, mode) {
    pause();
    const t = AppState.timer;
    t.targetMinutes = minutes;
    t.mode = mode;
    t.secondsLeft = minutes * 60;
    t.startedAt = null;
    syncDom();
  }

  async function complete(minutesToLog) {
    pause();
    const t = AppState.timer;
    const mins = Math.max(1, Math.round(minutesToLog || t.targetMinutes));

    await API.addStudySession({
      subject: t.subject,
      topic: t.topic || 'Focused Study Session',
      resource_id: t.resourceId || null,
      start_time: t.startedAt || null,
      duration_minutes: mins,
      session_type: t.mode,
      completed: true,
    });

    t.startedAt = null;
    t.secondsLeft = t.targetMinutes * 60;
    syncDom();

    UI.toast(`Logged ${mins}m ${t.mode} on ${t.subject}! Synced to Analytics.`, 'success');

    // Only refresh view if user is currently on /study or / (never overwrite /ncert or /pyqs!)
    if (window.location.pathname === '/study' || window.location.pathname === '/') {
      window.Router.renderCurrentRoute();
    }
  }

  return { formatClock, syncDom, start, pause, toggle, reset, setPreset, complete };
})();

// =========================================================================
// SIMPLE SHELL & HISTORY ROUTER
// =========================================================================
window.Router = (function () {
  const { esc, toast } = UI;
  let navSeq = 0;

  const NAV_LINKS = [
    { href: '/', label: 'Home', icon: 'dashboard', exact: true },
    { href: '/resources', label: 'Videos & Material', icon: 'video' },
    { href: '/ncert', label: 'NCERT (Class 6–12)', icon: 'layers' },
    { href: '/pyqs', label: 'Papers & PYQs', icon: 'fileText' },
    { href: '/roadmaps', label: 'Roadmaps', icon: 'map' },
    { href: '/study', label: 'Study & Timer', icon: 'clock' },
  ];

  function getTitle(pathname) {
    if (pathname === '/' || pathname === '/dashboard') return 'Home';
    if (pathname.startsWith('/resources') || pathname === '/saved' || pathname === '/current-affairs') return 'Videos & Material';
    if (pathname.startsWith('/ncert')) return 'NCERT (Class 6–12)';
    if (pathname.startsWith('/pyqs')) return 'Question Papers & PYQs';
    if (pathname.startsWith('/roadmaps')) return 'Subject Roadmaps';
    if (pathname.startsWith('/study')) return 'Study & Timer';
    if (pathname === '/profile' || pathname === '/settings') return 'Account & Targets';
    if (pathname === '/auth') return 'Sign In';
    return 'OpenUPSC';
  }

  function isActive(pathname, href, exact = false) {
    if (exact) return pathname === href || (href === '/' && pathname === '/dashboard');
    return pathname === href || pathname.startsWith(href + '/');
  }

  function renderSidebar() {
    const pathname = window.location.pathname;
    const p = AppState.profile || {};
    const displayName = p.full_name || 'Aspirant';
    const initial = displayName.charAt(0).toUpperCase();
    const streamlitUrl = API.getStreamlitUrl();

    document.getElementById('sidebar').innerHTML = `
      <a href="/" data-link class="sidebar-brand">
        <span class="brand-mark">O</span>
        <div>
          <span class="brand-name">OpenUPSC</span>
          <span class="brand-sub">Free UPSC CSE Hub</span>
        </div>
      </a>

      <nav class="sidebar-nav">
        ${NAV_LINKS.map((l) => {
          const act = isActive(pathname, l.href, l.exact);
          return `
            <a href="${l.href}" data-link class="nav-link ${act ? 'active' : ''}">
              <span class="left">${Icons(l.icon, 16)} <span>${esc(l.label)}</span></span>
            </a>`;
        }).join('')}

        <a href="${esc(streamlitUrl)}" target="_blank" rel="noopener noreferrer" class="analytics-cta-card">
          <div class="analytics-cta-title">
            <span class="flex items-center gap-2">${Icons('barChart', 15)} Analytics Studio</span>
            <span>↗</span>
          </div>
          <p class="analytics-cta-desc">
            Readiness score, 14-day study graphs, PYQ accuracy & Admin CRUD (Python Streamlit).
          </p>
        </a>
      </nav>

      <div class="sidebar-footer">
        <a href="/profile" data-link class="user-chip">
          <span class="avatar">${esc(initial)}</span>
          <div style="min-width:0">
            <span class="user-name">${esc(displayName)}</span>
            <span class="user-sub">${AppState.authenticated ? `CSE ${esc(p.target_attempt_year || '2028')}` : 'Demo Workspace'}</span>
          </div>
        </a>
        ${
          AppState.authenticated
            ? `<button type="button" class="btn-icon danger" id="sidebar-logout" title="Log out">${Icons('logout', 15)}</button>`
            : `<a href="/auth" data-link class="btn btn-primary btn-sm" style="padding:5px 10px">Log in</a>`
        }
      </div>
    `;

    const footerLink = document.getElementById('footer-streamlit-link');
    if (footerLink) footerLink.href = streamlitUrl;

    const logoutBtn = document.getElementById('sidebar-logout');
    if (logoutBtn) {
      logoutBtn.onclick = async () => {
        await API.logout();
        await API.loadWorkspace();
        refreshShell();
        toast('Logged out.', 'success');
        navigate('/auth');
      };
    }
  }

  function renderHeader() {
    const pathname = window.location.pathname;
    const p = AppState.profile || {};
    const initial = (p.full_name || 'A').charAt(0).toUpperCase();

    document.getElementById('top-header').innerHTML = `
      <div class="flex items-center gap-3">
        <a href="/" data-link class="mobile-brand">
          <span class="brand-mark">O</span>
          <span>OpenUPSC</span>
        </a>
        <span class="header-title">${esc(getTitle(pathname))}</span>
      </div>

      <div class="header-right">
        <a href="/study" data-link class="live-timer-pill hidden" id="header-live-timer"></a>

        <button type="button" class="btn btn-secondary btn-pill btn-sm" id="header-search-btn">
          ${Icons('search', 13)} <span>Search</span> <span class="kbd">⌘K</span>
        </button>

        ${
          AppState.authenticated
            ? `<a href="/profile" data-link class="avatar" title="${esc(p.full_name || 'Profile')}">${esc(initial)}</a>`
            : `<a href="/auth" data-link class="btn btn-primary btn-pill btn-sm">Log in</a>`
        }

        <button type="button" class="hamburger-btn" id="mobile-menu-toggle" aria-label="Open menu">
          ${Icons('menu', 20)}
        </button>
      </div>
    `;

    document.getElementById('header-search-btn').onclick = () => UI.openSearchModal();
    document.getElementById('mobile-menu-toggle').onclick = () => {
      document.getElementById('mobile-drawer').classList.toggle('hidden');
    };
    window.TimerController.syncDom();
  }

  function renderMobileNav() {
    const pathname = window.location.pathname;
    const streamlitUrl = API.getStreamlitUrl();

    document.getElementById('mobile-drawer').innerHTML = `
      <div class="grid grid-2" style="gap:8px">
        ${NAV_LINKS.map(
          (l) => `
          <a href="${l.href}" data-link class="card-sub text-xs font-bold" style="text-align:center;padding:11px" data-close-drawer>
            ${esc(l.label)}
          </a>`
        ).join('')}
        <a href="/resources?format=saved" data-link class="card-sub text-xs font-bold" style="text-align:center;padding:11px" data-close-drawer>Saved Vault</a>
        <a href="${esc(streamlitUrl)}" target="_blank" rel="noopener noreferrer" class="card-sub text-xs font-bold" style="text-align:center;padding:11px;color:var(--blue)">Analytics Studio ↗</a>
      </div>
      <div class="flex items-center justify-between mt-3" style="padding-top:10px;border-top:1px solid var(--surface-muted)">
        <a href="/profile" data-link class="text-xs font-bold" data-close-drawer>Account & Targets</a>
        ${
          AppState.authenticated
            ? `<button type="button" class="btn btn-ghost btn-sm" id="mobile-logout" style="color:var(--rose)">Log Out</button>`
            : `<a href="/auth" data-link class="text-xs font-bold" data-close-drawer>Log in / Sign up</a>`
        }
      </div>
    `;

    document.querySelectorAll('[data-close-drawer]').forEach((el) => {
      el.onclick = () => document.getElementById('mobile-drawer').classList.add('hidden');
    });
    const mLogout = document.getElementById('mobile-logout');
    if (mLogout) {
      mLogout.onclick = async () => {
        await API.logout();
        await API.loadWorkspace();
        refreshShell();
        navigate('/auth');
      };
    }

    const bottomItems = [
      { href: '/', label: 'Home', icon: 'dashboard', exact: true },
      { href: '/resources', label: 'Videos', icon: 'video' },
      { href: '/ncert', label: 'NCERT', icon: 'layers' },
      { href: '/pyqs', label: 'Papers', icon: 'fileText' },
      { href: '/study', label: 'Study', icon: 'clock' },
    ];
    document.getElementById('mobile-bottom-nav').innerHTML = bottomItems
      .map(
        (item) => `
        <a href="${item.href}" data-link class="mobile-nav-item ${isActive(pathname, item.href, item.exact) ? 'active' : ''}">
          ${Icons(item.icon, 17)}
          <span>${item.label}</span>
        </a>`
      )
      .join('');
  }

  function refreshShell() {
    renderSidebar();
    renderHeader();
    renderMobileNav();
  }

  async function renderCurrentRoute() {
    const seq = ++navSeq;
    const pathname = window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    const main = document.getElementById('main-content');

    // Leave fullscreen study mode if user navigates away from /study
    if (pathname !== '/study') {
      document.body.classList.remove('study-mode-active');
    }
    document.getElementById('mobile-drawer').classList.add('hidden');
    refreshShell();

    main.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading ${esc(getTitle(pathname))}...</p></div>`;

    try {
      if (pathname === '/' || pathname === '/dashboard' || pathname === '/progress') {
        await Pages.renderHome(main);
      } else if (pathname === '/resources') {
        await Pages.renderResources(main, params);
      } else if (pathname === '/saved') {
        await Pages.renderResources(main, params, 'saved');
      } else if (pathname === '/current-affairs') {
        const caParams = new URLSearchParams(params);
        caParams.set('pill', 'Current Affairs');
        await Pages.renderResources(main, caParams);
      } else if (pathname === '/ncert') {
        await Pages.renderNCERT(main, params);
      } else if (pathname === '/pyqs') {
        await Pages.renderPYQs(main, params);
      } else if (pathname === '/roadmaps') {
        await Pages.renderRoadmaps(main);
      } else if (pathname.startsWith('/roadmaps/')) {
        const subjectId = decodeURIComponent(pathname.replace('/roadmaps/', '').split('/')[0]);
        await Pages.renderRoadmapDetail(main, subjectId);
      } else if (pathname === '/study' || pathname.startsWith('/study/')) {
        await Pages.renderStudy(main, params);
      } else if (pathname === '/profile' || pathname === '/settings') {
        await Pages.renderProfile(main);
      } else if (pathname === '/auth') {
        await Pages.renderAuth(main, params);
      } else {
        if (seq !== navSeq) return;
        main.innerHTML = `<div class="card" style="text-align:center;padding:56px"><h2>Page Not Found</h2><a href="/" data-link class="btn btn-primary btn-pill mt-4">Return Home</a></div>`;
      }
    } catch (err) {
      if (seq !== navSeq) return;
      main.innerHTML = `<div class="card" style="text-align:center;padding:44px"><h3>Could not load page</h3><p class="text-xs text-muted mt-2">${esc(err.message)}</p><button class="btn btn-primary btn-pill mt-4" onclick="location.reload()">Reload</button></div>`;
    }

    if (seq === navSeq) {
      window.TimerController.syncDom();
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  }

  function navigate(url) {
    if (url === window.location.pathname + window.location.search) return;
    history.pushState({}, '', url);
    renderCurrentRoute();
  }

  function bindGlobalEvents() {
    document.addEventListener('click', async (e) => {
      const closeTarget = e.target.closest('[data-close-modal]');
      if (closeTarget) UI.closeModal(closeTarget.dataset.closeModal);

      if (e.target.classList && e.target.classList.contains('modal-backdrop')) {
        UI.closeModal(e.target.id);
      }

      const link = e.target.closest('a[data-link]');
      if (link && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
        e.preventDefault();
        navigate(link.getAttribute('href'));
        return;
      }

      const watchBtn = e.target.closest('[data-action="watch-video"]');
      if (watchBtn) {
        UI.openVideoModal({
          playlistId: watchBtn.dataset.playlist,
          url: watchBtn.dataset.url,
          title: watchBtn.dataset.title,
          provider: watchBtn.dataset.provider,
          itemId: watchBtn.dataset.id,
          subject: watchBtn.dataset.subject,
        });
        return;
      }

      const bmBtn = e.target.closest('[data-action="toggle-bookmark"]');
      if (bmBtn) {
        const id = bmBtn.dataset.id;
        try {
          const res = await API.toggleBookmark(id);
          bmBtn.innerHTML = res.bookmarked ? Icons('bookmarkFill', 15) : Icons('bookmark', 15);
          toast(res.bookmarked ? 'Saved to library.' : 'Removed from saved.', 'success');
        } catch (err) {
          toast(err.message, 'error');
        }
        return;
      }

      const noteBtn = e.target.closest('[data-action="open-notes"]');
      if (noteBtn) {
        UI.openNotesModal(noteBtn.dataset.id, noteBtn.dataset.title, noteBtn.dataset.category);
      }
    });

    document.addEventListener('change', async (e) => {
      const sel = e.target.closest('[data-action="update-progress"]');
      if (sel) {
        const id = sel.dataset.id;
        const pct = Number(sel.value);
        try {
          await API.updateProgress(id, pct);
          sel.classList.toggle('done', pct === 100);
          const card = sel.closest('[data-resource-card]');
          if (card) card.classList.toggle('card-completed', pct === 100);
          toast(`Progress saved (${pct}%).`, 'success');
        } catch (err) {
          toast(err.message, 'error');
        }
      }
    });

    window.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const modal = document.getElementById('search-modal');
        if (modal.classList.contains('hidden')) UI.openSearchModal();
        else UI.closeModal('search-modal');
      } else if (e.key === 'Escape') {
        ['search-modal', 'video-modal', 'notes-modal', 'custom-modal'].forEach(UI.closeModal);
        document.getElementById('mobile-drawer').classList.add('hidden');
      }
    });

    window.addEventListener('popstate', renderCurrentRoute);
  }

  async function init() {
    bindGlobalEvents();
    try {
      await API.loadWorkspace();
    } catch (err) {
      toast('Could not connect to FastAPI backend.', 'error');
    }
    await renderCurrentRoute();
  }

  return { init, navigate, refreshShell, renderCurrentRoute };
})();

document.addEventListener('DOMContentLoaded', () => {
  window.Router.init();
});
