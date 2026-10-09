import type { FeedItem } from "@/lib/types";

const DOT: Record<string, string> = { high: "bg-rely-500", medium: "bg-warn", low: "bg-ink-500" };

export function Feed({ items, colors, title, empty, onSelect, selected }: {
  items: FeedItem[]; colors: Record<string, string>; title: string; empty: string; onSelect: (momentId: string) => void; selected?: string | null;
}) {
  return (
    <div className="flex min-h-0 flex-1 flex-col" data-testid="feed">
      <div className="mb-2 text-meta font-bold uppercase tracking-wider text-ink-400">{title}</div>
      {items.length === 0 && <div className="text-dense text-ink-400">{empty}</div>}
      <ul className="min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">
        {items.map((it) => {
          const clickable = !!it.moment_id;
          return (
            <li key={it.id}>
              <button disabled={!clickable} onClick={() => it.moment_id && onSelect(it.moment_id)}
                className={`flex w-full items-start gap-2.5 rounded-lg border px-2.5 py-2 text-left transition ${selected && selected === it.moment_id ? "border-rely-500 bg-shell-800" : "border-shell-700 bg-shell-850 hover:border-shell-600"} ${clickable ? "" : "cursor-default"}`}>
                <span className="mt-0.5 font-mono text-meta tabular-nums text-ink-400">{it.clock}</span>
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: colors[it.team_id] }} />
                <span className="flex-1 text-dense leading-snug text-ink-50">
                  {it.kind === "goal" ? <b className="text-rely-400">{it.text}</b> : it.text}
                </span>
                {it.kind === "moment" && <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-sm ${DOT[it.severity]}`} title={it.severity} />}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
