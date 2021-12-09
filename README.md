# Projekt KUMA
## Kuidas kasutada?
KBD moodulit:
`import kbd_reader as kbd`

KPM moodulit:
`import kpm_reader as kpm`

Vaja on PyBinaryReader'it, pygame'i ja pygame-gui'd, saab installida kasutades `pip install binary-reader`, `pip install pygame` ja `pip install pygame-gui`.


1 ruut on 100 ms.

Parema klõpsuga saab muuta käesolevat nooti. Noote saab üles korjata vasaku klõpsuga.

"Left Ctrl" annab "Hold" noote ja "Left Shift" annab "Rapid" noote.

"Delete" kustutab käesoleva noodi.

"E" vajutades saab muuta noodi parameetreid.

Nooltega saab liigutada scrollbari.

## TODO list
* Muusika mängimine - Play/Pause nupp, liigutab scrollbari, kast laulu ajaga
* Help nupp
* Surface suurust vähendada (lõpus olevad nupud lähevad algusesse)
* Kasutada kpm moodulit, et sealt lugeda cutscene start time 

## Viited
https://github.com/SutandoTsukai181/PyBinaryReader

https://github.com/CapitanRetraso/Yakuza-010-Editor-Templates/blob/main/Dragon%20Engine/minigame/de_karaoke_kbd.bt
