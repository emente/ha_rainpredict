# MOSMIX Rain Predict

Home-Assistant-Integration, die Regenwahrscheinlichkeits-Sensoren direkt
aus der **MOSMIX_L**-Vorhersage des Deutschen Wetterdienstes (DWD)
bereitstellt — ohne Drittanbieter-Wetter-API dazwischen.

## Was sie macht

- Lädt den offiziellen DWD-MOSMIX-Stationskatalog und ermittelt die
  nächstgelegene Vorhersagestation zu einem über die UI konfigurierten
  Standort.
- Lädt die MOSMIX_L-Vorhersage (KMZ/KML) dieser Station direkt von
  `opendata.dwd.de`.
- Liest drei DWD-Niederschlagswahrscheinlichkeits-Elemente für +2h/+4h/+8h
  aus, macht daraus insgesamt 9 Sensoren:
  - **Regenwahrscheinlichkeit in 2h/4h/8h** (`wwP`)
  - **Regenwahrscheinlichkeit >0,1mm in 2h/4h/8h** (`R101`)
  - **Regenwahrscheinlichkeit >1,0mm in 2h/4h/8h** (`R110`)
- Aktualisiert alle 30 Minuten (der DWD veröffentlicht alle 6 Stunden
  einen neuen MOSMIX_L-Lauf).

Jeder Sensor liefert DWD-Stations-ID/-Name/-Entfernung sowie den exakten
Vorhersage-Zeitpunkt als Attribute.

## Definition der Elemente (exakt, aus den DWD-Metadaten)

Quelle: [`MetElementDefinition.xml`](https://opendata.dwd.de/weather/lib/MetElementDefinition.xml),
der offizielle Elementkatalog des DWD.

| Element | Einheit | Offizielle DWD-Beschreibung | Übersetzung |
|---|---|---|---|
| `wwP` | % (0–100) | Probability: Occurrence of precipitation within the last hour | Wahrscheinlichkeit: Auftreten von Niederschlag innerhalb der letzten Stunde |
| `R101` | % (0–100) | Probability of precipitation > 0.1 mm during the last hour | Wahrscheinlichkeit für Niederschlag > 0,1 mm innerhalb der letzten Stunde |
| `R110` | % (0–100) | Probability of precipitation > 1.0 mm during the last hour | Wahrscheinlichkeit für Niederschlag > 1,0 mm innerhalb der letzten Stunde |

**Was "innerhalb der letzten Stunde" praktisch bedeutet:** Jeder
MOSMIX_L-Zeitschritt ist stündlich. Der Wert zum Zeitpunkt *T* ist die
Wahrscheinlichkeit, dass der jeweilige Niederschlags-Zustand irgendwann
innerhalb des **einstündigen Fensters, das bei *T* endet**, aufgetreten
ist — keine Momentaufnahme im Sinne von "regnet es gerade jetzt". Da die
"+2h/+4h/+8h"-Sensoren auf den nächstgelegenen stündlichen Zeitschritt
einrasten (MOSMIX_L ist an volle UTC-Stunden gebunden, nicht an die
Sekunde des letzten Sensor-Updates), kann das tatsächlich beschriebene
Fenster bis zu ~30 Minuten von einem wörtlichen "in N Stunden ab jetzt"
abweichen. Das exakte Fensterende steht immer im Attribut
`forecast_valid_time` jedes Sensors.

**Wie die drei Elemente zusammen zu lesen sind:** `wwP` beantwortet
"tritt *irgendein* messbarer Niederschlag auf", unabhängig von der
Menge — das ist meist der Wert, den Wetter-Apps als ihre
Haupt-Regenwahrscheinlichkeit zeigen. `R101` und `R110` beantworten die
strengere Frage "wird eine bestimmte Rate *überschritten*" (0,1 mm/h ≈
Schwelle für leichten Nieselregen, 1,0 mm/h ≈ spürbarer Regen) — nützlich
für Automationen, die nur auf Regen reagieren sollen, den man tatsächlich
spürt, nicht auf einen einzelnen erkennbaren Tropfen. Da die Schwellen
kumulativ sind, sollten die Werte zur selben Vorhersagestunde von
`wwP` → `R101` → `R110` abnehmen.

## Installation über HACS

1. In Home Assistant: **HACS → ⋮ → Benutzerdefinierte Repositories**.
2. URL dieses Repositories mit Kategorie **Integration** hinzufügen.
3. **MOSMIX Rain Predict** installieren, danach Home Assistant neu
   starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen**, nach
   **MOSMIX Rain Predict** suchen.
5. Breiten-/Längengrad bestätigen oder anpassen (vorbelegt mit dem
   Home-Assistant-Standort) und absenden.

## Standort nachträglich ändern

Über **Einstellungen → Geräte & Dienste → MOSMIX Rain Predict →
Konfigurieren** lässt sich der Standort jederzeit ändern, ohne die
Integration neu einzurichten. Die neuen Koordinaten werden vor dem
Speichern gegen die DWD-API validiert; die nächstgelegene Station wird
danach automatisch neu ermittelt.

## Datenquelle & Attribution

Vorhersagedaten: Deutscher Wetterdienst (DWD), MOSMIX_L, über
[opendata.dwd.de](https://opendata.dwd.de). Kein API-Key nötig, keine
Verbindung zum/Zugehörigkeit zum DWD.

## Einschränkungen

- Alle drei Elemente sind Wahrscheinlichkeiten mit Stundenauflösung für
  ein einstündiges Fenster, das am passenden Zeitschritt endet — keine
  Momentaufnahmen. Siehe "Definition der Elemente" oben.
- Beim Ändern des Standorts über den Options-Flow werden alle 9 Sensoren
  auf die neue nächstgelegene Station umgestellt; die bisherige
  Vorhersagehistorie (Sensor-Verlauf) bleibt unter derselben Entity-ID
  erhalten, bezieht sich aber ab dem Umschaltzeitpunkt auf den neuen Ort.
