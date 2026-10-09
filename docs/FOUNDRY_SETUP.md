# Microsoft Foundry activation checklist

Status: **the Foundry provider is implemented and tested with stand-in clients. A real Foundry call has not been made.**
Nothing in this repository has been run against an Azure AI Foundry deployment. This guide is how to switch one on and
prove it works.

Rely Match Brain works without Foundry. The default mode (`AI_PROVIDER=none`) produces the same facts and grounded
template narratives with no network access, so the demo never depends on a provider being available.

## 1. What you need

| Requirement | Notes |
|---|---|
| Azure subscription | Any subscription where you can create an AI resource. |
| Azure AI Foundry project | Create it in the Azure portal. Choose your own name and region. |
| A model deployment in that project | Pick a chat model that supports JSON output. Choose the **deployment name** yourself. |
| Model inference endpoint and key | Copy both from the project's model deployment or endpoint page. |

Resource names, deployment names and endpoint hostnames are yours to choose. This repository does not assume any.

## 2. Environment variables

Set these in `.env` at the repository root (gitignored) or in your container environment.

| Variable | Required | Meaning |
|---|---|---|
| `AI_PROVIDER` | yes | `none` (templates, default) or `microsoft_foundry`. |
| `FOUNDRY_ENDPOINT` | when Foundry is on | The model inference endpoint from your project. The `.env.example` value is a placeholder shape; use the exact URL your portal shows. |
| `FOUNDRY_API_KEY` | when Foundry is on | Secret. Never commit it. |
| `FOUNDRY_MODEL` | when Foundry is on | The **deployment name** you created. The code default (`gpt-4o-mini`) is only an example; set your own. |
| `FOUNDRY_TIMEOUT_SECONDS` | no | Per-call timeout. Default `12`. A timeout falls back to templates. |

Only `rely_brain/llm.py` reads these variables or imports the Azure SDK. Route handlers and agents go through the
provider interface (`complete_json` for structured output, `stream_text` for streamed narrative).

## 3. Local setup

```bash
cp .env.example .env          # then edit .env; do not commit it
cd apps/api
python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate elsewhere
pip install -r requirements-dev.txt
uvicorn main:app --host 127.0.0.1 --port 8100
```

Then, in another terminal, `cd apps/web && pnpm install && pnpm dev`, and open http://127.0.0.1:3100.

## 4. Switch between modes

**Template mode (default, no network):**

```bash
AI_PROVIDER=none
```

**Microsoft Foundry mode:**

```bash
AI_PROVIDER=microsoft_foundry
FOUNDRY_ENDPOINT=<your endpoint>
FOUNDRY_API_KEY=<your key>
FOUNDRY_MODEL=<your deployment name>
```

Restart the API after changing these. The API reads them at startup.

**Fallback behaviour:** if Foundry is unreachable, times out, returns something that is not valid structured output, or
contains a number, score, player name or causal claim that the verifier cannot ground, the narrative falls back to the
template. The explanation still appears, labelled as a template, and the structured findings are unaffected.

## 5. Verify a real call

The API marks every narrative with its source. `source: "llm"` means the text came from Foundry and passed grounding
checks. `source: "template"` means it did not.

1. Start the API with `AI_PROVIDER=microsoft_foundry` and your settings.
2. Request the flagship moment (`until` is in seconds; 3603 is the 60:03 turning point):

   ```bash
   curl "http://127.0.0.1:8100/api/matches/hcf-wva-tactical-shift/explain?until=3603&persona=analyst&locale=en"
   ```

3. In the JSON response, check `narrative.source`. It should be `"llm"`.
4. In the same response, check `trace`. The entry for the `narrative` agent carries `provider` and `model`. A
   `"template"` source with `status: "fallback"` means the call failed; read the API log line for that request.
5. For a deliberately hostile check, call the same URL with `locale=tr` and `persona=fan`. The explanation should
   contain no numbers that are absent from the response's `verification` facts.

Expected outcome for a working setup: `narrative.source` is `"llm"`, `verification.coverage` is unchanged from the
template run (facts do not depend on the model), and the `narrative` trace entry has `status: "ok"`.

If you see `"template"` every time, the most likely causes are a wrong endpoint, a deployment name that does not match
`FOUNDRY_MODEL`, an invalid key, or a model that cannot return JSON.

## 6. Cost and limits

Narratives are cached per match state, moment, persona, locale and model, so repeat requests do not call Foundry again.
Requests are bounded by `FOUNDRY_TIMEOUT_SECONDS`. Check your own deployment's quota and pricing in the Azure portal;
this repository does not estimate cost.

## 7. What is and is not claimed

- Implemented: the provider, the structured-output path, streaming, caching, timeouts, template fallback and the trace.
- Tested: with fake clients and scripted replies (the evaluation suite runs offline).
- Not yet verified: any real Foundry call, its latency, its output quality, or its cost.
