# MOSMIX Rain Predict

Home-Assistant-Integration für Regen- und Windvorhersagen der nächsten
2, 4 und 8 Stunden, mit Daten direkt vom Deutschen Wetterdienst (DWD).
Kein Account und kein API-Schlüssel nötig.

## Sensoren

15 Sensoren, jeweils für **2h, 4h und 8h ab jetzt**:

- **Regenwahrscheinlichkeit** (9 Sensoren): Wahrscheinlichkeit, dass es
  irgendwann in diesem Zeitraum regnet. Es gibt drei Varianten: jeder
  Niederschlag, mehr als 0,1 mm und mehr als 1,0 mm pro Stunde.
- **Wind** (6 Sensoren): höchste erwartete Windgeschwindigkeit und
  höchste erwartete Windböe im Zeitraum, mit den Attributen `beaufort`
  und `beaufort_name`.

Die nächstgelegene DWD-Station wird automatisch gewählt, die Daten
werden alle 30 Minuten aktualisiert.

**Hinweis:** Der DWD liefert Regenwahrscheinlichkeiten nur pro Stunde.
Die Werte für 2h/4h/8h werden daraus berechnet und liegen tendenziell
etwas zu hoch. Die Einzelwerte stehen im Attribut `hourly_values`.

## Installation über HACS

1. In Home Assistant: **HACS → ⋮ → Benutzerdefinierte Repositories**.
2. URL dieses Repositories mit Kategorie **Integration** hinzufügen.
3. **MOSMIX Rain Predict** installieren, danach Home Assistant neu
   starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen**, nach
   **MOSMIX Rain Predict** suchen.
5. Breiten-/Längengrad bestätigen oder anpassen (vorbelegt mit dem
   Home-Assistant-Standort) und absenden.

Den Standort kannst du später unter **Geräte & Dienste → MOSMIX Rain
Predict → Konfigurieren** ändern.

## Datenquelle

Deutscher Wetterdienst (DWD), MOSMIX_L, über
[opendata.dwd.de](https://opendata.dwd.de). Keine Verbindung zum DWD.
