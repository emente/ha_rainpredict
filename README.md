# MOSMIX Rain+Wind Predict

Home-Assistant-Integration, die dir sagt, wie wahrscheinlich es in den
nächsten 2, 4 oder 8 Stunden regnet und wie stark der Wind dann
höchstens weht — mit Daten direkt vom Deutschen Wetterdienst (DWD),
nicht von irgendeiner Drittanbieter-Wetter-App.

## Was sie macht

Nach der Einrichtung bekommst du 15 neue Sensoren in Home Assistant:
9 für Regen und 6 für Wind.

**Regen:** Die 9 Regen-Sensoren zeigen jeweils einen Prozentwert
(0–100 %): die Wahrscheinlichkeit, dass es **irgendwann innerhalb der nächsten 2, 4 bzw. 8 Stunden**
regnet — nicht nur in einer einzelnen Stunde weit in der Zukunft,
sondern über den ganzen Zeitraum ab jetzt betrachtet. Diese Werte
kannst du ganz normal für Automationen nutzen, z.B. "wenn
Regenwahrscheinlichkeit innerhalb 2h über 60 %, schicke eine
Benachrichtigung 'Wäsche reinholen'".

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
Regen-Sensoren.

**Wind** funktioniert nach demselben Prinzip (Zeitraum ab jetzt, 2h, 4h
und 8h), nur dass hier keine Wahrscheinlichkeit angezeigt wird, sondern
der **höchste Wert, der in diesem Zeitraum erwartet wird**:

- **Höchste Windgeschwindigkeit innerhalb 2h/4h/8h** – der stärkste
  erwartete durchschnittliche Wind (wie er auch in Wetterberichten
  angegeben wird).
- **Höchste Windböe innerhalb 2h/4h/8h** – die stärkste erwartete
  einzelne Böe, also kurze Windspitzen. Die sind immer deutlich höher
  als der Durchschnittswind und für Dinge wie "Markise einfahren" oder
  "Sonnenschirm wegräumen" meist der bessere Auslöser.

Beide Wind-Sensoren haben zusätzlich die Attribute `beaufort` (Windstärke
0–12) und `beaufort_name` (z.B. "frische Brise", "Sturm"). Für Böen ist
die Beaufort-Angabe nur eine Orientierung — die Skala ist eigentlich für
den Durchschnittswind definiert.

Das ergibt 2 × 3 = 6 Wind-Sensoren. Der DWD liefert die Werte in m/s;
da die Sensoren als Windgeschwindigkeit gekennzeichnet sind, kann Home
Assistant sie in deiner bevorzugten Einheit (z.B. km/h) anzeigen — das
lässt sich in den Entitäts-Einstellungen des Sensors umstellen.

Im Hintergrund läuft das so: Die Integration sucht sich automatisch die
dir am nächsten liegende Wetterstation des DWD und holt von dort alle 30
Minuten die aktuelle Vorhersage. Das passiert automatisch im
Hintergrund — du musst dich um nichts kümmern, es ist kein Account und
kein API-Schlüssel nötig. Jeder Sensor zeigt zusätzlich als Info an,
welche Station verwendet wird, wie weit sie entfernt ist, und bis zu
welchem Zeitpunkt der betrachtete Zeitraum reicht.

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
| `FF` | m/s | Wind speed | Windgeschwindigkeit |
| `FX1` | m/s | Maximum wind gust within the last hour | Maximale Windböe innerhalb der letzten Stunde |

