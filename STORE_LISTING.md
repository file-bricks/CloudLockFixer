# Store Listing - CloudLockFixer

## Deutsch

### Kurzbeschreibung (max 100 Zeichen)
Lokales Windows-Werkzeug zur verzögerten Ausführung von Dateisperren in Cloud-Sync-Ordnern.

### Beschreibung (max 10.000 Zeichen)
CloudLockFixer ist ein schlankes, lokales Desktop- und Tray-Werkzeug für Windows, das typische Dateisperren in Ordnern von Cloud-Synchronisationsdiensten auflöst. Wenn Dateien während des Abgleichs blockiert sind, reiht CloudLockFixer Umbenennungen, Verschiebungen oder Löschungen in eine transparente Warteschlange ein und führt sie zuverlässig aus, sobald die Sperre freigegeben ist oder durch gezieltes temporäres Pausieren des jeweiligen Clients gelöst werden kann.

**Hauptfunktionen:**

- **Verzögerte Dateioperationen:** Umbenennen, Verschieben und Löschen von Dateien ohne lästige Fehlermeldungen bei aktiven Dateisperren.
- **Transparente Warteschlange:** Alle ausstehenden Operationen werden lokal verwaltet und können auf Knopfdruck oder im konfigurierten Zeitintervall abgearbeitet werden.
- **Sicheres Copy-and-Delete-Verfahren:** Robuster Fallback mit kryptografischem Prüfsummen-Vergleich vor dem Entfernen der Quelldatei.
- **Intelligente Provider-Erkennung:** Automatische Unterscheidung zwischen synchronisierten Ordnern und virtuell gemounteten Laufwerken zum Schutz des Dateisystems.
- **Präventiver Wächter:** Überwacht Verzeichnisse bei hoher Änderungsrate und verhindert Sperren vorausschauend.
- **Konfigurierbare Wiederholungen:** Einstellbare Wiederholungszyklen und verlässliche Desktop-Benachrichtigungen bei dauerhaft blockierten Aufgaben.
- **Mehrsprachige Benutzeroberfläche:** Vollständige Unterstützung für 6 Sprachen (Deutsch, Englisch, Spanisch, Chinesisch, Japanisch, Russisch) mit automatischer Spracherkennung.
- **Zero-Egress & Datenschutz:** 100 % lokal ohne Internetverbindung, ohne Telemetrie und ohne Registrierungszwang.

**Warum CloudLockFixer?**

- Keine verlorenen Dateioperationen durch blockierte Cloud-Synchronisation
- Minimale Systembelastung durch ressourcenschonenden Hintergrundbetrieb im Infobereich
- Vollständige Kontrolle über alle Warteschlangen und Zeitpläne
- Keine Werbung, keine Abonnements und keine Cloud-Abhängigkeiten

### Schlüsselwörter
Dateisperre, Cloud-Sync, Warteschlange, Hintergrundtool, Datei-Entsperrer, Tray-Tool, Task-Manager

### Kategorie
Utilities

---

## English

### Short Description (max 100 chars)
Local Windows utility for delayed file operations in locked cloud synchronization folders.

### Description (max 10,000 chars)
CloudLockFixer is a lightweight, local desktop and system tray utility designed to resolve persistent file lock conflicts in cloud-synchronized folders. When active file handles prevent renaming, moving, or deleting items, CloudLockFixer enqueues the operations into a transparent local task list and executes them cleanly as soon as the file lock is released or by safely pausing the corresponding sync client temporarily.

**Key Features:**

- **Delayed File Operations:** Effortlessly rename, move, and delete files that are temporarily locked by active sync routines.
- **Transparent Task Queue:** All pending actions are organized in a local queue and processed periodically or on demand.
- **Safe Copy-and-Delete Fallback:** Cryptographic checksum verification ensures complete data integrity before any source file is deleted.
- **Intelligent Provider Detection:** Distinguishes between standard sync directories and virtual drive mounts to protect filesystem integrity.
- **Preventive File Watcher:** Monitors active directories during bursts of modifications to prevent lockups proactively.
- **Configurable Retry Limits:** Tailor retry policies and receive optional desktop toasts when permanent obstacles arise.
- **Multilingual Interface:** Comprehensive support for 6 languages (English, German, Spanish, Chinese, Japanese, Russian) with automatic system language detection.
- **Zero-Egress Privacy:** Operates entirely offline with no network connections, no telemetry, and no account requirements.

**Why CloudLockFixer?**

- Eliminates frustrating "File in Use" errors in synchronized desktop directories
- Extremely lightweight background footprint in the Windows notification area
- Complete transparency with human-readable queues and detailed local diagnostics
- Open-source, local-first utility without ads, subscriptions, or remote dependencies

### Keywords
file lock, cloud sync, file unlocker, tray tool, task queue, background tool, file manager

### Category
Utilities

