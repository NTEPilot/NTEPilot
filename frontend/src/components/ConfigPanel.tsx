import type { ConfigField } from '../types/protocol';
import { useMotionParent } from '../lib/useMotionParent';
import { Switch } from './Switch';

interface ConfigPanelProps {
  fields: ConfigField[];
  values: Record<string, string | number | boolean>;
  onChange: (key: string, value: string | number | boolean) => void;
}

function valueFor(field: ConfigField, values: Record<string, string | number | boolean>) {
  return values[field.key] ?? field.value;
}

function asTextFieldElement(target: EventTarget & Element) {
  return target as HTMLElement & { value: string };
}

function asSelectElement(target: EventTarget & Element) {
  return target as HTMLElement & { value: string };
}

export function ConfigPanel({ fields, values, onChange }: ConfigPanelProps) {
  const [fieldsRef] = useMotionParent<HTMLDivElement>({ duration: 140 });

  if (fields.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-state-icon material-symbols-outlined" aria-hidden="true">tune</span>
        <span>暂无配置项</span>
      </div>
    );
  }

  return (
    <div className="config-fields" ref={fieldsRef}>
      {fields.map((field) => {
        const current = valueFor(field, values);

        if (field.type === 'boolean') {
          return (
            <div className="config-row" key={field.key}>
              <div className="config-copy">
                <span className="config-label">{field.label}</span>
                {field.description && <small className="config-description">{field.description}</small>}
              </div>
              <Switch checked={Boolean(current)} onChange={(checked) => onChange(field.key, checked)} label={field.label} />
            </div>
          );
        }

        if (field.type === 'select') {
          return (
            <div className="config-row" key={field.key}>
              <div className="config-copy">
                <span className="config-label">{field.label}</span>
                {field.description && <small className="config-description">{field.description}</small>}
              </div>
              <md-outlined-select
                className="config-input"
                label={field.label}
                value={String(current ?? '')}
                onChange={(event) => {
                  onChange(field.key, asSelectElement(event.currentTarget).value);
                }}
              >
                {(field.options ?? []).map((option) => (
                  <md-select-option key={option} value={option}>
                    <div slot="headline">{option}</div>
                  </md-select-option>
                ))}
              </md-outlined-select>
            </div>
          );
        }

        return (
          <div className="config-row" key={field.key}>
            <div className="config-copy">
              <span className="config-label">{field.label}</span>
              {field.description && <small className="config-description">{field.description}</small>}
            </div>
            <md-outlined-text-field
              className="config-input"
              label={field.label}
              type={field.type === 'number' ? 'number' : 'text'}
              min={field.min === undefined ? undefined : String(field.min)}
              max={field.max === undefined ? undefined : String(field.max)}
              step={field.step === undefined ? undefined : String(field.step)}
              supportingText={field.description}
              value={String(current ?? '')}
              onChange={(event) => {
                const rawValue = asTextFieldElement(event.currentTarget).value;
                const next = field.type === 'number' ? Number(rawValue) : rawValue;
                onChange(field.key, next);
              }}
            />
          </div>
        );
      })}
    </div>
  );
}
