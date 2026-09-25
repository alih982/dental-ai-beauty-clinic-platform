# Fix CORS SystemCheckError for makemigrations

## Plan Steps
- [x] 1. Create this TODO.md
- [x] 2. Edit backend/config/dynamic_settings.py (fix CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS strings)
- [x] 3. Edit backend/config/dynamic_settings_fixed.py (remove bare 'magicai.runflare.run')
- [x] 4. Investigated failure: Issue in backend/.env line 10: CORS_ALLOWED_ORIGINS=...magicai.runflare.run (bare). Backups same.
- [x] 5. Confirmed via grep .env*: culprit found.
- [ ] 6. Fix .env by replacing bare 'magicai.runflare.run' → 'http://magicai.runflare.run'
- [ ] 7. Retest: cd backend && python3 manage.py check
- [ ] 8. Update server .env similarly, complete task
- [ ] 5. Update TODO with test results
- [ ] 6. Complete task
