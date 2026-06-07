import type { ConfigField } from '../types/protocol';
import { Switch } from './Switch';

interface ConfigPanelProps {
  fields: ConfigField[];
  values: Record<string, string | number | boolean>;
  onChange: (key: string, value: string | number | boolean) => void;
}

function valueFor(field: ConfigField, values: Record<string, string | number | boolean>) {
  return values[field.key] ?? field.value;
}

export function ConfigPanel({ fields, values, onChange }: ConfigPanelProps) {
  if (fields.length === 0) {
    return <div className="empty-console-row">暂无配置项。</div>;
  }

  return (
    <div className="config-fields">
      {fields.map((field) => {
        const current = valueFor(field, values);

        if (field.type === 'boolean') {
          return (
            <div className="config-row" key={field.key}>
              <div>
                <span>{field.label}</span>
                {field.description && <small>{field.description}</small>}
              </div>
              <Switch checked={Boolean(current)} onChange={(checked) => onChange(field.key, checked)} label={field.label} />
            </div>
          );
        }

        return (
          <label className="config-row" key={field.key}>
            <div>
              <span>{field.label}</span>
              {field.description && <small>{field.description}</small>}
            </div>
            <input
              type={field.type === 'number' ? 'number' : 'text'}
              min={field.min}
              max={field.max}
              step={field.step}
              value={String(current ?? '')}
              onChange={(event) => {
                const next = field.type === 'number' ? Number(event.target.value) : event.target.value;
                onChange(field.key, next);
              }}
            />
          </label>
        );
      })}
    </div>
  );
}
