# Small tool for adding used textures to asset.json
import json
from pathlib import Path
asset_file = 'assets.json'
if Path(asset_file).is_file():
    with open(asset_file, 'r') as json_file:
        assets = json.load(json_file)
else:
    assets = dict()
    assets['Texture folder'] = ".\\assets\\textures"
    assets['Sheet texture'] = 'sheet.png'
    assets['Line texture'] = 'line.png'
    assets['Button prompts'] = dict()

running = True
while running:
    button_name = input('Enter the button layout name or just press enter to quit: ')
    if button_name == "":
        running = False
    else:
        button_texture = input('Enter the button texture filename: ')
        assets['Button prompts'][button_name] = button_texture

with open(asset_file, 'w') as f:
    json.dump(assets, f, indent=2)

print('Asset list saved.')