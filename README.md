# Domowa spiżarnia

Mobilna aplikacja webowa Flask + SQLite do prowadzenia wspólnej spiżarni i listy zakupów dla kilku domów.

## Funkcje

- wiele domów, np. Dom 1, Dom 2, mieszkanie, działka,
- produkty ze zdjęciami i licznikami `+ / −`,
- produkt nie znika po zejściu do `0`, usuwa się dopiero przyciskiem `Usuń`,
- pytanie o dodanie do listy zakupów, gdy ilość w danym domu spadnie do `0`,
- lista zakupów pokazuje, do którego domu brakuje produktu,
- około 100 gotowych produktów z grafikami, podzielonych na kategorie,
- zakładka **Notatki** do zapisywania pomysłów na ulepszenia aplikacji,
- PWA, czyli możliwość dodania aplikacji do ekranu głównego telefonu.

## Lokalnie

```bash
pip install -r requirements.txt
python app.py
```

## Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

Zalecane zmienne środowiskowe:

```bash
PYTHON_VERSION=3.11.9
DATA_DIR=/var/data
```

Dla trwałej bazy SQLite i uploadowanych zdjęć dodaj w Renderze persistent disk z mount path `/var/data`.
