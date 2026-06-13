# Google Workspace MCP Server (Python)

A FastAPI-based local server that acts as a secure tool bridge to Google Docs and Gmail via OAuth 2.0. Before performing any write or compose actions, the server displays the payload in the terminal and blocks for user confirmation.

---

## Setup Instructions

### 1. Enable APIs in Google Cloud Console
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Search for and enable the following APIs:
   - **Google Docs API**
   - **Gmail API**
4. Configure the **OAuth Consent Screen**:
   - Set User Type to **External** (or Internal if inside an organization).
   - Add the scopes:
     - `https://www.googleapis.com/auth/documents`
     - `https://www.googleapis.com/auth/gmail.compose`
   - Add your test email address as a **Test User** (required while in testing status).
5. Create credentials:
   - Go to the **Credentials** page.
   - Click **Create Credentials** -> **OAuth Client ID**.
   - Select application type: **Desktop App**.
   - Click **Create**, then download the client secrets JSON file.
   - Save the downloaded file inside this directory as `credentials.json`.

### 2. Install Dependencies
Create a virtual environment and install the required Python packages:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

---

## Running the Server

Start the FastAPI application:

```bash
python server.py
```

### Authentication Flow
1. On the first run, the server will detect that `token.json` is missing and automatically launch a Google OAuth login screen in your default web browser.
2. Log in using your registered Google test user email.
3. Click "Continue" through the safety warnings (since the app is unverified).
4. Once completed, a `token.json` file is saved in this directory. Subsequent runs will use this token directly and bypass browser login.

---

## API Endpoints

### 1. Append to Google Doc
Appends text or executes structured styling requests at the end of the document.

- **URL:** `POST /append_to_doc`
- **Payload Format (Plain Text):**
```json
{
  "doc_id": "YOUR_GOOGLE_DOC_ID",
  "content": "Line of text to append\n"
}
```
- **Payload Format (Structured Styles):**
```json
{
  "doc_id": "YOUR_GOOGLE_DOC_ID",
  "content": "[{\"insertText\":{\"text\":\"Theme Heading\\n\",\"endOfSegmentLocation\":{}}},{\"updateParagraphStyle\":{\"paragraphStyle\":{\"namedStyleType\":\"HEADING_3\"},\"fields\":\"namedStyleType\",\"range\":{\"startIndex\":1,\"endIndex\":14}}}]"
}
```

### 2. Create Email Draft
Creates a draft inside your Gmail account.

- **URL:** `POST /create_email_draft`
- **Payload Format:**
```json
{
  "to": ["stakeholder1@example.com", "stakeholder2@example.com"],
  "subject": "Groww Weekly Pulse — 2026-W24",
  "body": "Optional plain text body",
  "html_body": "<div><h2>HTML Teaser</h2><p>Teaser details...</p></div>",
  "text_body": "Plain text teaser details..."
}
```

---

## Console Approval Gate
When a POST request is received, the server blocks execution and displays an approval request in the terminal:

```text
==================================================
ACTION REQUESTED: append_to_doc
PAYLOAD:
{
  "doc_id": "YOUR_GOOGLE_DOC_ID",
  "content": "Line of text to append\n"
}
==================================================
Approve? (y/n): 
```

Only typing `y` or `yes` will execute the Google API request. Any other input returns an HTTP 403 Forbidden error to the requester.
