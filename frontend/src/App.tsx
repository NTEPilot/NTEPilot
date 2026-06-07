import { useState } from 'react';
import { Play, Plus, Save, Square, Wifi, WifiOff } from 'lucide-react';
import { ConfigPanel } from './components/ConfigPanel';
import { InstanceTabs } from './components/InstanceTabs';
import { ConsolePanel } from './components/ConsolePanel';
import { useWebSocketBridge } from './lib/useWebSocketBridge';

export function App() {
  const bridge = useWebSocketBridge();
  const [activePage, setActivePage] = useState<'general' | 'tools'>('general');
  const fishTask = bridge.tasks.find((task) => task.id === 'fish');
  const connected = bridge.status === 'open';
  const fishRunning = bridge.backendStatus.activeTask === 'fish';
  const statusText = {
    idle: '未连接',
    connecting: '连接中',
    open: '已连接',
    closed: '已断开',
    error: '连接错误',
  }[bridge.status];
  const activeTaskText = bridge.backendStatus.activeTask === 'fish'
    ? '钓鱼'
    : bridge.backendStatus.activeTask && bridge.backendStatus.activeTask !== 'idle'
      ? bridge.backendStatus.activeTask
      : '空闲';

  return (
    <div className="app-shell">
      <aside className="instance-rail" aria-label="实例">
        <div className="rail-title">实例</div>
        <InstanceTabs
          instances={bridge.instances}
          selectedInstance={bridge.selectedInstance}
          onSelect={bridge.setSelectedInstance}
        />
        <button
          className="rail-add"
          type="button"
          onClick={() => {
            const name = window.prompt('新实例名称');
            if (name?.trim()) bridge.createInstance(name.trim());
          }}
          title="创建实例"
        >
          <Plus size={18} />
        </button>
      </aside>

      <main className="workbench">
        <div className="run-bar">
          <div className="run-meta">
            <strong>{bridge.selectedInstance}</strong>
            <span>当前任务：{activeTaskText}</span>
          </div>
          <div className={`connection-state state-${bridge.status}`} title={bridge.url}>
            {connected ? <Wifi size={16} /> : <WifiOff size={16} />}
            {statusText}
          </div>
        </div>

        <div className="config-layout">
          <nav className="page-tabs" aria-label="配置页面">
            <button className={activePage === 'general' ? 'active' : ''} type="button" onClick={() => setActivePage('general')}>
              通用配置
            </button>
            <button className={activePage === 'tools' ? 'active' : ''} type="button" onClick={() => setActivePage('tools')}>
              工具
            </button>
          </nav>

          <section className="config-surface">
            <div className="surface-heading">
              <h1>{activePage === 'general' ? '通用配置' : '工具'}</h1>
              <button className="save-button" type="button" onClick={bridge.saveConfig}>
                <Save size={17} />
                保存
              </button>
            </div>
            {activePage === 'general' ? (
              <ConfigPanel
                fields={bridge.groupedFields.general ?? []}
                values={bridge.values}
                onChange={bridge.updateValue}
              />
            ) : (
              <div className="tool-list">
                <article className="tool-item">
                  <div className="tool-row">
                    <div>
                      <h2>钓鱼</h2>
                      <span>{fishTask?.description ?? '运行钓鱼工具'}</span>
                    </div>
                    <button
                      className={`tool-start${fishRunning ? ' is-running' : ''}`}
                      type="button"
                      onClick={() => {
                        if (fishRunning) bridge.stopTask(fishTask?.id ?? 'fish');
                        else bridge.startTask(fishTask?.id ?? 'fish');
                      }}
                    >
                      {fishRunning ? <Square size={17} /> : <Play size={17} />}
                      {fishRunning ? '停止' : '启动'}
                    </button>
                  </div>
                  <details className="tool-config">
                    <summary>钓鱼配置</summary>
                    <ConfigPanel
                      fields={bridge.groupedFields.fish ?? []}
                      values={bridge.values}
                      onChange={bridge.updateValue}
                    />
                  </details>
                </article>
              </div>
            )}
          </section>
        </div>
      </main>

      <ConsolePanel logs={bridge.logs} />
    </div>
  );
}
