# Projekt KUMA
## Kuidas kasutada?
KBD moodulit:
`import kbd_reader as kbd`

KPM moodulit:
`import kpm_reader as kpm`

Vaja on PyBinaryReader'it, pygame'i ja pygame-menu'd, saab installida kasutades `pip install binary-reader`, `pip install pygame` ja `pip install pygame-menu`.


1 ruut on 100 ms.

Parema klõpsuga saab muuta käesolevat nooti. Noote saab üles korjata vasaku klõpsuga.

"Left Ctrl" annab "Hold" noote ja "Left Shift" annab "Rapid" noote.

"Delete" kustutab käesoleva noodi.

"E" vajutades saab muuta noodi parameetreid.

## TODO list
* Edasi arendada kaste parameetrite muutmiseks (täpsem aeg, nupu tüüp, cue ID jne)
* Muusika mängimine?
* Kasutada kpm moodulit, et sealt lugeda cutscene start time 

## Viited
https://github.com/SutandoTsukai181/PyBinaryReader

https://github.com/CapitanRetraso/Yakuza-010-Editor-Templates/blob/main/Dragon%20Engine/minigame/de_karaoke_kbd.bt
