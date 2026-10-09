"use client";
import { SPEEDS, type Speed } from "@/lib/playback";
import type { Dict } from "@/lib/i18n";

export interface ControlHandlers {
  onPlayDemo: () => void; onToggle: () => void; onRestart: () => void; onSpeed: (s: Speed) => void; onHT: () => void; onFT: () => void;
  onJump: () => void; onExplain: () => void; onResponse: () => void; onRecap: () => void; onPersona: () => void; onLanguage: () => void;
}

export function Controls({ L, playing, speed, h, busy }: { L: Dict; playing: boolean; speed: Speed; h: ControlHandlers; busy?: string | null }) {
  const btn = "rounded-lg px-3 py-2 text-dense font-semibold transition disabled:opacity-50";
  const ghost = `${btn} bg-shell-800 text-ink-50 hover:bg-shell-700 border border-shell-600`;
  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="controls">
      <button className={`${btn} bg-rely-600 text-white hover:bg-rely-500`} onClick={h.onPlayDemo}>▶ {L.playDemo}</button>
      <div className="flex items-center gap-1 rounded-lg border border-shell-600 bg-shell-850 p-1">
        <button aria-label={playing ? L.pause : L.play} className="rounded-md px-2.5 py-1 text-dense text-ink-50 hover:bg-shell-700" onClick={h.onToggle}>{playing ? "❚❚" : "▶"}</button>
        <button aria-label={L.restart} className="rounded-md px-2.5 py-1 text-dense text-ink-50 hover:bg-shell-700" onClick={h.onRestart}>↺</button>
        {SPEEDS.map((s) => (
          <button key={s} aria-pressed={speed === s} onClick={() => h.onSpeed(s)}
            className={`rounded-md px-2 py-1 text-meta font-bold ${speed === s ? "bg-rely-600 text-white" : "text-ink-300 hover:bg-shell-700"}`}>{s}x</button>
        ))}
        <button className="rounded-md px-2 py-1 text-meta font-bold text-ink-300 hover:bg-shell-700" onClick={h.onHT}>{L.ht}</button>
        <button className="rounded-md px-2 py-1 text-meta font-bold text-ink-300 hover:bg-shell-700" onClick={h.onFT}>{L.ft}</button>
      </div>
      <button className={ghost} onClick={h.onJump}>{L.jump}</button>
      <button className={ghost} onClick={h.onExplain} disabled={busy === "explain"}>{L.explain}</button>
      <button className={ghost} onClick={h.onResponse} disabled={busy === "response"}>{L.response}</button>
      <button className={ghost} onClick={h.onRecap} disabled={busy === "recap"}>{L.recap}</button>
      <button className={ghost} onClick={h.onPersona}>{L.switchPersona}</button>
      <button className={ghost} onClick={h.onLanguage}>{L.switchLanguage}</button>
    </div>
  );
}
