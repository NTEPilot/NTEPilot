import { useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import type { LogEvent } from '../types/protocol';
import { MaterialIcon } from './MaterialIcon';
import { Switch } from './Switch';

interface ConsolePanelProps {
  logs: LogEvent[];
  open: boolean;
  onClose: () => void;
}

interface AnsiSegment {
  text: string;
  style: CSSProperties;
}

const ANSI_COLORS: Record<number, string> = {
  30: '#0b0f16',
  31: '#ff7b72',
  32: '#7ee787',
  33: '#f2cc60',
  34: '#79c0ff',
  35: '#d2a8ff',
  36: '#76e3ea',
  37: '#d8dee9',
  90: '#6e7681',
  91: '#ffa198',
  92: '#56d364',
  93: '#e3b341',
  94: '#58a6ff',
  95: '#bc8cff',
  96: '#39c5cf',
  97: '#f0f6fc',
};

const ANSI_BACKGROUND_COLORS: Record<number, string> = {
  40: '#0b0f16',
  41: '#5f1f1b',
  42: '#1f4b2c',
  43: '#5c450f',
  44: '#123456',
  45: '#42235f',
  46: '#184f55',
  47: '#3f4652',
  100: '#30363d',
  101: '#7d2a25',
  102: '#2f6f3e',
  103: '#806115',
  104: '#1f5d8f',
  105: '#633a8f',
  106: '#26747c',
  107: '#6e7681',
};

const ANSI_256_COLORS = [
  '#000000', '#800000', '#008000', '#808000', '#000080', '#800080', '#008080', '#c0c0c0',
  '#808080', '#ff0000', '#00ff00', '#ffff00', '#0000ff', '#ff00ff', '#00ffff', '#ffffff',
];

function ansi256ToColor(index: number) {
  if (index < 16) return ANSI_256_COLORS[index] ?? '#d8dee9';
  if (index >= 16 && index <= 231) {
    const value = index - 16;
    const r = Math.floor(value / 36);
    const g = Math.floor((value % 36) / 6);
    const b = value % 6;
    const channel = (n: number) => (n === 0 ? 0 : 55 + n * 40);
    return `rgb(${channel(r)}, ${channel(g)}, ${channel(b)})`;
  }
  if (index >= 232 && index <= 255) {
    const gray = 8 + (index - 232) * 10;
    return `rgb(${gray}, ${gray}, ${gray})`;
  }
  return '#d8dee9';
}

function parseAnsi(input: string): AnsiSegment[] {
  const segments: AnsiSegment[] = [];
  let style: CSSProperties = {};
  let index = 0;
  const pattern = /\x1b\[([0-9;]*)m/g;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(input)) !== null) {
    if (match.index > index) {
      segments.push({ text: input.slice(index, match.index), style: { ...style } });
    }

    const codes = match[1].split(';').filter(Boolean).map(Number);
    if (codes.length === 0 || codes.includes(0)) {
      style = {};
    }
    for (let i = 0; i < codes.length; i += 1) {
      const code = codes[i];
      if (code === 1) style.fontWeight = 700;
      if (code === 2) style.opacity = 0.72;
      if (code === 3) style.fontStyle = 'italic';
      if (code === 4) style.textDecoration = 'underline';
      if (code === 22) delete style.fontWeight;
      if (code === 23) delete style.fontStyle;
      if (code === 24) delete style.textDecoration;
      if (code === 39) delete style.color;
      if (code === 49) delete style.backgroundColor;
      if (ANSI_COLORS[code]) style.color = ANSI_COLORS[code];
      if (ANSI_BACKGROUND_COLORS[code]) style.backgroundColor = ANSI_BACKGROUND_COLORS[code];
      if (code === 38 && codes[i + 1] === 2) {
        const r = codes[i + 2] ?? 255;
        const g = codes[i + 3] ?? 255;
        const b = codes[i + 4] ?? 255;
        style.color = `rgb(${r}, ${g}, ${b})`;
        i += 4;
      }
      if (code === 48 && codes[i + 1] === 2) {
        const r = codes[i + 2] ?? 0;
        const g = codes[i + 3] ?? 0;
        const b = codes[i + 4] ?? 0;
        style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
        i += 4;
      }
      if (code === 38 && codes[i + 1] === 5) {
        style.color = ansi256ToColor(codes[i + 2] ?? 15);
        i += 2;
      }
      if (code === 48 && codes[i + 1] === 5) {
        style.backgroundColor = ansi256ToColor(codes[i + 2] ?? 0);
        i += 2;
      }
    }
    index = pattern.lastIndex;
  }

  if (index < input.length) {
    segments.push({ text: input.slice(index), style: { ...style } });
  }
  return segments;
}

function ConsoleLine({ log }: { log: LogEvent }) {
  const ansi = log.ansi ?? log.message;
  const segments = parseAnsi(ansi);

  return (
    <div className={`console-line level-${log.level}`}>
      <span className="console-time">{new Date(log.time).toLocaleTimeString()}</span>
      <span className="console-source">{log.source ?? '应用'}</span>
      <span className="console-message">
        {segments.map((segment, index) => (
          <span key={`${log.id}-${index}`} style={segment.style}>
            {segment.text}
          </span>
        ))}
      </span>
    </div>
  );
}

export function ConsolePanel({ logs, open, onClose }: ConsolePanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (autoScroll && ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [autoScroll, logs]);

  return (
    <>
      <button
        aria-label="关闭同步控制台"
        className={`sheet-scrim${open ? ' is-visible' : ''}`}
        onClick={onClose}
        type="button"
      />
      <aside className={`console-panel${open ? ' is-open' : ''}`} aria-label="同步控制台日志" aria-hidden={!open}>
        <div className="console-title">
          <div className="console-heading">
            <MaterialIcon name="terminal" />
            <span>同步控制台</span>
          </div>
          <div className="console-actions">
            <Switch checked={autoScroll} onChange={setAutoScroll} label="自动滚动" compact />
            <md-icon-button aria-label="关闭同步控制台" onClick={onClose}>
              <MaterialIcon name="close" />
            </md-icon-button>
          </div>
        </div>
        <div className="console-output" ref={ref}>
          {logs.map((log) => (
            <ConsoleLine key={log.id} log={log} />
          ))}
        </div>
      </aside>
    </>
  );
}
