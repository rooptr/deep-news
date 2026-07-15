/**
 * Anonymous flashcard sink for the Newspaper app.
 * Deploy as a web app accessible to anyone. No email or user identity is stored.
 */
const MAX_BODY_BYTES = 20000;
const MAX_WRITES_PER_MINUTE = 30;
const MAX_FIELD_LENGTHS = {category: 80, question: 5000, answer: 2000, explanation: 10000, source: 500};

function jsonResponse(body, status) {
  return ContentService.createTextOutput(JSON.stringify({status: status, ...body}))
    .setMimeType(ContentService.MimeType.JSON);
}

function cleanString(value, field) {
  if (typeof value !== 'string' || value.length > MAX_FIELD_LENGTHS[field]) throw new Error('invalid ' + field);
  return value.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '');
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents || e.postData.contents.length > MAX_BODY_BYTES) {
      return jsonResponse({error: 'invalid request body'}, 'error');
    }
    const input = JSON.parse(e.postData.contents);
    const card = {
      category: cleanString(input.category || 'DAILY QUIZ', 'category'),
      question: cleanString(input.question, 'question'),
      answer: cleanString(input.answer, 'answer'),
      explanation: cleanString(input.explanation || '', 'explanation'),
      source: cleanString(input.source || 'Daily Newspaper', 'source')
    };
    if (!card.question || !card.answer) throw new Error('question and answer are required');

    const props = PropertiesService.getScriptProperties();
    const spreadsheetId = props.getProperty('SCRIPT_PROPERTY_SPREADSHEET_ID');
    const sheetName = props.getProperty('SCRIPT_PROPERTY_SHEET_NAME') || 'Flashcards';
    if (!spreadsheetId) throw new Error('server storage is not configured');
    const lock = LockService.getScriptLock();
    lock.waitLock(5000);
    try {
      const cache = CacheService.getScriptCache();
      const writeCount = Number(cache.get('global_write_count') || 0);
      if (writeCount >= MAX_WRITES_PER_MINUTE) {
        return jsonResponse({error: 'rate limit exceeded'}, 'error');
      }
      cache.put('global_write_count', String(writeCount + 1), 60);
      const sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(sheetName);
      if (!sheet) throw new Error('storage sheet is missing');
      sheet.appendRow([new Date(), card.category, card.question, card.answer, card.explanation, card.source]);
    } finally {
      lock.releaseLock();
    }
    return jsonResponse({message: 'saved'}, 'ok');
  } catch (error) {
    console.error(error.message);
    return jsonResponse({error: 'request rejected'}, 'error');
  }
}

function doGet() {
  return jsonResponse({message: 'anonymous flashcard service'}, 'ok');
}
