import { useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import { ConfigPanel } from './components/ConfigPanel';
import { ConsolePanel } from './components/ConsolePanel';
import { InstanceTabs } from './components/InstanceTabs';
import { MaterialIcon } from './components/MaterialIcon';
import { Switch } from './components/Switch';
import { useMotionParent } from './lib/useMotionParent';
import { useThemeMode } from './lib/useThemeMode';
import { useWebSocketBridge } from './lib/useWebSocketBridge';
import type { BackendTask, SchedulerPlan } from './types/protocol';

type PageId = 'general' | 'team' | 'tools' | 'plan';

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

const PAGES: Array<{ id: PageId; label: string; icon: string; eyebrow: string }> = [
  { id: 'general', label: '通用配置', icon: 'tune', eyebrow: 'General' },
  { id: 'team', label: '队伍', icon: 'groups', eyebrow: 'Team' },
  { id: 'tools', label: '工具', icon: 'construction', eyebrow: 'Tools' },
  { id: 'plan', label: '计划', icon: 'event_repeat', eyebrow: 'Plan' },
];

const CONSOLE_WIDTH_KEY = 'ntepilot.logPanelWidth';
const DEFAULT_CONSOLE_WIDTH = 440;
const MIN_CONSOLE_WIDTH = 320;
const MAX_CONSOLE_WIDTH = 960;
const DEFAULT_PLAN_TIME = '00:00';
const DEFAULT_PLAN_PRIORITY = 0;

function clampConsoleWidth(width: number) {
  const viewportLimit = typeof window === 'undefined' ? MAX_CONSOLE_WIDTH : Math.max(MIN_CONSOLE_WIDTH, window.innerWidth - 48);
  return Math.min(Math.max(width, MIN_CONSOLE_WIDTH), Math.min(MAX_CONSOLE_WIDTH, viewportLimit));
}

function readConsoleWidth() {
  const saved = Number(localStorage.getItem(CONSOLE_WIDTH_KEY));
  return Number.isFinite(saved) && saved > 0 ? clampConsoleWidth(saved) : DEFAULT_CONSOLE_WIDTH;
}

export function App() {
  const bridge = useWebSocketBridge();
  const { isDark, toggleTheme } = useThemeMode();
  const [activePage, setActivePage] = useState<PageId>('general');
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [consoleWidth, setConsoleWidth] = useState(readConsoleWidth);
  const [openToolConfigs, setOpenToolConfigs] = useState<Record<string, boolean>>({});
  const [newInstanceName, setNewInstanceName] = useState('');
  const [selectedPlanTask, setSelectedPlanTask] = useState<BackendTask | null>(null);
  const [editingPlan, setEditingPlan] = useState<SchedulerPlan | null>(null);
  const [planTime, setPlanTime] = useState(DEFAULT_PLAN_TIME);
  const [planPriority, setPlanPriority] = useState(DEFAULT_PLAN_PRIORITY);
  const [planValues, setPlanValues] = useState<Record<string, string | number | boolean>>({});
  const [shellRef] = useMotionParent<HTMLDivElement>();
  const [topMetaRef] = useMotionParent<HTMLDivElement>();
  const [contentRef] = useMotionParent<HTMLElement>();
  const [toolListRef] = useMotionParent<HTMLDivElement>();
  const [planListRef] = useMotionParent<HTMLDivElement>();
  const createDialogRef = useRef<MaterialDialogElement | null>(null);
  const planDialogRef = useRef<MaterialDialogElement | null>(null);
  const newInstanceInputRef = useRef<TextFieldElement | null>(null);
  const planTimeInputRef = useRef<TextFieldElement | null>(null);
  const tabsRef = useRef<MaterialTabsElement | null>(null);
  const connected = bridge.status === 'open';
  const activePageIndex = PAGES.findIndex((page) => page.id === activePage);
  const activePageMeta = PAGES[activePageIndex] ?? PAGES[0];
  const shellStyle = { '--app-console-width': `${consoleWidth}px` } as CSSProperties;
  const taskTitleById = useMemo(() => {
    return [...bridge.tasks, ...bridge.scheduleTasks].reduce<Record<string, string>>((titles, task) => {
      titles[task.id] = task.title;
      return titles;
    }, {});
  }, [bridge.tasks, bridge.scheduleTasks]);
  const statusText = {
    idle: '未连接',
    connecting: '连接中',
    open: '已连接',
    closed: '已断开',
    error: '连接错误',
  }[bridge.status];
  const schedulerStatus = bridge.backendStatus.scheduler ?? bridge.scheduler.status;
  const schedulerStatusText = {
    disabled: '关闭',
    idle: '开启',
    waiting: '等待空闲',
    running: '运行中',
    error: '错误',
  }[schedulerStatus ?? 'disabled'];
  const activeTaskText = bridge.backendStatus.activeTask && bridge.backendStatus.activeTask !== 'idle'
    ? (taskTitleById[bridge.backendStatus.activeTask] ?? bridge.backendStatus.activeTask)
    : '空闲';
  const selectedPlanConfigFields = selectedPlanTask
    ? (bridge.groupedFields[selectedPlanTask.configGroup ?? `schedule.${selectedPlanTask.id}`] ?? [])
    : [];
  const sortedPlans = useMemo(() => {
    return [...bridge.scheduler.plans].sort((left, right) => (
      left.time.localeCompare(right.time)
      || right.priority - left.priority
      || left.id.localeCompare(right.id)
    ));
  }, [bridge.scheduler.plans]);

  useEffect(() => {
    if (tabsRef.current && tabsRef.current.activeTabIndex !== activePageIndex) {
      tabsRef.current.activeTabIndex = activePageIndex;
    }
  }, [activePageIndex]);

  useEffect(() => {
    localStorage.setItem(CONSOLE_WIDTH_KEY, String(consoleWidth));
  }, [consoleWidth]);

  useEffect(() => {
    const dialog = createDialogRef.current;
    if (!dialog) return undefined;
    const handleClosed = () => {
      setNewInstanceName('');
      if (newInstanceInputRef.current) newInstanceInputRef.current.value = '';
    };
    dialog.addEventListener('closed', handleClosed);
    return () => dialog.removeEventListener('closed', handleClosed);
  }, []);

  useEffect(() => {
    const dialog = planDialogRef.current;
    if (!dialog) return undefined;
    const handleClosed = () => {
      setSelectedPlanTask(null);
      setEditingPlan(null);
      setPlanTime(DEFAULT_PLAN_TIME);
      setPlanPriority(DEFAULT_PLAN_PRIORITY);
      setPlanValues({});
    };
    dialog.addEventListener('closed', handleClosed);
    return () => dialog.removeEventListener('closed', handleClosed);
  }, []);

  function openCreateDialog() {
    setNewInstanceName('');
    void createDialogRef.current?.show();
    window.setTimeout(() => newInstanceInputRef.current?.focus(), 60);
  }

  function createInstance() {
    const name = (newInstanceInputRef.current?.value ?? newInstanceName).trim();
    if (!name) return;
    bridge.createInstance(name);
    void createDialogRef.current?.close('create');
  }

  function openPlanDialog(task: BackendTask) {
    setSelectedPlanTask(task);
    setEditingPlan(null);
    setPlanTime(DEFAULT_PLAN_TIME);
    setPlanPriority(DEFAULT_PLAN_PRIORITY);
    setPlanValues({ ...bridge.values });
    void planDialogRef.current?.show();
    window.setTimeout(() => planTimeInputRef.current?.focus(), 60);
  }

  function openEditPlan(plan: SchedulerPlan) {
    const task = bridge.scheduleTasks.find((item) => item.id === plan.taskId);
    if (!task) return;
    setSelectedPlanTask(task);
    setEditingPlan(plan);
    setPlanTime(plan.time);
    setPlanPriority(plan.priority);
    setPlanValues({
      ...bridge.values,
      ...(plan.values || {}),
    });
    void planDialogRef.current?.show();
    window.setTimeout(() => planTimeInputRef.current?.focus(), 60);
  }

  function savePlan() {
    if (!selectedPlanTask) return;
    const time = (planTimeInputRef.current?.value ?? planTime).trim();
    if (!time) return;
    if (editingPlan) {
      bridge.updateSchedulePlan(editingPlan.id, selectedPlanTask.id, time, Number(planPriority), planValues);
    } else {
      bridge.addSchedulePlan(selectedPlanTask.id, time, Number(planPriority), planValues);
    }
    void planDialogRef.current?.close(editingPlan ? 'update' : 'create');
  }

  function renderToolsPage() {
    return (
      <div className="tool-list" ref={toolListRef}>
        {bridge.tasks.length === 0 && (
          <div className="empty-state">
            <span className="empty-state-icon material-symbols-outlined" aria-hidden="true">construction</span>
            <span>暂无工具</span>
          </div>
        )}
        {bridge.tasks.map((task) => {
          const configGroup = task.configGroup ?? task.id;
          const configFields = bridge.groupedFields[configGroup] ?? [];
          const configOpen = Boolean(openToolConfigs[task.id]);
          const running = bridge.backendStatus.activeTask === task.id;

          return (
            <article className="tool-item" key={task.id}>
              <div className="tool-row">
                <div className="tool-title">
                  <div>
                    <h3>{task.title}</h3>
                    {task.description && <span>{task.description}</span>}
                  </div>
                </div>
                {running ? (
                  <md-filled-tonal-button className="danger-action" hasIcon onClick={() => bridge.stopTask(task.id)}>
                    <MaterialIcon name="stop" slot="icon" />
                    停止
                  </md-filled-tonal-button>
                ) : (
                  <md-filled-button hasIcon onClick={() => bridge.startTask(task.id)}>
                    <MaterialIcon name="play_arrow" slot="icon" filled />
                    启动
                  </md-filled-button>
                )}
              </div>
              {configFields.length > 0 && (
                <>
                  <md-divider />
                  <div className="tool-config">
                    <button
                      aria-label={`${task.title}配置`}
                      aria-expanded={configOpen}
                      className="tool-config-toggle"
                      onClick={() => setOpenToolConfigs((current) => ({ ...current, [task.id]: !configOpen }))}
                      type="button"
                    >
                      <MaterialIcon name={configOpen ? 'expand_less' : 'expand_more'} />
                    </button>
                    {configOpen && (
                      <ConfigPanel
                        fields={configFields}
                        values={bridge.values}
                        onChange={bridge.updateValue}
                      />
                    )}
                  </div>
                </>
              )}
            </article>
          );
        })}
      </div>
    );
  }

  function renderPlanPage() {
    return (
      <div className="planner-layout">
        <aside className="scheduler-catalog" aria-label="支持的计划任务">
          {bridge.scheduleTasks.length === 0 && (
            <div className="empty-state compact-empty">
              <span>暂无任务</span>
            </div>
          )}
          {bridge.scheduleTasks.map((task) => (
            <article className="scheduler-task" key={task.id}>
              <h4>{task.title}</h4>
              <md-icon-button aria-label={`添加${task.title}计划`} onClick={() => openPlanDialog(task)}>
                <MaterialIcon name="add" />
              </md-icon-button>
            </article>
          ))}
        </aside>

        <section className="plan-board" aria-label="每日计划">
          <div className="scheduler-toolbar">
            <Switch checked={bridge.scheduler.enabled} onChange={bridge.setSchedulerEnabled} ariaLabel="计划器" />
          </div>

          <div className="plan-list" ref={planListRef}>
            {sortedPlans.length === 0 && (
              <div className="empty-state">
                <span className="empty-state-icon material-symbols-outlined" aria-hidden="true">event_repeat</span>
                <span>暂无计划</span>
              </div>
            )}
            {sortedPlans.map((plan) => {
              const running = bridge.scheduler.activePlanId === plan.id;
              const title = taskTitleById[plan.taskId] ?? plan.taskId;
              return (
                <article className="plan-item" key={plan.id}>
                  <div className="plan-main">
                    <h3>{title}</h3>
                    <div className="plan-meta">
                      <span>{plan.time}</span>
                      <span>优先级 {plan.priority}</span>
                      {plan.lastStatus && <span>{plan.lastStatus}</span>}
                    </div>
                    {plan.values && Object.keys(plan.values).length > 0 && (
                      <div className="plan-overrides" style={{ fontSize: '11px', color: 'var(--md-sys-color-on-surface-variant)', display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                        {Object.entries(plan.values).map(([k, v]) => {
                          const f = bridge.fields.find(field => field.key === k);
                          return (
                            <span key={k} style={{ background: 'var(--md-sys-color-surface-container-high, rgba(0,0,0,0.05))', padding: '2px 6px', borderRadius: '4px' }}>
                              {f ? f.label : k}: {String(v)}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  <div className="plan-actions">
                    {running ? (
                      <md-filled-tonal-button className="danger-action" hasIcon onClick={() => bridge.stopTask(plan.taskId)}>
                        <MaterialIcon name="stop" slot="icon" />
                        停止
                      </md-filled-tonal-button>
                    ) : (
                      <>
                        <md-icon-button aria-label={`配置${title}计划`} onClick={() => openEditPlan(plan)}>
                          <MaterialIcon name="edit" />
                        </md-icon-button>
                        <md-icon-button aria-label={`删除${title}计划`} onClick={() => bridge.removeSchedulePlan(plan.id)}>
                          <MaterialIcon name="delete" />
                        </md-icon-button>
                      </>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className={`app-shell${consoleOpen ? ' console-open' : ''}`} ref={shellRef} style={shellStyle}>
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
            <div className="scheduler-chip">
              <MaterialIcon name="event_repeat" />
              <span>计划：{schedulerStatusText}</span>
            </div>
          </div>
          <div className="top-actions">
            <md-icon-button aria-label={isDark ? '切换到亮色主题' : '切换到暗色主题'} onClick={toggleTheme}>
              <MaterialIcon name={isDark ? 'light_mode' : 'dark_mode'} />
            </md-icon-button>
            <md-icon-button aria-label="打开日志" onClick={() => setConsoleOpen(true)}>
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
              <span className="eyebrow">{activePageMeta.eyebrow}</span>
              <h2>{activePageMeta.label}</h2>
            </div>
          </div>

          {activePage === 'general' ? (
            <ConfigPanel
              fields={bridge.groupedFields.general ?? []}
              values={bridge.values}
              onChange={bridge.updateValue}
            />
          ) : activePage === 'team' ? (
            <ConfigPanel
              fields={bridge.groupedFields.team ?? []}
              values={bridge.values}
              onChange={bridge.updateValue}
            />
          ) : activePage === 'plan' ? (
            renderPlanPage()
          ) : (
            renderToolsPage()
          )}
        </section>
      </main>

      {consoleOpen && (
        <ConsolePanel
          logs={bridge.logs}
          width={consoleWidth}
          onClose={() => setConsoleOpen(false)}
          onWidthChange={(width) => setConsoleWidth(clampConsoleWidth(width))}
        />
      )}

      <md-dialog ref={createDialogRef}>
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
          <md-text-button onClick={() => void createDialogRef.current?.close('cancel')}>取消</md-text-button>
          <md-filled-button onClick={createInstance}>创建</md-filled-button>
        </div>
      </md-dialog>

      <md-dialog ref={planDialogRef}>
        <div slot="headline">
          {selectedPlanTask ? `${editingPlan ? '配置' : '添加'}${selectedPlanTask.title}计划` : '添加计划'}
        </div>
        <form
          className="dialog-content plan-dialog-content"
          id="create-plan-form"
          slot="content"
          onSubmit={(event) => {
            event.preventDefault();
            savePlan();
          }}
        >
          <div className="plan-dialog-grid">
            <md-outlined-text-field
              ref={planTimeInputRef}
              label="运行时间"
              type="time"
              value={planTime}
              onInput={(event) => setPlanTime((event.currentTarget as TextFieldElement).value)}
              onChange={(event) => setPlanTime((event.currentTarget as TextFieldElement).value)}
            />
            <md-outlined-text-field
              label="优先级"
              type="number"
              step="1"
              value={String(planPriority)}
              onInput={(event) => setPlanPriority(Number((event.currentTarget as TextFieldElement).value))}
              onChange={(event) => setPlanPriority(Number((event.currentTarget as TextFieldElement).value))}
            />
          </div>
          {selectedPlanConfigFields.length > 0 && (
            <ConfigPanel
              fields={selectedPlanConfigFields}
              values={planValues}
              onChange={(key, val) => setPlanValues((prev) => ({ ...prev, [key]: val }))}
            />
          )}
        </form>
        <div slot="actions">
          <md-text-button onClick={() => void planDialogRef.current?.close('cancel')}>取消</md-text-button>
          <md-filled-button onClick={savePlan}>确认</md-filled-button>
        </div>
      </md-dialog>
    </div>
  );
}
