import type { KeyMoments } from "@/lib/types";

/** Bottom timeline: momentum (known so far), seen markers, scrubber. Markers after `t` are never drawn. */
export function Timeline({ t, duration, series, markers, colors, homeId, onSeek, label }: {
  t: number; duration: number; series: number[]; markers: KeyMoments["markers"]; colors: Record<string, string>;
  homeId: string; onSeek: (t: number) => void; label: string;
}) {
  const W = 1000;
  const H = 56;
  const x = (s: number) => (s / duration) * W;
  const pts = series.map((v, i) => `${x(i * 60).toFixed(1)},${(H / 2 - (v / 100) * (H / 2 - 4)).toFixed(1)}`).join(" ");
  const seen = markers.filter((m) => m.second <= t);
  return (
    <div className="relative h-full w-full select-none" data-testid="timeline">
      <div className="absolute left-0 top-0 text-meta uppercase tracking-wider text-ink-400">{label}</div>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-full w-full cursor-pointer"
        onClick={(e) => {
          const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
          onSeek(((e.clientX - r.left) / r.width) * duration);
        }}>
        <rect x={0} y={0} width={W} height={H} fill="transparent" />
        <line x1={0} x2={W} y1={H / 2} y2={H / 2} stroke="#323B4A" strokeWidth={1} />
        <rect x={0} y={0} width={x(t)} height={H} fill="#FF6B2C" fillOpacity={0.06} />
        <line x1={x(2700)} x2={x(2700)} y1={0} y2={H} stroke="#667085" strokeDasharray="3 3" />
        {series.length > 1 && <polyline points={pts} fill="none" stroke="#D5DBE3" strokeWidth={1.6} vectorEffect="non-scaling-stroke" />}
        {seen.map((m) => (
          <g key={m.id}>
            {m.type === "goal" ? (
              <circle cx={x(m.second)} cy={m.team_id === homeId ? 8 : H - 8} r={5} fill={colors[m.team_id]} stroke="#fff" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
            ) : (
              <rect x={x(m.second) - 4} y={m.team_id === homeId ? 2 : H - 14} width={8} height={12} rx={2}
                fill={m.severity === "high" ? "#FF6B2C" : m.severity === "medium" ? "#E8B03D" : "#667085"} />
            )}
          </g>
        ))}
        <line x1={x(t)} x2={x(t)} y1={0} y2={H} stroke="#FF6B2C" strokeWidth={2} vectorEffect="non-scaling-stroke" />
      </svg>
    </div>
  );
}
