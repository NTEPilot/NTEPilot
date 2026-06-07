import { useEffect, useRef, useState } from 'react';
import { ConfigPanel } from './components/ConfigPanel';
import { InstanceTabs } from './components/InstanceTabs';
import { ConsolePanel } from './components/ConsolePanel';
import { MaterialIcon } from './components/MaterialIcon';
import { useMotionParent } from './lib/useMotionParent';
import { useWebSocketBridge } from './lib/useWebSocketBridge';
import { useThemeMode } from './lib/useThemeMode';

type PageId = 'general' | 'tools';

interface MaterialDialogElement extends HTMLElement {
  show: () => Promise<void>;
  close: (returnValue?: string) => Promise<void>;
}

interface MaterialTabsElement extends HTMLElement {
  activeTabIndex: number;
}

interface TextFieldElement extends HTMLElement {
  value: string;
}

const PAGES: Array<{ id: PageId; label: string; icon: string }> = [
  { id: 'general', label: '通用配置', icon: 'tune' },
  { id: 'tools', label: '工具', icon: 'construction' },
];

export function App() {
  const bridge = useWebSocketBridge();
  const { isDark, toggleTheme } = useThemeMode();
  const [activePage, setActivePage] = useState<PageId>('general');
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [fishConfigOpen, setFishConfigOpen] = useState(false);
  const [newInstanceName, setNewInstanceName] = useState('');
  const [shellRef] = useMotionParent<HTMLDivElement>();
  const [topMetaRef] = useMotionParent<HTMLDivElement>();
  const [contentRef] = useMotionParent<HTMLElement>();
  const [toolListRef] = useMotionParent<HTMLDivElement>();
  const [toolConfigRef] = useMotionParent<HTMLDivElement>();
  const dialogRef = useRef<MaterialDialogElement | null>(null);
  const newInstanceInputRef = useRef<TextFieldElement | null>(null);
  const tabsRef = useRef<MaterialTabsElement | null>(null);
  const fishTask = bridge.tasks.find((task) => task.id === 'fish');
  const connected = bridge.status === 'open';
  const fishRunning = bridge.backendStatus.activeTask === 'fish';
  const activePageIndex = PAGES.findIndex((page) => page.id === activePage);
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

  useEffect(() => {
    if (tabsRef.current && tabsRef.current.activeTabIndex !== activePageIndex) {
      tabsRef.current.activeTabIndex = activePageIndex;
    }
  }, [activePageIndex]);

  function openCreateDialog() {
    setNewInstanceName('');
    void dialogRef.current?.show();
    window.setTimeout(() => newInstanceInputRef.current?.focus(), 60);
  }

  function createInstance() {
    const name = (newInstanceInputRef.current?.value ?? newInstanceName).trim();
    if (!name) return;
    bridge.createInstance(name);
    void dialogRef.current?.close('create');
  }

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return undefined;
    const handleClosed = () => {
      setNewInstanceName('');
      if (newInstanceInputRef.current) newInstanceInputRef.current.value = '';
    };
    dialog.addEventListener('closed', handleClosed);
    return () => dialog.removeEventListener('closed', handleClosed);
  }, []);

  return (
    <div className={`app-shell${consoleOpen ? ' console-open' : ''}`} ref={shellRef}>
      <aside className="instance-rail" aria-label="实例导航">
        <div className="brand-mark" aria-label="NTEPilot">
          <span className="brand-logo">N</span>
          <div>
            <strong>NTEPilot</strong>
            <span>控制台</span>
          </div>
        </div>

        <div className="rail-section-title">实例</div>
        <InstanceTabs
          instances={bridge.instances}
          selectedInstance={bridge.selectedInstance}
          onSelect={bridge.setSelectedInstance}
        />
        <md-outlined-button className="rail-add" hasIcon onClick={openCreateDialog}>
          <MaterialIcon name="add" slot="icon" />
          新建实例
        </md-outlined-button>
      </aside>

      <main className="workbench">
        <header className="top-app-bar">
          <div className="top-title">
            <span className="eyebrow">当前实例</span>
            <h1>{bridge.selectedInstance}</h1>
          </div>
          <div className="top-meta" ref={topMetaRef}>
            <div className="status-chip" title={bridge.url}>
              <MaterialIcon name={connected ? 'wifi' : 'wifi_off'} filled={connected} />
              <span>{statusText}</span>
            </div>
            <div className="task-chip">
              <MaterialIcon name="radio_button_checked" />
              <span>任务：{activeTaskText}</span>
            </div>
          </div>
          <div className="top-actions">
            <md-icon-button aria-label={isDark ? '切换到亮色主题' : '切换到暗色主题'} onClick={toggleTheme}>
              <MaterialIcon name={isDark ? 'light_mode' : 'dark_mode'} />
            </md-icon-button>
            <md-icon-button aria-label="打开同步控制台" onClick={() => setConsoleOpen(true)}>
              <MaterialIcon name="terminal" />
            </md-icon-button>
            <md-filled-button className="save-action" hasIcon onClick={bridge.saveConfig}>
              <MaterialIcon name="save" slot="icon" />
              保存
            </md-filled-button>
          </div>
        </header>

        <section className="page-strip" aria-label="配置页面">
          <md-tabs
            ref={tabsRef}
            activeTabIndex={activePageIndex}
            onChange={(event) => {
              const index = (event.currentTarget as MaterialTabsElement).activeTabIndex;
              setActivePage(PAGES[index]?.id ?? 'general');
            }}
          >
            {PAGES.map((page) => (
              <md-primary-tab key={page.id}>
                <MaterialIcon name={page.icon} slot="icon" filled={activePage === page.id} />
                {page.label}
              </md-primary-tab>
            ))}
          </md-tabs>
        </section>

        <section className="content-surface" ref={contentRef}>
          <div className="surface-heading">
            <div>
              <span className="eyebrow">{activePage === 'general' ? 'General' : 'Tools'}</span>
              <h2>{activePage === 'general' ? '通用配置' : '工具'}</h2>
            </div>
          </div>

          {activePage === 'general' ? (
            <ConfigPanel
              fields={bridge.groupedFields.general ?? []}
              values={bridge.values}
              onChange={bridge.updateValue}
            />
          ) : (
            <div className="tool-list" ref={toolListRef}>
              <article className="tool-item">
                <div className="tool-row">
                  <div className="tool-title">
                    <div>
                      <h3>{fishTask?.title ?? '钓鱼'}</h3>
                      <span>{fishTask?.description ?? '运行钓鱼工具'}</span>
                    </div>
                  </div>
                  {fishRunning ? (
                    <md-filled-tonal-button className="danger-action" hasIcon onClick={() => bridge.stopTask(fishTask?.id ?? 'fish')}>
                      <MaterialIcon name="stop" slot="icon" />
                      停止
                    </md-filled-tonal-button>
                  ) : (
                    <md-filled-button hasIcon onClick={() => bridge.startTask(fishTask?.id ?? 'fish')}>
                      <MaterialIcon name="play_arrow" slot="icon" filled />
                      启动
                    </md-filled-button>
                  )}
                </div>
                <md-divider />
                <div className="tool-config" ref={toolConfigRef}>
                  <button
                    aria-expanded={fishConfigOpen}
                    className="tool-config-toggle"
                    onClick={() => setFishConfigOpen((current) => !current)}
                    type="button"
                  >
                    <span>钓鱼配置</span>
                    <MaterialIcon name={fishConfigOpen ? 'expand_less' : 'expand_more'} />
                  </button>
                  {fishConfigOpen && (
                  <ConfigPanel
                    fields={bridge.groupedFields.fish ?? []}
                    values={bridge.values}
                    onChange={bridge.updateValue}
                  />
                  )}
                </div>
              </article>
            </div>
          )}
        </section>
      </main>

      {consoleOpen && (
        <ConsolePanel logs={bridge.logs} onClose={() => setConsoleOpen(false)} />
      )}

      <md-dialog
        ref={dialogRef}
      >
        <div slot="headline">新建实例</div>
        <form
          className="dialog-content"
          id="create-instance-form"
          slot="content"
          onSubmit={(event) => {
            event.preventDefault();
            createInstance();
          }}
        >
          <md-outlined-text-field
            ref={newInstanceInputRef}
            autoFocus
            label="实例名称"
            value={newInstanceName}
            onInput={(event) => setNewInstanceName((event.currentTarget as TextFieldElement).value)}
            onChange={(event) => setNewInstanceName((event.currentTarget as TextFieldElement).value)}
          />
        </form>
        <div slot="actions">
          <md-text-button onClick={() => void dialogRef.current?.close('cancel')}>取消</md-text-button>
          <md-filled-button onClick={createInstance}>创建</md-filled-button>
        </div>
      </md-dialog>
    </div>
  );
}
