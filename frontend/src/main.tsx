import ReactDOM from 'react-dom/client';
import '@fontsource/material-symbols-outlined/latin-400.css';
import '@material/web/button/filled-button.js';
import '@material/web/button/filled-tonal-button.js';
import '@material/web/button/outlined-button.js';
import '@material/web/button/text-button.js';
import '@material/web/dialog/dialog.js';
import '@material/web/divider/divider.js';
import '@material/web/iconbutton/icon-button.js';
import '@material/web/list/list-item.js';
import '@material/web/list/list.js';
import '@material/web/switch/switch.js';
import '@material/web/tabs/primary-tab.js';
import '@material/web/tabs/tabs.js';
import '@material/web/textfield/outlined-text-field.js';
import { App } from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <App />,
);
