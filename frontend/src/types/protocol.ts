export type ConnectionStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

export type ConfigFieldType = 'text' | 'integer' | 'float' | 'boolean' | 'select';

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
  options?: string[];
}

export interface BackendTask {
  id: string;
  title: string;
  description?: string;
  configGroup?: string;
}

export interface BackendStatus {
  device?: string;
  activeTask?: string;
  scheduler?: SchedulerStatus;
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
  source?: 'manual' | 'scheduler';
  planId?: string;
}

export type SchedulerStatus = 'disabled' | 'idle' | 'waiting' | 'running' | 'error';

export interface SchedulerPlan {
  id: string;
  taskId: string;
  time: string;
  priority: number;
  last_run_date?: string;
  values?: Record<string, string | number | boolean>;
}

export interface BackendSchedulerState {
  enabled: boolean;
  status: SchedulerStatus;
  plans: SchedulerPlan[];
  activePlanId?: string;
  lastError?: string;
  updatedAt?: string;
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
  | { type: 'scheduler.catalog'; tasks: BackendTask[] }
  | { type: 'scheduler.state'; instance: string; scheduler: BackendSchedulerState }
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
  requestId?: string;
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

export interface SchedulerCatalogMessage {
  type: 'scheduler.catalog';
}

export interface SchedulerGetMessage {
  type: 'scheduler.get';
  instance: string;
}

export interface SchedulerSetEnabledMessage {
  type: 'scheduler.set_enabled';
  requestId: string;
  instance: string;
  enabled: boolean;
}

export interface SchedulerPlanAddMessage {
  type: 'scheduler.plan.add';
  requestId: string;
  instance: string;
  taskId: string;
  time: string;
  priority: number;
  values?: Record<string, string | number | boolean>;
}

export interface SchedulerPlanUpdateMessage {
  type: 'scheduler.plan.update';
  requestId: string;
  instance: string;
  planId: string;
  taskId: string;
  time: string;
  priority: number;
  values?: Record<string, string | number | boolean>;
}

export interface SchedulerPlanRemoveMessage {
  type: 'scheduler.plan.remove';
  requestId: string;
  instance: string;
  planId: string;
}

export interface SchedulerPlanRunMessage {
  type: 'scheduler.plan.run';
  requestId: string;
  instance: string;
  planId: string;
}

export type FrontendMessage =
  | FrontendHello
  | InstanceListMessage
  | InstanceCreateMessage
  | ConfigGetMessage
  | ConfigUpdateMessage
  | TaskListMessage
  | TaskStartMessage
  | TaskStopMessage
  | SchedulerCatalogMessage
  | SchedulerGetMessage
  | SchedulerSetEnabledMessage
  | SchedulerPlanAddMessage
  | SchedulerPlanUpdateMessage
  | SchedulerPlanRemoveMessage
  | SchedulerPlanRunMessage;