**Warum "kumulativ" nicht trivial ist:** Der DWD selbst liefert diese
Elemente nur stündlich, d.h. jeder Rohwert deckt nur ein einzelnes
1-Stunden-Fenster ab (z.B. "Wahrscheinlichkeit für Regen zwischen 11
und 12 Uhr"). Es gibt bei DWD keinen fertigen "Wahrscheinlichkeit für
Regen irgendwann in den nächsten 2/4/8 Stunden"-Wert für genau diese
Zeiträume (nur fertige 6h/12h/24h-Varianten, die nicht zu unseren
2h/4h/8h passen). Die Integration berechnet den kumulativen Wert
deshalb selbst, aus den einzelnen Stundenwerten:

```
P(mind. 1x Regen in N Stunden) = 1 - (1-p₁) × (1-p₂) × ... × (1-p_N)
```

Dabei sind p₁...p_N die stündlichen Einzelwahrscheinlichkeiten für die
nächsten N vollen Stunden. **Wichtige Einschränkung:** Diese Formel
setzt voraus, dass sich Regen in einer Stunde nicht auf die
Wahrscheinlichkeit in der nächsten Stunde auswirkt (statistische
Unabhängigkeit). In der Realität ist Regenwetter aber "klumpig" —
wenn es um 11 Uhr regnet, regnet es um 12 Uhr eher öfter weiter, statt
seltener. Der berechnete Wert liegt deshalb tendenziell etwas **zu
hoch** gegenüber der tatsächlichen Wahrscheinlichkeit. Er ist die beste
Näherung, die sich aus den öffentlich verfügbaren MOSMIX-Stundenwerten
bilden lässt, aber keine von DWD selbst berechnete Größe.

**Wind:** Hier wird nichts kombiniert, sondern schlicht das Maximum über
die Stundenwerte des Zeitraums genommen (`max(FF)` bzw. `max(FX1)` über
die nächsten N Stunden). Bei `FF` ist das der höchste stündliche
Windgeschwindigkeitswert, bei `FX1` die höchste Böe, die der DWD für
irgendeine dieser Stunden erwartet. Da `FF` selbst nur ein
Stunden-Rasterwert ist, kann eine kurze Windspitze zwischen zwei
Stunden darin untergehen — deshalb gibt es zusätzlich den Böen-Sensor.
Fehlt für eine der Stunden ein Wert, wird der Sensor "nicht verfügbar"
statt ein möglicherweise zu niedriges Maximum anzuzeigen.

Jeder Sensor hat als Attribut `hourly_values` die einzelnen
Rohwahrscheinlichkeiten, aus denen sich der angezeigte Wert
zusammensetzt, und `window_end` den Zeitpunkt, bis zu dem der Zeitraum
reicht — zur Nachvollziehbarkeit.

**Wie die drei Elemente zusammen zu lesen sind:** `wwP` beantwortet
"tritt *irgendein* messbarer Niederschlag auf", unabhängig von der
Menge — das ist meist der Wert, den Wetter-Apps als ihre
Haupt-Regenwahrscheinlichkeit zeigen. `R101` und `R110` beantworten die
strengere Frage "wird eine bestimmte Rate *überschritten*" (0,1 mm/h ≈
Schwelle für leichten Nieselregen, 1,0 mm/h ≈ spürbarer Regen) — nützlich
für Automationen, die nur auf Regen reagieren sollen, den man tatsächlich
spürt, nicht auf einen einzelnen erkennbaren Tropfen. Da die Schwellen
kumulativ sind, sollten die Werte zum selben Zeitraum von
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

- Die kumulativen Werte sind eine Näherung (Unabhängigkeitsannahme über
  die Stundenwerte) und tendenziell leicht zu hoch — keine offizielle
  DWD-Kennzahl. Siehe "Technische Details zu den Elementen" oben.
- Da MOSMIX_L nur stündliche Zeitschritte liefert, überschneidet sich
  das betrachtete Zeitfenster leicht mit der laufenden Stunde (bis zu
  ~1h Rückblick statt rein zukunftsgerichtet 0h).
- Die Wind-Werte sind das Maximum über Stundenwerte einer Modellvorhersage
  für den Stationsstandort; lokale Windverhältnisse (Straßenschluchten,
  Hanglagen) kann sie nicht abbilden.
- Beim Ändern des Standorts über den Options-Flow werden alle 15 Sensoren
  auf die neue nächstgelegene Station umgestellt; die bisherige
  Vorhersagehistorie (Sensor-Verlauf) bleibt unter derselben Entity-ID
  erhalten, bezieht sich aber ab dem Umschaltzeitpunkt auf den neuen Ort.
