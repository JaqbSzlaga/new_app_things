# Domowa spiżarnia

Prosta aplikacja Flask na GitHub + Render do pilnowania rzeczy spożywczych w kilku domach.

## Funkcje

- dodawanie wielu domów, np. `Dom 1`, `Dom 2`, `Mieszkanie`, `Działka`,
- jeden wspólny katalog produktów,
- zdjęcie produktu,
- osobny licznik ilości `+ / −` dla każdego domu,
- produkt nie znika, gdy ilość spadnie do `0`,
- przy zejściu z `1` do `0` aplikacja pyta, czy dodać produkt do listy zakupów,
- wspólna lista zakupów z licznikami, oznaczaniem jako kupione i usuwaniem,
- usuwanie produktu oraz domu.

## Uruchomienie lokalnie

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Potem otwórz:

```text
http://127.0.0.1:5000
```

Na Mac/Linux aktywacja venv wygląda tak:

```bash
source .venv/bin/activate
```

## Wrzucenie na GitHub

```bash
git init
git add .
git commit -m "Initial grocery pantry app"
git branch -M main
git remote add origin https://github.com/TWOJ_LOGIN/TWOJE_REPO.git
git push -u origin main
```

## Render

Projekt ma gotowy `render.yaml`, więc Render może utworzyć Web Service z dyskiem automatycznie.

Najważniejsze ustawienia ręczne, jeśli robisz bez `render.yaml`:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Environment: `Python 3`
- Environment variable: `PYTHON_VERSION=3.11.9`
- Environment variable: `DATA_DIR=/var/data`
- Disk mount path: `/var/data`

Render ma domyślnie efemeryczny system plików, więc bez persistent disk dane i zdjęcia mogą zniknąć po restarcie/redeployu. Dysk zachowuje tylko pliki zapisane pod jego mount path, np. `/var/data`.

## Ważne

To jest wersja startowa bez logowania. Każdy, kto ma link do aplikacji, może zmieniać produkty i listę zakupów. Następny sensowny krok to dodanie prostego hasła rodzinnego albo kont użytkowników.
