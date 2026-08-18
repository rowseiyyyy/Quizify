# TODO: Replace Mock Dashboard Data with Real User Activity

## Frontend (`index.html`)
- [x] Remove hardcoded mock state defaults (`state.stats`, `state.uploads`, `state.history`, `state.subjectsBSCS`, `state.subjectsBSIT`, `state.questionBank`, `state.flashcardBank`)
- [x] Create `loadDashboardStats()` to fetch real data from `GET /analytics/me`
- [x] Create `loadAnalytics()` to fetch and store real analytics data
- [x] Create `loadAdminDashboard()` to fetch real stats from `GET /admin/dashboard`
- [x] Update `renderers.dashboard()` to use real stats + real uploads, with empty states
- [x] Update `renderers.analytics()` to use real analytics data (weekly scores, subject performance, strongest/weakest, AI insight), with empty states
- [x] Update `renderers.history()` to use real quiz history, with empty state
- [x] Update `renderers.upload()` to use real uploads, with empty state
- [x] Update `renderers.admin()` to use real admin dashboard stats
- [x] Wire `enterApp()` and page navigation to load real data on demand
- [x] Ensure `loadUploads()` and `loadHistory()` re-render current page and handle empty data
- [x] Remove hardcoded landing-page marketing stats (2,400+, 860+, 94%)
- [x] Remove mock "18 Days / 76%" streak widget on landing page
- [x] Reset state on logout so stale data never persists between accounts

## Verification
- [x] Backend smoke test passes (auth, uploads, quizzes, flashcards, analytics, admin)
- [x] Frontend JavaScript syntax validated with Node
- [x] Confirm all mock/hardcoded dashboard values removed from source

