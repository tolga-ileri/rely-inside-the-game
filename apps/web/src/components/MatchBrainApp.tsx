"use client";
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { api } from "@/lib/api";
import { t as dict } from "@/lib/i18n";
import { clock, initialPlayback, playbackReducer, shouldFetch } from "@/lib/playback";
import type { ExplainResponse, KeyMoments, LiveResponse, Locale, MatchMeta, Persona, Recap, TacticalResponse, WhatIf } from "@/lib/types";
import { LOCALES, PERSONAS } from "@/lib/types";
import { Controls } from "./Controls";
import { Crest } from "./Crest";
import { Feed } from "./Feed";
import { EvidencePanel, RecapPanel, StudioPreview, TacticalPanel, TracePanel, WhyPanel } from "./Panels";
import { Pitch } from "./Pitch";
import { Timeline } from "./Timeline";

type Tab = "why" | "evidence" | "trace" | "tactics" | "recap";
const DEMO_MATCH = "hcf-wva-tactical-shift";

export function MatchBrainApp({ matchId = DEMO_MATCH, demoMode = false, fail }: { matchId?: string; demoMode?: boolean; fail?: string }) {
  const [meta, setMeta] = useState<MatchMeta | null>(null);
  const [km, setKm] = useState<KeyMoments | null>(null);
  const [pb, dispatch] = useReducer(playbackReducer, initialPlayback());
  const [live, setLive] = useState<LiveResponse | null>(null);
  const [persona, setPersona] = useState<Persona>("analyst");
  const [locale, setLocale] = useState<Locale>("en");
  const [tab, setTab] = useState<Tab | null>(null);
  const [ex, setEx] = useState<ExplainResponse | null>(null);
  const [resp, setResp] = useState<TacticalResponse | null>(null);
  const [whatIf, setWhatIf] = useState<WhatIf | null>(null);
  const [recap, setRecap] = useState<Recap | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const demoRun = useRef(false);
  const lastFetched = useRef<number | null>(null);
  const seenHeadline = useRef<string | null>(null);
  const L = dict(locale);

  useEffect(() => {
    api.meta(matchId).then(setMeta).catch(() => setError("API unreachable. Start the API on 127.0.0.1:8100."));
    api.keymoments(matchId).then(setKm).catch(() => undefined);
  }, [matchId]);

  // Playback clock
  useEffect(() => {
    if (!pb.playing) return;
    let last = performance.now();
    const id = setInterval(() => {
      const now = performance.now();
      dispatch({ type: "tick", dtMs: now - last });
      last = now;
    }, 100);
    return () => clearInterval(id);
  }, [pb.playing]);

  // Live state: only events <= floor(t) are requested.
  const until = Math.floor(pb.t);
  const fetchLive = useCallback((u: number) => {
    lastFetched.current = u;
    api.live(matchId, u, locale, undefined, fail).then((r) => { setLive(r); setError(null); }).catch(() => setError("API unreachable. Start the API on 127.0.0.1:8100."));
  }, [matchId, locale, fail]);
  useEffect(() => {
    if (!pb.playing || shouldFetch(lastFetched.current, until, Math.max(5, pb.speed / 2))) fetchLive(until);
  }, [until, pb.playing, pb.speed, fetchLive]);

  // Demo run: pause on the first headline turning point and announce it.
  useEffect(() => {
    if (!live?.headline_id || !demoRun.current) return;
    const head = live.moments.find((m) => m.id === live.headline_id);
    if (head && head.id !== seenHeadline.current && head.severity === "high" && ["sub_shift", "red_card"].includes(head.type)) {
      seenHeadline.current = head.id;
      demoRun.current = false;
      dispatch({ type: "pause" });
      setSelected(head.id);
      setBanner(`${L.turningPoint} · ${head.detected_clock} · ${head.title_localized}`);
    }
  }, [live, L.turningPoint]);

  const colors = useMemo(() => Object.fromEntries((meta?.teams ?? []).map((t) => [t.team_id, t.color])), [meta]);
  const names = useMemo(() => Object.fromEntries((meta?.teams ?? []).flatMap((t) => t.players.map((p) => [p.player_id, p.name]))), [meta]);
  const home = meta?.teams.find((t) => t.side === "home");
  const away = meta?.teams.find((t) => t.side === "away");

  const explain = useCallback(async (momentId?: string | null, p: Persona = persona, l: Locale = locale, u = until, open = true) => {
    setBusy("explain");
    try {
      const r = await api.explain(matchId, u, p, l, momentId ?? selected ?? live?.headline_id ?? undefined, fail);
      setEx(r);
      setSelected(r.moment.id);
      if (open) setTab((cur) => (cur && cur !== "tactics" && cur !== "recap" ? cur : "why"));
    } catch {
      setBanner(L.noMoment);
    } finally {
      setBusy(null);
    }
  }, [matchId, persona, locale, until, selected, live?.headline_id, fail, L.noMoment]);

  const generateResponse = useCallback(async (playbook = "amplify_3_2_5", l: Locale = locale, open = true) => {
    setBusy("response");
    try {
      const r = await api.response(matchId, until, l, selected ?? live?.headline_id ?? undefined, playbook);
      setResp(r);
      if (open) setTab("tactics");
    } catch {
      setBanner(L.noMoment);
    } finally {
      setBusy(null);
    }
  }, [matchId, until, locale, selected, live?.headline_id, L.noMoment]);

  const generateRecap = useCallback(async (l: Locale = locale) => {
    setBusy("recap");
    const ft = meta?.duration_seconds ?? 5400;
    dispatch({ type: "seek", t: ft, play: false });
    try {
      setRecap(await api.recap(matchId, ft, l));
      setTab("recap");
    } finally {
      setBusy(null);
    }
  }, [matchId, locale, meta]);

  // Persona / language changes re-render narrative only (facts are fixed server-side).
  const changePersona = (p: Persona) => {
    setPersona(p);
    if (ex) explain(ex.moment.id, p, locale, ex.moment.detected_at > until ? ex.moment.detected_at : until);
  };
  const changeLocale = (l: Locale) => {
    setLocale(l);
    if (ex) explain(ex.moment.id, persona, l, until, false);
    if (resp) generateResponse(resp.playbook, l, false);
    if (recap) api.recap(matchId, meta?.duration_seconds ?? 5400, l).then(setRecap);
    if (whatIf && resp) api.whatif(matchId, until, l, whatIf.option, resp.moment_id).then(setWhatIf);
  };

  const handlers = {
    onPlayDemo: () => {
      const start = meta?.demo.start_second ?? km?.demo.start_second ?? 3000;
      demoRun.current = true;
      seenHeadline.current = null;
      setBanner(null); setTab(null); setEx(null); setResp(null); setRecap(null); setWhatIf(null); setSelected(null);
      lastFetched.current = null;
      dispatch({ type: "speed", speed: 20 });
      dispatch({ type: "seek", t: start, play: true });
    },
    onToggle: () => dispatch({ type: "toggle" }),
    onRestart: () => { demoRun.current = false; setBanner(null); lastFetched.current = null; dispatch({ type: "restart" }); },
    onSpeed: (s: 1 | 5 | 20) => dispatch({ type: "speed", speed: s }),
    onHT: () => { lastFetched.current = null; dispatch({ type: "seek", t: km?.half_time ?? 2700, play: false }); },
    onFT: () => { lastFetched.current = null; dispatch({ type: "seek", t: km?.full_time ?? 5400, play: false }); },
    onJump: () => {
      if (!km?.headline) return;
      const u = km.headline.detected_at + 5;
      demoRun.current = false;
      lastFetched.current = null;
      dispatch({ type: "seek", t: u, play: false });
      setSelected(km.headline.id);
      explain(km.headline.id, persona, locale, u);
    },
    onExplain: () => explain(),
    onResponse: () => generateResponse(),
    onRecap: () => generateRecap(),
    onPersona: () => changePersona(PERSONAS[(PERSONAS.indexOf(persona) + 1) % PERSONAS.length]),
    onLanguage: () => changeLocale(LOCALES[(LOCALES.indexOf(locale) + 1) % LOCALES.length]),
  };

  const st = live?.state;
  const momentView = !!(tab && ex);
  const showSeq = momentView && ex
    ? ex.events.filter((e) => ex.moment.linked_event_ids.includes(e.event_id) && e.event_type !== "Substitution")
    : st?.current_sequence ?? [];
  const tabs: [Tab, string, boolean][] = [["why", L.why, !!ex], ["evidence", L.evidence, !!ex], ["trace", L.trace, !!(ex || live)], ["tactics", L.tactics, !!resp], ["recap", L.recapTab, !!recap]];

  return (
    <div className="flex h-screen min-h-[760px] flex-col bg-shell-950 text-ink-50">
      {/* Top bar */}
      <header className="flex h-[68px] shrink-0 items-center gap-4 border-b border-shell-700 bg-shell-900 px-5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rely-600 text-[15px] font-black text-white">R</div>
          <div className="leading-tight">
            <div className="text-[14px] font-bold">Rely Match Brain</div>
            <div className="text-[11px] text-ink-400">Inside the Game · hackathon edition</div>
          </div>
        </div>
        {home && away && (
          <div className="mx-auto flex items-center gap-4" data-testid="scoreboard">
            <div className="flex items-center gap-2"><span className="text-right text-[15px] font-semibold">{home.name}</span><Crest {...home.crest} color={home.color} /></div>
            <div className="flex items-center gap-2 rounded-xl bg-shell-800 px-4 py-1.5">
              <span className="text-[26px] font-black tabular-nums">{st?.score[home.team_id] ?? 0}</span>
              <span className="text-ink-400">–</span>
              <span className="text-[26px] font-black tabular-nums">{st?.score[away.team_id] ?? 0}</span>
            </div>
            <div className="flex items-center gap-2"><Crest {...away.crest} color={away.color} /><span className="text-[15px] font-semibold">{away.name}</span></div>
            <div className="ml-2 flex flex-col items-center">
              <span className="font-mono text-[20px] font-bold tabular-nums text-rely-400" data-testid="clock">{clock(pb.t)}</span>
              <span className="text-[10px] uppercase tracking-wider text-ink-400">{pb.t >= (meta?.duration_seconds ?? 5400) ? L.ft : pb.t >= 2700 ? "2H" : "1H"} · {pb.speed}x</span>
            </div>
          </div>
        )}
        <div className="flex items-center gap-2">
          <span className="rounded-md border border-rely-600/60 bg-rely-600/10 px-2 py-1 text-[11px] font-bold tracking-wider text-rely-400" data-testid="synthetic-label">{L.synthetic}</span>
          <select aria-label="persona" value={persona} onChange={(e) => changePersona(e.target.value as Persona)} className="rounded-md border border-shell-600 bg-shell-800 px-2 py-1 text-[12px]">
            {PERSONAS.map((p) => <option key={p} value={p}>{L.persona[p]}</option>)}
          </select>
          <select aria-label="language" value={locale} onChange={(e) => changeLocale(e.target.value as Locale)} className="rounded-md border border-shell-600 bg-shell-800 px-2 py-1 text-[12px]">
            {LOCALES.map((l) => <option key={l} value={l}>{l.toUpperCase()}</option>)}
          </select>
        </div>
      </header>

      <div className="relative flex min-h-0 flex-1">
        {/* Center */}
        <main className="flex min-w-0 flex-1 flex-col gap-3 p-4">
          {error && <div className="rounded-lg border border-risk/50 bg-risk/10 px-3 py-2 text-dense text-risk">{error}</div>}
          {banner && (
            <button onClick={() => { setBanner(null); explain(selected); }} className="flex items-center gap-3 rounded-lg border border-rely-500 bg-rely-600/15 px-3 py-2 text-left text-[14px] font-semibold text-ink-50" data-testid="banner">
              <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-rely-500" />{banner}<span className="ml-auto text-[12px] text-rely-400">{L.explain} →</span>
            </button>
          )}
          <div className="relative min-h-0 flex-1 rounded-xl bg-pitch-700 p-2">
            {tab === "tactics" && resp ? (
              <div className="absolute inset-2 z-10 bg-pitch-700"><StudioPreview resp={resp} colors={colors} caption={`Studio preview · ${resp.team} · ${resp.from_shape} → ${resp.to_shape}`} /></div>
            ) : null}
            {home && <Pitch events={showSeq} homeId={home.team_id} colors={colors} caption={momentView ? L.keyEvents : L.liveSeq} />}
            <div className="absolute left-4 top-3 rounded bg-black/45 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-white">{L.sequenceViewer} · {momentView && ex ? `${L.keyEvents} · ${ex.moment.clock}` : L.liveSeq}</div>
            {home && away && <div className="absolute bottom-3 left-4 text-[11px] font-semibold text-white/80">{home.short} →</div>}
            {home && away && <div className="absolute bottom-3 right-4 text-[11px] font-semibold text-white/80">← {away.short}</div>}
          </div>
          {st && home && away && (
            <div className="grid shrink-0 grid-cols-5 gap-2" data-testid="stats">
              <StatBox k={L.shots} h={`${st.teams[home.team_id].shots} (${st.teams[home.team_id].shots_on_target})`} a={`${st.teams[away.team_id].shots} (${st.teams[away.team_id].shots_on_target})`} />
              <StatBox k={L.passShare} h={`${Math.round(st.teams[home.team_id].possession * 100)}%`} a={`${Math.round(st.teams[away.team_id].possession * 100)}%`} />
              <ChannelBox L={L} label={`${L.entries} · 10'`} h={st.last10[home.team_id]} a={st.last10[away.team_id]} hc={home.color} ac={away.color} />
              <StatBox k={`${L.highPress} · 5'`} h={String(st.last5[home.team_id].high_pressures)} a={String(st.last5[away.team_id].high_pressures)} />
              <div className="rounded-lg border border-shell-700 bg-shell-850 px-3 py-2">
                <div className="text-[11px] uppercase tracking-wider text-ink-400">{L.momentum}</div>
                <div className="mt-1 h-2 overflow-hidden rounded bg-shell-700">
                  <div className="h-full" style={{ width: `${50 + st.momentum / 2}%`, background: home.color }} />
                </div>
                <div className="mt-1 flex justify-between text-[12px] font-semibold"><span>{home.short}</span><span className="tabular-nums text-ink-300">{st.momentum > 0 ? "+" : ""}{Math.round(st.momentum)}</span><span>{away.short}</span></div>
              </div>
            </div>
          )}
          <Controls L={L} playing={pb.playing} speed={pb.speed} h={handlers} busy={busy} />
        </main>

        {/* Right feed */}
        <aside className={`${tab ? "hidden" : "flex"} w-[360px] shrink-0 flex-col border-l border-shell-700 bg-shell-900 p-4`}>
          <Feed items={live?.feed ?? []} colors={colors} title={L.feed} empty={L.noFeed} selected={selected}
            onSelect={(id) => { setSelected(id); explain(id); }} />
          {live?.verification && (
            <div className="mt-3 rounded-lg border border-shell-700 bg-shell-850 p-2.5 text-[12px] text-ink-300">
              {L.coverage}: <b className="text-ink-50">{Math.round(live.verification.coverage * 100)}%</b> · {live.verification.supported}/{live.verification.total_claims} {L.supported}
              {!demoMode && <span className="ml-1 text-ink-400">· {st?.events_processed} events</span>}
            </div>
          )}
        </aside>

        {/* Context drawer */}
        {tab && (
          <section className="flex w-[560px] shrink-0 flex-col border-l border-shell-600 bg-shell-900 min-[1400px]:w-[620px]" data-testid="drawer">
            <div className="flex items-center gap-1 border-b border-shell-700 px-3 pt-2">
              {tabs.filter(([, , on]) => on).map(([k, label]) => (
                <button key={k} onClick={() => setTab(k)} className={`rounded-t-md px-3 py-2 text-[12.5px] font-semibold ${tab === k ? "bg-shell-800 text-ink-50 shadow-[inset_0_-2px_0_#FF6B2C]" : "text-ink-400 hover:text-ink-50"}`}>{label}</button>
              ))}
              <button onClick={() => setTab(null)} className="ml-auto rounded px-2 py-1 text-ink-400 hover:text-ink-50" aria-label={L.close}>✕</button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-4">
              {tab === "why" && ex && home && <WhyPanel L={L} ex={ex} persona={persona} onPersona={changePersona} playerNames={names} />}
              {tab === "evidence" && ex && <EvidencePanel L={L} ex={ex} demo={demoMode} />}
              {tab === "trace" && <TracePanel L={L} trace={ex?.trace ?? live?.trace ?? []} v={ex?.verification ?? live?.verification ?? null} />}
              {tab === "tactics" && resp && <TacticalPanel L={L} resp={resp} colors={colors} whatIf={whatIf} locale={locale}
                onWhatIf={(o) => api.whatif(matchId, until, locale, o, resp.moment_id).then(setWhatIf)} onPlaybook={(o) => generateResponse(o)} showPreview={false} />}
              {tab === "recap" && recap && <RecapPanel L={L} recap={recap} chapters={live?.chapters ?? []} />}
            </div>
          </section>
        )}
      </div>

      {/* Timeline */}
      <footer className="h-[84px] shrink-0 border-t border-shell-700 bg-shell-900 px-5 py-2">
        {home && (
          <Timeline t={pb.t} duration={meta?.duration_seconds ?? 5400} series={st?.momentum_series ?? []} markers={km?.markers ?? []}
            colors={colors} homeId={home.team_id} label={`${L.momentum} · ${home.short} ↑ / ${away?.short} ↓`}
            onSeek={(s) => { demoRun.current = false; lastFetched.current = null; dispatch({ type: "seek", t: s }); }} />
        )}
      </footer>
    </div>
  );
}

