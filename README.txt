###########################################
	Ubuntu Server 22.04 LTS
###########################################

1) Kontrola instalace Pythonu
Příkaz: python3 --version
Nainstalovaný Python by měl být ve verzi 3.8.10 (který je v distribuci defaultně)
	- V případě, že není. Příkaz: sudo apt install python3-pip


2) Instalace vyžadovaných knihoven aplikace
Příkaz: pip install -r requirements.txt

Pozn.: Je nutné být uvnitř složky, kde je aplikace umístěna např. v ./barmaid_bot
Není zde popsáno, jak na vzdálený server soubory přemístit (např. FileZillou).


3) Instalace FFmpeg
Příkaz: sudo apt install ffmpeg


4) Vytvoření aplikace na platformě
WEB: https://discord.com/developers/applications

Zde je nutné se přihlásit pod svůj účet, vytvořit aplikaci, v sekci "Bot" poté pomocí tlačítka "Reset Token" získat vlastní "connection token".


5) Úprava proměnných prostředí
Soubor: .env-example přejmenovat pouze na .env
A do obsahu souboru vložit získaný "connection token" na příslušné místo. Označeno placeholderem.


6) Získání identifikátoru aplikace
WEB: https://discord.com/developers/applications

Na webu v sekci "OAuth2" je "Client Information" a popiskem "CLIENT ID" a jeho číslem pod ním ke zkopírování.


7) Nastavení aplikace
WEB: https://discord.com/developers/applications

Na webu ještě vytvoříme pod sekcí "OAuth2" v podsekci "General" jako "Default Authorization Link" se zvolí možnost "In-app Authorization" a zvolí se následující
možnosti pro "Scopes" možnost "Bot" a "application.commands"; pro sekci "Bot Permissions" pouze "Administrator" tyto změny se uloží.


8) Nastavení identifikátoru
Soubor: config.json
Podle získaného identifikátoru aplikace "CLIENT ID" vyplníme soubor na příslušných místech. Označeno placeholderem.


9) Spuštění aplikace
Příkaz: python3 barmaid.py


----------------------------------------------
Pozn.: Na skutečném vzdáleném serveru a ponechání běhu aplikace i přes ukončené vzdálené spojení 
může posloužit program "screen", který je již v distribuci.

### TLDR ###

Spuštění aplikace:
screen
python3 barmaid.py
(Ctrl+A+D například skrze PuTTY program)

Návrat k aplikaci:
screen -r

