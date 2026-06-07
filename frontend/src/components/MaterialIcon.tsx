interface MaterialIconProps {
  name: string;
  className?: string;
  filled?: boolean;
  slot?: string;
}

export function MaterialIcon({ name, className, filled = false, slot }: MaterialIconProps) {
  return (
    <span
      aria-hidden="true"
      className={`material-symbols-outlined material-icon${className ? ` ${className}` : ''}`}
      slot={slot}
      style={{ fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' 400, 'GRAD' 0, 'opsz' 24` }}
    >
      {name}
    </span>
  );
}