function StatBox({ k, h, a }: { k: string; h: string; a: string }) {
  return (
    <div className="rounded-lg border border-shell-700 bg-shell-850 px-3 py-2">
      <div className="text-[11px] uppercase tracking-wider text-ink-400">{k}</div>
      <div className="mt-0.5 flex justify-between text-[17px] font-bold tabular-nums"><span>{h}</span><span className="text-ink-300">{a}</span></div>
    </div>
  );
}

function ChannelBox({ L, label, h, a, hc, ac }: { L: ReturnType<typeof dict>; label: string; h: LiveResponse["state"]["last10"][string]; a: LiveResponse["state"]["last10"][string]; hc: string; ac: string }) {
  const max = Math.max(1, h.entries_L, h.entries_C, h.entries_R, a.entries_L, a.entries_C, a.entries_R);
  return (
    <div className="rounded-lg border border-shell-700 bg-shell-850 px-3 py-2">
      <div className="text-[11px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className="mt-1 grid grid-cols-3 gap-1">
        {(["L", "C", "R"] as const).map((c) => (
          <div key={c} className="flex flex-col items-center">
            <div className="flex h-6 items-end gap-0.5">
              <div className="w-2 rounded-sm" style={{ height: `${(h[`entries_${c}`] / max) * 24}px`, background: hc }} />
              <div className="w-2 rounded-sm" style={{ height: `${(a[`entries_${c}`] / max) * 24}px`, background: ac }} />
            </div>
            <span className="text-[10px] text-ink-400">{L.channels[c].slice(0, 1)} {h[`entries_${c}`]}·{a[`entries_${c}`]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
