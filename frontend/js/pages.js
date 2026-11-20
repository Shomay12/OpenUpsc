/* Simplified, Student-First OpenUPSC Page Renderers (Vanilla JS + FastAPI) */
window.Pages = (function () {
  const { esc, safeUrl, extractPlaylistId, formatMinutes, timeGreeting, plural, toast, seniorBox, resourceCard } = UI;

  const CANONICAL_STAGES = [
    'Zero Foundation',
    'Foundation (Class 6-12)',
    'Standard Core',
    'Prelims Focused',
    'Mains Focused',
  ];

  const SUBJECT_SHELF = [
    { name: 'NCERT (6–12)', desc: '36 Official PDFs + Video Playlists', href: '/ncert', tag: 'Start Here' },
    { name: 'Indian Polity', desc: 'Atish Mathur, Laxmikanth, Bookstawa, PRS', href: '/resources?pill=Indian+Polity', tag: 'GS-2' },
    { name: 'History', desc: 'Spectrum, Ancient, Medieval & Modern Videos', href: '/resources?pill=History', tag: 'GS-1' },
    { name: 'Art & Culture', desc: 'Class 11 Fine Arts, Bookstawa & CCRT', href: '/resources?pill=Art+%26+Culture', tag: 'GS-1' },
    { name: 'Geography', desc: 'Amit Sengupta, G.C. Leong & Mapping', href: '/resources?pill=Geography', tag: 'GS-1' },
    { name: 'Economy', desc: 'Mrunal Patel, Macroeconomics & Budget PDF', href: '/resources?pill=Economy', tag: 'GS-3' },
    { name: 'Environment', desc: 'PMF IAS, Sudarshan Gurjar & Ramsar Maps', href: '/resources?pill=Environment', tag: 'Prelims + GS-3' },
    { name: 'Science & Tech', desc: '100 High-Yield Topics & ISRO Portal', href: '/resources?pill=Science+%26+Tech', tag: 'Prelims + GS-3' },
    { name: 'Ethics (GS-4)', desc: 'Atish Mathur, ForumIAS & 2nd ARC PDFs', href: '/resources?pill=Ethics', tag: 'GS-4' },
    { name: 'CSAT Paper-II', desc: 'UNGIST Quant, Reading Comp & CSAT PYQs', href: '/resources?pill=CSAT', tag: 'Qualifying' },
    { name: 'Question Papers', desc: 'Official UPSC Prelims, CSAT & Mains PDFs', href: '/pyqs', tag: 'PYQs' },
    { name: 'Current Affairs', desc: 'Vision Monthly PDFs, Sansad TV, PIB & PT365', href: '/resources?pill=Current+Affairs', tag: 'Daily' },
  ];

  // =========================================================================
  // 1. HOME (/ and /dashboard)
  // =========================================================================
  async function renderHome(container) {
    const [resources] = await Promise.all([API.getResources(), API.loadWorkspace()]);
    const p = AppState.profile || {};
    const a = AppState.analytics || {};
    const firstName = (p.full_name || 'Aspirant').split(' ')[0];
    const streamlitUrl = API.getStreamlitUrl();

    // Dynamic "Continue Studying" derived from real latest session or first incomplete today block
    const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });
    const nextBlock = (AppState.timetable || []).find(
      (t) => !t.completed && (t.dayOfWeek === 'Daily' || t.dayOfWeek === todayName)
    );
    const lastSess = (AppState.studySessions || [])[0];
    const resumeSubject = nextBlock ? nextBlock.subject : lastSess ? lastSess.subject : 'Indian Polity';
    const resumeTopic = nextBlock
      ? nextBlock.topic
      : lastSess && lastSess.topic
      ? lastSess.topic
      : 'Class 11 Indian Constitution at Work';
    const resumeHint = nextBlock
      ? `Next scheduled block (${nextBlock.startTime} – ${nextBlock.endTime})`
      : lastSess
      ? `Last studied (${lastSess.durationMinutes} min)`
      : 'Recommended starting point for beginners';

    // Top 4 featured playable video courses
    const featuredIds = [
      'res-atish-magna-carta',
      'res-mrunal-economy-beginners',
      'res-bookstawa-modern',
      'res-ungist-csat-full',
    ];
    const featured = featuredIds
      .map((id) => resources.find((r) => r.id === id))
      .filter(Boolean);

    container.innerHTML = `
      <div class="page-stack">
        <!-- Clean Welcome + Instant Search -->
        <section class="card flex-col gap-4">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <span class="eyebrow">${esc(p.preparation_stage || 'UPSC CSE Workspace')} · TARGET CSE ${esc(p.target_attempt_year || '2028')}</span>
              <h1 class="page-title">${timeGreeting()}, ${esc(firstName)}.</h1>
              <p class="page-subtitle">All free, verified UPSC CSE video courses, Class 6–12 NCERT PDFs, and official past question papers in one clean place.</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <a href="/resources" data-link class="btn btn-primary">Browse All Videos & PDFs ${Icons('arrowRight', 14)}</a>
              <a href="/pyqs" data-link class="btn btn-outline">Official Papers & PYQs</a>
            </div>
          </div>

          <div class="search-box">
            <span class="search-icon">${Icons('search', 16)}</span>
            <input type="text" id="home-quick-search" class="input" placeholder="Search any UPSC topic, NCERT chapter, educator (Mrunal, Atish Mathur, Bookstawa), or PYQ paper..." />
          </div>
        </section>

        <!-- Compact 4-Metric Snapshot + Streamlit Analytics Highlight -->
        <section class="grid grid-4">
          <div class="card" style="padding:16px">
            <span class="eyebrow">Today's Study</span>
            <div class="font-display font-bold mt-1" style="font-size:24px">${formatMinutes(a.today_minutes)}</div>
            <span class="text-xs text-muted">${a.today_target_percent || 0}% of ${p.daily_target_hours || 4}h daily goal</span>
          </div>
          <div class="card" style="padding:16px">
            <span class="eyebrow">Readiness Score</span>
            <div class="font-display font-bold mt-1" style="font-size:24px">${a.readiness_score || 0}<span class="text-xs text-muted">/100</span></div>
            <span class="text-xs text-muted">Syllabus ${a.overall_progress_percent || 0}% · Consistency ${a.consistency_score || 0}%</span>
          </div>
          <div class="card" style="padding:16px">
            <span class="eyebrow">PYQ Accuracy</span>
            <div class="font-display font-bold mt-1" style="font-size:24px">${a.pyq_accuracy_percent || 0}%</div>
            <span class="text-xs text-muted">${a.pyq_total_correct || 0}/${a.pyq_total_attempted || 0} practiced</span>
          </div>
          <div class="card" style="padding:16px">
            <span class="eyebrow">Study Streak</span>
            <div class="font-display font-bold mt-1" style="font-size:24px;color:var(--emerald)">${plural(a.study_streak_days ?? 0, 'Day', 'Days')}</div>
            <span class="text-xs text-muted">${a.catalog_total_resources || resources.length} free resources ready</span>
          </div>
        </section>

        <!-- Continue Studying + Deep Analytics Banner -->
        <section class="grid grid-2">
          <div class="card flex-col justify-between gap-3">
            <div>
              <span class="eyebrow">CONTINUE STUDYING</span>
              <h2 class="mt-1" style="font-size:19px">${esc(resumeSubject)}</h2>
              <p class="text-sm text-muted mt-1">${esc(resumeTopic)}</p>
              <p class="text-xs text-muted mt-2">${esc(resumeHint)}</p>
            </div>
            <div class="flex flex-wrap gap-2 mt-2">
              <a href="/study?subject=${encodeURIComponent(resumeSubject)}&topic=${encodeURIComponent(resumeTopic)}&duration=50" data-link class="btn btn-primary btn-sm">
                ${Icons('play', 12)} <span>Start 50m Focus Session</span>
              </a>
              <a href="/study" data-link class="btn btn-secondary btn-sm">Open Study Plan</a>
            </div>
          </div>

          <div class="card card-dark flex-col justify-between gap-3">
            <div>
              <span class="eyebrow" style="color:#93C5FD">DEEP ANALYTICS · PYTHON STREAMLIT</span>
              <h2 class="mt-1" style="font-size:19px">Track Readiness, Weak Subjects & PYQ Trends</h2>
              <p class="text-xs mt-2" style="color:#CBD5E1">
                All important analytics live in Streamlit Studio: 14-day study graphs, subject time splits, PYQ accuracy breakdown, NCERT Class 6–12 audit, CSV exports, and Catalog Admin.
              </p>
            </div>
            <div>
              <a href="${esc(streamlitUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn-blue btn-sm">
                ${Icons('barChart', 14)} <span>Open Streamlit Analytics Studio ↗</span>
              </a>
            </div>
          </div>
        </section>

        <!-- Browse by Subject (Zero Hunting!) -->
        <section class="flex-col gap-3">
          <div class="section-header" style="margin-bottom:0">
            <div>
              <span class="eyebrow">ZERO-SEARCH SUBJECT SHELF</span>
              <h2 class="mt-1" style="font-size:20px">Pick a Subject & Start Learning</h2>
            </div>
            <a href="/resources" data-link class="btn btn-ghost btn-sm">View all ${resources.length} resources ${Icons('chevronRight', 14)}</a>
          </div>
          <div class="grid grid-4">
            ${SUBJECT_SHELF.map(
              (s) => `
              <a href="${s.href}" data-link class="card card-interactive flex-col justify-between gap-2" style="padding:16px">
                <div class="flex items-center justify-between">
                  <span class="badge badge-neutral font-mono">${esc(s.tag)}</span>
                  <span class="text-muted">${Icons('arrowUpRight', 14)}</span>
                </div>
                <div>
                  <h3 style="font-size:15px">${esc(s.name)}</h3>
                  <p class="text-xs text-muted mt-1">${esc(s.desc)}</p>
                </div>
              </a>`
            ).join('')}
          </div>
        </section>

        <!-- Top Free Video Courses (Watch Right Inside OpenUPSC!) -->
        <section class="flex-col gap-3">
          <div class="section-header" style="margin-bottom:0">
            <div>
              <span class="eyebrow">WATCH FREE RIGHT HERE</span>
              <h2 class="mt-1" style="font-size:20px">Top-Rated Free Video Playlists</h2>
            </div>
            <a href="/resources?format=video" data-link class="btn btn-ghost btn-sm">All video courses ${Icons('chevronRight', 14)}</a>
          </div>
          <div class="grid grid-2">
            ${featured.map(resourceCard).join('')}
          </div>
        </section>
      </div>
    `;

    const homeSearch = document.getElementById('home-quick-search');
    if (homeSearch) {
      homeSearch.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const q = homeSearch.value.trim();
          if (q) window.Router.navigate(`/resources?search=${encodeURIComponent(q)}`);
          else UI.openSearchModal();
        }
      });
    }
  }

  // =========================================================================
  // 2. VIDEOS & STUDY MATERIAL (/resources, /saved, /current-affairs)
  // =========================================================================
  async function renderResources(container, params, forcedFormat = null) {
    const resources = await API.getResources(true);

    // Always initialize cleanly from URL query params (fixes stale filter bug!)
    let searchQuery = params.get('search') || '';
    let selectedPill = params.get('pill') || params.get('level') || 'All';
    let selectedFormat = forcedFormat || params.get('format') || 'all';

    const subjectPills = [
      'All',
      'NCERT',
      'Indian Polity',
      'History',
      'Art & Culture',
      'Geography',
      'Economy',
      'Environment',
      'Science & Tech',
      'Ethics',
      'CSAT',
      'Question Papers',
      'Current Affairs',
      'Mains & Essay',
      'Interview',
    ];

    const formatTabs = [
      { id: 'all', label: 'All Material' },
      { id: 'video', label: '▶ Video Playlists' },
      { id: 'pdf', label: 'Official PDFs & Books' },
      { id: 'paper', label: 'Question Papers' },
      { id: 'notes', label: 'Notes & Portals' },
      { id: 'saved', label: '★ Saved' },
    ];

    function filterItems() {
      const q = searchQuery.trim().toLowerCase();
      return resources.filter((res) => {
        if (selectedFormat === 'video' && res.type !== 'YouTube' && !res.youtubePlaylistId) return false;
        if (selectedFormat === 'pdf' && res.type !== 'PDF') return false;
        if (selectedFormat === 'paper' && res.type !== 'PYQ' && res.subject !== 'Question Papers') return false;
        if (selectedFormat === 'notes' && !['Notes', 'Website'].includes(res.type)) return false;
        if (selectedFormat === 'saved' && !AppState.bookmarkedIds.includes(res.id)) return false;

        if (selectedPill !== 'All') {
          const p = selectedPill.toLowerCase();
          const hit =
            res.subject.toLowerCase() === p ||
            res.subject.toLowerCase().includes(p) ||
            res.level.toLowerCase() === p ||
            res.category.toLowerCase().includes(p) ||
            (res.tags || []).some((t) => t.toLowerCase() === p || t.toLowerCase().includes(p));
          if (!hit) return false;
        }

        if (q) {
          const hit =
            res.title.toLowerCase().includes(q) ||
            res.description.toLowerCase().includes(q) ||
            res.subject.toLowerCase().includes(q) ||
            res.provider.toLowerCase().includes(q) ||
            (res.tags || []).some((t) => t.toLowerCase().includes(q));
          if (!hit) return false;
        }
        return true;
      });
    }

    function drawList() {
      const filtered = filterItems();
      const countEl = document.getElementById('res-count');
      const gridEl = document.getElementById('res-grid');
      const videosCount = filtered.filter((r) => r.youtubePlaylistId || r.type === 'YouTube').length;
      if (countEl) {
        countEl.innerHTML = `Showing <strong>${filtered.length}</strong> free verified resources (${videosCount} video playlists)`;
      }
      if (gridEl) {
        gridEl.innerHTML = filtered.length
          ? filtered.map(resourceCard).join('')
          : `<div class="card" style="grid-column:1/-1;text-align:center;padding:48px">
               <h3>No matching resources found</h3>
               <p class="text-xs text-muted mt-2">Try switching format tab or clearing your search filter.</p>
               <button type="button" class="btn btn-primary btn-pill btn-sm mt-3" id="empty-res-reset">Reset Filters</button>
             </div>`;
        const emptyReset = document.getElementById('empty-res-reset');
        if (emptyReset) emptyReset.onclick = resetAll;
      }
    }

    function resetAll() {
      searchQuery = '';
      selectedPill = 'All';
      selectedFormat = 'all';
      const inp = document.getElementById('res-search-input');
      if (inp) inp.value = '';
      container.querySelectorAll('[data-fmt]').forEach((b) => b.classList.toggle('active', b.dataset.fmt === 'all'));
      container.querySelectorAll('[data-res-pill]').forEach((b) => b.classList.toggle('active', b.dataset.resPill === 'All'));
      drawList();
    }

    container.innerHTML = `
      <div class="page-stack">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <span class="eyebrow">CURATED FREE LIBRARY</span>
            <h1 class="page-title">Videos, Books & Study Material</h1>
            <p class="page-subtitle">Handpicked free UPSC CSE YouTube playlists, official NCERT/Govt PDFs, question papers, and topper copies. Watch videos right inside OpenUPSC.</p>
          </div>
          <a href="${esc(API.getStreamlitUrl())}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-pill btn-sm">
            ${Icons('plus', 13)} <span>Add / Manage in Streamlit ↗</span>
          </a>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="segmented">
            ${formatTabs
              .map((t) => `<button type="button" class="seg-btn ${selectedFormat === t.id ? 'active' : ''}" data-fmt="${t.id}">${t.label}</button>`)
              .join('')}
          </div>
          <div class="search-box" style="min-width:260px;flex:1;max-width:420px">
            <span class="search-icon">${Icons('search', 15)}</span>
            <input type="text" id="res-search-input" class="input" value="${esc(searchQuery)}" placeholder="Filter by topic, educator, or book..." />
          </div>
        </div>

        <div class="pills-bar">
          ${subjectPills
            .map((pill) => `<button type="button" class="pill-tab ${selectedPill === pill ? 'active' : ''}" data-res-pill="${esc(pill)}">${esc(pill)}</button>`)
            .join('')}
        </div>

        <div class="flex items-center justify-between text-xs text-muted">
          <span id="res-count"></span>
          <button type="button" class="btn btn-ghost btn-sm" id="res-reset">${Icons('reset', 12)} <span>Reset</span></button>
        </div>

        <div class="grid grid-3" id="res-grid"></div>
      </div>
    `;

    drawList();

    document.getElementById('res-search-input').addEventListener('input', (e) => {
      searchQuery = e.target.value;
      drawList();
    });
    container.querySelectorAll('[data-fmt]').forEach((btn) => {
      btn.onclick = () => {
        selectedFormat = btn.dataset.fmt;
        container.querySelectorAll('[data-fmt]').forEach((b) => b.classList.toggle('active', b === btn));
        drawList();
      };
    });
    container.querySelectorAll('[data-res-pill]').forEach((btn) => {
      btn.onclick = () => {
        selectedPill = btn.dataset.resPill;
        container.querySelectorAll('[data-res-pill]').forEach((b) => b.classList.toggle('active', b === btn));
        drawList();
      };
    });
    document.getElementById('res-reset').onclick = resetAll;
  }

  // =========================================================================
  // 3. NCERT CLASS 6–12 (/ncert)
  // =========================================================================
  async function renderNCERT(container, params) {
    const books = await API.getNCERT();
    let selectedClass = Number(params.get('class'));
    if (!(selectedClass >= 6 && selectedClass <= 12)) selectedClass = 6;
    let selectedBookId = params.get('book') || '';

    function draw() {
      const classBooks = books.filter((b) => b.classNum === selectedClass);
      const activeBook = classBooks.find((b) => b.id === selectedBookId) || classBooks[0];
      if (activeBook) selectedBookId = activeBook.id;

      const activeVidPid = activeBook ? extractPlaylistId(activeBook.recommendedLectureUrl) : null;
      const activePct = activeBook ? Number(AppState.progressMap[activeBook.id] || 0) : 0;
      const pctSteps = [0, 25, 50, 75, 100];
      if (!pctSteps.includes(activePct)) { pctSteps.push(activePct); pctSteps.sort((a, b) => a - b); }

      container.innerHTML = `
        <div class="page-stack">
          <div>
            <span class="eyebrow">OFFICIAL TEXTBOOKS + FREE LECTURES</span>
            <h1 class="page-title">NCERT Foundation (Class 6–12)</h1>
            <p class="page-subtitle">Direct official NCERT PDF downloads paired with verified YouTube playlists and UPSC chapter priorities.</p>
          </div>

          <div class="pills-bar">
            ${[6, 7, 8, 9, 10, 11, 12]
              .map((c) => `<button type="button" class="pill-tab ${selectedClass === c ? 'active' : ''}" data-ncert-cls="${c}">Class ${c}</button>`)
              .join('')}
          </div>

          <div class="grid grid-4">
            ${classBooks
              .map((b) => {
                const isSel = activeBook && activeBook.id === b.id;
                const uPct = Number(AppState.progressMap[b.id] || 0);
                return `
                  <button type="button" class="card-sub card-interactive ${isSel ? 'card-dark' : ''}" data-ncert-book="${esc(b.id)}" style="text-align:left">
                    <div class="flex items-start justify-between gap-2">
                      <strong class="font-display text-sm">${esc(b.subjectName)}</strong>
                      <span class="badge ${isSel ? 'badge-outline' : 'badge-neutral'}">${esc(b.readingPriority)}</span>
                    </div>
                    <div class="text-xs mt-1" style="opacity:0.8">${esc(b.bookTitle)}</div>
                    <div class="flex items-center justify-between mt-3 text-xs" style="opacity:0.75">
                      <span>${(b.chapters || []).length} chapters</span>
                      <span class="font-mono font-bold">${uPct > 0 ? uPct + '%' : ''}</span>
                    </div>
                  </button>`;
              })
              .join('')}
          </div>

          ${
            activeBook
              ? `
            <section class="card flex-col gap-4">
              <div class="flex flex-wrap items-start justify-between gap-4" style="padding-bottom:16px;border-bottom:1px solid var(--surface-muted)">
                <div style="max-width:640px">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="badge badge-neutral">Class ${activeBook.classNum} · ${esc(activeBook.subjectName)}</span>
                    <span class="badge badge-dark">${esc(activeBook.readingPriority)}</span>
                    <span class="text-xs text-muted">~${activeBook.estimatedHours}h</span>
                  </div>
                  <h2 class="mt-2" style="font-size:24px">${esc(activeBook.bookTitle)}</h2>
                  <p class="text-sm text-muted mt-1">${esc(activeBook.whyItMatters)}</p>
                </div>

                <div class="flex flex-wrap items-center gap-2">
                  <a href="${esc(safeUrl(activeBook.officialPdfUrl))}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
                    ${Icons('fileText', 13)} <span>Official NCERT PDF</span> ${Icons('arrowUpRight', 12)}
                  </a>
                  ${
                    activeVidPid
                      ? `<button type="button" class="btn btn-video btn-sm"
                           data-action="watch-video"
                           data-playlist="${esc(activeVidPid)}"
                           data-url="${esc(safeUrl(activeBook.recommendedLectureUrl))}"
                           data-title="${esc(activeBook.recommendedLectureTitle || activeBook.bookTitle)}"
                           data-provider="${esc(activeBook.recommendedLectureChannel || 'YouTube')}"
                           data-id="${esc(activeBook.id)}"
                           data-subject="${esc(activeBook.subjectName)}">
                           ${Icons('play', 12)} <span>Watch Playlist</span>
                         </button>`
                      : ''
                  }
                  <select class="progress-select ${activePct === 100 ? 'done' : ''}" data-action="update-progress" data-id="${esc(activeBook.id)}">
                    ${pctSteps.map((v) => `<option value="${v}" ${activePct === v ? 'selected' : ''}>${v === 100 ? '✓ Done' : v + '% Done'}</option>`).join('')}
                  </select>
                  <button type="button" class="btn btn-outline btn-sm"
                    data-action="open-notes"
                    data-id="${esc(activeBook.id)}"
                    data-title="${esc(activeBook.bookTitle)}"
                    data-category="${esc(activeBook.subjectName)}">
                    ${Icons('edit', 13)} <span>Notes</span>
                  </button>
                </div>
              </div>

              ${seniorBox(activeBook.seniorHinglishAdvice, 'Senior Hinglish Tip')}

              <div class="grid grid-2">
                <div class="card-sub">
                  <strong class="text-xs" style="color:var(--emerald)">✓ What to Focus On</strong>
                  <p class="text-xs text-muted mt-1">${esc(activeBook.whatToFocusOn)}</p>
                </div>
                <div class="card-sub">
                  <strong class="text-xs" style="color:var(--amber)">— What to Skip</strong>
                  <p class="text-xs text-muted mt-1">${esc(activeBook.whatToSkip || 'Skip elementary classroom activities and fill-in-the-blanks.')}</p>
                </div>
              </div>

              <div class="flex-col gap-2 mt-1">
                <div class="flex items-center justify-between">
                  <h3 style="font-size:16px">Chapters (${(activeBook.chapters || []).length})</h3>
                  <button type="button" class="btn btn-ghost btn-sm" id="suggest-book-btn">+ Suggest Better Video</button>
                </div>
                ${(activeBook.chapters || [])
                  .map((ch) => {
                    const priCls = ch.priority === 'Must Read' ? 'badge-dark' : ch.priority === 'Important' ? 'badge-neutral' : 'badge-outline';
                    return `
                      <div class="card-sub flex flex-wrap items-start justify-between gap-3">
                        <div style="flex:1;min-width:240px">
                          <div class="flex items-center gap-2 flex-wrap">
                            <span class="font-mono text-xs font-bold text-muted">Ch ${ch.number}</span>
                            <span class="badge ${priCls}">${esc(ch.priority)}</span>
                            <strong class="text-sm">${esc(ch.title)}</strong>
                          </div>
                          <p class="text-xs text-muted mt-1">${esc(ch.upscRelevanceNote)}</p>
                        </div>
                        <a href="/study?subject=${encodeURIComponent(activeBook.subjectName)}&topic=${encodeURIComponent(`Class ${activeBook.classNum} Ch ${ch.number}: ${ch.title}`)}&duration=25" data-link class="btn btn-secondary btn-pill btn-sm">
                          ${Icons('play', 11)} <span>Study</span>
                        </a>
                      </div>`;
                  })
                  .join('')}
              </div>
            </section>`
              : ''
          }
        </div>
      `;

      container.querySelectorAll('[data-ncert-cls]').forEach((b) => {
        b.onclick = () => {
          selectedClass = Number(b.dataset.ncertCls);
          selectedBookId = '';
          history.replaceState({}, '', `/ncert?class=${selectedClass}`);
          draw();
        };
      });
      container.querySelectorAll('[data-ncert-book]').forEach((b) => {
        b.onclick = () => {
          selectedBookId = b.dataset.ncertBook;
          history.replaceState({}, '', `/ncert?class=${selectedClass}&book=${encodeURIComponent(selectedBookId)}`);
          draw();
        };
      });

      const sugBtn = document.getElementById('suggest-book-btn');
      if (sugBtn && activeBook) {
        sugBtn.onclick = () => {
          const modal = UI.openCustomModal(`
            <div class="modal-header">
              <h3>Suggest a Free Resource</h3>
              <button type="button" class="btn-icon" data-close-modal="custom-modal">${Icons('x', 18)}</button>
            </div>
            <form id="suggest-form" class="modal-body">
              <p class="text-xs text-muted">Class ${activeBook.classNum} ${esc(activeBook.subjectName)} — ${esc(activeBook.bookTitle)}</p>
              <div class="form-group">
                <label class="form-label">YouTube Playlist or Official Notes URL</label>
                <input type="url" name="url" class="input" required placeholder="https://www.youtube.com/playlist?list=..." />
              </div>
              <div class="form-group">
                <label class="form-label">Educator / Channel Name</label>
                <input type="text" name="channel" class="input" placeholder="e.g. Amit Sengupta, Bookstawa, PMF IAS" />
              </div>
              <div class="flex justify-between gap-2 mt-2">
                <button type="button" class="btn btn-secondary btn-pill" data-close-modal="custom-modal">Cancel</button>
                <button type="submit" class="btn btn-primary btn-pill">Submit Suggestion</button>
              </div>
            </form>
          `);
          modal.querySelector('#suggest-form').onsubmit = async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await API.submitSuggestion({
                subject: activeBook.subjectName,
                chapter_title: activeBook.bookTitle,
                chapter_num: 0,
                url: fd.get('url'),
                channel: fd.get('channel'),
              });
              UI.closeModal('custom-modal');
              toast('Submitted! Reviewable inside Streamlit Admin Studio.', 'success');
            } catch (err) {
              toast(err.message, 'error');
            }
          };
        };
      }
    }

    draw();
  }

  // =========================================================================
  // 4. OFFICIAL QUESTION PAPERS & INTERACTIVE PYQS (/pyqs)
  // =========================================================================
  async function renderPYQs(container, params) {
    const { pyqs, questionPapers } = await API.getPYQsAndPapers();

    let selectedType = params.get('type') || 'All';
    let selectedSubject = params.get('subject') || 'All';
    const revealed = {};

    // Dynamically derive subject filters so Environment & Ethics are never hidden
    const dynamicSubjects = ['All', ...Array.from(new Set(pyqs.map((p) => p.subject)))];

    function updateAccuracyStrip() {
      const a = AppState.analytics || {};
      const el = document.getElementById('pyq-score-strip');
      if (el) {
        el.innerHTML = `Attempted: <strong>${a.pyq_total_attempted || 0}</strong> · Correct: <strong>${a.pyq_total_correct || 0}</strong> · Accuracy: <strong style="color:var(--emerald)">${a.pyq_accuracy_percent || 0}%</strong>`;
      }
    }

    function renderSinglePyqCard(pyq, idx) {
      const attempt = AppState.pyqAttempts[pyq.id];
      const chosen = attempt ? attempt.selectedOption : null;
      const isRev = !!revealed[pyq.id] || !!attempt;
      const numStr = String(idx + 1).padStart(2, '0');

      return `
        <article class="card flex-col gap-3" id="pyq-card-${esc(pyq.id)}">
          <div class="flex items-center justify-between gap-2" style="padding-bottom:10px;border-bottom:1px solid var(--surface-muted)">
            <div class="flex flex-wrap items-center gap-2 text-xs">
              <span class="font-mono font-bold text-muted">${numStr}</span>
              <span class="badge badge-dark">${esc(pyq.type)} ${pyq.year}</span>
              <span class="badge badge-neutral">${esc(pyq.subject)}</span>
              <span class="text-muted">${esc(pyq.topic)}</span>
            </div>
            <button type="button" class="btn btn-ghost btn-sm"
              data-action="open-notes"
              data-id="${esc(pyq.id)}"
              data-title="${esc(`${pyq.subject} PYQ (${pyq.year})`)}"
              data-category="PYQ Note">
              ${Icons('edit', 13)} <span>Note</span>
            </button>
          </div>

          <p style="white-space:pre-line;font-size:14px;line-height:1.6">${esc(pyq.question)}</p>

          ${
            pyq.options && pyq.options.length
              ? `
            <div class="grid grid-2">
              ${pyq.options
                .map((opt, oIdx) => {
                  let cls = '';
                  if (isRev && opt === pyq.correctAnswer) cls = 'correct';
                  else if (isRev && chosen === opt && opt !== pyq.correctAnswer) cls = 'wrong';
                  return `
                    <button type="button" class="pyq-option ${cls}" data-pyq-opt="${esc(pyq.id)}" data-opt-idx="${oIdx}">
                      <span class="font-mono font-bold text-muted">${String.fromCharCode(65 + oIdx)}</span>
                      <span>${esc(opt)}</span>
                    </button>`;
                })
                .join('')}
            </div>`
              : ''
          }

          <div class="flex flex-wrap items-center justify-between gap-2">
            <button type="button" class="btn btn-secondary btn-pill btn-sm" data-pyq-reveal="${esc(pyq.id)}">
              ${Icons('eye', 13)} <span>${isRev ? 'Hide Explanation' : 'Show Explanation'}</span>
            </button>
            ${
              pyq.relatedSubjectPath
                ? `<a href="${esc(pyq.relatedSubjectPath)}" data-link class="btn btn-ghost btn-sm">Study Related Topic ${Icons('arrowUpRight', 13)}</a>`
                : ''
            }
          </div>

          ${
            isRev
              ? `
            <div class="card-sub flex-col gap-2">
              ${pyq.correctAnswer ? `<div><span class="badge badge-emerald">Correct: ${esc(pyq.correctAnswer)}</span></div>` : ''}
              <p class="text-xs" style="white-space:pre-line;line-height:1.6">${esc(pyq.explanation)}</p>
              <div class="resource-tip"><strong>Senior Tip:</strong> ${esc(pyq.seniorApproachTip)}</div>
            </div>`
              : ''
          }
        </article>
      `;
    }

    function drawList() {
      const filtered = pyqs.filter((p) => {
        if (selectedType !== 'All' && p.type !== selectedType) return false;
        if (selectedSubject !== 'All' && p.subject !== selectedSubject) return false;
        return true;
      });
      const listEl = document.getElementById('pyq-list');
      if (!listEl) return;
      listEl.innerHTML = filtered.map((p, idx) => renderSinglePyqCard(p, idx)).join('');
      bindPyqCardEvents(filtered);
      updateAccuracyStrip();
    }

    function bindPyqCardEvents(filtered) {
      const listEl = document.getElementById('pyq-list');
      if (!listEl) return;
      listEl.querySelectorAll('[data-pyq-opt]').forEach((btn) => {
        btn.onclick = async () => {
          const id = btn.dataset.pyqOpt;
          const idx = filtered.findIndex((x) => x.id === id);
          const pyq = filtered[idx];
          if (!pyq) return;
          const selectedOption = pyq.options[Number(btn.dataset.optIdx)];
          const isCorrect = selectedOption === pyq.correctAnswer;
          revealed[id] = true;
          try {
            await API.recordPyqAttempt({
              pyq_id: id,
              subject: pyq.subject,
              selected_option: selectedOption,
              is_correct: isCorrect,
            });
            // In-place card update preserves scroll position!
            const cardEl = document.getElementById(`pyq-card-${id}`);
            if (cardEl) {
              cardEl.outerHTML = renderSinglePyqCard(pyq, idx);
              bindPyqCardEvents(filtered);
            }
            updateAccuracyStrip();
            toast(isCorrect ? 'Correct! Synced to Analytics.' : 'Review explanation — synced to Analytics.', isCorrect ? 'success' : 'default');
          } catch (err) {
            toast(err.message, 'error');
          }
        };
      });

      listEl.querySelectorAll('[data-pyq-reveal]').forEach((btn) => {
        btn.onclick = () => {
          const id = btn.dataset.pyqReveal;
          const idx = filtered.findIndex((x) => x.id === id);
          const pyq = filtered[idx];
          if (!pyq) return;
          revealed[id] = !revealed[id];
          const cardEl = document.getElementById(`pyq-card-${id}`);
          if (cardEl) {
            cardEl.outerHTML = renderSinglePyqCard(pyq, idx);
            bindPyqCardEvents(filtered);
          }
        };
      });
    }

    container.innerHTML = `
      <div class="page-stack">
        <div>
          <span class="eyebrow">OFFICIAL EXAM ARCHIVES & PRACTICE</span>
          <h1 class="page-title">Question Papers & PYQs</h1>
          <p class="page-subtitle">Download authentic UPSC Prelims, CSAT & Mains PDFs directly, and practice past questions with live accuracy tracking in Streamlit Analytics.</p>
        </div>

        <!-- Official UPSC Question Papers Download Archive -->
        <section class="flex-col gap-3">
          <div class="section-header" style="margin-bottom:0">
            <div>
              <span class="eyebrow">DIRECT DOWNLOAD ARCHIVES</span>
              <h2 class="mt-1" style="font-size:19px">Official UPSC Question Papers & Answer Booklets</h2>
            </div>
          </div>
          <div class="grid grid-4">
            ${questionPapers
              .map(
                (qp) => `
              <a href="${esc(safeUrl(qp.url))}" target="_blank" rel="noopener noreferrer" class="card card-interactive flex-col justify-between gap-2" style="padding:16px">
                <div>
                  <div class="flex items-center justify-between gap-1">
                    <span class="badge badge-blue">${esc(qp.stage)}</span>
                    <span class="font-mono text-xs text-muted">${esc(qp.years)}</span>
                  </div>
                  <h3 class="mt-2" style="font-size:14px">${esc(qp.title)}</h3>
                  <p class="text-xs text-muted mt-1">${esc(qp.description)}</p>
                </div>
                <div class="flex items-center justify-between text-xs font-bold mt-2" style="padding-top:8px;border-top:1px solid var(--surface-muted)">
                  <span class="text-muted">${esc(qp.provider)}</span>
                  <span>Open PDF ↗</span>
                </div>
              </a>`
              )
              .join('')}
          </div>
        </section>

        <!-- Interactive Practice PYQs -->
        <section class="flex-col gap-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span class="eyebrow">PRACTICE & TRACK ACCURACY</span>
              <h2 class="mt-1" style="font-size:19px">Interactive UPSC Past Questions (${pyqs.length})</h2>
            </div>
            <div class="flex items-center gap-3 flex-wrap">
              <span class="text-xs text-muted" id="pyq-score-strip"></span>
              <button type="button" class="btn btn-ghost btn-sm" id="pyq-reset-btn">${Icons('reset', 12)} <span>Reset Attempts</span></button>
            </div>
          </div>

          <div class="card flex flex-wrap items-center justify-between gap-3" style="padding:12px 16px">
            <div class="segmented">
              ${['All', 'Prelims', 'Mains']
                .map((t) => `<button type="button" class="seg-btn ${selectedType === t ? 'active' : ''}" data-pyq-type="${t}">${t}</button>`)
                .join('')}
            </div>
            <div class="pills-bar">
              ${dynamicSubjects
                .map((s) => `<button type="button" class="pill-tab ${selectedSubject === s ? 'active' : ''}" data-pyq-subj="${esc(s)}" style="padding:5px 12px">${esc(s)}</button>`)
                .join('')}
            </div>
          </div>

          <div class="flex-col gap-3" id="pyq-list"></div>
        </section>
      </div>
    `;

    drawList();

    container.querySelectorAll('[data-pyq-type]').forEach((b) => {
      b.onclick = () => {
        selectedType = b.dataset.pyqType;
        container.querySelectorAll('[data-pyq-type]').forEach((x) => x.classList.toggle('active', x === b));
        drawList();
      };
    });
    container.querySelectorAll('[data-pyq-subj]').forEach((b) => {
      b.onclick = () => {
        selectedSubject = b.dataset.pyqSubj;
        container.querySelectorAll('[data-pyq-subj]').forEach((x) => x.classList.toggle('active', x === b));
        drawList();
      };
    });
    document.getElementById('pyq-reset-btn').onclick = async () => {
      if (!confirm('Clear all your saved PYQ attempts?')) return;
      try {
        await API.resetPyqAttempts();
        Object.keys(revealed).forEach((k) => delete revealed[k]);
        toast('PYQ attempts reset.', 'success');
        drawList();
      } catch (err) {
        toast(err.message, 'error');
      }
    };
  }

  // =========================================================================
  // 5. ROADMAPS (/roadmaps & /roadmaps/:subject)
  // =========================================================================
  async function renderRoadmaps(container) {
    const roadmaps = await API.getRoadmaps();
    container.innerHTML = `
      <div class="page-stack">
        <div>
          <span class="eyebrow">STEP-BY-STEP PATHWAYS</span>
          <h1 class="page-title">Subject Roadmaps</h1>
          <p class="page-subtitle">Clear stage-by-stage progression from NCERT basics to standard video courses and PYQ mastery.</p>
        </div>

        <div class="grid grid-2">
          ${roadmaps
            .map(
              (rm) => `
            <a href="/roadmaps/${esc(rm.subjectId)}" data-link class="card card-interactive flex-col justify-between gap-3">
              <div>
                <div class="flex items-center justify-between">
                  <h2 style="font-size:18px">${esc(rm.subjectName)}</h2>
                  <span class="badge badge-neutral font-mono">${rm.steps.length} Steps</span>
                </div>
                <p class="text-xs text-muted mt-2">${esc(rm.description)}</p>
              </div>
              <div class="flex items-center justify-between text-xs font-bold" style="padding-top:10px;border-top:1px solid var(--surface-muted)">
                <span class="text-muted">NCERT → Standard → PYQs</span>
                <span>Open Pathway →</span>
              </div>
            </a>`
            )
            .join('')}
        </div>

        <section class="card">
          <div class="section-header">
            <h3 style="font-size:16px">Other High-Yield UPSC Pillars</h3>
            <a href="/resources" data-link class="btn btn-ghost btn-sm">Full Library →</a>
          </div>
          <div class="grid grid-4">
            <a href="/resources?pill=Environment" data-link class="card-sub card-interactive"><strong class="text-sm">Environment & Ecology</strong><p class="text-xs text-muted mt-1">PMF IAS + Sudarshan Gurjar + Ramsar Maps</p></a>
            <a href="/resources?pill=Ethics" data-link class="card-sub card-interactive"><strong class="text-sm">Ethics (GS-4)</strong><p class="text-xs text-muted mt-1">Atish Mathur + ForumIAS + 2nd ARC PDFs</p></a>
            <a href="/resources?pill=CSAT" data-link class="card-sub card-interactive"><strong class="text-sm">CSAT Paper-II</strong><p class="text-xs text-muted mt-1">UNGIST Full Course + RC + Solved PYQs</p></a>
            <a href="/resources?pill=Science+%26+Tech" data-link class="card-sub card-interactive"><strong class="text-sm">Science & Tech</strong><p class="text-xs text-muted mt-1">Drishti 100 Topics + ISRO + PRS Briefs</p></a>
          </div>
        </section>
      </div>
    `;
  }

  async function renderRoadmapDetail(container, subjectId) {
    const roadmaps = await API.getRoadmaps();
    const roadmap = roadmaps.find((r) => r.subjectId === subjectId);
    if (!roadmap) {
      container.innerHTML = `<div class="card" style="text-align:center;padding:56px"><h2>Roadmap Not Found</h2><a href="/roadmaps" data-link class="btn btn-primary mt-4">Back to Roadmaps</a></div>`;
      return;
    }

    // Local step index scoped cleanly to this render (never leaks across subjects!)
    let stepIdx = 0;
    const pyqSubjMap = { history: 'History', polity: 'Indian Polity', geography: 'Geography', economy: 'Economy' };

    function draw() {
      const step = roadmap.steps[stepIdx];
      const stepPct = Number(AppState.progressMap[step.id] || 0);

      container.innerHTML = `
        <div class="page-stack">
          <div>
            <a href="/roadmaps" data-link class="btn btn-ghost btn-sm" style="padding-left:0">${Icons('arrowLeft', 14)} Back to Roadmaps</a>
            <h1 class="page-title">${esc(roadmap.subjectName)}</h1>
            <p class="page-subtitle">${esc(roadmap.description)}</p>
          </div>

          ${seniorBox(roadmap.overviewAdvice, `${roadmap.subjectName} Strategy`)}

          <div class="grid grid-6">
            ${roadmap.steps
              .map((st, idx) => {
                const isSel = idx === stepIdx;
                const done = Number(AppState.progressMap[st.id] || 0) === 100;
                return `
                  <button type="button" class="card-sub ${isSel ? 'card-dark' : ''}" data-rm-step="${idx}" style="text-align:left;padding:12px">
                    <div class="flex items-center justify-between font-mono text-xs">
                      <span style="opacity:0.7">${String(idx + 1).padStart(2, '0')}</span>
                      ${done ? '<span style="color:#34D399;font-weight:700">✓</span>' : ''}
                    </div>
                    <div class="font-display font-bold text-xs mt-1">${esc(st.title.split('(')[0])}</div>
                  </button>`;
              })
              .join('')}
          </div>

          <section class="card flex-col gap-4">
            <div class="flex flex-wrap items-start justify-between gap-3" style="padding-bottom:14px;border-bottom:1px solid var(--surface-muted)">
              <div>
                <span class="eyebrow">Step ${String(step.stepNumber).padStart(2, '0')} · ${esc(step.level)} · ~${esc(step.estimatedTime)}</span>
                <h2 class="mt-1" style="font-size:22px">${esc(step.title)}</h2>
                <p class="text-sm text-muted mt-1">${esc(step.tagline)}</p>
              </div>
              <div class="flex items-center gap-2">
                <select class="progress-select ${stepPct === 100 ? 'done' : ''}" id="rm-step-progress" data-id="${esc(step.id)}">
                  ${[0, 25, 50, 75, 100].map((v) => `<option value="${v}" ${stepPct === v ? 'selected' : ''}>${v === 100 ? '✓ Done' : v + '% Done'}</option>`).join('')}
                </select>
                <button type="button" class="btn btn-secondary btn-sm"
                  data-action="open-notes"
                  data-id="${esc(step.id)}"
                  data-title="${esc(step.title)}"
                  data-category="${esc(roadmap.subjectName)}">
                  ${Icons('edit', 13)} <span>Notes</span>
                </button>
              </div>
            </div>

            ${seniorBox(step.seniorGuidance, 'Focus Guidance')}

            <div class="grid grid-2">
              <div class="card-sub">
                <strong class="text-xs">Action Checklist</strong>
                <ul style="margin:8px 0 0;padding-left:18px;display:flex;flex-direction:column;gap:6px">
                  ${(step.actionChecklist || []).map((c) => `<li class="text-xs text-muted">${esc(c)}</li>`).join('')}
                </ul>
              </div>
              <div class="card-sub flex-col justify-between gap-2">
                <div>
                  <strong class="text-xs">PYQ Focus</strong>
                  <p class="text-xs text-muted mt-2">${esc(step.pyqFocusArea)}</p>
                </div>
                <a href="/pyqs?subject=${encodeURIComponent(pyqSubjMap[subjectId] || 'All')}" data-link class="btn btn-ghost btn-sm" style="align-self:flex-start;padding-left:0">
                  Practice ${esc(pyqSubjMap[subjectId] || '')} PYQs ↗
                </a>
              </div>
            </div>

            ${
              step.resources && step.resources.length
                ? `
              <div class="flex-col gap-2 mt-1">
                <h3 style="font-size:15px">Verified Free Video Series for this Step</h3>
                <div class="grid grid-2">${step.resources.map(resourceCard).join('')}</div>
              </div>`
                : ''
            }

            <div class="flex items-center justify-between mt-2" style="padding-top:12px;border-top:1px solid var(--surface-muted)">
              <button type="button" class="btn btn-outline btn-pill btn-sm" id="rm-prev" ${stepIdx === 0 ? 'disabled' : ''}>← Previous</button>
              ${
                stepIdx < roadmap.steps.length - 1
                  ? `<button type="button" class="btn btn-primary btn-pill btn-sm" id="rm-next">Next Step →</button>`
                  : `<a href="/roadmaps" data-link class="btn btn-primary btn-pill btn-sm">All Roadmaps →</a>`
              }
            </div>
          </section>
        </div>
      `;

      container.querySelectorAll('[data-rm-step]').forEach((b) => {
        b.onclick = () => { stepIdx = Number(b.dataset.rmStep); draw(); };
      });
      const stepSel = document.getElementById('rm-step-progress');
      if (stepSel) {
        stepSel.onchange = async () => {
          try {
            await API.updateProgress(step.id, Number(stepSel.value));
            toast(`Step progress set to ${stepSel.value}%.`, 'success');
            draw();
          } catch (err) { toast(err.message, 'error'); }
        };
      }
      const prev = document.getElementById('rm-prev');
      if (prev) prev.onclick = () => { stepIdx = Math.max(0, stepIdx - 1); draw(); };
      const next = document.getElementById('rm-next');
      if (next) next.onclick = () => { stepIdx = Math.min(roadmap.steps.length - 1, stepIdx + 1); draw(); };
    }

    draw();
  }

  // =========================================================================
  // 6. UNIFIED STUDY WORKSPACE (/study — Timer + Today's Plan + Recent Logs)
  // =========================================================================
  async function renderStudy(container, params) {
    await API.loadWorkspace();
    const t = AppState.timer;

    // Pre-fill timer subject/topic only when timer isn't currently running
    if (!t.isRunning) {
      if (params.get('subject')) t.subject = params.get('subject');
      if (params.get('topic')) t.topic = params.get('topic');
      if (params.get('resourceId')) t.resourceId = params.get('resourceId');
      if (params.get('duration')) {
        const mins = Math.max(1, Math.min(180, Number(params.get('duration')) || 25));
        t.targetMinutes = mins;
        t.secondsLeft = mins * 60;
        t.mode = 'Focus';
      }
    }

    let showAllDays = false;
    let addingBlock = false;
    let editingBlock = null;

    const baseSubjects = [
      'History',
      'Indian Polity',
      'Geography',
      'Economy',
      'Environment',
      'Art & Culture',
      'Science & Tech',
      'Ethics',
      'CSAT',
      'Current Affairs',
      'Mains & Essay',
    ];

    function draw() {
      const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' });
      const timetable = AppState.timetable || [];
      const visibleBlocks = showAllDays
        ? timetable
        : timetable.filter((b) => b.dayOfWeek === 'Daily' || b.dayOfWeek === todayName);

      const sessions = AppState.studySessions || [];
      const a = AppState.analytics || {};
      const subjectChoices = baseSubjects.includes(t.subject) ? baseSubjects : [t.subject, ...baseSubjects];
      const totalSec = t.targetMinutes * 60;
      const pct = totalSec > 0 ? Math.min(100, ((totalSec - t.secondsLeft) / totalSec) * 100) : 0;
      const isStudyMode = document.body.classList.contains('study-mode-active');

      const formDefaults = editingBlock || {
        subject: 'Indian Polity',
        dayOfWeek: 'Daily',
        startTime: '06:30',
        endTime: '07:30',
        topic: '',
        resourceTitle: '',
      };

      container.innerHTML = `
        <div class="page-stack">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span class="eyebrow">FOCUS & DAILY ROUTINE</span>
              <h1 class="page-title">Study Workspace</h1>
            </div>
            <div class="flex items-center gap-2">
              <button type="button" class="btn btn-outline btn-pill btn-sm" id="toggle-study-mode">
                ${isStudyMode ? `${Icons('minimize', 13)} Exit Focus Mode` : `${Icons('maximize', 13)} Fullscreen Focus`}
              </button>
              <a href="${esc(API.getStreamlitUrl())}" target="_blank" rel="noopener noreferrer" class="btn btn-blue btn-pill btn-sm">
                ${Icons('barChart', 13)} <span>Full Study Charts ↗</span>
              </a>
            </div>
          </div>

          <section class="grid ${isStudyMode ? '' : 'grid-2'}">
            <!-- FOCUS TIMER CARD -->
            <div class="card flex-col items-center gap-4" style="text-align:center;padding:30px 24px">
              <div class="segmented">
                <button type="button" class="seg-btn ${t.mode === 'Focus' && t.targetMinutes === 25 ? 'active' : ''}" data-preset="25" data-mode="Focus">25m Focus</button>
                <button type="button" class="seg-btn ${t.mode === 'Focus' && t.targetMinutes === 50 ? 'active' : ''}" data-preset="50" data-mode="Focus">50m Focus</button>
                <button type="button" class="seg-btn ${t.mode === 'Short Break' ? 'active' : ''}" data-preset="5" data-mode="Short Break">5m Break</button>
              </div>

              <div class="timer-display" id="timer-clock">${window.TimerController.formatClock(t.secondsLeft)}</div>

              <div class="progress-track" style="max-width:220px;height:5px">
                <div class="progress-fill" id="timer-bar" style="width:${pct}%"></div>
              </div>

              <div class="flex-col items-center gap-2 w-full" style="max-width:340px">
                <select id="timer-subject" class="select" style="text-align:center;font-weight:700">
                  ${subjectChoices.map((s) => `<option value="${esc(s)}" ${t.subject === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}
                </select>
                <input type="text" id="timer-topic" class="input" style="text-align:center" value="${esc(t.topic)}" placeholder="Topic or chapter name..." />
              </div>

              <div class="flex flex-wrap items-center justify-center gap-2 mt-1">
                <button type="button" class="btn ${t.isRunning ? 'btn-secondary' : 'btn-primary'} btn-pill" id="timer-toggle" style="min-width:118px">
                  ${t.isRunning ? `${Icons('pause', 14)} Pause` : `${Icons('play', 14)} Start`}
                </button>
                <button type="button" class="btn btn-secondary btn-pill" id="timer-reset" title="Reset">${Icons('reset', 14)}</button>
                <button type="button" class="btn btn-outline btn-pill" id="timer-complete">
                  ${Icons('checkCircle', 14)} <span>Finish & Log</span>
                </button>
              </div>

              <p class="text-xs text-muted">
                Today's focus: <strong>${formatMinutes(a.today_minutes)}</strong> · Weekly: <strong>${formatMinutes(a.weekly_minutes)}</strong>
              </p>
            </div>

            <!-- TODAY'S STUDY PLAN & TIMETABLE -->
            ${
              !isStudyMode
                ? `
              <div class="card flex-col gap-3">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 style="font-size:17px">${showAllDays ? 'All Timetable Blocks' : `Today's Plan (${todayName})`}</h2>
                    <span class="text-xs text-muted">${a.timetable_completed || 0}/${a.timetable_total || 0} completed today</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <button type="button" class="btn btn-ghost btn-sm" id="tt-toggle-days">${showAllDays ? 'Today Only' : 'All Days'}</button>
                    <button type="button" class="btn btn-primary btn-pill btn-sm" id="tt-add-btn">${Icons('plus', 13)} Add Block</button>
                  </div>
                </div>

                ${
                  addingBlock
                    ? `
                  <form id="tt-form" class="card-sub grid grid-2" style="gap:10px">
                    <div class="form-group">
                      <label class="form-label">Subject</label>
                      <select name="subject" class="select">
                        ${baseSubjects.map((s) => `<option value="${esc(s)}" ${formDefaults.subject === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}
                      </select>
                    </div>
                    <div class="form-group">
                      <label class="form-label">Day</label>
                      <select name="day_of_week" class="select">
                        ${['Daily', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                          .map((d) => `<option value="${d}" ${formDefaults.dayOfWeek === d ? 'selected' : ''}>${d}</option>`)
                          .join('')}
                      </select>
                    </div>
                    <div class="form-group">
                      <label class="form-label">Start</label>
                      <input type="time" name="start_time" class="input" value="${esc(formDefaults.startTime)}" required />
                    </div>
                    <div class="form-group">
                      <label class="form-label">End</label>
                      <input type="time" name="end_time" class="input" value="${esc(formDefaults.endTime)}" required />
                    </div>
                    <div class="form-group" style="grid-column:1/-1">
                      <label class="form-label">Topic</label>
                      <input type="text" name="topic" class="input" required value="${esc(formDefaults.topic)}" placeholder="e.g. Laxmikanth Parliament Chapter" />
                    </div>
                    <div class="flex justify-between gap-2" style="grid-column:1/-1">
                      <button type="button" class="btn btn-secondary btn-sm" id="tt-cancel-btn">Cancel</button>
                      <button type="submit" class="btn btn-primary btn-sm">${editingBlock ? 'Update Block' : 'Save Block'}</button>
                    </div>
                  </form>`
                    : ''
                }

                <div class="flex-col gap-2">
                  ${
                    visibleBlocks.length
                      ? visibleBlocks
                          .map(
                            (b) => `
                        <div class="check-row ${b.completed ? 'done' : ''}">
                          <div class="flex items-start gap-3" style="min-width:0">
                            <button type="button" class="check-circle ${b.completed ? 'checked' : ''}" data-tt-check="${esc(b.id)}" data-done="${b.completed ? '1' : '0'}">
                              ${b.completed ? Icons('check', 12) : ''}
                            </button>
                            <div style="min-width:0">
                              <div class="flex items-center gap-2 flex-wrap">
                                <span class="font-mono text-xs text-muted">${esc(b.startTime)}–${esc(b.endTime)}</span>
                                <span class="badge badge-neutral">${esc(b.subject)}</span>
                                ${showAllDays ? `<span class="text-xs text-muted">${esc(b.dayOfWeek)}</span>` : ''}
                              </div>
                              <div class="text-sm font-bold mt-1" style="${b.completed ? 'text-decoration:line-through;color:var(--muted)' : ''}">${esc(b.topic)}</div>
                            </div>
                          </div>
                          <div class="flex items-center gap-1" style="flex-shrink:0">
                            <button type="button" class="btn btn-secondary btn-sm" data-tt-load="${esc(b.id)}" title="Load into Timer">${Icons('play', 11)}</button>
                            <button type="button" class="btn-icon" data-tt-edit="${esc(b.id)}" title="Edit">${Icons('edit', 14)}</button>
                            <button type="button" class="btn-icon danger" data-tt-del="${esc(b.id)}" title="Delete">${Icons('trash', 14)}</button>
                          </div>
                        </div>`
                          )
                          .join('')
                      : `<p class="text-xs text-muted" style="padding:20px;text-align:center">No blocks scheduled for ${todayName}. Click <strong>+ Add Block</strong> to plan your day.</p>`
                  }
                </div>
              </div>`
                : ''
            }
          </section>

          <!-- RECENT STUDY LOGS -->
          ${
            !isStudyMode
              ? `
            <section class="card flex-col gap-3">
              <div class="section-header" style="margin-bottom:0">
                <div>
                  <h2 style="font-size:17px">Recent Study Sessions (${a.total_sessions || 0} focus sessions)</h2>
                  <p class="text-xs text-muted">Open Streamlit Studio for 14-day charts, subject splits & CSV exports.</p>
                </div>
                <a href="${esc(API.getStreamlitUrl())}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">Open Charts ↗</a>
              </div>
              <div class="flex-col gap-2">
                ${
                  sessions.length
                    ? sessions
                        .slice(0, 8)
                        .map(
                          (s) => `
                      <div class="card-sub flex flex-wrap items-center justify-between gap-2" style="padding:11px 14px">
                        <div class="flex flex-wrap items-center gap-2">
                          <span class="badge badge-neutral">${esc(s.subject)}</span>
                          <strong class="text-xs">${esc(s.topic || 'Focus Session')}</strong>
                          <span class="font-mono text-xs text-muted">${s.durationMinutes}m · ${esc(s.sessionType)} · ${esc((s.startTime || '').slice(0, 10))}</span>
                        </div>
                        <button type="button" class="btn-icon danger" data-del-sess="${esc(s.id)}" title="Delete session">${Icons('trash', 14)}</button>
                      </div>`
                        )
                        .join('')
                    : `<p class="text-xs text-muted">No sessions recorded yet. Start your first 25-minute block above!</p>`
                }
              </div>
            </section>`
              : ''
          }
        </div>
      `;

      // Bindings
      document.getElementById('toggle-study-mode').onclick = () => {
        document.body.classList.toggle('study-mode-active');
        draw();
      };

      container.querySelectorAll('[data-preset]').forEach((b) => {
        b.onclick = () => {
          window.TimerController.setPreset(Number(b.dataset.preset), b.dataset.mode);
          draw();
        };
      });

      document.getElementById('timer-subject').onchange = (e) => { t.subject = e.target.value; };
      document.getElementById('timer-topic').oninput = (e) => { t.topic = e.target.value; };

      document.getElementById('timer-toggle').onclick = () => {
        window.TimerController.toggle();
        draw();
      };
      document.getElementById('timer-reset').onclick = () => {
        window.TimerController.reset();
        draw();
      };
      document.getElementById('timer-complete').onclick = async (e) => {
        const btn = e.currentTarget;
        const elapsedSecs = t.targetMinutes * 60 - t.secondsLeft;
        let minsToLog = Math.floor(elapsedSecs / 60);
        if (elapsedSecs < 60) {
          const ok = confirm(`You've only elapsed ${elapsedSecs}s on this timer. Log a manual ${t.targetMinutes}-minute ${t.subject} session anyway?`);
          if (!ok) return;
          minsToLog = t.targetMinutes;
        }
        btn.disabled = true;
        try {
          await window.TimerController.complete(minsToLog);
          draw();
        } finally {
          btn.disabled = false;
        }
      };

      const togDays = document.getElementById('tt-toggle-days');
      if (togDays) togDays.onclick = () => { showAllDays = !showAllDays; draw(); };
      const addBtn = document.getElementById('tt-add-btn');
      if (addBtn) addBtn.onclick = () => { editingBlock = null; addingBlock = !addingBlock; draw(); };
      const cancelBtn = document.getElementById('tt-cancel-btn');
      if (cancelBtn) cancelBtn.onclick = () => { addingBlock = false; editingBlock = null; draw(); };

      const ttForm = document.getElementById('tt-form');
      if (ttForm) {
        ttForm.onsubmit = async (e) => {
          e.preventDefault();
          const fd = new FormData(ttForm);
          const start = fd.get('start_time');
          const end = fd.get('end_time');
          if (end <= start) { toast('End time must be after start time.', 'error'); return; }
          const payload = {
            subject: fd.get('subject'),
            day_of_week: fd.get('day_of_week'),
            start_time: start,
            end_time: end,
            topic: fd.get('topic'),
          };
          try {
            if (editingBlock) await API.updateTimetable(editingBlock.id, payload);
            else await API.createTimetable(payload);
            addingBlock = false;
            editingBlock = null;
            toast('Timetable updated.', 'success');
            draw();
          } catch (err) { toast(err.message, 'error'); }
        };
      }

      container.querySelectorAll('[data-tt-check]').forEach((b) => {
        b.onclick = async () => {
          try {
            await API.updateTimetable(b.dataset.ttCheck, { completed: b.dataset.done !== '1' });
            draw();
          } catch (err) { toast(err.message, 'error'); }
        };
      });
      container.querySelectorAll('[data-tt-load]').forEach((b) => {
        b.onclick = () => {
          const item = timetable.find((x) => x.id === b.dataset.ttLoad);
          if (!item) return;
          window.TimerController.pause();
          t.subject = item.subject;
          t.topic = item.topic;
          t.targetMinutes = 50;
          t.secondsLeft = 50 * 60;
          t.mode = 'Focus';
          toast(`Loaded "${item.subject}" into Focus Timer.`, 'success');
          draw();
        };
      });
      container.querySelectorAll('[data-tt-edit]').forEach((b) => {
        b.onclick = () => {
          editingBlock = timetable.find((x) => x.id === b.dataset.ttEdit) || null;
          addingBlock = true;
          draw();
        };
      });
      container.querySelectorAll('[data-tt-del]').forEach((b) => {
        b.onclick = async () => {
          if (!confirm('Remove this timetable block?')) return;
          try {
            await API.deleteTimetable(b.dataset.ttDel);
            toast('Block removed.', 'success');
            draw();
          } catch (err) { toast(err.message, 'error'); }
        };
      });
      container.querySelectorAll('[data-del-sess]').forEach((b) => {
        b.onclick = async () => {
          if (!confirm('Delete this logged study session?')) return;
          try {
            await API.deleteStudySession(b.dataset.delSess);
            toast('Session deleted.', 'success');
            draw();
          } catch (err) { toast(err.message, 'error'); }
        };
      });
    }

    draw();
  }

  // =========================================================================
  // 7. UNIFIED ACCOUNT & SETTINGS (/profile and /settings)
  // =========================================================================
  async function renderProfile(container) {
    await API.loadWorkspace();
    const p = AppState.profile || {};
    const initial = (p.full_name || 'A').charAt(0).toUpperCase();
    const stages = CANONICAL_STAGES.includes(p.preparation_stage)
      ? CANONICAL_STAGES
      : [p.preparation_stage, ...CANONICAL_STAGES].filter(Boolean);

    container.innerHTML = `
      <div class="page-stack" style="max-width:700px">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="avatar lg">${esc(initial)}</div>
            <div>
              <h1 class="page-title" style="font-size:26px;margin:0">${esc(p.full_name || 'Aspirant')}</h1>
              <p class="text-xs text-muted">${esc(p.email || '')} ${AppState.isDemo ? '· Demo Workspace' : ''}</p>
            </div>
          </div>
          ${
            AppState.authenticated
              ? `<button type="button" class="btn btn-secondary btn-pill btn-sm" id="prof-logout">${Icons('logout', 13)} Log Out</button>`
              : `<a href="/auth" data-link class="btn btn-primary btn-pill btn-sm">Sign In / Sign Up</a>`
          }
        </div>

        <form id="prof-form" class="card flex-col gap-4">
          <h2 style="font-size:17px">Profile & Study Targets</h2>
          <div class="grid grid-2">
            <div class="form-group">
              <label class="form-label">Display Name</label>
              <input type="text" name="full_name" class="input" required value="${esc(p.full_name || '')}" />
            </div>
            <div class="form-group">
              <label class="form-label">Preparation Stage</label>
              <select name="preparation_stage" class="select">
                ${stages.map((s) => `<option value="${esc(s)}" ${p.preparation_stage === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Daily Study Goal (1–16 Hours)</label>
              <input type="number" name="daily_target_hours" class="input" min="1" max="16" required value="${p.daily_target_hours || 4}" />
            </div>
            <div class="form-group">
              <label class="form-label">Target UPSC Attempt Year</label>
              <select name="target_attempt_year" class="select">
                ${['2026', '2027', '2028', '2029', '2030'].map((y) => `<option value="${y}" ${p.target_attempt_year === y ? 'selected' : ''}>UPSC CSE ${y}</option>`).join('')}
              </select>
            </div>
          </div>
          <div><button type="submit" class="btn btn-primary btn-pill">Save Profile & Targets</button></div>
        </form>

        ${
          AppState.authenticated
            ? `
          <form id="pw-form" class="card flex-col gap-3">
            <h2 style="font-size:17px">Change Password</h2>
            <div class="grid grid-2">
              <div class="form-group">
                <label class="form-label">New Password</label>
                <input type="password" name="pw1" class="input" required minlength="6" placeholder="••••••••" />
              </div>
              <div class="form-group">
                <label class="form-label">Confirm Password</label>
                <input type="password" name="pw2" class="input" required minlength="6" placeholder="••••••••" />
              </div>
            </div>
            <div><button type="submit" class="btn btn-secondary btn-pill">Update Password</button></div>
          </form>

          ${
            !AppState.isDemo
              ? `
            <div class="card" style="background:var(--rose-bg);border-color:var(--rose-border)">
              <h3 style="font-size:15px;color:#9F1239">Delete Account</h3>
              <p class="text-xs mt-1" style="color:#881337">Permanently removes your personal workspace, notes, progress, and study logs from SQLite.</p>
              <button type="button" class="btn btn-danger btn-pill btn-sm mt-3" id="del-acc-btn">Delete Account</button>
            </div>`
              : ''
          }`
            : ''
        }
      </div>
    `;

    document.getElementById('prof-form').onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await API.updateProfile({
          full_name: fd.get('full_name'),
          preparation_stage: fd.get('preparation_stage'),
          daily_target_hours: Number(fd.get('daily_target_hours')),
          target_attempt_year: fd.get('target_attempt_year'),
        });
        await API.loadWorkspace();
        window.Router.refreshShell();
        toast('Profile saved.', 'success');
        renderProfile(container);
      } catch (err) { toast(err.message, 'error'); }
    };

    const logoutBtn = document.getElementById('prof-logout');
    if (logoutBtn) {
      logoutBtn.onclick = async () => {
        await API.logout();
        await API.loadWorkspace();
        window.Router.refreshShell();
        toast('Logged out.', 'success');
        window.Router.navigate('/auth');
      };
    }

    const pwForm = document.getElementById('pw-form');
    if (pwForm) {
      pwForm.onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData(pwForm);
        if (fd.get('pw1') !== fd.get('pw2')) { toast('Passwords do not match.', 'error'); return; }
        try {
          await API.updatePassword(fd.get('pw1'));
          pwForm.reset();
          toast('Password updated.', 'success');
        } catch (err) { toast(err.message, 'error'); }
      };
    }

    const delBtn = document.getElementById('del-acc-btn');
    if (delBtn) {
      delBtn.onclick = async () => {
        if (!confirm('Permanently delete your account and all study records?')) return;
        try {
          await API.deleteAccount();
          await API.loadWorkspace();
          window.Router.refreshShell();
          toast('Account deleted.', 'success');
          window.Router.navigate('/');
        } catch (err) { toast(err.message, 'error'); }
      };
    }
  }

  // =========================================================================
  // 8. AUTH (/auth)
  // =========================================================================
  async function renderAuth(container, params) {
    let authMode = params.get('mode') === 'signup' ? 'signup' : 'login';

    function draw() {
      container.innerHTML = `
        <div class="page-stack" style="max-width:420px;margin:20px auto">
          <div style="text-align:center">
            <div class="brand-mark" style="width:40px;height:40px;font-size:17px;border-radius:11px;margin:0 auto">O</div>
            <h1 class="page-title mt-3" style="font-size:26px">${authMode === 'signup' ? 'Create Free Account' : 'Log In to OpenUPSC'}</h1>
            <p class="text-xs text-muted mt-1">Local FastAPI + SQLite account. Your study progress syncs automatically with Streamlit Analytics.</p>
          </div>

          <section class="card flex-col gap-4">
            <div class="segmented w-full" style="display:grid;grid-template-columns:1fr 1fr">
              <button type="button" class="seg-btn ${authMode === 'login' ? 'active' : ''}" data-auth="login">Log In</button>
              <button type="button" class="seg-btn ${authMode === 'signup' ? 'active' : ''}" data-auth="signup">Sign Up</button>
            </div>

            <form id="auth-form" class="flex-col gap-3">
              ${
                authMode === 'signup'
                  ? `<div class="form-group">
                       <label class="form-label">Full Name</label>
                       <input type="text" name="full_name" class="input" required placeholder="e.g. Aarav Sharma" />
                     </div>`
                  : ''
              }
              <div class="form-group">
                <label class="form-label">Email</label>
                <input type="email" name="email" class="input" required placeholder="aspirant@example.com" />
              </div>
              <div class="form-group">
                <label class="form-label">Password (min 6 chars)</label>
                <input type="password" name="password" class="input" required minlength="6" placeholder="••••••••" />
              </div>
              <button type="submit" class="btn btn-primary btn-pill w-full mt-2">
                ${authMode === 'signup' ? 'Create Free Workspace' : 'Log In'}
              </button>
            </form>

            <div style="text-align:center;border-top:1px solid var(--surface-muted);padding-top:12px">
              <button type="button" class="btn btn-secondary btn-pill w-full" id="demo-login-btn">
                Continue as Demo Aspirant (Khushi)
              </button>
            </div>
          </section>
        </div>
      `;

      container.querySelectorAll('[data-auth]').forEach((b) => {
        b.onclick = () => { authMode = b.dataset.auth; draw(); };
      });

      document.getElementById('auth-form').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          if (authMode === 'signup') {
            await API.signup({ full_name: fd.get('full_name'), email: fd.get('email'), password: fd.get('password') });
            toast('Workspace created!', 'success');
          } else {
            await API.login({ email: fd.get('email'), password: fd.get('password') });
            toast('Signed in!', 'success');
          }
          await API.loadWorkspace();
          window.Router.refreshShell();
          window.Router.navigate('/');
        } catch (err) { toast(err.message, 'error'); }
      };

      document.getElementById('demo-login-btn').onclick = async () => {
        try {
          await API.demoLogin();
          await API.loadWorkspace();
          window.Router.refreshShell();
          toast('Signed into Demo Workspace (Khushi).', 'success');
          window.Router.navigate('/');
        } catch (err) { toast(err.message, 'error'); }
      };
    }

    draw();
  }

  return {
    renderHome,
    renderResources,
    renderNCERT,
    renderPYQs,
    renderRoadmaps,
    renderRoadmapDetail,
    renderStudy,
    renderProfile,
    renderAuth,
  };
})();
