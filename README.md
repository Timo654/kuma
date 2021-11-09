# Projekt KUMA
## Kuidas kasutada?
KBD moodulit:
`import kbd_reader as kbd`

KPM moodulit:
`import kpm_reader as kpm`

Vaja on PyBinaryReader'it, pygame'i ja pygame-menu'd, saab installida kasutades `pip install binary-reader`, `pip install pygame` ja `pip install pygame-menu`.

Parema klõpsuga saab muuta käesolevat nooti. Noote saab üles korjata vasaku klõpsuga.

"Left Ctrl" annab "Hold" noote ja "Left Shift" annab "Rapid" noote.

"Delete" kustutab käesoleva noodi.

## TODO list
* Välja mõelda, mis skaalat graafilises kasutajaliideses kasutada (võibolla teisendada sekunditeks ja jagada 250ms kaupa, et 4 ruutu oleks 1 sekund)
* Ühendada graafikaline kasutajaliides kbd mooduliga, et faile lugeda ning salvestada
* Tekitada nupp faili(de) avamiseks ja kast parameetrite muutmiseks (täpsem aeg, nupu tüüp jne)
* Kasutada kpm moodulit, et sealt lugeda cutscene start time

## Viited
https://github.com/SutandoTsukai181/PyBinaryReader

https://github.com/CapitanRetraso/Yakuza-010-Editor-Templates/blob/main/Dragon%20Engine/minigame/de_karaoke_kbd.bt
