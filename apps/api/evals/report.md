# Rely Match Brain - AI evaluation report

Mode: **full**, matches: elt-hcf-balanced, kmr-hcf-high-press, wva-kmr-late-comeback, kmr-elt-red-card, hcf-wva-tactical-shift

> Offline evaluation: deterministic templates and scripted fake LLM replies. No Azure AI Foundry calls were made.

| Category | Passed | Total |
|---|---|---|
| turning point explanation | 5 | 5 |
| numeric grounding | 10 | 10 |
| unsupported event rejection | 10 | 10 |
| persona style | 20 | 20 |
| language adherence | 10 | 10 |
| recommendation grounding | 5 | 5 |
| agent failure fallback | 25 | 25 |

**Overall: 85/85 cases passed.**

## Cases

### turning point explanation
- PASS `elt-hcf-balanced:sub_shift` sub_shift @ 4021s, numbers ['1', '17', '3', '77']
- PASS `kmr-hcf-high-press:sub_shift` sub_shift @ 3901s, numbers ['0', '33', '64']
- PASS `wva-kmr-late-comeback:sub_shift` sub_shift @ 4390s, numbers ['1', '22', '55']
- PASS `kmr-elt-red-card:red_card` red_card @ 2281s, numbers ['34', '80']
- PASS `hcf-wva-tactical-shift:sub_shift` sub_shift @ 3603s, numbers ['1', '25', '3', '75']

### numeric grounding
- PASS `elt-hcf-balanced:templates x12` all numbers grounded
- PASS `elt-hcf-balanced:adversarial_numbers` final source=template
- PASS `kmr-hcf-high-press:templates x12` all numbers grounded
- PASS `kmr-hcf-high-press:adversarial_numbers` final source=template
- PASS `wva-kmr-late-comeback:templates x12` all numbers grounded
- PASS `wva-kmr-late-comeback:adversarial_numbers` final source=template
- PASS `kmr-elt-red-card:templates x12` all numbers grounded
- PASS `kmr-elt-red-card:adversarial_numbers` final source=template
- PASS `hcf-wva-tactical-shift:templates x12` all numbers grounded
- PASS `hcf-wva-tactical-shift:adversarial_numbers` final source=template

### unsupported event rejection
- PASS `elt-hcf-balanced:fabricated` rejected=3
- PASS `elt-hcf-balanced:unknown_player_text` template
- PASS `kmr-hcf-high-press:fabricated` rejected=3
- PASS `kmr-hcf-high-press:unknown_player_text` template
- PASS `wva-kmr-late-comeback:fabricated` rejected=3
- PASS `wva-kmr-late-comeback:unknown_player_text` template
- PASS `kmr-elt-red-card:fabricated` rejected=3
- PASS `kmr-elt-red-card:unknown_player_text` template
- PASS `hcf-wva-tactical-shift:fabricated` rejected=3
- PASS `hcf-wva-tactical-shift:unknown_player_text` template

### persona style
- PASS `elt-hcf-balanced:coach`
- PASS `elt-hcf-balanced:analyst`
- PASS `elt-hcf-balanced:broadcaster`
- PASS `elt-hcf-balanced:fan` Since Felix Aukland came on, Elmstead Town keep attacking down the right.
- PASS `kmr-hcf-high-press:coach`
- PASS `kmr-hcf-high-press:analyst`
- PASS `kmr-hcf-high-press:broadcaster`
- PASS `kmr-hcf-high-press:fan` Since Jude Kerrigan came on, Kingsmere Rovers keep attacking down the centre.
- PASS `wva-kmr-late-comeback:coach`
- PASS `wva-kmr-late-comeback:analyst`
- PASS `wva-kmr-late-comeback:broadcaster`
- PASS `wva-kmr-late-comeback:fan` Since Rafa Corvo came on, Westvale Athletic keep attacking down the centre.
- PASS `kmr-elt-red-card:coach`
- PASS `kmr-elt-red-card:analyst`
- PASS `kmr-elt-red-card:broadcaster`
- PASS `kmr-elt-red-card:fan` Elmstead Town are down to ten and Kingsmere Rovers are camped in their half.
- PASS `hcf-wva-tactical-shift:coach`
- PASS `hcf-wva-tactical-shift:analyst`
- PASS `hcf-wva-tactical-shift:broadcaster`
- PASS `hcf-wva-tactical-shift:fan` Since Kai Okafor came on, Harbour City FC keep attacking down the right.

### language adherence
- PASS `elt-hcf-balanced:tr` english stopwords=0, numbers identical=True
- PASS `elt-hcf-balanced:es` english stopwords=0, numbers identical=True
- PASS `kmr-hcf-high-press:tr` english stopwords=0, numbers identical=True
- PASS `kmr-hcf-high-press:es` english stopwords=0, numbers identical=True
- PASS `wva-kmr-late-comeback:tr` english stopwords=0, numbers identical=True
- PASS `wva-kmr-late-comeback:es` english stopwords=0, numbers identical=True
- PASS `kmr-elt-red-card:tr` english stopwords=0, numbers identical=True
- PASS `kmr-elt-red-card:es` english stopwords=0, numbers identical=True
- PASS `hcf-wva-tactical-shift:tr` english stopwords=0, numbers identical=True
- PASS `hcf-wva-tactical-shift:es` english stopwords=0, numbers identical=True

### recommendation grounding
- PASS `elt-hcf-balanced:recommendations` 6 recommendations, all verified=True
- PASS `kmr-hcf-high-press:recommendations` 6 recommendations, all verified=True
- PASS `wva-kmr-late-comeback:recommendations` 6 recommendations, all verified=True
- PASS `kmr-elt-red-card:recommendations` 6 recommendations, all verified=True
- PASS `hcf-wva-tactical-shift:recommendations` 4 recommendations, all verified=True

### agent failure fallback
- PASS `elt-hcf-balanced:event_analyst`
- PASS `elt-hcf-balanced:tactical_analyst`
- PASS `elt-hcf-balanced:evidence_verifier`
- PASS `elt-hcf-balanced:narrative`
- PASS `elt-hcf-balanced:foundry_timeout`
- PASS `kmr-hcf-high-press:event_analyst`
- PASS `kmr-hcf-high-press:tactical_analyst`
- PASS `kmr-hcf-high-press:evidence_verifier`
- PASS `kmr-hcf-high-press:narrative`
- PASS `kmr-hcf-high-press:foundry_timeout`
- PASS `wva-kmr-late-comeback:event_analyst`
- PASS `wva-kmr-late-comeback:tactical_analyst`
- PASS `wva-kmr-late-comeback:evidence_verifier`
- PASS `wva-kmr-late-comeback:narrative`
- PASS `wva-kmr-late-comeback:foundry_timeout`
- PASS `kmr-elt-red-card:event_analyst`
- PASS `kmr-elt-red-card:tactical_analyst`
- PASS `kmr-elt-red-card:evidence_verifier`
- PASS `kmr-elt-red-card:narrative`
- PASS `kmr-elt-red-card:foundry_timeout`
- PASS `hcf-wva-tactical-shift:event_analyst`
- PASS `hcf-wva-tactical-shift:tactical_analyst`
- PASS `hcf-wva-tactical-shift:evidence_verifier`
- PASS `hcf-wva-tactical-shift:narrative`
- PASS `hcf-wva-tactical-shift:foundry_timeout`
