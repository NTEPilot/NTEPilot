import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type {
  BackendInstance,
  BackendMessage,
  BackendStatus,
  BackendTask,
  ConfigField,
  ConnectionStatus,
  FrontendMessage,
  LogEvent,
  TaskEvent,
} from '../types/protocol';

const CLIENT_VERSION = '0.4.0';
const SELECTED_INSTANCE_KEY = 'ntepilot.selectedInstance';

type ConfigValues = Record<string, string | number | boolean>;

function defaultWsUrl() {
  const override = new URLSearchParams(window.location.search).get('ws');
  if (override) return override;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
}

function normalizeLog(event: BackendMessage & { type: 'log' }): LogEvent {
  return {
    id: event.event.id ?? crypto.randomUUID(),
    time: event.event.time ?? new Date().toISOString(),
    level: event.event.level,
    source: event.event.source,
    message: event.event.message,
    ansi: event.event.ansi,
  };
}

function normalizeTask(event: BackendMessage & { type: 'task' }): TaskEvent {
  return {
    ...event.task,
    updatedAt: event.task.updatedAt ?? new Date().toISOString(),
  };
}

export function useWebSocketBridge(initialUrl = defaultWsUrl()) {
  const [url, setUrl] = useState(initialUrl);
  const [status, setStatus] = useState<ConnectionStatus>('idle');
  const [selectedInstance, setSelectedInstanceState] = useState(() => localStorage.getItem(SELECTED_INSTANCE_KEY) || 'NTE');
  const [instances, setInstances] = useState<BackendInstance[]>([]);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({});
  const [fields, setFields] = useState<ConfigField[]>([]);
  const [values, setValues] = useState<ConfigValues>({});
  const [tasks, setTasks] = useState<BackendTask[]>([]);
  const [taskEvents, setTaskEvents] = useState<Record<string, TaskEvent[]>>({});
  const [logs, setLogs] = useState<LogEvent[]>([
    {
      id: 'local-boot',
      time: new Date().toISOString(),
      level: 'info',
      source: '前端',
      message: `前端已加载。WebSocket 地址：${initialUrl}`,
    },
  ]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);
  const manuallyClosed = useRef(false);
  const selectedInstanceRef = useRef(selectedInstance);
  const valuesRef = useRef(values);

  useEffect(() => {
    selectedInstanceRef.current = selectedInstance;
    localStorage.setItem(SELECTED_INSTANCE_KEY, selectedInstance);
  }, [selectedInstance]);

  useEffect(() => {
    valuesRef.current = values;
  }, [values]);

  const appendLog = useCallback((entry: Omit<LogEvent, 'id' | 'time'> & Partial<Pick<LogEvent, 'id' | 'time'>>) => {
    setLogs((current) => [
      ...current,
      {
        id: entry.id ?? crypto.randomUUID(),
        time: entry.time ?? new Date().toISOString(),
        level: entry.level,
        source: entry.source,
        message: entry.message,
        ansi: entry.ansi,
      },
    ].slice(-1000));
  }, []);

  const send = useCallback((message: FrontendMessage) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      appendLog({ level: 'warning', source: '前端', message: 'WebSocket 未连接。' });
      return false;
    }

    socket.send(JSON.stringify(message));
    return true;
  }, [appendLog]);

  const requestConfig = useCallback((instance: string) => {
    send({ type: 'config.get', instance });
  }, [send]);

  const setSelectedInstance = useCallback((instance: string) => {
    setSelectedInstanceState(instance);
    setFields([]);
    setValues({});
    requestConfig(instance);
  }, [requestConfig]);

  const applySchema = useCallback((instance: string, incomingFields: ConfigField[]) => {
    if (instance !== selectedInstanceRef.current) {
      return;
    }
    setFields(incomingFields);
    setValues(
      incomingFields.reduce<ConfigValues>((next, field) => {
        next[field.key] = field.value;
        return next;
      }, {}),
    );
  }, []);

  const handleMessage = useCallback((raw: MessageEvent<string>) => {
    let message: BackendMessage;
    try {
      message = JSON.parse(raw.data) as BackendMessage;
    } catch {
      appendLog({ level: 'error', source: '前端', message: `无法解析后端消息：${raw.data}` });
      return;
    }

    switch (message.type) {
      case 'hello':
        if (message.instances) setInstances(message.instances);
        if (message.currentInstance && !localStorage.getItem(SELECTED_INSTANCE_KEY)) {
          setSelectedInstanceState(message.currentInstance);
        }
        if (message.status) setBackendStatus(message.status);
        appendLog({
          level: 'success',
          source: message.app ?? '后端',
          message: `连接成功${message.version ? `，后端版本 ${message.version}` : ''}。`,
        });
        break;
      case 'instance.list':
        setInstances(message.instances);
        if (!message.instances.some((item) => item.name === selectedInstanceRef.current) && message.instances[0]) {
          setSelectedInstance(message.instances[0].name);
        }
        break;
      case 'config.schema':
        applySchema(message.instance, message.fields);
        break;
      case 'task.catalog':
        setTasks(message.tasks);
        break;
      case 'status':
        if (message.instance === selectedInstanceRef.current) {
          setBackendStatus(message.status);
        }
        break;
      case 'log':
        setLogs((current) => [...current, normalizeLog(message)].slice(-1000));
        break;
      case 'task':
        setTaskEvents((current) => {
          const existing = current[message.instance] ?? [];
          const next = normalizeTask(message);
          const index = existing.findIndex((task) => task.id === next.id);
          const updated = [...existing];
          if (index === -1) updated.push(next);
          else updated[index] = next;
          return { ...current, [message.instance]: updated.slice(-100) };
        });
        break;
      case 'call.result':
        appendLog({
          level: message.ok ? 'success' : 'error',
          source: '后端',
          message: message.ok ? `操作完成：${message.requestId}` : `操作失败：${message.error ?? message.requestId}`,
        });
        break;
      default:
        appendLog({ level: 'warning', source: '前端', message: '收到未知消息类型。' });
    }
  }, [appendLog, applySchema, setSelectedInstance]);

  const connect = useCallback((nextUrl = url) => {
    if (reconnectTimer.current) {
      window.clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    manuallyClosed.current = false;
    socketRef.current?.close();
    setStatus('connecting');
    setUrl(nextUrl);

    const socket = new WebSocket(nextUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus('open');
      send({
        type: 'hello',
        client: 'ntepilot-frontend',
        version: CLIENT_VERSION,
        wants: ['instances', 'config', 'tasks', 'logs', 'status'],
      });
      send({ type: 'instance.list' });
      send({ type: 'config.get', instance: selectedInstanceRef.current });
      send({ type: 'task.list' });
    };

    socket.onmessage = handleMessage;
    socket.onerror = () => {
      setStatus('error');
      appendLog({ level: 'error', source: '前端', message: `连接失败：${nextUrl}` });
    };
    socket.onclose = () => {
      setStatus((current) => (current === 'error' ? 'error' : 'closed'));
      if (!manuallyClosed.current) {
        reconnectTimer.current = window.setTimeout(() => connect(nextUrl), 2500);
      }
    };
  }, [appendLog, handleMessage, send, url]);

  const disconnect = useCallback(() => {
    manuallyClosed.current = true;
    if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current);
    reconnectTimer.current = null;
    socketRef.current?.close();
    socketRef.current = null;
    setStatus('closed');
  }, []);

  const updateValue = useCallback((key: string, value: string | number | boolean) => {
    setValues((current) => ({ ...current, [key]: value }));
  }, []);

  const saveConfig = useCallback(() => {
    const requestId = crypto.randomUUID();
    send({ type: 'config.update', requestId, instance: selectedInstanceRef.current, values: valuesRef.current });
    appendLog({ level: 'info', source: '前端', message: `已请求保存实例配置：${selectedInstanceRef.current}。` });
  }, [appendLog, send]);

  const createInstance = useCallback((name: string) => {
    const requestId = crypto.randomUUID();
    send({ type: 'instance.create', requestId, name });
    setSelectedInstanceState(name);
    setFields([]);
    setValues({});
  }, [send]);

  const startTask = useCallback((taskId: string) => {
    const requestId = crypto.randomUUID();
    send({ type: 'task.start', requestId, instance: selectedInstanceRef.current, taskId, values: valuesRef.current });
    appendLog({ level: 'info', source: '前端', message: `已请求启动任务：${selectedInstanceRef.current}/${taskId}` });
  }, [appendLog, send]);

  const stopTask = useCallback((taskId: string) => {
    const requestId = crypto.randomUUID();
    send({ type: 'task.stop', requestId, instance: selectedInstanceRef.current, taskId });
    appendLog({ level: 'info', source: '前端', message: `已请求停止任务：${selectedInstanceRef.current}/${taskId}` });
  }, [appendLog, send]);

  useEffect(() => {
    connect(initialUrl);
    return () => disconnect();
  }, []);

  const groupedFields = useMemo(() => {
    return fields.reduce<Record<string, ConfigField[]>>((groups, field) => {
      groups[field.group] = groups[field.group] ?? [];
      groups[field.group].push(field);
      return groups;
    }, {});
  }, [fields]);

  return {
    url,
    setUrl,
    status,
    selectedInstance,
    instances,
    backendStatus,
    fields,
    groupedFields,
    values,
    tasks,
    taskEvents: taskEvents[selectedInstance] ?? [],
    logs,
    connect,
    disconnect,
    setSelectedInstance,
    createInstance,
    updateValue,
    saveConfig,
    startTask,
    stopTask,
  };
}