---

## Español

### Descripción breve (máx. 100 caracteres)
Utilidad de Windows para resolver bloqueos de archivos en carpetas sincronizadas en la nube.

### Descripción (máx. 10.000 caracteres)
CloudLockFixer es una utilidad local ligera para el escritorio y la bandeja del sistema de Windows, diseñada para resolver conflictos de bloqueo de archivos en carpetas sincronizadas en la nube. Cuando los identificadores de archivo activos impiden renombrar, mover o eliminar elementos durante la sincronización, CloudLockFixer encola las operaciones en una lista transparente de tareas locales y las ejecuta de forma limpia tan pronto como se libera el bloqueo o pausando temporalmente el cliente de sincronización correspondiente de forma segura.

**Características principales:**

- **Operaciones de archivo pospuestas:** Renombre, mueva y elimine archivos retenidos temporalmente por rutinas de sincronización activas sin errores molestos.
- **Cola de tareas transparente:** Todas las acciones pendientes se organizan localmente y se procesan periódicamente o a petición.
- **Procedimiento seguro de copia y eliminación:** Verificación de suma de comprobación criptográfica para garantizar la integridad absoluta de los datos antes de borrar cualquier archivo de origen.
- **Detección inteligente de proveedores:** Distingue entre carpetas sincronizadas estándar y unidades virtuales montadas para proteger la estructura del sistema de archivos.
- **Monitor preventivo de archivos:** Supervisa directorios activos durante ráfagas de cambios para prevenir bloqueos de manera proactiva.
- **Límites de reintento configurables:** Ajuste los ciclos de reintento y reciba notificaciones opcionales en el escritorio cuando surjan obstáculos permanentes.
- **Interfaz multilingüe:** Compatibilidad completa con 6 idiomas (español, alemán, inglés, chino, japonés y ruso) con detección automática del idioma del sistema.
- **Privacidad y cero fugas (Zero-Egress):** Funciona totalmente sin conexión, sin conexión a Internet, sin telemetría y sin necesidad de registro ni cuenta.

**¿Por qué CloudLockFixer?**

- Elimina errores frustrantes de "Archivo en uso" en directorios locales sincronizados
- Mínimo impacto en los recursos del sistema gracias a su funcionamiento en segundo plano
- Control total sobre todas las colas de tareas y la programación de reintentos
- Sin publicidad, sin suscripciones y sin dependencias remotas

### Palabras clave
bloqueo de archivos, sincronizacion, desbloqueador, bandeja del sistema, cola de tareas, segundo plano, gestor de archivos

### Categoría
Utilities

---

## 简体中文

### 简短说明 (最多 100 字符)
用于在云同步文件夹中解决文件锁定并延迟执行文件操作的 Windows 本地工具。

### 详细描述 (最多 10,000 字符)
CloudLockFixer 是一款轻量级的 Windows 桌面及系统托盘本地实用工具，专门用于解决云同步文件夹中常见的文件锁定冲突。当活跃的文件句柄阻止重命名、移动或删除操作时，CloudLockFixer 会将这些操作存入透明的本地任务队列中，并在锁定释放后自动可靠地执行，或通过安全地暂时暂停相应同步客户端来快速解决。

**主要功能：**

- **延迟文件操作：** 轻松重命名、移动和删除被同步例程锁定的文件，无需忍受烦人的系统错误弹窗。
- **透明任务队列：** 所有待处理操作均在本地进行组织管理，可根据配置的时间间隔或按需一键处理。
- **安全的“先复制后删除”机制：** 在删除源文件前执行严格的加密校验和对比，确保数据完整性万无一失。
- **智能同步提供商识别：** 自动区分标准同步文件夹与虚拟挂载驱动器，严密保护本地文件系统。
- **预防性文件监视器：** 在高频更改期间监视活动目录，主动预防潜在的文件锁定。
- **可配置的重试策略：** 灵活定制重试次数与间隔，遇到持续阻塞的任务时提供系统桌面通知。
- **完整多语言界面：** 全面支持 6 种语言（中文、德语、英语、西班牙语、日语、俄语），支持系统语言自动检测。
- **零数据外泄与隐私保护 (Zero-Egress)：** 100% 完全离线运行，无需互联网连接，无遥测追踪，无需注册账户。

**为什么选择 CloudLockFixer？**

- 告别同步文件夹中令人困扰的“文件正在被使用”报错
- 驻留系统托盘安静运行，系统资源占用极低
- 人性化队列与日志，完全透明掌控各项任务
- 无广告、无订阅、无外部云端依赖的本地优先开源工具

### 关键词
文件锁定, 云同步, 文件解锁, 系统托盘, 任务队列, 后台工具, 文件管理

### 类别
Utilities

---

## 日本語

### 簡単な説明 (最大 100 文字)
クラウド同期フォルダ内のファイルロックを遅延処理で解決するWindows用ローカルユーティリティ。

