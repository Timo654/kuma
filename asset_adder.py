# Small tool for adding used textures to asset.json
import json
from pathlib import Path
asset_file = 'assets.json'
if Path(asset_file).is_file():
    with open(asset_file, 'r', encoding='UTF-8') as json_file:
        assets = json.load(json_file)
else:
    assets = dict()
    assets['Texture folder'] = ".\\assets\\textures"
    assets['Sheet texture'] = 'sheet.png'
    assets['Line texture'] = 'line.png'
    assets['Button prompts'] = dict()
    assets['Languages'] = dict()

adding_languages = True
while adding_languages:
    language_name = input('Enter the language name (in the native language) or enter to stop: ')
    if language_name == "":
        adding_languages = False
    else:
        assets['Languages'][language_name] = input('Enter the language code: ')


running = True
while running:
    controller_name = input(
        'Enter the button layout name or just press enter to quit: ')
    if controller_name == "":
        running = False
    else:
        button_texture = input('Enter the button texture filename: ')
        assets['Button prompts'][controller_name] = list()
        assets['Button prompts'][controller_name].append(button_texture)
        button_names = [input('Enter the right button name: '), input('Enter the down button name: '), input(
            'Enter the left button name: '), input('Enter the up button name: ')]
        assets['Button prompts'][controller_name].append(button_names)


with open(asset_file, 'w', encoding='UTF-8') as f:
    json.dump(assets, f, indent=2, ensure_ascii=False)

print('Asset list saved.')
