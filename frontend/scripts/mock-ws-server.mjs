import { WebSocketServer } from 'ws';

const port = Number(process.env.NTEPILOT_WS_PORT ?? 9150);
const server = new WebSocketServer({ host: '127.0.0.1', port });

const instances = {
  NTE: {
    general: {
      name: 'NTE',
      serial: '127.0.0.1:16448',
      package_name: 'com.pwrd.cloud.yh.laohu',
      activity_name: 'com.pwrd.cloudgame.client_core.ui.HomeActivity',
      websocket_host: '127.0.0.1',
      websocket_port: 9150,
    },
    tools: {
      fish: {
        sell_fish: true,
        buy_bait: true,
        buy_bait_stack_count: 5,
        green_bar_safe_proportion: 0.4,
      },
    },
  },
};

const fields = [
  { key: 'general.serial', label: '设备序列号', type: 'text', group: 'general', description: 'ADB 设备或模拟器序列号' },
  { key: 'general.package_name', label: '应用包名', type: 'text', group: 'general' },
  { key: 'general.activity_name', label: '启动 Activity', type: 'text', group: 'general' },
  { key: 'general.websocket_host', label: '监听地址', type: 'text', group: 'general' },
  { key: 'general.websocket_port', label: '监听端口', type: 'number', group: 'general', min: 1, max: 65535, step: 1 },
  { key: 'tools.fish.sell_fish', label: '自动卖鱼', type: 'boolean', group: 'fish' },
  { key: 'tools.fish.buy_bait', label: '自动买鱼饵', type: 'boolean', group: 'fish' },
  { key: 'tools.fish.buy_bait_stack_count', label: '鱼饵购买组数', type: 'number', group: 'fish', min: 1, max: 20, step: 1 },
  { key: 'tools.fish.green_bar_safe_proportion', label: '绿条安全比例', type: 'number', group: 'fish', min: 0, max: 1, step: 0.05 },
];

const tasks = [
  {
    id: 'fish',
    title: '钓鱼',
    description: '运行钓鱼工具',
  },
];
const activeTasks = {};

function instanceList() {
  return Object.keys(instances).map((name) => ({ name: instances[name].general.name }));
}

function getPath(data, path) {
  return path.split('.').reduce((current, part) => current?.[part], data);
}

function setPath(data, path, value) {
  const parts = path.split('.');
  let current = data;
  for (const part of parts.slice(0, -1)) {
    current[part] ??= {};
    current = current[part];
  }
  current[parts.at(-1)] = value;
}

function updateConfig(instance, values = {}) {
  instances[instance] = structuredClone(instances[instance] ?? instances.NTE);
  instances[instance].general.name = instance;
  for (const [key, value] of Object.entries(values)) {
    setPath(instances[instance], key, value);
  }
}

function schema(instance = 'NTE') {
  const config = instances[instance] ?? instances.NTE;
  return fields.map((field) => ({ ...field, value: getPath(config, field.key) }));
}

function status(instance = 'NTE', activeTask = 'idle') {
  const config = instances[instance] ?? instances.NTE;
  return {
    device: config.general.serial,
    packageName: config.general.package_name,
    activeTask,
  };
}

function send(ws, message) {
  if (ws.readyState === ws.OPEN) {
    ws.send(JSON.stringify(message));
  }
}

server.on('connection', (ws) => {
  send(ws, {
    type: 'hello',
    app: 'NTEPilot mock backend',
    version: '0.4.0',
    currentInstance: 'NTE',
    instances: instanceList(),
    status: status('NTE'),
  });
  send(ws, { type: 'instance.list', instances: instanceList() });
  send(ws, { type: 'config.schema', instance: 'NTE', fields: schema('NTE') });
  send(ws, { type: 'task.catalog', tasks });
  send(ws, {
    type: 'log',
    event: {
      level: 'info',
      source: 'mock',
      message: '模拟服务已就绪',
      ansi: '\u001b[38;2;114;223;189m模拟服务已就绪\u001b[0m',
      time: new Date().toISOString(),
    },
  });

  ws.on('message', (buffer) => {
    let message;
    try {
      message = JSON.parse(buffer.toString());
    } catch {
      send(ws, { type: 'log', event: { level: 'error', source: 'mock', message: '无效 JSON', time: new Date().toISOString() } });
      return;
    }

    const instance = message.instance || 'NTE';

    if (message.type === 'instance.list') {
      send(ws, { type: 'instance.list', instances: instanceList() });
      return;
    }

    if (message.type === 'instance.create') {
      updateConfig(message.name);
      send(ws, { type: 'instance.list', instances: instanceList() });
      send(ws, { type: 'config.schema', instance: message.name, fields: schema(message.name) });
      send(ws, { type: 'call.result', requestId: message.requestId, ok: true, result: { instance: message.name } });
      return;
    }

    if (message.type === 'config.get') {
      send(ws, { type: 'config.schema', instance, fields: schema(instance) });
      return;
    }

    if (message.type === 'task.list') {
      send(ws, { type: 'task.catalog', tasks });
      return;
    }

    if (message.type === 'config.update') {
      updateConfig(instance, message.values);
      send(ws, { type: 'config.schema', instance, fields: schema(instance) });
      send(ws, { type: 'status', instance, status: status(instance) });
      send(ws, { type: 'call.result', requestId: message.requestId, ok: true, result: { updated: true, instance } });
      return;
    }

    if (message.type === 'task.start') {
      updateConfig(instance, message.values);
      activeTasks[instance] = message.taskId;
      send(ws, { type: 'status', instance, status: status(instance, message.taskId) });
      send(ws, {
        type: 'task',
        instance,
        task: { id: message.taskId, title: '钓鱼', status: 'running', detail: '任务已启动', updatedAt: new Date().toISOString() },
      });
      send(ws, { type: 'call.result', requestId: message.requestId, ok: true, result: { instance, taskId: message.taskId, status: 'running' } });
      return;
    }

    if (message.type === 'task.stop') {
      delete activeTasks[instance];
      send(ws, { type: 'status', instance, status: status(instance) });
      send(ws, {
        type: 'task',
        instance,
        task: { id: message.taskId, title: '钓鱼', status: 'cancelled', detail: '任务已停止', updatedAt: new Date().toISOString() },
      });
      send(ws, { type: 'call.result', requestId: message.requestId, ok: true, result: { instance, taskId: message.taskId, status: 'aborted' } });
    }
  });
});

console.log(`mock websocket server listening on ws://127.0.0.1:${port}`);
