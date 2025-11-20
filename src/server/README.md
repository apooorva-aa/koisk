# koisk proxy

Small Node/Express proxy to keep your Gemini / Generative Language API key on the server. Designed to run on a Raspberry Pi 4 or any lightweight host.

Prereqs
- Node.js 18+ (or Node 16 with global fetch polyfill)
- npm

Install

```powershell
cd src/server
npm install
```

Run (PowerShell)

```powershell
$env:GEMINI_API_KEY = "your_real_api_key_here"
node proxy.js
```

Run (Linux / Raspberry Pi)

```bash
export GEMINI_API_KEY="your_real_api_key_here"
node proxy.js
```

Testing with curl

```bash
curl -X POST http://localhost:3000/api/generate -H "Content-Type: application/json" -d '{"prompt":"Hello from test"}'
```

Notes
- The proxy reads `GEMINI_API_KEY` (or `OPENAI_API_KEY`) from environment variables.
- For Google Generative Language API the endpoint used defaults to `text-bison-001` but can be changed by setting `GEMINI_ENDPOINT`.
- Keep this server behind HTTPS in production and restrict CORS origin.
- Service-account authentication via `google-auth-library` is optional. To enable it, install the library in `src/server`:

	```powershell
	cd src/server
	npm install google-auth-library
	```

	Then set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your service account JSON file before starting the proxy.

Model selection
----------------
- You can change which model is used without editing `proxy.js`:
	- Set `GEMINI_MODEL` to the model id you want (for example, a flash model). The proxy builds the endpoint automatically.
		- PowerShell:
			```powershell
			$env:GEMINI_MODEL = "gemini-flash-1"
			npm start
			```
		- Bash (Raspberry Pi):
			```bash
			export GEMINI_MODEL="gemini-flash-1"
			npm start
			```
	- Or set the full endpoint URL directly with `GEMINI_ENDPOINT` (e.g. `https://generativelanguage.googleapis.com/v1/models/gemini-flash-1:generate`).

Examples: set key + model (PowerShell)
```powershell
$env:GEMINI_API_KEY = "YOUR_KEY"
$env:GEMINI_MODEL = "gemini-flash-1"
npm start
```

Examples: set key + model (bash)
```bash
export GEMINI_API_KEY="YOUR_KEY"
export GEMINI_MODEL="gemini-flash-1"
npm start
```

Note: replace `gemini-flash-1` with the exact model identifier you have access to. If you get 404 from the provider, try switching API version or confirm model id in provider docs.
