/**
 * CloudLockFixer — Web Companion Client Logic
 * 100% Local-First / Zero-Egress / Offline PWA
 */
'use strict';

// 6-Sprachen-Übersetzungskatalog (Tier-2 nach Policy P-006)
const I18N = {
  de: {
    companion_subtitle: "Web Companion & Snapshot-Viewer",
    sr_language: "Sprache",
    drop_zone_prompt: "Snapshot-Datei (JSON) hier ablegen oder Datei auswählen",
    btn_choose_file: "Snapshot laden",
    btn_load_sample: "Demo-Snapshot",
    drop_zone_hint: "cloudlockfixer-snapshot-v1.json (Zero-Egress, 100% lokal im Browser)",
    meta_generated_at: "Stand:",
    meta_version: "Version:",
    meta_platform: "Plattform:",
    tab_overview: "Übersicht",
    tab_queue: "Queue-Monitor",
    tab_providers: "Sync-Provider",
    tab_settings: "Einstellungen",
    kpi_total: "Tasks Gesamt",
    kpi_pending: "Offen / Fällig",
    kpi_deferred: "Im Backoff (Verzögert)",
    kpi_failed: "Fehlversuche",
    kpi_providers: "Aktive Provider",
    title_quick_status: "Aktuelle Systemgesundheit",
    msg_no_data: "Noch kein Snapshot geladen. Bitte eine Datei öffnen oder Demo-Snapshot wählen.",
    ph_search_queue: "Nach Pfad oder Task-ID filtern...",
    filter_all: "Alle Status",
    filter_pending: "Offen / Fällig",
    filter_deferred: "Im Backoff",
    filter_failed: "Fehler",
    filter_done: "Erledigt",
    col_id: "ID",
    col_op: "Operation",
    col_src: "Datei / Ordner",
    col_status: "Status",
    col_retries: "Versuche",
    col_next_try: "Nächster Versuch",
    msg_queue_empty: "Keine passenden Einträge vorhanden.",
    title_service_settings: "Dienst-Einstellungen",
    title_about: "Über CloudLockFixer",
    about_desc: "Delayed Action Service für Cloud-Sync-gesperrte Datei- und Ordneroperationen via copy+delete-Workaround mit exponentiellem Backoff.",
    feat_zero_egress: "100% Local-First / Zero-Egress (kein Tracking, kein Upload)",
    feat_offline: "PWA Offline-Fähigkeit via Service Worker",
    feat_i18n: "Tier-2 Internationalisierung (6 Sprachen)",
    feat_mit: "Open Source unter MIT-Lizenz",
    status_active: "Aktiv",
    status_paused: "Pausiert",
    status_stopped: "Gestoppt",
    status_due_now: "Sofort fällig",
    status_deferred_until: "Verzögert bis {time}",
    provider_mount_folder: "Ordner-Mount",
    provider_mount_virtual: "Virtueller Mount (FUSE/Drive)",
    prov_roots: "Erkannte Sync-Roots: {count}"
  },
  en: {
    companion_subtitle: "Web Companion & Snapshot Viewer",
    sr_language: "Language",
    drop_zone_prompt: "Drop snapshot JSON file here or choose a file",
    btn_choose_file: "Load Snapshot",
    btn_load_sample: "Demo Snapshot",
    drop_zone_hint: "cloudlockfixer-snapshot-v1.json (Zero-Egress, 100% local in browser)",
    meta_generated_at: "Generated:",
    meta_version: "Version:",
    meta_platform: "Platform:",
    tab_overview: "Overview",
    tab_queue: "Queue Monitor",
    tab_providers: "Sync Providers",
    tab_settings: "Settings",
    kpi_total: "Total Tasks",
    kpi_pending: "Pending / Due",
    kpi_deferred: "In Backoff (Deferred)",
    kpi_failed: "Failed Tasks",
    kpi_providers: "Active Providers",
    title_quick_status: "System Health Summary",
    msg_no_data: "No snapshot loaded yet. Please select a JSON file or load the demo snapshot.",
    ph_search_queue: "Filter by path or task ID...",
    filter_all: "All statuses",
    filter_pending: "Pending / Due",
    filter_deferred: "In Backoff",
    filter_failed: "Failed",
    filter_done: "Done",
    col_id: "ID",
    col_op: "Operation",
    col_src: "File / Folder",
    col_status: "Status",
    col_retries: "Retries",
    col_next_try: "Next Attempt",
    msg_queue_empty: "No matching entries found.",
    title_service_settings: "Service Settings",
    title_about: "About CloudLockFixer",
    about_desc: "Delayed Action Service for cloud-sync-locked file and folder operations via copy+delete workaround with exponential backoff.",
    feat_zero_egress: "100% Local-First / Zero-Egress (no tracking, no uploads)",
    feat_offline: "PWA offline capability via Service Worker",
    feat_i18n: "Tier-2 internationalization (6 languages)",
    feat_mit: "Open Source under MIT license",
    status_active: "Active",
    status_paused: "Paused",
    status_stopped: "Stopped",
    status_due_now: "Due now",
    status_deferred_until: "Deferred until {time}",
    provider_mount_folder: "Folder Mount",
    provider_mount_virtual: "Virtual Mount (FUSE/Drive)",
    prov_roots: "Detected sync roots: {count}"
  },
  es: {
    companion_subtitle: "Compañero Web y Visor de Instantáneas",
    sr_language: "Idioma",
    drop_zone_prompt: "Suelte el archivo JSON aquí o elija un archivo",
    btn_choose_file: "Cargar Instantánea",
    btn_load_sample: "Instantánea Demo",
    drop_zone_hint: "cloudlockfixer-snapshot-v1.json (Zero-Egress, 100% local en el navegador)",
    meta_generated_at: "Generado:",
    meta_version: "Versión:",
    meta_platform: "Plataforma:",
    tab_overview: "Resumen",
    tab_queue: "Monitor de Cola",
    tab_providers: "Proveedores",
    tab_settings: "Configuración",
    kpi_total: "Tareas Totales",
    kpi_pending: "Pendientes",
    kpi_deferred: "En Espera (Backoff)",
    kpi_failed: "Fallidas",
    kpi_providers: "Proveedores Activos",
    title_quick_status: "Estado del Sistema",
    msg_no_data: "No se ha cargado ninguna instantánea. Por favor seleccione un archivo.",
    ph_search_queue: "Filtrar por ruta o ID...",
    filter_all: "Todos los estados",
    filter_pending: "Pendientes",
    filter_deferred: "En Espera",
    filter_failed: "Fallidas",
    filter_done: "Completadas",
    col_id: "ID",
    col_op: "Operación",
    col_src: "Archivo / Carpeta",
    col_status: "Estado",
    col_retries: "Reintentos",
    col_next_try: "Próximo Intento",
    msg_queue_empty: "No se encontraron entradas coincidentes.",
    title_service_settings: "Configuración del Servicio",
    title_about: "Acerca de CloudLockFixer",
    about_desc: "Servicio de acción diferida para operaciones bloqueadas por sincronización en la nube.",
    feat_zero_egress: "100% Local-First / Zero-Egress",
    feat_offline: "PWA sin conexión mediante Service Worker",
    feat_i18n: "Internacionalización Tier-2 (6 idiomas)",
    feat_mit: "Código abierto bajo licencia MIT",
    status_active: "Activo",
    status_paused: "Pausado",
    status_stopped: "Detenido",
    status_due_now: "Vence ahora",
    status_deferred_until: "Pospuesto hasta {time}",
    provider_mount_folder: "Montaje de Carpeta",
    provider_mount_virtual: "Montaje Virtual",
    prov_roots: "Rutas de sincronización: {count}"
  },
  zh: {
    companion_subtitle: "Web 助手与快照查看器",
    sr_language: "语言",
    drop_zone_prompt: "将快照 JSON 文件拖放到此处或选择文件",
    btn_choose_file: "加载快照",
    btn_load_sample: "示例快照",
    drop_zone_hint: "cloudlockfixer-snapshot-v1.json (零外流，100% 浏览器本地解析)",
    meta_generated_at: "生成时间：",
    meta_version: "版本：",
    meta_platform: "平台：",
    tab_overview: "概览",
    tab_queue: "队列监视器",
    tab_providers: "同步提供商",
    tab_settings: "设置",
    kpi_total: "任务总数",
    kpi_pending: "待处理 / 到期",
    kpi_deferred: "退避延迟中",
    kpi_failed: "失败任务",
    kpi_providers: "活跃提供商",
    title_quick_status: "系统健康摘要",
    msg_no_data: "尚未加载快照。请选择文件或加载示例快照。",
    ph_search_queue: "按路径或任务 ID 过滤...",
    filter_all: "所有状态",
    filter_pending: "待处理",
    filter_deferred: "延迟中",
    filter_failed: "失败",
    filter_done: "已完成",
    col_id: "ID",
    col_op: "操作",
    col_src: "文件 / 目录",
    col_status: "状态",
    col_retries: "重试次数",
    col_next_try: "下次尝试",
    msg_queue_empty: "没有匹配的队列条目。",
    title_service_settings: "服务设置",
    title_about: "关于 CloudLockFixer",
    about_desc: "针对云同步锁定文件和目录操作的延迟操作服务（采用 copy+delete 变通机制和指数退避）。",
    feat_zero_egress: "100% 本地优先 / 零数据外流",
    feat_offline: "通过 Service Worker 实现 PWA 离线运行",
    feat_i18n: "Tier-2 国际化支持（6 种语言）",
    feat_mit: "遵循 MIT 许可证开源",
    status_active: "运行中",
    status_paused: "已暂停",
    status_stopped: "已停止",
    status_due_now: "立即执行",
    status_deferred_until: "延迟至 {time}",
    provider_mount_folder: "文件夹挂载",
    provider_mount_virtual: "虚拟挂载",
    prov_roots: "检测到的同步根目录：{count}"
  },
  ja: {
    companion_subtitle: "Webコンパニオン＆スナップショットビューアー",
    sr_language: "言語",
    drop_zone_prompt: "スナップショットJSONファイルをドロップするか、ファイルを選択",
    btn_choose_file: "スナップショット読込",
    btn_load_sample: "デモスナップショット",
    drop_zone_hint: "cloudlockfixer-snapshot-v1.json (外部送信ゼロ、100% ブラウザ内で完結)",
    meta_generated_at: "生成日時:",
    meta_version: "バージョン:",
    meta_platform: "プラットフォーム:",
    tab_overview: "概要",
    tab_queue: "キュー監視",
    tab_providers: "同期プロバイダー",
    tab_settings: "設定",
    kpi_total: "総タスク数",
    kpi_pending: "保留中 / 実行可能",
    kpi_deferred: "バックオフ遅延中",
    kpi_failed: "失敗タスク",
    kpi_providers: "稼働プロバイダー",
    title_quick_status: "システム状態の要約",
    msg_no_data: "スナップショットが読み込まれていません。ファイルを選択してください。",
    ph_search_queue: "パスまたはタスクIDで絞り込み...",
    filter_all: "すべてのステータス",
    filter_pending: "保留中",
    filter_deferred: "遅延中",
    filter_failed: "失敗",
    filter_done: "完了",
    col_id: "ID",
    col_op: "操作",
    col_src: "ファイル / フォルダ",
    col_status: "ステータス",
    col_retries: "試行回数",
    col_next_try: "次回実行",
    msg_queue_empty: "一致するエントリはありません。",
    title_service_settings: "サービス設定",
    title_about: "CloudLockFixer について",
    about_desc: "クラウド同期によってロックされたファイル・フォルダ操作を安全に遅延実行するサービス。",
    feat_zero_egress: "100% ローカル優先 / 外部送信ゼロ",
    feat_offline: "Service Worker による完全オフライン対応",
    feat_i18n: "Tier-2 国際化対応（6言語）",
    feat_mit: "MITライセンスのオープンソース",
    status_active: "稼働中",
    status_paused: "一時停止中",
    status_stopped: "停止",
    status_due_now: "即時実行可能",
    status_deferred_until: "{time} まで延期",
    provider_mount_folder: "フォルダマウント",
    provider_mount_virtual: "仮想マウント",
    prov_roots: "検出された同期限ルート: {count}"
  },
  ru: {
    companion_subtitle: "Веб-компаньон и просмотр снимков",
    sr_language: "Язык",
    drop_zone_prompt: "Перетащите файл снимка JSON сюда или выберите файл",
    btn_choose_file: "Загрузить снимок",
    btn_load_sample: "Демо-снимок",
    drop_zone_hint: "cloudlockfixer-snapshot-v1.json (Zero-Egress, 100% локально в браузере)",
    meta_generated_at: "Создан:",
    meta_version: "Версия:",
    meta_platform: "Платформа:",
    tab_overview: "Обзор",
    tab_queue: "Монитор очереди",
    tab_providers: "Синхронизаторы",
    tab_settings: "Настройки",
    kpi_total: "Всего задач",
    kpi_pending: "В ожидании",
    kpi_deferred: "С задержкой (Backoff)",
    kpi_failed: "Ошибки",
    kpi_providers: "Активные провайдеры",
    title_quick_status: "Сводка о состоянии системы",
    msg_no_data: "Снимок пока не загружен. Выберите файл JSON или загрузите демо-снимок.",
    ph_search_queue: "Фильтр по пути или ID задачи...",
    filter_all: "Все статусы",
    filter_pending: "В ожидании",
    filter_deferred: "Отложено",
    filter_failed: "Ошибки",
    filter_done: "Выполнено",
    col_id: "ID",
    col_op: "Операция",
    col_src: "Файл / Каталог",
    col_status: "Статус",
    col_retries: "Попытки",
    col_next_try: "Следующая попытка",
    msg_queue_empty: "Нет подходящих записей.",
    title_service_settings: "Параметры службы",
    title_about: "О CloudLockFixer",
    about_desc: "Служба отложенных действий для заблокированных облачной синхронизацией файлов с экспоненциальным backoff.",
    feat_zero_egress: "100% Local-First / Zero-Egress (без отправки данных)",
    feat_offline: "Офлайн-режим PWA через Service Worker",
    feat_i18n: "Интернационализация Tier-2 (6 языков)",
    feat_mit: "Открытый исходный код под лицензией MIT",
    status_active: "Активен",
    status_paused: "Приостановлен",
    status_stopped: "Остановлен",
    status_due_now: "Готово к выполнению",
    status_deferred_until: "Отложено до {time}",
    provider_mount_folder: "Папка",
    provider_mount_virtual: "Виртуальный диск",
    prov_roots: "Обнаружено путей: {count}"
  }
};

