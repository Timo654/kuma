# DE Karaoke Editor - KUMA
image::media/icon_full.png[KUMA]
## How to use?
# Precompiled builds
Grab the latest build from [Releases tab](https://github.com/Timo654/kuma/releases/tag/latest).
It's a PyInstaller executable, so it's possible that it will trigger antivirus software. If you don't trust it, you can install the newest version of Python3 and use the .py file.
To find instructions on how to use the tool, go to the menu bar, pick 'Help' and 'How to use'.

# From source
To use KUMA, you first need to install the libraries specified in 'requirements.txt'.
After that, run 'src/gui_kuma.py'. 
To find instructions on how to use the tool, go to the menu bar, pick 'Help' and 'How to use'.

## Importing files from other games
This tool allows you to import map files from Lost Judgment dancing, Persona Dancing, Old Engine karaoke, Yakuza 5 Princess League, Ishin dancing, Zero disco, decompiled Project DIVA MegaMix+ beatmaps and Project Heartbeat json files.
The imported maps might not be identical to how they were in the original game, due to differences in the karaoke system. Feel free to file an issue for any import related issues you find. 

## Exporting to other games
This tool has very experimental Lost Judgment dbd export support, and also a way of exporting the file as JSON. The exported JSON files can be imported back into KUMA. 

## Contributing
Feel free to make any pull requests, I'll try to review them. The code is somewhat of a mess, though. Filing issues is also appreciated.
image::media/kuma.png[Screenshot of the GUI]
## Credits
https://github.com/SutandoTsukai181/PyBinaryReader

https://github.com/CapitanRetraso/Yakuza-010-Editor-Templates/blob/main/Dragon%20Engine/minigame/de_karaoke_kbd.bt

https://github.com/MyreMylar/pygame_paint

https://github.com/TheBigKahuna353/Inventory_system

https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/other/scrollbar.py

https://github.com/TGEnigma/010-Editor-Templates/blob/master/templates/p4d_mns.bt
