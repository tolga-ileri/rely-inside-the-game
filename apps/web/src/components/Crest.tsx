/** Fictional geometric crest: a shape plus initials. No real club marks. */
export function Crest({ shape, initials, color, size = 36 }: { shape: string; initials: string; color: string; size?: number }) {
  const s = 40;
  const path =
    shape === "shield" ? "M20 2 L36 8 L34 26 Q30 34 20 38 Q10 34 6 26 L4 8 Z"
      : shape === "diamond" ? "M20 2 L38 20 L20 38 L2 20 Z"
        : shape === "hexagon" ? "M20 2 L36 11 L36 29 L20 38 L4 29 L4 11 Z"
          : "";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${s} ${s}`} aria-label={`${initials} crest`} role="img">
      {path ? <path d={path} fill={color} stroke="#fff" strokeOpacity={0.85} strokeWidth={2} /> : <circle cx={20} cy={20} r={18} fill={color} stroke="#fff" strokeOpacity={0.85} strokeWidth={2} />}
      <text x={20} y={24.5} textAnchor="middle" fontSize={12} fontWeight={800} fill="#fff" fontFamily="system-ui, sans-serif">{initials}</text>
    </svg>
  );
}
