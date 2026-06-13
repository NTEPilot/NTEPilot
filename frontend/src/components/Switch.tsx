interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  ariaLabel?: string;
  compact?: boolean;
}

export function Switch({ checked, onChange, label, ariaLabel, compact = false }: SwitchProps) {
  return (
    <label className={`switch-control${compact ? ' is-compact' : ''}`}>
      {label && <span className="switch-label">{label}</span>}
      <md-switch
        aria-label={ariaLabel ?? label}
        icons
        selected={checked}
        onChange={(event) => onChange(Boolean((event.currentTarget as HTMLElement & { selected?: boolean }).selected))}
      />
    </label>
  );
}