let currentLang = 'de';
let currentSnapshot = null;

// Service Worker Registrierung (Offline PWA)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(err => {
      console.warn('ServiceWorker registration error:', err);
    });
  });
}

function t(key, params = {}) {
  const langDict = I18N[currentLang] || I18N['de'];
  let text = langDict[key] || (I18N['en'] && I18N['en'][key]) || key;
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(`{${k}}`, v);
  }
  return text;
}

function updateTranslations() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    el.placeholder = t(key);
  });
  if (currentSnapshot) {
    renderSnapshot(currentSnapshot);
  }
}

// Initialisierung DOM Events
document.addEventListener('DOMContentLoaded', () => {
  // Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const savedTheme = localStorage.getItem('clf_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';

  themeToggle.addEventListener('click', () => {
    const active = document.documentElement.getAttribute('data-theme');
    const next = active === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('clf_theme', next);
    themeIcon.textContent = next === 'dark' ? '☀️' : '🌙';
  });

  // Sprache Selector
  const langSelect = document.getElementById('lang-select');
  const navLang = (navigator.language || 'de').split('-')[0];
  if (I18N[navLang]) {
    currentLang = navLang;
    langSelect.value = navLang;
  }
  langSelect.addEventListener('change', (e) => {
    currentLang = e.target.value;
    updateTranslations();
  });

  // Tab Navigation
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const targetId = `tab-${btn.getAttribute('data-tab')}`;
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add('active');
    });
  });

  // Drag & Drop
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFile(e.target.files[0]);
  });

  document.getElementById('btn-load-sample').addEventListener('click', loadSampleData);

  // Suche und Filter in Queue
  document.getElementById('queue-search').addEventListener('input', filterQueue);
  document.getElementById('queue-filter-status').addEventListener('change', filterQueue);

  updateTranslations();
});

function handleFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result);
      if (!data.schema_name || !data.schema_name.includes('cloudlockfixer')) {
        alert("Hinweis: Datei scheint kein gültiger CloudLockFixer-Snapshot zu sein.");
      }
      currentSnapshot = data;
      renderSnapshot(data);
    } catch (err) {
      alert("Fehler beim Parsen der JSON-Datei: " + err.message);
    }
  };
  reader.readAsText(file, 'UTF-8');
}

function loadSampleData() {
  const sample = {
    schema_name: "cloudlockfixer-snapshot-v1",
    schema_version: "1.0.0",
    generated_at: new Date().toISOString(),
    app: {
      name: "CloudLockFixer",
      version: "0.2.3",
      license: "MIT",
      homepage: "https://github.com/file-bricks/CloudLockFixer"
    },
    environment: {
      platform: "win32",
      python_version: "3.12.10",
      data_dir_name: "CloudLockFixer"
    },
    settings: {
      interval_min: 120,
      max_retries: 10,
      notifications_enabled: true,
      language: currentLang,
      backoff_base_sec: 60,
      backoff_max_sec: 3600,
      backoff_multiplier: 2.0
    },
    queue_summary: {
      total: 3,
      pending: 1,
      in_progress: 0,
      deferred: 1,
      failed: 1,
      permanent_failed: 0,
      done: 0
    },
    tasks: [
      {
        id: "clf001a1",
        status: "pending",
        retry_count: 0,
        created_at: new Date(Date.now() - 3600000).toISOString(),
        last_try: "",
        last_error: "",
        last_outcome: "retryable",
        step_index: 0,
        next_try_at: "",
        is_due: true,
        steps: [
          { op: "rename", src_name: "Finanzbericht_2026_Entwurf.docx", src_display: "C:/Users/.../OneDrive/Dokumente/Finanzbericht_2026_Entwurf.docx", arg_display: "Finanzbericht_2026_Final.docx" }
        ]
      },
      {
        id: "clf002b2",
        status: "pending",
        retry_count: 3,
        created_at: new Date(Date.now() - 7200000).toISOString(),
        last_try: new Date(Date.now() - 600000).toISOString(),
        last_error: "WinError 32: Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird",
        last_outcome: "retryable",
        step_index: 0,
        next_try_at: new Date(Date.now() + 1800000).toISOString(),
        is_due: false,
        steps: [
          { op: "move", src_name: "Projektdaten_Archiv.tar.gz", src_display: "C:/Sync/Projektdaten_Archiv.tar.gz", arg_display: "C:/Archive/Projektdaten_Archiv.tar.gz" }
        ]
      },
      {
        id: "clf003c3",
        status: "failed",
        retry_count: 10,
        created_at: new Date(Date.now() - 86400000).toISOString(),
        last_try: new Date(Date.now() - 3600000).toISOString(),
        last_error: "FileNotFoundError: Quelldatei existiert nicht mehr am Pfad",
        last_outcome: "permanent",
        step_index: 0,
        next_try_at: "",
        is_due: false,
        steps: [
          { op: "delete", src_name: "Temporaer_Lock_Test.tmp", src_display: "C:/Dropbox/Temporaer_Lock_Test.tmp", arg_display: "" }
        ]
      }
    ],
    providers: [
      { name: "OneDrive", mount_type: "folder", is_running: true, roots_count: 1 },
      { name: "Google Drive", mount_type: "virtual", is_running: false, roots_count: 1 },
      { name: "Dropbox", mount_type: "folder", is_running: true, roots_count: 1 }
    ]
  };

  currentSnapshot = sample;
  renderSnapshot(sample);
}

