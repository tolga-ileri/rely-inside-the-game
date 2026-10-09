# Azure AI Foundry integration

## Status

- Implemented: `apps/api/rely_brain/llm.py` (`FoundryProvider`) using the `azure-ai-inference` SDK
  (`ChatCompletionsClient.complete`, `response_format="json_object"`, `stream=True` for token streaming).
- Tested: `apps/api/tests/test_llm_foundry.py` and the eval suite use injected fake clients. They cover valid JSON,
  invented numbers (regeneration), unknown players (fallback), timeouts, non-JSON replies, cache hits and streaming.
- **Not yet run against a live Foundry endpoint.** No credentials were available while this was built. The default
  `AI_PROVIDER=none` uses deterministic templates, so the demo never depends on the network.

## Configuration

Set these in your shell or in a git-ignored `.env`:

```
AI_PROVIDER=microsoft_foundry
FOUNDRY_ENDPOINT=https://<resource>.services.ai.azure.com/models
FOUNDRY_API_KEY=<key>
FOUNDRY_MODEL=<deployment name, e.g. gpt-4o-mini>
FOUNDRY_TIMEOUT_SECONDS=12
```

On Azure Container Apps the key is passed as a secure Bicep parameter and stored as a Container Apps secret
(`infra/azure/main.bicep`).

## How the Narrative agent uses Foundry

1. Input: locale-invariant **facts** for one moment (numbers, names, windows), the persona style guide, the target
   language, the list of allowed entities and the verified recommendations. No raw event stream is sent.
2. The system prompt requires JSON `{headline, explanation, bullets}`, only numbers from FACTS, only names from ENTITIES,
   and no score predictions.
3. The Evidence Verifier checks the reply (numeric grounding + entity validation). On failure, one regeneration is
   requested with the issues listed. If it fails again, or if the call errors or times out, the grounded template is used
   and the trace shows `status=fallback`.
4. Results are cached by `sha256(state_hash | moment | persona | locale | model)`.
5. `GET /api/matches/{id}/explain/stream` streams tokens through SSE when the provider supports streaming. The final
   event always carries the verified result.

## Verifying a live run

1. Set the variables above and start the API.
2. `GET /ready` should show `"ai_provider": "microsoft_foundry"` and the model name.
3. Open the app, click *Explain Moment*, and check the **Agent Trace**: the `narrative` row should show provider
   `microsoft_foundry`, the model, and `fallback: no`. The Why panel badge then reads "Foundry · verified".
4. Run `python -m evals.run_evals`. It stays offline by design; add live Foundry cases only once credentials exist.
