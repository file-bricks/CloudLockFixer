"""Minimale i18n-Unterstützung (6 Sprachen: Deutsch, Englisch, Spanisch, Chinesisch, Japanisch, Russisch).

Übersetzungskatalog als strukturiertes Dict — kein externes Framework nötig.
Die aktive Sprache wird beim Start gesetzt (Config oder System-Locale) und bleibt
für die Laufzeit konstant.
"""
from __future__ import annotations

import locale
from typing import Literal

Language = Literal["de", "en", "es", "zh", "ja", "ru"]

_CATALOG: dict[str, dict[Language, str]] = {
    'status_no_tasks': {
        'de': 'keine offenen Aufgaben',
        'en': 'no pending tasks',
        'es': 'sin tareas pendientes',
        'zh': '无待处理任务',
        'ja': '保留中のタスクはありません',
        'ru': 'нет ожидающих задач',
    },
    'status_open': {
        'de': '{n} offen ({retrying} mit Fehlversuch, {failed} fehlgeschlagen)',
        'en': '{n} pending ({retrying} with retries, {failed} failed)',
        'es': '{n} pendiente(s) ({retrying} con reintento, {failed} fallida(s))',
        'zh': '{n} 个待处理（{retrying} 个正在重试，{failed} 个失败）',
        'ja': '{n} 件保留中（再試行中 {retrying} 件、失敗 {failed} 件）',
        'ru': '{n} в очереди ({retrying} с повторной попыткой, {failed} с ошибкой)',
    },
    'status_running': {
        'de': 'läuft…',
        'en': 'running…',
        'es': 'ejecutando…',
        'zh': '正在运行…',
        'ja': '実行中…',
        'ru': 'выполняется…',
    },
    'actions_done': {
        'de': '{n} Aktion(en) erledigt.',
        'en': '{n} action(s) completed.',
        'es': '{n} acción(es) completada(s).',
        'zh': '已完成 {n} 个操作。',
        'ja': '{n} 件のアクションが完了しました。',
        'ru': '{n} действие(й) выполнено.',
    },
    'add_task': {
        'de': 'Task hinzufügen…',
        'en': 'Add task…',
        'es': 'Añadir tarea…',
        'zh': '添加任务…',
        'ja': 'タスクを追加…',
        'ru': 'Добавить задачу…',
    },
    'run_now': {
        'de': 'Jetzt ausführen',
        'en': 'Run now',
        'es': 'Ejecutar ahora',
        'zh': '立即运行',
        'ja': '今すぐ実行',
        'ru': 'Запустить сейчас',
    },
    'run_now_with_pause': {
        'de': 'Jetzt ausführen (mit Sync-Pause)',
        'en': 'Run now (with sync pause)',
        'es': 'Ejecutar ahora (con pausa de sincronización)',
        'zh': '立即运行（暂停同步）',
        'ja': '今すぐ実行（同期一時停止あり）',
        'ru': 'Запустить сейчас (с приостановкой синхронизации)',
    },
    'open_data_folder': {
        'de': 'Datenordner öffnen',
        'en': 'Open data folder',
        'es': 'Abrir carpeta de datos',
        'zh': '打开数据文件夹',
        'ja': 'データフォルダーを開く',
        'ru': 'Открыть папку с данными',
    },
    'interval_menu': {
        'de': 'Intervall',
        'en': 'Interval',
        'es': 'Intervalo',
        'zh': '执行间隔',
        'ja': '実行間隔',
        'ru': 'Интервал',
    },
    'autostart_label': {
        'de': 'Mit Windows starten',
        'en': 'Start with Windows',
        'es': 'Iniciar con Windows',
        'zh': '随 Windows 启动',
        'ja': 'Windows 起動時に実行',
        'ru': 'Запуск вместе с Windows',
    },
    'context_menu_label': {
        'de': 'Explorer-Kontextmenü',
        'en': 'Explorer context menu',
        'es': 'Menú contextual del Explorador',
        'zh': '资源管理器右键菜单',
        'ja': 'エクスプローラーのコンテキストメニュー',
        'ru': 'Контекстное меню Проводника',
    },
    'watcher_label': {
        'de': 'Präventiv-Wächter',
        'en': 'Preventive watcher',
        'es': 'Vigilante preventivo',
        'zh': '预防性监视器',
        'ja': '予防的監視機能',
        'ru': 'Превентивный наблюдатель',
    },
    'add_watch_dir': {
        'de': 'Wächter-Ordner hinzufügen…',
        'en': 'Add watcher folder…',
        'es': 'Añadir carpeta de vigilancia…',
        'zh': '添加监视文件夹…',
        'ja': '監視フォルダーを追加…',
        'ru': 'Добавить папку для наблюдения…',
    },
    'quit_label': {
        'de': 'Beenden',
        'en': 'Quit',
        'es': 'Salir',
        'zh': '退出',
        'ja': '終了',
        'ru': 'Выход',
    },
    'action_choose': {
        'de': 'Aktion wählen:',
        'en': 'Choose action:',
        'es': 'Elegir acción:',
        'zh': '选择操作：',
        'ja': 'アクションを選択:',
        'ru': 'Выберите действие:',
    },
    'action_rename': {
        'de': 'Umbenennen',
        'en': 'Rename',
        'es': 'Renombrar',
        'zh': '重命名',
        'ja': '名前の変更',
        'ru': 'Переименовать',
    },
    'action_move': {
        'de': 'Verschieben',
        'en': 'Move',
        'es': 'Mover',
        'zh': '移动',
        'ja': '移動',
        'ru': 'Переместить',
    },
    'action_delete': {
        'de': 'Löschen',
        'en': 'Delete',
        'es': 'Eliminar',
        'zh': '删除',
        'ja': '削除',
        'ru': 'Удалить',
    },
    'source_kind_choose': {
        'de': 'Quelle auswählen:',
        'en': 'Choose source type:',
        'es': 'Seleccionar tipo de origen:',
        'zh': '选择源类型：',
        'ja': 'ソースの種類を選択:',
        'ru': 'Выберите тип источника:',
    },
    'source_kind_folder': {
        'de': 'Ordner',
        'en': 'Folder',
        'es': 'Carpeta',
        'zh': '文件夹',
        'ja': 'フォルダー',
        'ru': 'Папка',
    },
    'source_kind_file': {
        'de': 'Datei',
        'en': 'File',
        'es': 'Archivo',
        'zh': '文件',
        'ja': 'ファイル',
        'ru': 'Файл',
    },
    'choose_folder': {
        'de': 'Ordner wählen',
        'en': 'Choose folder',
        'es': 'Elegir carpeta',
        'zh': '选择文件夹',
        'ja': 'フォルダーを選択',
        'ru': 'Выбрать папку',
    },
    'choose_file': {
        'de': 'Datei wählen',
        'en': 'Choose file',
        'es': 'Elegir archivo',
        'zh': '选择文件',
        'ja': 'ファイルを選択',
        'ru': 'Выбрать файл',
    },
    'rename_prompt': {
        'de': 'Neuer Name:',
        'en': 'New name:',
        'es': 'Nuevo nombre:',
        'zh': '新名称：',
        'ja': '新しい名前:',
        'ru': 'Новое имя:',
    },
    'choose_target': {
        'de': 'Zielordner wählen',
        'en': 'Choose target folder',
        'es': 'Elegir carpeta de destino',
        'zh': '选择目标文件夹',
        'ja': '移動先フォルダーを選択',
        'ru': 'Выбрать целевую папку',
    },
    'confirm_delete': {
        'de': "'{src}' verzögert löschen?",
        'en': "Delete '{src}' (deferred)?",
        'es': "¿Eliminar '{src}' de forma diferida?",
        'zh': '确定要延迟删除“{src}”吗？',
        'ja': "'{src}' を遅延削除しますか？",
        'ru': "Удалить '{src}' с задержкой?",
    },
    'confirm_delete_title': {
        'de': 'Löschen',
        'en': 'Delete',
        'es': 'Eliminar',
        'zh': '删除',
        'ja': '削除',
        'ru': 'Удаление',
    },
    'queued_notification': {
        'de': 'Eingereiht:\n{desc}\n\nWird beim nächsten Lauf erledigt.',
        'en': 'Queued:\n{desc}\n\nWill be processed on next run.',
        'es': 'En cola:\n{desc}\n\nSe procesará en la próxima ejecución.',
        'zh': '已加入队列：\n{desc}\n\n将在下次运行时处理。',
        'ja': 'キューに追加されました:\n{desc}\n\n次回の実行時に処理されます。',
        'ru': 'В очереди:\n{desc}\n\nБудет обработано при следующем запуске.',
    },
    'watch_dir_added': {
        'de': 'Wächter-Ordner: {d}',
        'en': 'Watcher folder: {d}',
        'es': 'Carpeta de vigilancia: {d}',
        'zh': '监视文件夹：{d}',
        'ja': '監視フォルダー: {d}',
        'ru': 'Папка для наблюдения: {d}',
    },
    'watcher_dir_title': {
        'de': 'Ordner für Präventiv-Wächter',
        'en': 'Folder for preventive watcher',
        'es': 'Carpeta para vigilante preventivo',
        'zh': '预防性监视文件夹',
        'ja': '予防的監視フォルダー',
        'ru': 'Папка превентивного наблюдения',
    },
    'already_running': {
        'de': 'Läuft bereits.',
        'en': 'Already running.',
        'es': 'Ya se está ejecutando.',
        'zh': '程序已在运行中。',
        'ja': '既に実行中です。',
        'ru': 'Уже запущено.',
    },
    'no_tray': {
        'de': 'Kein System-Tray verfügbar.',
        'en': 'No system tray available.',
        'es': 'No hay bandeja del sistema disponible.',
        'zh': '系统托盘不可用。',
        'ja': 'システムトレイが利用できません。',
        'ru': 'Системный трей недоступен.',
    },
    'language_menu': {
        'de': 'Sprache / Language',
        'en': 'Language / Sprache',
        'es': 'Idioma / Language',
        'zh': '语言 / Language',
        'ja': '言語 / Language',
        'ru': 'Язык / Language',
    },
    'language_auto': {
        'de': 'Auto (System)',
        'en': 'Auto (System)',
        'es': 'Automático (Sistema)',
        'zh': '自动（跟随系统）',
        'ja': '自動（システム設定）',
        'ru': 'Авто (Система)',
    },
    'restart_required': {
        'de': 'Neustart erforderlich für Sprachwechsel.',
        'en': 'Restart required for language change.',
        'es': 'Es necesario reiniciar para cambiar el idioma.',
        'zh': '更改语言后需要重启生效。',
        'ja': '言語変更を適用するには再起動が必要です。',
        'ru': 'Для смены языка требуется перезапуск.',
    },
    'setting_change_failed': {
        'de': '{setting} konnte nicht geändert werden. Die bisherige Einstellung bleibt aktiv.',
        'en': 'Could not change {setting}. The previous setting remains active.',
        'es': 'No se pudo cambiar {setting}. La configuración anterior sigue activa.',
        'zh': '无法更改 {setting}。保留之前的设置。',
        'ja': '{setting} を変更できませんでした。以前の設定が維持されます。',
        'ru': 'Не удалось изменить {setting}. Сохранена предыдущая настройка.',
    },
    'cli_desc': {
        'de': 'CloudLockFixer CLI',
        'en': 'CloudLockFixer CLI',
        'es': 'CLI de CloudLockFixer',
        'zh': 'CloudLockFixer 命令行工具',
        'ja': 'CloudLockFixer CLI',
        'ru': 'CLI CloudLockFixer',
    },
    'cli_add_help': {
        'de': 'Task einreihen',
        'en': 'Queue a task',
        'es': 'Poner tarea en cola',
        'zh': '向队列添加任务',
        'ja': 'タスクをキューに追加',
        'ru': 'Добавить задачу в очередь',
    },
    'cli_list_help': {
        'de': 'Queue anzeigen',
        'en': 'Show queue',
        'es': 'Mostrar cola',
        'zh': '显示任务队列',
        'ja': 'キューを表示',
        'ru': 'Показать очередь',
    },
    'cli_run_help': {
        'de': 'Queue jetzt abarbeiten',
        'en': 'Process queue now',
        'es': 'Procesar cola ahora',
        'zh': '立即处理任务队列',
        'ja': 'キューを今すぐ処理',
        'ru': 'Обработать очередь сейчас',
    },
    'cli_pause_help': {
        'de': 'Sync-Client für den Lauf pausieren (M2)',
        'en': 'Pause sync client during run (M2)',
        'es': 'Pausar cliente de sincronización durante la ejecución (M2)',
        'zh': '运行时暂停同步客户端 (M2)',
        'ja': '実行中に同期クライアントを一時停止 (M2)',
        'ru': 'Приостановить клиент синхронизации во время работы (M2)',
    },
    'cli_context_help': {
        'de': 'Explorer-Kontextmenü verwalten',
        'en': 'Manage Explorer context menu',
        'es': 'Administrar menú contextual del Explorador',
        'zh': '管理资源管理器右键菜单',
        'ja': 'エクスプローラーのコンテキストメニューを管理',
        'ru': 'Управление контекстным меню Проводника',
    },
    'cli_gui_add_help': {
        'de': 'Dialog zum Einreihen (vom Kontextmenü)',
        'en': 'Queuing dialog (from context menu)',
        'es': 'Diálogo para poner en cola (desde el menú contextual)',
        'zh': '添加任务对话框（来自右键菜单）',
        'ja': 'キュー追加ダイアログ（コンテキストメニュー用）',
        'ru': 'Диалог добавления в очередь (из контекстного меню)',
    },
    'queue_empty': {
        'de': 'Queue leer.',
        'en': 'Queue empty.',
        'es': 'Cola vacía.',
        'zh': '队列为空。',
        'ja': 'キューは空です。',
        'ru': 'Очередь пуста.',
    },
    'queued_msg': {
        'de': 'Eingereiht: {id}  {desc}',
        'en': 'Queued: {id}  {desc}',
        'es': 'En cola: {id}  {desc}',
        'zh': '已加入队列：{id}  {desc}',
        'ja': 'キュー追加: {id}  {desc}',
        'ru': 'В очереди: {id}  {desc}',
    },
    'invalid_chain': {
        'de': 'Leere/ungültige Kette.',
        'en': 'Empty/invalid chain.',
        'es': 'Cadena vacía o no válida.',
        'zh': '空链或无效任务链。',
        'ja': '空または無効なチェーンです。',
        'ru': 'Пустая или недопустимая цепочка.',
    },
    'run_summary': {
        'de': 'Lauf fertig: {done} erledigt, {failed} weiterhin offen, {permanent} endgültig fehlgeschlagen (Start: {start} offen).{paused}',
        'en': 'Run complete: {done} done, {failed} still pending, {permanent} permanently failed (start: {start} pending).{paused}',
        'es': 'Ejecución completada: {done} completada(s), {failed} aún pendiente(s), {permanent} fallida(s) permanente(s) (inicio: {start} pendiente(s)).{paused}',
        'zh': '运行完成：已完成 {done} 个，仍有 {failed} 个待处理，{permanent} 个永久失败（初始：{start} 个待处理）。{paused}',
        'ja': '実行完了: {done} 件完了、{failed} 件保留中、{permanent} 件完全失敗（開始時: {start} 件保留中）。{paused}',
        'ru': 'Выполнение завершено: {done} выполнено, {failed} все еще в очереди, {permanent} окончательно не удалось (начало: {start} в очереди).{paused}',
    },
    'paused_providers': {
        'de': ' Pausiert: {names}',
        'en': ' Paused: {names}',
        'es': ' Pausado(s): {names}',
        'zh': ' 已暂停：{names}',
        'ja': ' 一時停止中: {names}',
        'ru': ' Приостановлено: {names}',
    },
    'context_installed': {
        'de': 'Kontextmenü installiert.',
        'en': 'Context menu installed.',
        'es': 'Menú contextual instalado.',
        'zh': '右键菜单已安装。',
        'ja': 'コンテキストメニューをインストールしました。',
        'ru': 'Контекстное меню установлено.',
    },
    'context_install_failed': {
        'de': 'Installation fehlgeschlagen.',
        'en': 'Installation failed.',
        'es': 'Error al instalar el menú contextual.',
        'zh': '右键菜单安装失败。',
        'ja': 'コンテキストメニューのインストールに失敗しました。',
        'ru': 'Ошибка установки контекстного меню.',
    },
    'context_removed': {
        'de': 'Kontextmenü entfernt.',
        'en': 'Context menu removed.',
        'es': 'Menú contextual eliminado.',
        'zh': '右键菜单已移除。',
        'ja': 'コンテキストメニューを削除しました。',
        'ru': 'Контекстное меню удалено.',
    },
    'context_remove_failed': {
        'de': 'Entfernen fehlgeschlagen.',
        'en': 'Removal failed.',
        'es': 'Error al eliminar el menú contextual.',
        'zh': '右键菜单移除失败。',
        'ja': 'コンテキストメニューの削除に失敗しました。',
        'ru': 'Ошибка удаления контекстного меню.',
    },
    'context_status_installed': {
        'de': 'installiert',
        'en': 'installed',
        'es': 'instalado',
        'zh': '已安装',
        'ja': 'インストール済み',
        'ru': 'установлено',
    },
    'context_status_not_installed': {
        'de': 'nicht installiert',
        'en': 'not installed',
        'es': 'no instalado',
        'zh': '未安装',
        'ja': '未インストール',
        'ru': 'не установлено',
    },
    'gui_rename_title': {
        'de': 'Verzögert umbenennen',
        'en': 'Deferred rename',
        'es': 'Renombrado diferido',
        'zh': '延迟重命名',
        'ja': '遅延リネーム',
        'ru': 'Отложенное переименование',
    },
    'gui_rename_prompt': {
        'de': 'Neuer Name für:\n{src}',
        'en': 'New name for:\n{src}',
        'es': 'Nuevo nombre para:\n{src}',
        'zh': '新名称（针对）：\n{src}',
        'ja': '新しい名前:\n{src}',
        'ru': 'Новое имя для:\n{src}',
    },
    'gui_move_title': {
        'de': 'Zielordner wählen',
        'en': 'Choose target folder',
        'es': 'Elegir carpeta de destino',
        'zh': '选择目标文件夹',
        'ja': '移動先フォルダーを選択',
        'ru': 'Выбрать целевую папку',
    },
    'gui_delete_title': {
        'de': 'Verzögert löschen',
        'en': 'Deferred delete',
        'es': 'Eliminación diferida',
        'zh': '延迟删除',
        'ja': '遅延削除',
        'ru': 'Отложенное удаление',
    },
    'gui_delete_confirm': {
        'de': "'{src}'\nverzögert löschen?",
        'en': "Delete '{src}'\n(deferred)?",
        'es': "¿Eliminar '{src}'\nde forma diferida?",
        'zh': '确定要延迟删除\n“{src}”吗？',
        'ja': "'{src}' を\n遅延削除しますか？",
        'ru': "Удалить '{src}'\nс задержкой?",
    },
    'gui_queued_title': {
        'de': 'CloudLockFixer',
        'en': 'CloudLockFixer',
        'es': 'CloudLockFixer',
        'zh': 'CloudLockFixer',
        'ja': 'CloudLockFixer',
        'ru': 'CloudLockFixer',
    },
    'gui_queued_msg': {
        'de': 'Eingereiht:\n{desc}\n\nWird beim nächsten Lauf erledigt.',
        'en': 'Queued:\n{desc}\n\nWill be processed on next run.',
        'es': 'En cola:\n{desc}\n\nSe procesará en la próxima ejecución.',
        'zh': '已加入队列：\n{desc}\n\n将在下次运行时处理。',
        'ja': 'キューに追加されました:\n{desc}\n\n次回の実行時に処理されます。',
        'ru': 'В очереди:\n{desc}\n\nБудет обработано при следующем запуске.',
    },
    'ctx_delayed_rename': {
        'de': 'Verzögert umbenennen',
        'en': 'Deferred rename',
        'es': 'Renombrar de forma diferida',
        'zh': '延迟重命名',
        'ja': '遅延リネーム',
        'ru': 'Отложенное переименование',
    },
    'ctx_delayed_move': {
        'de': 'Verzögert verschieben',
        'en': 'Deferred move',
        'es': 'Mover de forma diferida',
        'zh': '延迟移动',
        'ja': '遅延移動',
        'ru': 'Отложенное перемещение',
    },
    'ctx_delayed_delete': {
        'de': 'Verzögert löschen',
        'en': 'Deferred delete',
        'es': 'Eliminar de forma diferida',
        'zh': '延迟删除',
        'ja': '遅延削除',
        'ru': 'Отложенное удаление',
    },
    'queue_txt_header': {
        'de': "# CloudLockFixer — Aufgaben-Queue (eine Zeile = ein Task)\n# Syntax (Pfade mit Leerzeichen in Anführungszeichen):\n#   rename <pfad> <neuerName>\n#   move <quelle> <ziel>\n#   delete <pfad>\n#   Verkettung mit &&:   move <a> <b> && delete <c>\n# Aufgenommene Zeilen werden automatisch zu '#>' auskommentiert.\n",
        'en': "# CloudLockFixer — Task Queue (one line = one task)\n# Syntax (paths with spaces in quotes):\n#   rename <path> <newName>\n#   move <source> <target>\n#   delete <path>\n#   Chain with &&:   move <a> <b> && delete <c>\n# Processed lines are automatically commented out with '#>'.\n",
        'es': "# CloudLockFixer — Cola de tareas (una línea = una tarea)\n# Sintaxis (rutas con espacios entre comillas):\n#   rename <ruta> <nuevoNombre>\n#   move <origen> <destino>\n#   delete <ruta>\n#   Encadenar con &&:   move <a> <b> && delete <c>\n# Las líneas procesadas se comentan automáticamente con '#>'.\n",
        'zh': "# CloudLockFixer — 任务队列（一行 = 一个任务）\n# 语法（包含空格的路径请加双引号）：\n#   rename <路径> <新名称>\n#   move <源路径> <目标路径>\n#   delete <路径>\n#   使用 && 串联：   move <a> <b> && delete <c>\n# 已处理的行将自动注释为 '#>'。\n",
        'ja': "# CloudLockFixer — タスクキュー（1行 = 1タスク）\n# 構文（空白を含むパスは引用符で囲んでください）:\n#   rename <パス> <新しい名前>\n#   move <移動元> <移動先>\n#   delete <パス>\n#   && で連結:   move <a> <b> && delete <c>\n# 処理された行は自動的に '#>' でコメントアウトされます。\n",
        'ru': "# CloudLockFixer — Очередь задач (одна строка = одна задача)\n# Синтаксис (пути с пробелами указывайте в кавычках):\n#   rename <путь> <новоеИмя>\n#   move <источник> <назначение>\n#   delete <путь>\n#   Объединение через &&:   move <a> <b> && delete <c>\n# Обработанные строки автоматически комментируются символом '#>'.\n",
    },
    'parse_error': {
        'de': 'FEHLER',
        'en': 'ERROR',
        'es': 'ERROR',
        'zh': '错误',
        'ja': 'エラー',
        'ru': 'ОШИБКА',
    },
    'task_failed_max_retries': {
        'de': 'Nach {n} Fehlversuchen aufgegeben: {err}',
        'en': 'Gave up after {n} failed attempts: {err}',
        'es': 'Abandonado tras {n} reintentos fallidos: {err}',
        'zh': '在重试 {n} 次失败后放弃：{err}',
        'ja': '{n} 回の再試行失敗後に断念しました: {err}',
        'ru': 'Прекращено после {n} неудачных попыток: {err}',
    },
    'task_failed_unknown_error': {
        'de': 'unbekannter Fehler',
        'en': 'unknown error',
        'es': 'error desconocido',
        'zh': '未知错误',
        'ja': '不明なエラー',
        'ru': 'неизвестная ошибка',
    },
}

_current: Language = "de"


def detect_language() -> Language:
    """Sprache aus System-Locale ableiten (Fallback: Deutsch)."""
    try:
        lang, _ = locale.getlocale()
        if lang:
            lang_lower = lang.lower()
            if lang_lower.startswith("en"):
                return "en"
            if lang_lower.startswith("es"):
                return "es"
            if lang_lower.startswith("zh"):
                return "zh"
            if lang_lower.startswith("ja"):
                return "ja"
            if lang_lower.startswith("ru"):
                return "ru"
            if lang_lower.startswith("de"):
                return "de"
    except Exception:
        # locale.Error (Subclass von Exception) und ValueError/TypeError
        # bei ungültiger oder nicht gesetzter System-Locale abfangen.
        pass
    return "de"


def set_language(lang: Language) -> None:
    global _current
    _current = lang


def get_language() -> Language:
    return _current


def t(key: str, **kwargs: object) -> str:
    """Übersetze einen Schlüssel in die aktive Sprache."""
    entry = _CATALOG.get(key)
    if entry is None:
        return key
    text = entry.get(_current) or entry.get("de") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def available_keys() -> list[str]:
    return sorted(_CATALOG.keys())