function renderSnapshot(data) {
  // Metadata Bar
  const metaBar = document.getElementById('snapshot-meta-bar');
  metaBar.classList.remove('hidden');

  const genDate = data.generated_at ? new Date(data.generated_at).toLocaleString(currentLang) : "-";
  document.getElementById('meta-time').textContent = genDate;
  document.getElementById('meta-version').textContent = data.app ? data.app.version : "-";
  document.getElementById('meta-platform').textContent = data.environment ? data.environment.platform : "-";

  // KPIs
  const qSum = data.queue_summary || {};
  document.getElementById('kpi-total').textContent = qSum.total || 0;
  document.getElementById('kpi-pending').textContent = qSum.pending || 0;
  document.getElementById('kpi-deferred').textContent = qSum.deferred || 0;
  document.getElementById('kpi-failed').textContent = (qSum.failed || 0) + (qSum.permanent_failed || 0);

  const activeProvs = (data.providers || []).filter(p => p.is_running).length;
  document.getElementById('kpi-providers').textContent = activeProvs;

  // Overview Status Summary
  const statusContainer = document.getElementById('quick-status-text');
  let summaryHtml = `<p><strong>${data.app?.name || 'CloudLockFixer'} v${data.app?.version || ''}</strong> (${data.environment?.platform || ''}, Python ${data.environment?.python_version || ''})</p>`;
  if (qSum.deferred > 0) {
    summaryHtml += `<p style="color: var(--badge-deferred-text); margin-top: 0.5rem;">⚠️ ${qSum.deferred} Task(s) befinden sich im exponentiellen Backoff und werden später wiederholt.</p>`;
  }
  if (qSum.failed > 0 || qSum.permanent_failed > 0) {
    summaryHtml += `<p style="color: var(--badge-failed-text); margin-top: 0.25rem;">❌ ${qSum.failed + qSum.permanent_failed} Task(s) haben das Wiederholungslimit erreicht.</p>`;
  }
  if (qSum.pending === 0 && qSum.failed === 0 && qSum.deferred === 0) {
    summaryHtml += `<p style="color: var(--badge-done-text); margin-top: 0.5rem;">✓ Alle Aufgaben abgearbeitet. Die Warteschlange ist sauber.</p>`;
  }
  statusContainer.innerHTML = summaryHtml;

  // Queue Table
  renderQueueTable(data.tasks || []);

  // Providers Grid
  renderProviders(data.providers || []);

  // Settings List
  renderSettings(data.settings || {}, data.environment || {});
}