### 詳細な説明 (最大 10,000 文字)
CloudLockFixer は、クラウド同期フォルダ内で発生するファイルロック競合を安全に解決するために設計された、軽量な Windows デスクトップおよびシステムトレイ用ローカルユーティリティです。同期処理によってファイルがブロックされ、名前の変更、移動、削除が妨げられた場合でも、CloudLockFixer は操作を透明なローカルキューに保持し、ロックが解除された時点または同期クライアントを安全に一時停止することで確実に処理を実行します。

**主な機能:**

- **遅延ファイル操作:** 同期ルーチンによってロックされたファイルを、煩わしいエラーに悩まされることなくスムーズに名前変更、移動、削除します。
- **透明性の高いタスクキュー:** すべての保留中の操作はローカルで整理され、定期的にまたは手動でワンクリック処理できます。
- **安全なコピー＆削除プロシージャ:** 元ファイルを削除する前に暗号化チェックサムを照合し、データの完全性を確実に保護します。
- **インテリジェントなプロバイダー検出:** 通常の同期フォルダと仮想マウントドライブを自動的に判別し、ファイルシステムの安全を保ちます。
- **予防的ファイルウォッチャー:** 頻繁に変更が発生するディレクトリを監視し、ファイルロックの発生を未然に防ぎます。
- **柔軟なリトライ設定:** 再試行ポリシーをカスタマイズでき、永続的なブロックが発生した場合はデスクトップ通知を受け取ることができます。
- **多言語対応インターフェース:** 6言語（日本語、ドイツ語、英語、スペイン語、中国語、ロシア語）を完全にサポートし、システム言語を自動検出します。
- **プライバシー保護とゼロエグレス (Zero-Egress):** 外部インターネット接続不要、テレメトリ収集なし、アカウント登録不要で、100% ローカル完結で動作します。

**CloudLockFixer が選ばれる理由:**

- 同期フォルダで頻発する「ファイルが使用中」エラーによる中断を解消
- システムトレイ常駐による極めて軽量なリソース消費
- キューの状態をいつでも確認でき、高度な透明性と自己管理を実現
- 広告なし、サブスクリプションなし、外部依存なしの完全ローカル設計

### キーワード
ファイルロック, クラウド同期, ロック解除, システムトレイ, タスクキュー, バックグラウンド, ファイル管理

### カテゴリ
Utilities

---

## Русский

### Краткое описание (макс. 100 символов)
Утилита Windows для отложенных файловых операций при блокировках в папках облачной синхронизации.

### Описание (макс. 10.000 символов)
CloudLockFixer — это компактная локальная утилита для рабочего стола и системного трея Windows, предназначенная для устранения типичных конфликтов блокировки файлов в папках облачной синхронизации. Когда активные файловые дескрипторы блокируют переименование, перемещение или удаление файлов, CloudLockFixer помещает эти операции в прозрачную локальную очередь задач и чисто выполняет их, как только блокировка снимается или путем безопасной кратковременной приостановки соответствующего клиента синхронизации.

**Основные возможности:**

- **Отложенные файловые операции:** Простое переименование, перемещение и удаление файлов, заблокированных процессами синхронизации, без раздражающих ошибок.
- **Прозрачная очередь задач:** Все ожидающие действия упорядочиваются локально и обрабатываются периодически или по запросу пользователя.
- **Безопасная процедура копирования и удаления:** Проверка криптографической контрольной суммы гарантирует полную сохранность данных перед удалением исходного файла.
- **Интеллектуальное обнаружение провайдеров:** Автоматически различает стандартные папки синхронизации и виртуальные диски для надежной защиты файловой системы.
- **Превентивный мониторинг файлов:** Отслеживает активные каталоги при частых изменениях, предотвращая возможные блокировки заранее.
- **Настраиваемые лимиты повторов:** Гибкая настройка политики повторных попыток и системные уведомления на рабочем столе при постоянных препятствиях.
- **Многоязычный интерфейс:** Полная поддержка 6 языков (русский, немецкий, английский, испанский, китайский, японский) с автоматическим определением языка системы.
- **Приватность и нулевая утечка данных (Zero-Egress):** Работает полностью автономно без подключения к интернету, без телеметрии и без необходимости регистрации.

**Преимущества CloudLockFixer:**

- Избавляет от повторяющихся ошибок «Файл занят другим процессом» в синхронизируемых папках
- Минимальное потребление системных ресурсов при работе в фоновом режиме системного трея
- Полный визуальный контроль над всеми очередями задач и параметрами повторов
- Открытый исходный код, отсутствие рекламы, подписок и сторонних облачных зависимостей

### Ключевые слова
блокировка файлов, синхронизация, разблокировка, системный трей, очередь задач, фоновый режим, управление файлами

### Категория
Utilities
