import type { BackendInstance } from '../types/protocol';

interface InstanceTabsProps {
  instances: BackendInstance[];
  selectedInstance: string;
  onSelect: (instance: string) => void;
}

export function InstanceTabs({ instances, selectedInstance, onSelect }: InstanceTabsProps) {
  const visibleInstances = instances.length > 0 ? instances : [{ name: selectedInstance }];

  return (
    <div className="instance-tabs">
      {visibleInstances.map((instance) => (
        <button
          className={instance.name === selectedInstance ? 'active' : ''}
          key={instance.name}
          type="button"
          onClick={() => onSelect(instance.name)}
          title={instance.name}
        >
          {instance.name}
        </button>
      ))}
    </div>
  );
}
