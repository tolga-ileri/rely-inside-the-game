"use client";
import { useEffect, useState } from "react";
import type { Dict } from "@/lib/i18n";
import { clock } from "@/lib/playback";
import type { AgentTrace, ExplainResponse, LiveResponse, Moment, Persona, Recap, TacticalResponse, Verification, WhatIf, WindowMetrics } from "@/lib/types";
import { PERSONAS } from "@/lib/types";
import { PitchGrass, PitchLines } from "./Pitch";

const pct = (v: number) => `${Math.round(v * 100)}%`;

function shortId(id: string, demo: boolean) {
  return demo ? `#${id.slice(-5)}` : id;
}

export function PersonaLens({ L, persona, onPersona }: { L: Dict; persona: Persona; onPersona: (p: Persona) => void }) {
  return (
    <div className="flex items-center gap-2" data-testid="persona-lens">
      <span className="text-meta uppercase tracking-wider text-ink-400">{L.lens}</span>
      <div className="flex rounded-lg border border-shell-600 bg-shell-850 p-0.5">
        {PERSONAS.map((p) => (
          <button key={p} aria-pressed={persona === p} onClick={() => onPersona(p)}
            className={`rounded-md px-2.5 py-1 text-meta font-semibold ${persona === p ? "bg-rely-600 text-white" : "text-ink-300 hover:text-ink-50"}`}>{L.persona[p]}</button>
        ))}
      </div>
    </div>
  );
}

function metricRows(m: Moment, w: WindowMetrics, L: Dict): [string, string][] {
  const ch = (m.params.channel as string) || null;
  const rows: [string, string][] = [];
  if (m.type === "sub_shift" && ch) {
    const n = w[`prog_${ch}` as keyof WindowMetrics] as number;
    rows.push([`${L.channels[ch as "L"]} · ${L.progressive}`, `${n}/${w.progressive_actions} (${w.progressive_actions ? pct(n / w.progressive_actions) : "0%"})`]);
  }
  if (m.type === "channel_dominance" && ch) {
    const n = w[`entries_${ch}` as keyof WindowMetrics] as number;
    rows.push([`${L.entries} · ${L.channels[ch as "L"]}`, `${n}/${w.final_third_entries}`]);
  }
  rows.push([L.passShare, pct(w.pass_share)]);
  rows.push([L.entries, `${w.final_third_entries} (L ${w.entries_L} · C ${w.entries_C} · R ${w.entries_R})`]);
  rows.push([L.shots, `${w.shots} (${w.shots_on_target})`]);
  rows.push([L.box, String(w.box_entries)]);
  rows.push([L.highPress, String(w.high_pressures)]);
  return rows;
}

function WindowCard({ title, w, m, L, accent }: { title: string; w: WindowMetrics | null; m: Moment; L: Dict; accent?: boolean }) {
  return (
    <div className={`rounded-lg border p-2.5 ${accent ? "border-rely-600/60 bg-rely-600/5" : "border-shell-700 bg-shell-850"}`}>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-meta font-bold uppercase tracking-wider text-ink-300">{title}</span>
        {w && <span className="font-mono text-[11px] text-ink-400">{clock(w.start)}–{clock(w.end)}</span>}
      </div>
      {w ? (
        <dl className="space-y-0.5">
          {metricRows(m, w, L).map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2 text-[12.5px] leading-5"><dt className="min-w-0 truncate text-ink-300" title={k}>{k}</dt><dd className="whitespace-nowrap font-semibold tabular-nums text-ink-50">{v}</dd></div>
          ))}
        </dl>
      ) : <div className="text-meta text-ink-400">—</div>}
    </div>
  );
}

