/* OpenUPSC FastAPI REST Client & Reactive State Cache */
window.AppState = {
  authenticated: false,
  isDemo: true,
  profile: null,
  progressMap: {},
  bookmarkedIds: [],
  notes: {},
  pyqAttempts: {},
  timetable: [],
  studySessions: [],
  analytics: null,
  // Cached curriculum & catalog datasets
  ncert: null,
  roadmaps: null,
  resources: null,
  pyqs: null,
  questionPapers: null,
  currentAffairs: null,
  // Global Focus Timer state (survives route navigation)
  timer: {
    mode: 'Focus',
    targetMinutes: 25,
    secondsLeft: 25 * 60,
    isRunning: false,
    subject: 'Indian Polity',
    topic: 'Fundamental Rights & Constitutional Framework',
    resourceId: '',
    startedAt: null,
    intervalId: null,
  },
};

window.API = (function () {
  function getStreamlitUrl() {
    const proto = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const host = window.location.hostname || 'localhost';
    return `${proto}//${host}:8501`;
  }

  async function request(url, options = {}) {
    const config = {
      ...options,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    };
    const res = await fetch(url, config);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      let message = `Request failed (${res.status})`;
      if (Array.isArray(data.detail)) {
        message = data.detail.map((e) => e.msg || String(e)).join('; ');
      } else if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (data.message) {
        message = data.message;
      }
      throw new Error(message);
    }
    return data;
  }

  return {
    getStreamlitUrl,
    async loadWorkspace() {
      const data = await request('/api/workspace');
      AppState.authenticated = data.authenticated;
      AppState.isDemo = data.is_demo;
      AppState.profile = data.profile;
      AppState.progressMap = data.progressMap || {};
      AppState.bookmarkedIds = data.bookmarkedIds || [];
      AppState.notes = data.notes || {};
      AppState.pyqAttempts = data.pyqAttempts || {};
      AppState.timetable = data.timetable || [];
      AppState.studySessions = data.studySessions || [];
      AppState.analytics = data.analytics || null;
      return data;
    },

    async getNCERT(force = false) {
      if (!AppState.ncert || force) {
        const data = await request('/api/ncert');
        AppState.ncert = data.books;
      }
      return AppState.ncert;
    },

    async getRoadmaps(force = false) {
      if (!AppState.roadmaps || force) {
        const data = await request('/api/roadmaps');
        AppState.roadmaps = data.roadmaps;
      }
      return AppState.roadmaps;
    },

    async getResources(force = false) {
      if (!AppState.resources || force) {
        const data = await request('/api/resources');
        AppState.resources = data.resources;
      }
      return AppState.resources;
    },

    async getPYQsAndPapers(force = false) {
      if (!AppState.pyqs || !AppState.questionPapers || force) {
        const data = await request('/api/pyqs');
        AppState.pyqs = data.pyqs || [];
        AppState.questionPapers = data.questionPapers || [];
      }
      return { pyqs: AppState.pyqs, questionPapers: AppState.questionPapers };
    },

    async getCurrentAffairs(force = false) {
      if (!AppState.currentAffairs || force) {
        const data = await request('/api/current-affairs');
        AppState.currentAffairs = data.categories;
      }
      return AppState.currentAffairs;
    },

    search(q) {
      return request(`/api/search?q=${encodeURIComponent(q)}`);
    },

    // Auth & Profile
    signup(payload) {
      return request('/api/auth/signup', { method: 'POST', body: JSON.stringify(payload) });
    },
    login(payload) {
      return request('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
    },
    demoLogin() {
      return request('/api/auth/demo', { method: 'POST' });
    },
    logout() {
      return request('/api/auth/logout', { method: 'POST' });
    },
    updateProfile(payload) {
      return request('/api/profile', { method: 'PUT', body: JSON.stringify(payload) });
    },
    updatePassword(new_password) {
      return request('/api/auth/password', { method: 'PUT', body: JSON.stringify({ new_password }) });
    },
    deleteAccount() {
      return request('/api/auth/account', { method: 'DELETE' });
    },

    // Progress, Notes, Bookmarks, PYQ Attempts
    async updateProgress(itemId, progressPercentage) {
      const res = await request(`/api/progress/${encodeURIComponent(itemId)}`, {
        method: 'PUT',
        body: JSON.stringify({ progress_percentage: Number(progressPercentage) }),
      });
      AppState.progressMap[itemId] = Number(progressPercentage);
      if (res.analytics) AppState.analytics = res.analytics;
      return res;
    },

    async saveNote(itemId, content, itemTitle = '', itemCategory = '') {
      const res = await request(`/api/notes/${encodeURIComponent(itemId)}`, {
        method: 'PUT',
        body: JSON.stringify({ content, item_title: itemTitle, item_category: itemCategory }),
      });
      AppState.notes[itemId] = content;
      return res;
    },

    async toggleBookmark(resourceId) {
      const res = await request(`/api/bookmarks/${encodeURIComponent(resourceId)}/toggle`, {
        method: 'POST',
      });
      AppState.bookmarkedIds = res.bookmarkedIds || [];
      return res;
    },

    async recordPyqAttempt(payload) {
      const res = await request('/api/pyq-attempts', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      AppState.pyqAttempts[payload.pyq_id] = {
        selectedOption: payload.selected_option,
        isCorrect: payload.is_correct,
      };
      if (res.analytics) AppState.analytics = res.analytics;
      return res;
    },

    async resetPyqAttempts() {
      const res = await request('/api/pyq-attempts', { method: 'DELETE' });
      AppState.pyqAttempts = {};
      if (res.analytics) AppState.analytics = res.analytics;
      return res;
    },

    // Study sessions
    async addStudySession(payload) {
      const res = await request('/api/study-sessions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      await this.loadWorkspace();
      return res;
    },

    async deleteStudySession(id) {
      const res = await request(`/api/study-sessions/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
      await this.loadWorkspace();
      return res;
    },

    // Timetable
    async createTimetable(payload) {
      const res = await request('/api/timetable', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      await this.loadWorkspace();
      return res;
    },

    async updateTimetable(id, payload) {
      const res = await request(`/api/timetable/${encodeURIComponent(id)}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      await this.loadWorkspace();
      return res;
    },

    async deleteTimetable(id) {
      const res = await request(`/api/timetable/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
      await this.loadWorkspace();
      return res;
    },

    submitSuggestion(payload) {
      return request('/api/suggestions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
  };
})();
