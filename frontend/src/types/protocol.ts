export type ConnectionStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

export type ConfigFieldType = 'text' | 'number' | 'boolean';

export interface BackendInstance {
  name: string;
  path?: string;
}

export interface ConfigField {
  key: string;
  label: string;
  type: ConfigFieldType;
  group: string;
  description?: string;
  value: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
}

export interface BackendTask {
  id: string;
  title: string;
  description?: string;
}

export interface BackendStatus {
  device?: string;
  packageName?: string;
  activeTask?: string;
}

export interface LogEvent {
  id: string;
  time: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'success';
  source?: string;
  message: string;
  ansi?: string;
}

export interface TaskEvent {
  id: string;
  title: string;
  status: 'queued' | 'running' | 'done' | 'error' | 'cancelled';
  detail?: string;
  updatedAt: string;
}

export type BackendMessage =
  | {
      type: 'hello';
      app?: string;
      version?: string;
      currentInstance?: string;
      instances?: BackendInstance[];
      status?: BackendStatus;
    }
  | { type: 'instance.list'; instances: BackendInstance[] }
  | { type: 'config.schema'; instance: string; fields: ConfigField[] }
  | { type: 'task.catalog'; tasks: BackendTask[] }
  | { type: 'status'; instance: string; status: BackendStatus }
  | { type: 'log'; event: Omit<LogEvent, 'id' | 'time'> & Partial<Pick<LogEvent, 'id' | 'time'>> }
  | { type: 'task'; instance: string; task: Omit<TaskEvent, 'updatedAt'> & Partial<Pick<TaskEvent, 'updatedAt'>> }
  | { type: 'call.result'; requestId: string; ok: boolean; result?: unknown; error?: string };

export interface FrontendHello {
  type: 'hello';
  client: 'ntepilot-frontend';
  version: string;
  wants: string[];
}

export interface InstanceListMessage {
  type: 'instance.list';
}

export interface InstanceCreateMessage {
  type: 'instance.create';
  requestId: string;
  name: string;
}

export interface ConfigGetMessage {
  type: 'config.get';
  instance: string;
}

export interface ConfigUpdateMessage {
  type: 'config.update';
  requestId: string;
  instance: string;
  values: Record<string, string | number | boolean>;
}

export interface TaskListMessage {
  type: 'task.list';
}

export interface TaskStartMessage {
  type: 'task.start';
  requestId: string;
  instance: string;
  taskId: string;
  values?: Record<string, string | number | boolean>;
}

export interface TaskStopMessage {
  type: 'task.stop';
  requestId: string;
  instance: string;
  taskId: string;
}

export type FrontendMessage =
  | FrontendHello
  | InstanceListMessage
  | InstanceCreateMessage
  | ConfigGetMessage
  | ConfigUpdateMessage
  | TaskListMessage
  | TaskStartMessage
  | TaskStopMessage;