function renderQueueTable(tasks) {
  const tbody = document.getElementById('queue-table-body');
  if (!tasks || tasks.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">${t('msg_queue_empty')}</td></tr>`;
    return;
  }

  tbody.innerHTML = tasks.map(task => {
    let statusBadgeClass = 'badge-pending';
    let statusLabel = task.status;

    if (!task.is_due && task.next_try_at) {
      statusBadgeClass = 'badge-deferred';
      statusLabel = t('filter_deferred');
    } else if (task.status === 'failed' || task.status === 'permanent_failed') {
      statusBadgeClass = 'badge-failed';
      statusLabel = t('filter_failed');
    } else if (task.status === 'done') {
      statusBadgeClass = 'badge-done';
      statusLabel = t('filter_done');
    } else if (task.status === 'pending') {
      statusLabel = t('filter_pending');
    }

    const firstStep = (task.steps && task.steps[0]) || {};
    const op = firstStep.op || "-";
    const src = firstStep.src_name || firstStep.src_display || "-";
    const nextTry = task.next_try_at ? new Date(task.next_try_at).toLocaleTimeString(currentLang) : (task.is_due ? t('status_due_now') : "-");

    return `
      <tr>
        <td><code>${task.id}</code></td>
        <td><strong>${op.toUpperCase()}</strong></td>
        <td title="${firstStep.src_display || ''}">${src}</td>
        <td><span class="badge ${statusBadgeClass}">${statusLabel}</span></td>
        <td>${task.retry_count}</td>
        <td>${nextTry}</td>
      </tr>
    `;
  }).join('');
}

