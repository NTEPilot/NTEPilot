interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  compact?: boolean;
}

export function Switch({ checked, onChange, label, compact = false }: SwitchProps) {
  return (
    <label className={`switch-control${compact ? ' is-compact' : ''}`}>
      <span className="switch-label">{label}</span>
      <md-switch
        aria-label={label}
        icons
        selected={checked}
        onChange={(event) => onChange(Boolean((event.currentTarget as HTMLElement & { selected?: boolean }).selected))}
      />
    </label>
  );
}
