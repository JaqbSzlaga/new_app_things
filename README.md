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

## Zmiany v4

- Gotowe produkty w oknie dodawania są teraz mniejsze i układają się w siatkę po 3 kafelki na telefonie.
- Można zaznaczyć kilka gotowych produktów naraz i dodać je jednym przyciskiem.
- Ilość początkowa ustawiona w sekcji domów zostanie zastosowana do wszystkich zaznaczonych produktów.
- Zmieniono wersję cache PWA, żeby telefon szybciej pobrał nowy wygląd.


## v6
- Poprawione okno dodawania produktów na telefonie.
- Gotowe produkty są teraz zwykłą pionową listą ze zdjęciem, nazwą, kategorią i kółkiem wyboru.
- Można zaznaczać kilka produktów i dodać je jednym przyciskiem.


## v7
- Cały widok dodawania produktów przepisany od zera.
- Usunięte stare klasy kafelków z pickera.
- Nowy picker to prosta lista: checkbox, zdjęcie, nazwa, kategoria.

## Darmowy zapis danych przez PostgreSQL
Ta wersja zapisuje domy, produkty, liczniki, listę zakupów i notatki w PostgreSQL, jeśli ustawisz zmienną środowiskową `DATABASE_URL`.

Na Renderze ustaw:

```text
DATABASE_URL=postgresql://...
```

Bez `DATABASE_URL` aplikacja działa lokalnie na SQLite.