function filterQueue() {
  if (!currentSnapshot || !currentSnapshot.tasks) return;
  const search = document.getElementById('queue-search').value.toLowerCase();
  const filter = document.getElementById('queue-filter-status').value;

  const filtered = currentSnapshot.tasks.filter(t => {
    const matchesSearch = !search ||
      t.id.toLowerCase().includes(search) ||
      (t.steps && t.steps.some(s => (s.src_display || '').toLowerCase().includes(search) || (s.src_name || '').toLowerCase().includes(search)));

    let matchesStatus = true;
    if (filter === 'pending') matchesStatus = t.status === 'pending' && t.is_due;
    else if (filter === 'deferred') matchesStatus = !t.is_due && Boolean(t.next_try_at);
    else if (filter === 'failed') matchesStatus = t.status === 'failed' || t.status === 'permanent_failed';
    else if (filter === 'done') matchesStatus = t.status === 'done';

    return matchesSearch && matchesStatus;
  });

  renderQueueTable(filtered);
}

function renderProviders(providers) {
  const container = document.getElementById('providers-grid');
  if (!providers || providers.length === 0) {
    container.innerHTML = `<p class="status-summary">Keine Cloud-Synchronisationsdienste erkannt.</p>`;
    return;
  }

  container.innerHTML = providers.map(p => {
    const isRunning = p.is_running;
    const badgeClass = isRunning ? 'badge-done' : 'badge-pending';
    const statusText = isRunning ? t('status_active') : t('status_stopped');
    const mountType = p.mount_type === 'virtual' ? t('provider_mount_virtual') : t('provider_mount_folder');

    return `
      <div class="provider-card">
        <div class="provider-header">
          <span class="provider-name">${p.name}</span>
          <span class="badge ${badgeClass}">${statusText}</span>
        </div>
        <div class="provider-meta">${mountType}</div>
        <div class="provider-meta">${t('prov_roots', { count: p.roots_count || 0 })}</div>
      </div>
    `;
  }).join('');
}

function renderSettings(settings, env) {
  const container = document.getElementById('settings-list');
  const rows = [
    { key: "Intervall", val: `${settings.interval_min || 120} Min.` },
    { key: "Max. Retries", val: settings.max_retries === null ? "Unbegrenzt" : settings.max_retries },
    { key: "Benachrichtigungen", val: settings.notifications_enabled ? "Aktiv" : "Deaktiviert" },
    { key: "Sprache", val: settings.language || "de" },
    { key: "Backoff Basis", val: `${settings.backoff_base_sec || 60} Sek.` },
    { key: "Backoff Multiplikator", val: `${settings.backoff_multiplier || 2.0}x` },
    { key: "Backoff Maximum", val: `${settings.backoff_max_sec || 3600} Sek.` },
    { key: "Betriebssystem", val: env.platform || "-" },
    { key: "Python-Version", val: env.python_version || "-" },
  ];

  container.innerHTML = rows.map(r => `
    <div class="kv-row">
      <span class="kv-key">${r.key}</span>
      <span class="kv-val">${r.val}</span>
    </div>
  `).join('');
}
