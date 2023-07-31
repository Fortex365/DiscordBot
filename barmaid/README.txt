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
Pozn.: Zde je nutné se přihlásit pod svůj účet, vytvořit aplikaci jako bot, a zkopírovat "connection token".

5) Úprava proměnných prostředí
Soubor: .env-example
Soubor přejmenovat pouze na .env
Do obsahu souboru vložit získaný "connection token" na příslušné místo.

6) Získání identifikátoru aplikace
WEB: https://discord.com/developers/applications
Pozn.: Na webu vytvoříme pod sekcí OAuth2 pozvánku a nastavíme mu pravomoce "administrator". Vygenerovaný odkaz pozvánky zkopírujeme.

7) Nastavení identifikátoru
Soubor: config.json
Podle zkopírované pozvánky bota příslušně vyplníme obsah souboru. Zkopírovaný odkaz by měl být shodný s klíčem "BOT_INVITE_URL" až na odlišný identifikátor.
Nastavíme taktéž ostatní klíče, stačí upravit již existující identifikátor za svůj vlastní.

8) Spuštění aplikace
Příkaz: python3 barmaid.py



Pozn.: Na skutečném vzdáleném serveru a ponechání běhu aplikace i přes ukončené spojení může posloužit program "screen", který je již v distribuci.
### TLDR ###

Spuštění aplikace:
screen
python3 barmaid.py
(Ctrl+A+D detach from session using PuTTY for example)

Návrat k aplikaci:
screen -r

