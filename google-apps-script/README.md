# Anonymous single-user flashcard service

1. Create a private Google Sheet with a `Flashcards` tab.
2. Add columns: `created_at`, `category`, `question`, `answer`, `explanation`, `source`.
3. Open **Extensions → Apps Script**, paste in `Code.gs`, and set Script Properties:
   - `SCRIPT_PROPERTY_SPREADSHEET_ID`: the Sheet ID
   - `SCRIPT_PROPERTY_SHEET_NAME`: `Flashcards`
4. Deploy as a Web App:
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Authorize the Spreadsheet permission request and deploy a new version.
6. Replace the old Apps Script URL in `index.html` with the new deployment URL.
7. Test from a private browser window; saving must work without a Google login.

The Sheet must remain private. The Sheet ID is stored only in Apps Script properties, never in the website. The Apps Script URL is necessarily visible in browser JavaScript because the static site must call it. No email or user identity is collected. This endpoint is public, so validation and the global write limit reduce abuse but cannot prevent a determined attacker from submitting requests.
