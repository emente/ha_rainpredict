# MOSMIX Rain Predict

Home-Assistant-Integration, die dir sagt, wie wahrscheinlich es in 2, 4
oder 8 Stunden regnet — mit Daten direkt vom Deutschen Wetterdienst
(DWD), nicht von irgendeiner Drittanbieter-Wetter-App.

## Was sie macht

Nach der Einrichtung bekommst du 9 neue Sensoren in Home Assistant, die
jeweils einen Prozentwert (0–100 %) anzeigen: die Regenwahrscheinlichkeit
in 2, 4 und 8 Stunden. Diese Werte kannst du ganz normal für
Automationen nutzen, z.B. "wenn Regenwahrscheinlichkeit in 2h über 60 %,
schicke eine Benachrichtigung 'Wäsche reinholen'".

Es gibt davon drei Varianten, weil "Regenwahrscheinlichkeit" nicht
gleich "Regenwahrscheinlichkeit" ist:

- **Regenwahrscheinlichkeit** – wie wahrscheinlich ist überhaupt
  irgendein Niederschlag, und sei es nur ein bisschen Nieselregen.
  Das ist der Wert, den die meisten Wetter-Apps als Hauptzahl zeigen.
- **Regenwahrscheinlichkeit >0,1mm** – wie wahrscheinlich ist
  spürbarer, aber noch leichter Regen.
- **Regenwahrscheinlichkeit >1,0mm** – wie wahrscheinlich ist
  richtiger, deutlich nasser Regen.

Alle drei gibt es jeweils für 2h, 4h und 8h im Voraus — macht 3 × 3 = 9
Sensoren.

Im Hintergrund läuft das so: Die Integration sucht sich automatisch die
dir am nächsten liegende Wetterstation des DWD und holt von dort alle 30
Minuten die aktuelle Vorhersage. Das passiert automatisch im
Hintergrund — du musst dich um nichts kümmern, es ist kein Account und
kein API-Schlüssel nötig. Jeder Sensor zeigt zusätzlich als Info an,
welche Station verwendet wird, wie weit sie entfernt ist, und für welchen
genauen Zeitpunkt der Wert gilt.

## Technische Details zu den Elementen (für Interessierte)

Der Rest dieses Abschnitts ist nur für Leute interessant, die genau
wissen wollen, was die DWD-Werte im Detail bedeuten. Für die normale
Nutzung reicht das Verständnis aus dem Abschnitt oben.

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
  Momentaufnahmen. Siehe "Technische Details zu den Elementen" oben.
- Beim Ändern des Standorts über den Options-Flow werden alle 9 Sensoren
  auf die neue nächstgelegene Station umgestellt; die bisherige
  Vorhersagehistorie (Sensor-Verlauf) bleibt unter derselben Entity-ID
  erhalten, bezieht sich aber ab dem Umschaltzeitpunkt auf den neuen Ort.
