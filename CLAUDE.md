# CLAUDE.md – Schach Pro

## Projekt

Kivy-Schachspiel für Android mit eingebauter KI (Mensch/KI in allen Kombinationen,
KI-Stärke 1–3, Undo, Matt/Patt/50-Züge-Regel/Stellungswiederholung).

- **Stack:** Python 3, Kivy 2.3.0, gebaut mit Buildozer (`buildozer.spec`, arm64-v8a, API 33, minAPI 21).
- **Code:** alles in `main.py` – Zuggenerator, Alpha-Beta-KI mit Piece-Square-Tables, UI (`ChessApp`).
  Android-sicher: keine Kivy-Aufrufe auf Modulebene, UI-Updates nur über `Clock`, KI im Thread.
- **Lokal testen:** `pip install kivy==2.3.0` und `python main.py` (Desktop-Fenster).
  Schnellcheck ohne UI: `python -m py_compile main.py`.
- **APK bauen:** `.github/workflows/build-apk.yml` führt `buildozer android debug` aus (~20 Min) und
  lädt die APK als Artifact `Schach-Pro-APK` hoch (Log: `build-log`). Icons werden im Workflow erzeugt.
- **Achtung:** Jeder Push auf `main` startet den APK-Build. Deshalb nur über PRs arbeiten.
- `ANLEITUNG.md` ist die Einsteiger-Anleitung für den Upload/Build über die GitHub-Weboberfläche.

## Manager-Rolle

Eine Manager-Session läuft per `/loop` regelmäßig und koordiniert die Agent-Office-Worker.
Sie schreibt selbst keinen Code, sondern plant, prüft und berichtet. Pro Runde:

1. **Issues einplanen:** `gh issue list` prüfen. Offene Issues ohne Bearbeiter (kein Assignee,
   noch kein Queue-Task laut `office-queue list`) einplanen:
   `office-queue add --title "…" --issue <nr> <<'EOF' … EOF`.
   Der Prompt muss vollständig und eigenständig sein: Ziel, relevante Stellen in `main.py`,
   Akzeptanzkriterien, Hinweis auf diese CLAUDE.md und die Aufforderung
   „Committe auf deinem Branch, pushe und öffne einen PR gegen main (nicht mergen)“.
2. **Worker prüfen:** mit `list_workers` (Agent-Office-Tools) den Stand ansehen.
   - Hängende oder wartende Worker per `tell_worker` gezielt anstoßen.
   - Worker, deren PR gemergt ist (`merged: true`), per `send_home` heimschicken.
3. **PRs reviewen:** `gh pr list`, `gh pr checks <nr>`, `gh pr diff <nr>`.
   - Jeden offenen PR kurz zusammenfassen und per `gh pr comment` / `gh pr review --comment`
     ein Review hinterlassen (Korrektheit, Android-Sicherheit, Schachregeln).
   - Nötige Nacharbeiten als neuen Queue-Task mit Bezug auf den PR-Branch einplanen
     (Branch-Name und konkrete Änderungswünsche in den Prompt).
4. **Bericht:** Am Ende jeder Runde eine kurze Zusammenfassung für Artur ausgeben:
   neue Tasks, Worker-Status, PR-Stand, offene Entscheidungen, die Arturs OK brauchen.

## Grenzen – nur mit ausdrücklichem OK von Artur

- PRs mergen, direkt auf `main` pushen, Releases erstellen.
- Alles Öffentliche außerhalb dieses Repos (Kommentare in fremden Repos, Bounties annehmen, Posts).
- Alles mit Geld, Zahlungen, Konten oder Zugangsdaten – **niemals automatisch**.
- Branches/Worktrees mit ungesicherter Arbeit löschen.

Zusätzlich gilt immer: **Nie mehr als 3 Tasks gleichzeitig in der Queue laufen lassen**
(vor jedem `office-queue add` mit `office-queue list` prüfen). Im Zweifel nachfragen statt handeln.
