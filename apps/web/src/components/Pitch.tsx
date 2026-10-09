import type { MatchEvent } from "@/lib/types";

const W = 105;
const H = 68;

export function PitchLines() {
  return (
    <g fill="none" stroke="#fff" strokeOpacity={0.85} strokeWidth={0.35}>
      <rect x={0.5} y={0.5} width={W - 1} height={H - 1} />
      <line x1={W / 2} y1={0.5} x2={W / 2} y2={H - 0.5} />
      <circle cx={W / 2} cy={H / 2} r={9.15} />
      <circle cx={W / 2} cy={H / 2} r={0.5} fill="#fff" />
      <rect x={0.5} y={H / 2 - 20.16} width={16.5} height={40.32} />
      <rect x={W - 17} y={H / 2 - 20.16} width={16.5} height={40.32} />
      <rect x={0.5} y={H / 2 - 9.16} width={5.5} height={18.32} />
      <rect x={W - 6} y={H / 2 - 9.16} width={5.5} height={18.32} />
      <rect x={-1.2} y={H / 2 - 3.66} width={1.7} height={7.32} />
      <rect x={W - 0.5} y={H / 2 - 3.66} width={1.7} height={7.32} />
      <circle cx={11} cy={H / 2} r={0.4} fill="#fff" />
      <circle cx={W - 11} cy={H / 2} r={0.4} fill="#fff" />
      <path d={`M 17 ${H / 2 - 7.3} A 9.15 9.15 0 0 1 17 ${H / 2 + 7.3}`} />
      <path d={`M ${W - 17} ${H / 2 - 7.3} A 9.15 9.15 0 0 0 ${W - 17} ${H / 2 + 7.3}`} />
    </g>
  );
}

export function PitchGrass({ id = "grass" }: { id?: string }) {
  return (
    <>
      <defs>
        <pattern id={id} width={W / 10} height={H} patternUnits="userSpaceOnUse">
          <rect width={W / 20} height={H} fill="#2C7F43" />
          <rect x={W / 20} width={W / 20} height={H} fill="#277A3E" />
        </pattern>
        <marker id={`${id}-arrow`} viewBox="0 0 10 10" refX={8} refY={5} markerWidth={4} markerHeight={4} orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#fff" />
        </marker>
        <marker id={`${id}-arrow-o`} viewBox="0 0 10 10" refX={8} refY={5} markerWidth={4} markerHeight={4} orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#FF6B2C" />
        </marker>
      </defs>
      <rect x={-3} y={-3} width={W + 6} height={H + 6} fill={`url(#${id})`} rx={1.5} />
    </>
  );
}

/** Convert an event's team-frame coordinates to the screen: home attacks left->right, away right->left. */
export function toScreen(x: number, y: number, isHome: boolean): [number, number] {
  const sx = isHome ? x : 100 - x;
  const sy = isHome ? y : 100 - y;
  return [(sx / 100) * W, (sy / 100) * H];
}

const DRAWN = new Set(["Pass", "Carry", "Shot", "Pressure", "Cross", "Dribble"]);

export function Pitch({ events, homeId, colors, caption, numbered = true }: {
  events: MatchEvent[]; homeId: string; colors: Record<string, string>; caption?: string; numbered?: boolean;
}) {
  const drawn = events.filter((e) => DRAWN.has(e.event_type)).slice(-14);
  return (
    <svg viewBox={`-3 -3 ${W + 6} ${H + 6}`} className="h-full w-full" preserveAspectRatio="xMidYMid meet" role="img" aria-label={caption || "Pitch"} data-testid="pitch">
      <PitchGrass id="main-grass" />
      <PitchLines />
      {drawn.map((e, i) => {
        const home = e.team_id === homeId;
        const [x1, y1] = toScreen(e.start_x, e.start_y, home);
        const hasEnd = e.end_x !== null && e.end_y !== null;
        const [x2, y2] = hasEnd ? toScreen(e.end_x as number, e.end_y as number, home) : [x1, y1];
        const c = colors[e.team_id] || "#fff";
        if (e.event_type === "Pressure") {
          return (
            <g key={e.event_id}>
              <circle cx={x1} cy={y1} r={2.1} fill="none" stroke="#F0645A" strokeWidth={0.5} strokeDasharray="1 0.6" />
              {numbered && <Num x={x1} y={y1 - 3.2} n={i + 1} fill="#F0645A" />}
            </g>
          );
        }
        const shot = e.event_type === "Shot";
        return (
          <g key={e.event_id}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={shot ? "#FF6B2C" : "#fff"} strokeOpacity={e.outcome === "Incomplete" ? 0.5 : 0.95}
              strokeWidth={shot ? 0.75 : 0.45} strokeDasharray={e.event_type === "Carry" || e.event_type === "Dribble" ? "1.2 0.8" : undefined}
              markerEnd={`url(#main-grass-arrow${shot ? "-o" : ""})`} />
            <circle cx={x1} cy={y1} r={1.25} fill={c} stroke="#fff" strokeWidth={0.3} />
            {numbered && <Num x={x1} y={y1 - 2.4} n={i + 1} />}
            {e.outcome === "Goal" && <text x={x2 - 1} y={y2 - 2} fontSize={2.6} fill="#FFE7D6" fontWeight={800}>GOAL</text>}
          </g>
        );
      })}
    </svg>
  );
}

function Num({ x, y, n, fill = "#0B0E13" }: { x: number; y: number; n: number; fill?: string }) {
  return (
    <g>
      <circle cx={x} cy={y} r={1.35} fill="#fff" fillOpacity={0.95} />
      <text x={x} y={y + 0.62} textAnchor="middle" fontSize={1.7} fontWeight={800} fill={fill}>{n}</text>
    </g>
  );
}
