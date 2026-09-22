# Test-Evidence

`publish-smoke-local.json` enthält den aktuellen, beim Publish ausgeführten Mac-Chrome-Testlauf.
`source-provenance.json` belegt die Byte-Gleichheit mit der gelieferten Miniature Edition.
`initial-smoke-test-assumption.json` dokumentiert auch den ersten Durchlauf: 32/33 bestanden. Der Nacht-Test nahm fälschlich an, dass zwei Klicks vom gespeicherten Startthema immer zur Nacht führen. Der Test wählt jetzt **Nachtschicht explizit über das Grafikmenü**. Die Anwendung wurde dabei nicht geändert.

Die Screenshots stammen aus dem echten Canvas-/DOM-Rendering in isolierten Chrome-Profilen. QA-Hooks frieren Bots ein und bewegen die Spielfigur über die reguläre Wegfindung zur Aufgabenstation; es sind keine generierten Illustrationen. Mobilansichten sind emuliert, keine Messungen auf physischen Geräten. Safari und Online-Multiplayer wurden nicht getestet.

## Trump Among Us — Branding-Update

`publish-smoke-local.json` und die Screenshots wurden nach der Umbenennung in Headless Google Chrome auf dem Linux-CI-Runner neu erstellt. `rename-branding.json` prüft zusätzlich sechs Bildschirmbreiten. `source-provenance.json` und der erste Testlauf bleiben unveränderte historische Herkunftsnachweise der ursprünglichen Miniature Edition. Der lokale Speicherschlüssel wurde absichtlich beibehalten.