export function WhyPanel({ L, ex, persona, onPersona, playerNames }: {
  L: Dict; ex: ExplainResponse; persona: Persona; onPersona: (p: Persona) => void; playerNames: Record<string, string>;
}) {
  const m = ex.moment;
  const n = ex.narrative;
  const trig = m.trigger;
  const trigText = trig.event_type === "Substitution"
    ? `${clock(m.timestamp)} · ${playerNames[trig.player_in as string] ?? ""} ⇄ ${playerNames[trig.player_id as string] ?? ""}`
    : trig.event_type === "Card" ? `${clock(m.timestamp)} · ${playerNames[trig.player_id as string] ?? ""} 🟥`
      : `${clock(m.detected_at)} · ${String(trig.description ?? "")}`;
  return (
    <div className="space-y-3" data-testid="why-panel">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-meta font-bold uppercase tracking-wider text-rely-400">{L.why}</div>
          <h2 className="mt-0.5 text-[19px] font-bold leading-tight text-ink-50">{m.title_localized}</h2>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-meta text-ink-300">
            <span className="rounded bg-shell-700 px-1.5 py-0.5 font-mono">{m.clock}</span>
            <span className={`rounded px-1.5 py-0.5 font-bold uppercase ${m.severity === "high" ? "bg-rely-600 text-white" : "bg-warn/20 text-warn"}`}>{m.severity}</span>
            <span>{L.confidence} <b className="text-ink-50">{Math.round(m.confidence * 100)}%</b></span>
            {!m.after_window_complete && <span className="text-ink-400">· {L.openWindow}</span>}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-stretch gap-2">
        <WindowCard title={L.before} w={m.before_state} m={m} L={L} />
        <div className="flex w-[118px] flex-col items-center justify-center rounded-lg border border-shell-600 bg-shell-800 p-2 text-center">
          <div className="text-meta font-bold uppercase tracking-wider text-rely-400">{L.trigger}</div>
          <div className="mt-1 text-[12px] leading-4 text-ink-50">{trigText}</div>
        </div>
        <WindowCard title={L.after} w={m.after_state} m={m} L={L} accent />
      </div>
      <div className="rounded-lg border border-shell-700 bg-shell-850 p-3">
        <div className="mb-2 flex items-center justify-between gap-2">
          <PersonaLens L={L} persona={persona} onPersona={onPersona} />
          {n && <span className="rounded bg-positive/15 px-1.5 py-0.5 text-[11px] font-semibold text-positive">{n.source === "llm" ? "Foundry" : "Template"} · verified</span>}
        </div>
        <div className="mb-1 text-[11px] text-ink-400">{L.sameEvidence}</div>
        {n ? (
          <div data-testid="narrative">
            <div className="text-[15px] font-semibold text-ink-50">{n.headline}</div>
            <p className="mt-1 text-[13.5px] leading-relaxed text-ink-200">{n.explanation}</p>
            {n.bullets.length > 0 && <ul className="mt-1.5 space-y-1">{n.bullets.map((b) => <li key={b} className="flex gap-2 text-[13px] text-ink-200"><span className="text-rely-400">▸</span>{b}</li>)}</ul>}
          </div>
        ) : (
          <div className="rounded-md border border-warn/40 bg-warn/10 p-2 text-dense text-warn" data-testid="unavailable">{L.unavailable}. {ex.explanation_unavailable}</div>
        )}
      </div>
      {ex.claims.length > 0 && (
        <div data-testid="claims">
          <div className="mb-1 text-meta font-bold uppercase tracking-wider text-ink-400">Agent reasoning · structured (EN)</div>
          <ul className="space-y-1">
            {ex.claims.filter((c) => ["finding", "hypothesis", "recommendation", "risk"].includes(c.kind)).slice(0, 5).map((c) => (
              <li key={c.id} className="flex items-start gap-2 rounded-md border border-shell-700 bg-shell-850 px-2 py-1.5 text-[12px] leading-snug">
                <span className="mt-0.5 w-[104px] shrink-0 text-[9.5px] font-bold uppercase tracking-wide text-ink-400">{c.kind}</span>
                <span className="flex-1 text-ink-200">{c.text}{c.caveat ? <span className="text-ink-400"> · {c.caveat}</span> : null}</span>
                <span className={`shrink-0 rounded px-1 text-[10px] font-bold ${c.kind === "hypothesis" ? "bg-warn/15 text-warn" : c.verified ? "bg-positive/15 text-positive" : "bg-risk/15 text-risk"}`}>
                  {c.kind === "hypothesis" ? "causal" : c.verified ? "✓ verified" : "rejected"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {persona === "broadcaster" && (
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1.5">
            <div className="text-meta font-bold uppercase tracking-wider text-ink-400">{L.storyCards}</div>
            {ex.story_cards.slice(-2).map((c) => (
              <div key={c.moment_id} className="rounded-lg border-l-4 border-rely-500 bg-shell-800 p-2">
                <div className="text-[12px] font-bold text-ink-50">{c.clock} · {c.title}</div>
                <div className="mt-0.5 text-[12px] text-ink-300">{c.stat}</div>
              </div>
            ))}
          </div>
          <div>
            <div className="text-meta font-bold uppercase tracking-wider text-ink-400">{L.prep}</div>
            <ul className="mt-1 space-y-1">{ex.commentator_prep.map((p) => <li key={p} className="text-[12px] text-ink-200">• {p}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  );
}

export function EvidencePanel({ L, ex, demo }: { L: Dict; ex: ExplainResponse; demo: boolean }) {
  const m = ex.moment;
  const groups: [string, typeof m.evidence][] = [
    [L.events, m.evidence.filter((e) => e.kind === "event")],
    [L.window, m.evidence.filter((e) => e.kind === "window")],
    [L.metrics, m.evidence.filter((e) => e.kind === "metric")],
    [L.sequence, m.evidence.filter((e) => e.kind === "sequence")],
    [L.rule, m.evidence.filter((e) => e.kind === "rule")],
  ];
  return (
    <div className="space-y-3" data-testid="evidence-panel">
      <VerificationBar L={L} v={ex.verification} />
      {groups.filter(([, items]) => items.length).map(([title, items]) => (
        <section key={title}>
          <div className="mb-1 text-meta font-bold uppercase tracking-wider text-ink-400">{title}</div>
          <ul className="space-y-1">
            {items.map((e) => (
              <li key={e.id} className="rounded-md border border-shell-700 bg-shell-850 px-2.5 py-1.5 text-[12.5px]" data-testid="evidence-item">
                <div className="flex justify-between gap-2">
                  <span className="text-ink-200">{e.label}</span>
                  {e.value !== null && <b className="tabular-nums text-ink-50">{String(e.value)}{e.unit ?? ""}</b>}
                </div>
                <div className="mt-0.5 flex flex-wrap gap-1">
                  {e.timestamp !== null && <span className="rounded bg-shell-700 px-1 font-mono text-[11px] text-ink-300">{clock(e.timestamp)}</span>}
                  {e.window && <span className="rounded bg-shell-700 px-1 font-mono text-[11px] text-ink-300">{clock(e.window[0])}–{clock(e.window[1])}</span>}
                  {e.event_ids.slice(0, 10).map((id) => <span key={id} className="rounded bg-shell-700 px-1 font-mono text-[11px] text-info">{shortId(id, demo)}</span>)}
                  {e.event_ids.length > 10 && <span className="text-[11px] text-ink-400">+{e.event_ids.length - 10}</span>}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
      <div className="text-[11px] text-ink-400">{L.rule}: {m.rule}</div>
    </div>
  );
}

export function VerificationBar({ L, v }: { L: Dict; v: Verification | null }) {
  if (!v) return null;
  return (
    <div className="rounded-lg border border-shell-700 bg-shell-850 p-2.5">
      <div className="flex items-baseline justify-between">
        <span className="text-meta font-bold uppercase tracking-wider text-ink-400">{L.coverage}</span>
        <b className="text-[18px] tabular-nums text-ink-50">{pct(v.coverage)}</b>
      </div>
      <div className="mt-1.5 flex h-2 overflow-hidden rounded bg-shell-700">
        <div className="bg-positive" style={{ width: pct(v.supported / Math.max(1, v.total_claims)) }} />
        <div className="bg-warn" style={{ width: pct(v.unverifiable / Math.max(1, v.total_claims)) }} />
        <div className="bg-risk" style={{ width: pct(v.rejected / Math.max(1, v.total_claims)) }} />
      </div>
      <div className="mt-1 text-[11px] text-ink-300">{v.supported} {L.supported} · {v.unverifiable} {L.unverifiable} · {v.rejected} {L.rejected}</div>
    </div>
  );
}

export function TracePanel({ L, trace, v }: { L: Dict; trace: AgentTrace[]; v: Verification | null }) {
  return (
    <div className="space-y-3" data-testid="trace-panel">
      <table className="w-full text-left text-[12.5px]">
        <thead className="text-meta uppercase tracking-wider text-ink-400">
          <tr className="[&>th]:px-1.5"><th className="py-1">{L.agent}</th><th>{L.status}</th><th className="text-right">ms</th><th>{L.provider}</th><th>{L.model}</th><th>{L.fallback}</th><th className="text-right">{L.outputs}</th></tr>
        </thead>
        <tbody>
          {trace.map((r) => (
            <tr key={r.agent} className="border-t border-shell-700 align-top [&>td]:px-1.5">
              <td className="py-1.5 font-semibold text-ink-50">{r.agent.replaceAll("_", " ")}{r.note && <div className="max-w-[210px] text-[10.5px] font-normal leading-tight text-ink-400">{r.note}</div>}</td>
              <td><span className={`rounded px-1.5 py-0.5 text-[11px] font-bold ${r.status === "ok" ? "bg-positive/15 text-positive" : r.status === "fallback" ? "bg-warn/15 text-warn" : "bg-risk/15 text-risk"}`}>{r.status}</span></td>
              <td className="text-right tabular-nums text-ink-200">{r.ms.toFixed(1)}</td>
              <td className="text-ink-300">{r.provider}</td>
              <td className="text-ink-300">{r.model ?? "—"}</td>
              <td className="text-ink-300">{r.fallback_used ? "yes" : "no"}</td>
              <td className="text-right tabular-nums text-ink-200">{r.outputs}{r.evidence_coverage !== null ? ` · ${pct(r.evidence_coverage)}` : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <VerificationBar L={L} v={v} />
      <p className="text-[11px] leading-4 text-ink-400">Prompts and provider credentials are never shown. Deterministic stages (state, detector, analysts, verifier) run without AI; the Narrative agent uses the configured provider with a grounded template fallback.</p>
    </div>
  );
}

const PW = 105;
const PH = 68;

export function StudioPreview({ resp, colors, caption }: { resp: TacticalResponse; colors: Record<string, string>; caption?: string }) {
  const [animate, setAnimate] = useState(false);
  const [run, setRun] = useState(0);
  useEffect(() => {
    setAnimate(false);
    const id = setTimeout(() => setAnimate(true), 500);
    return () => clearTimeout(id);
  }, [resp.playbook, resp.moment_id, run]);
  const c = colors[resp.team_id] || "#1F4E8C";
  return (
    <div className="relative h-full w-full">
      <svg viewBox={`-3 -3 ${PW + 6} ${PH + 6}`} className="h-full w-full" data-testid="studio-preview" data-animated={animate ? "1" : "0"} role="img" aria-label={`${resp.from_shape} to ${resp.to_shape}`}>
        <PitchGrass id="studio-grass" />
        <PitchLines />
        {resp.players.filter((p) => p.moves).map((p) => (
          <line key={`l-${p.role}`} x1={(p.from[0] / 100) * PW} y1={(p.from[1] / 100) * PH} x2={(p.to[0] / 100) * PW} y2={(p.to[1] / 100) * PH}
            stroke="#FF6B2C" strokeWidth={0.45} strokeDasharray="1.2 0.8" markerEnd="url(#studio-grass-arrow-o)" opacity={animate ? 0.9 : 0.35} />
        ))}
        {resp.players.map((p) => {
          const [x, y] = animate ? p.to : p.from;
          return (
            <g key={p.role} style={{ transform: `translate(${(x / 100) * PW}px, ${(y / 100) * PH}px)`, transition: "transform 1.8s cubic-bezier(.4,.1,.2,1)" }}>
              <circle r={2.7} fill={p.moves ? "#FF6B2C" : c} stroke="#fff" strokeWidth={0.45} />
              <text y={0.95} textAnchor="middle" fontSize={2.6} fontWeight={800} fill="#fff">{p.number}</text>
              <text y={5.2} textAnchor="middle" fontSize={2} fill="#fff" fillOpacity={0.95}>{p.role}</text>
            </g>
          );
        })}
      </svg>
      {caption && <div className="absolute left-3 top-2 rounded bg-black/45 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-white">{caption}</div>}
      <button onClick={() => setRun((r) => r + 1)} aria-label="replay" className="absolute bottom-2 right-2 rounded bg-black/50 px-2 py-0.5 text-[12px] text-white">↻</button>
    </div>
  );
}

export function TacticalPanel({ L, resp, colors, whatIf, onWhatIf, onPlaybook, locale, showPreview = true }: {
  L: Dict; resp: TacticalResponse; colors: Record<string, string>; whatIf: WhatIf | null; onWhatIf: (o: string) => void;
  onPlaybook: (o: string) => void; locale: string; showPreview?: boolean;
}) {
  const [saved, setSaved] = useState(false);
  const save = () => {
    try {
      const key = "rely.demoTactics";
      const prev = JSON.parse(localStorage.getItem(key) || "[]");
      prev.push({ saved_at: new Date().toISOString(), team: resp.team, playbook: resp.playbook, from: resp.from_shape, to: resp.to_shape, locale, players: resp.players.map((p) => ({ role: p.role, to: p.to })) });
      localStorage.setItem(key, JSON.stringify(prev.slice(-10)));
      setSaved(true);
    } catch {
      setSaved(false);
    }
  };
  return (
    <div className="space-y-3" data-testid="tactical-panel">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-meta font-bold uppercase tracking-wider text-rely-400">{L.tactics} · {resp.team}</div>
          <h2 className="text-[18px] font-bold text-ink-50">{resp.name}</h2>
        </div>
        <div className="flex items-center gap-1 rounded-lg bg-shell-800 px-2 py-1 font-mono text-[15px] font-bold text-ink-50">
          {resp.from_shape}<span className="text-rely-400">→</span>{resp.to_shape}
        </div>
      </div>
      {showPreview && <div className="h-[230px] rounded-lg bg-pitch-700 p-1"><StudioPreview resp={resp} colors={colors} /></div>}
      <div className="grid grid-cols-3 gap-2 text-center">
        <Stat k={L.backLine} v={`${resp.formation_impact.back_line[0]} → ${resp.formation_impact.back_line[1]}`} />
        <Stat k={L.frontLine} v={`${resp.formation_impact.front_line[0]} → ${resp.formation_impact.front_line[1]}`} />
        <Stat k={L.impact} v={resp.formation_impact.phase} />
      </div>
      <div className="rounded-lg border border-shell-700 bg-shell-850 p-2.5">
        <div className="text-meta font-bold uppercase tracking-wider text-ink-400">{L.instruction}</div>
        <p className="mt-0.5 text-[13px] text-ink-50">{resp.instruction}</p>
        <div className="mt-2 text-meta font-bold uppercase tracking-wider text-ink-400">{L.movements}</div>
        <ul className="mt-0.5 space-y-0.5">{resp.players.filter((p) => p.moves).map((p) => (
          <li key={p.role} className="text-[12.5px] text-ink-200"><b className="text-ink-50">#{p.number} {p.name}</b> ({p.role}) {p.text}</li>
        ))}</ul>
        <div className="mt-2 rounded-md border border-risk/40 bg-risk/10 p-2 text-[12.5px] text-ink-50"><b className="text-risk">{L.risk}: </b>{resp.risk}</div>
      </div>
      <div>
        <div className="mb-1 flex items-center justify-between">
          <span className="text-meta font-bold uppercase tracking-wider text-ink-400">{L.whatIf}</span>
          <button onClick={save} className="rounded-md bg-rely-600 px-2.5 py-1 text-[12px] font-semibold text-white hover:bg-rely-500">{saved ? `✓ ${L.saved}` : L.saveTactic}</button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {resp.options.map((o) => (
            <button key={o} onClick={() => { onWhatIf(o); if (o !== "counter_5_4_1") onPlaybook(o); }}
              className={`rounded-md border px-2 py-1 text-[12px] ${whatIf?.option === o ? "border-rely-500 bg-rely-600/15 text-ink-50" : "border-shell-600 text-ink-300 hover:text-ink-50"}`}>{o.replaceAll("_", " ")}</button>
          ))}
        </div>
        {whatIf && (
          <dl className="mt-2 space-y-1 rounded-lg border border-shell-700 bg-shell-850 p-2.5 text-[12.5px]" data-testid="whatif">
            <Row k={L.effect} v={whatIf.effect} /><Row k={L.advantage} v={whatIf.advantage} /><Row k={L.risk} v={whatIf.risk} />
            <Row k={L.players} v={whatIf.players.map((p) => `#${p.number} ${p.name} (${p.role})`).join(", ")} />
            <Row k={L.limitations} v={whatIf.limitations} />
          </dl>
        )}
      </div>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return <div className="rounded-lg bg-shell-800 p-2"><div className="text-[11px] uppercase tracking-wider text-ink-400">{k}</div><div className="text-[14px] font-bold text-ink-50">{v}</div></div>;
}
function Row({ k, v }: { k: string; v: string }) {
  return <div><dt className="inline font-semibold text-ink-50">{k}: </dt><dd className="inline text-ink-200">{v}</dd></div>;
}

const FORMATS = ["thirty_seconds", "analyst_two_minutes", "coach", "broadcast", "fan", "social"] as const;

export function RecapPanel({ L, recap, chapters }: { L: Dict; recap: Recap; chapters: LiveResponse["chapters"] }) {
  const [fmt, setFmt] = useState<(typeof FORMATS)[number]>("thirty_seconds");
  return (
    <div className="space-y-3" data-testid="recap-panel">
      <div className="text-meta font-bold uppercase tracking-wider text-rely-400">{L.recapTab} · {recap.status}</div>
      <div className="flex flex-wrap gap-1">
        {FORMATS.map((f) => (
          <button key={f} aria-pressed={fmt === f} onClick={() => setFmt(f)}
            className={`rounded-md px-2.5 py-1 text-[12px] font-semibold ${fmt === f ? "bg-rely-600 text-white" : "bg-shell-800 text-ink-300 hover:text-ink-50"}`}>{L.formats[f]}</button>
        ))}
      </div>
      <div className="whitespace-pre-line rounded-lg border border-shell-700 bg-shell-850 p-3 text-[13.5px] leading-relaxed text-ink-50" data-testid="recap-text">{recap[fmt]}</div>
      {chapters.length > 0 && (
        <div>
          <div className="mb-1 text-meta font-bold uppercase tracking-wider text-ink-400">{L.story}</div>
          <ol className="space-y-1">
            {chapters.map((c) => (
              <li key={c.moment_id} className="flex gap-2 text-[12.5px]"><span className="font-mono text-ink-400">{c.clock}</span><span className="text-ink-50">{c.title}</span></li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
