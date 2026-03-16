# Schach Pro APK bauen — Schritt-für-Schritt

## Was du brauchst
- Einen Browser (Chrome, Firefox, Edge)
- Die ZIP-Datei `schach-pro-github.zip`
- ~25 Minuten Zeit

---

## Schritt 1: GitHub-Account anlegen (3 Min)

1. Öffne **https://github.com/signup**
2. E-Mail eingeben → Passwort → Username wählen
3. E-Mail bestätigen (Link in der Mail klicken)
4. Fertig — du bist eingeloggt

---

## Schritt 2: Neues Repository erstellen (1 Min)

1. Klicke oben rechts auf das **+** Symbol → **New repository**
2. Name: `schach-pro`
3. **Public** auswählen (GitHub Actions ist bei Public-Repos kostenlos)
4. Haken bei **Add a README file** → NICHT setzen
5. Klicke **Create repository**

---

## Schritt 3: Dateien hochladen (2 Min)

1. Du siehst jetzt eine leere Repo-Seite
2. Klicke auf **"uploading an existing file"** (blauer Link in der Mitte)
3. **WICHTIG**: Entpacke zuerst die ZIP-Datei auf deinem PC!
   - Rechtsklick auf `schach-pro-github.zip` → "Alle extrahieren"
4. Ziehe ALLE Dateien + Ordner aus dem entpackten Ordner ins Browser-Fenster:
   - `main.py`
   - `buildozer.spec`
   - `README.md`
   - `.github/` (ganzer Ordner!)

   **ACHTUNG**: Der `.github` Ordner ist versteckt!
   → Im Windows Explorer: Oben auf "Ansicht" → "Ausgeblendete Elemente" anhaken
   → Dann siehst du den `.github` Ordner

5. Unten auf **Commit changes** klicken

---

## Schritt 4: Build startet automatisch! (20 Min warten)

1. Klicke oben auf den Tab **Actions**
2. Du siehst "Build Schach Pro APK" — mit einem gelben Kreis (= läuft)
3. Klicke drauf um den Fortschritt zu sehen
4. Warte bis der Kreis **grün** wird (✅)

---

## Schritt 5: APK herunterladen (1 Min)

1. Wenn der Build grün ist → klicke auf den Build-Namen
2. Scrolle nach unten zu **Artifacts**
3. Klicke auf **Schach-Pro-APK** → Download startet
4. Du bekommst eine ZIP-Datei mit der APK drin

---

## Schritt 6: Auf Android installieren (2 Min)

1. APK per USB, Google Drive, WhatsApp oder E-Mail aufs Handy
2. Datei auf dem Handy antippen
3. Android fragt: "Unbekannte Quellen zulassen" → **Erlauben**
4. **Installieren** → **Öffnen**
5. Fertig! ♟

---

## Falls der Build fehlschlägt (roter Kreis ❌)

1. Klicke auf den fehlgeschlagenen Build
2. Klicke auf "build" → die rote Zeile aufklappen
3. **Screenshot machen** und im Chat senden
4. Alternativ: Unter "Artifacts" gibt es "build-log" zum Herunterladen

---

## Alternative: Dateien einzeln hochladen

Falls das ZIP-Entpacken nicht klappt, kannst du die Dateien
auch einzeln erstellen:

1. Im Repository: **Add file** → **Create new file**
2. Name: `.github/workflows/build-apk.yml`
   (GitHub erstellt die Ordner automatisch wenn du `/` tippst)
3. Inhalt reinkopieren → **Commit**
4. Wiederholen für `buildozer.spec` und `main.py`
