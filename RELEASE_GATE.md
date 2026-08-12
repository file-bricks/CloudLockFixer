# CloudLockFixer — Windows-Release-Gate

**Status:** nicht als Release freigegeben
**Kanonische Source-Version:** `0.2.2`
**Baseline-Tag:** `v0.2.2`
**Historischer Initial-Tag:** `v1.0.0`

## Versions- und Release-Vertrag

`pyproject.toml` (`project.version`) und `cloudlockfixer.__version__` sind die
kanonische Source-Version und müssen beide `0.2.2` ergeben. `v1.0.0` bezeichnet
den historischen Initial-Tag; er darf nicht als Freigabe des aktuellen HEAD
oder der unreleased Änderungen interpretiert werden. Der aktuelle Source-Stand
bleibt bis zum Abschluss dieses Gates `unreleased`.

Vor einem Tag oder Upload müssen diese Werte und der Arbeitsbaum frisch
ausgelesen werden. Ein grüner Testlauf ersetzt weder die Windows-Freigabe noch
die Prüfung der tatsächlichen Paketartefakte.

## Reproduzierbarer Smoke-Lauf (Windows)

Der Smoke-Lauf wird in einem lokalen, nicht synchronisierten temporären Ordner
ausgeführt. Er darf keine echte Cloud-Wurzel, keinen produktiven Datenordner,
keinen laufenden Sync-Client und keine Registry-Einstellung verändern.

```powershell
git status --short --branch
git diff --check
$env:PYTHONPATH = "src"
$env:PYTHONIOENCODING = "utf-8"
python -m pytest -q
python -m pytest tests/source_platform_smoke.py -q
```

Zusätzlich ist auf einem echten Windows-Arbeitsplatz manuell zu protokollieren:

1. `START.bat` beziehungsweise das geprüfte PyInstaller-Artefakt startet die
   Tray-App mit genau einem Prozess und schreibt Startfehler in den vorgesehenen
   lokalen Datenordner.
2. Das Tray-Menü zeigt Status, *Run now*, *Add task*, *Open data folder*,
   Intervall, Autostart, Kontextmenü, Wächter, Sprache und *Quit*. Die Prüfung
   darf die Umschalter nicht aktivieren oder deaktivieren.
3. Eine `rename`-, `move`- und `delete`-Probe arbeitet ausschließlich in einem
   neu angelegten Temp-Baum. Die copy+delete-Fallback-Kopie muss vor dem
   Quell-Löschen per Inhaltsdigest verifiziert werden; ein falscher Digest muss
   die Quelle erhalten.
4. Provider- und Volume-Label-Discovery wird mit Test-Doubles geprüft. Nur die
   bekannten exakten Labels `Google Drive` und `pCloud Drive` dürfen
   einen virtuellen Mount ergeben; frei umbenannte Labels wie `My Google Drive`
   oder `pCloud Backup` müssen ausgeschlossen bleiben. Es werden dabei keine
   realen Provider-Prozesse beendet oder gestartet.
5. Autostart- und Explorer-Kontextmenü-Gates werden in einer isolierten Prüfung
   nur gelesen oder mit explizitem Cleanup ausgeführt. Kein Smoke-Lauf darf
   ungefragt HKCU, Dateien außerhalb des Temp-Baums oder einen Cloud-Client
   verändern.

## Freigabegrenzen

Die folgenden Nachweise bleiben bis zu ihrer separaten Bestätigung offen:

- native PyInstaller-Build-/Startprüfung des konkreten Release-Artefakts;
- echte Windows-Tray-/Login-Interaktion und echte Provider-Prozessmodelle;
- Sicherheitsreview für Registry, Kontextmenü, Prozesssteuerung und destruktive
  Dateisystemoperationen;
- Tag, Upload, Store- oder sonstige Veröffentlichung.

Ein bestandener Source-/CI-Smoke ist daher ein **Release-Gate-Nachweis**, keine
Behauptung, dass `1.0.0` veröffentlicht oder sicherheitsseitig freigegeben ist.
