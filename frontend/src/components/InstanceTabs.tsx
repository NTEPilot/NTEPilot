import type { BackendInstance } from '../types/protocol';
import { useMotionParent } from '../lib/useMotionParent';
import { MaterialIcon } from './MaterialIcon';

interface InstanceTabsProps {
  instances: BackendInstance[];
  selectedInstance: string;
  onSelect: (instance: string) => void;
}

export function InstanceTabs({ instances, selectedInstance, onSelect }: InstanceTabsProps) {
  const [tabsRef] = useMotionParent<HTMLElement>();
  const visibleInstances = instances.length > 0 ? instances : [{ name: selectedInstance }];

  return (
    <md-list className="instance-tabs" ref={tabsRef}>
      {visibleInstances.map((instance) => (
        <md-list-item
          className={instance.name === selectedInstance ? 'active' : ''}
          key={instance.name}
          type="button"
          onClick={() => onSelect(instance.name)}
          title={instance.name}
        >
          <MaterialIcon name="devices" slot="start" filled={instance.name === selectedInstance} />
          {instance.name}
        </md-list-item>
      ))}
    </md-list>
  );
}
