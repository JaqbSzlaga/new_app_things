# Domowa spiżarnia

Prosta aplikacja Flask na GitHub + Render do pilnowania rzeczy spożywczych w kilku domach.

## Funkcje

- dodawanie wielu domów, np. `Dom 1`, `Dom 2`, `Mieszkanie`, `Działka`,
- jeden wspólny katalog produktów,
- licznik `+ / −` osobno dla każdego produktu w każdym domu,
- produkt nie znika, gdy ilość spadnie do `0`,
- przy zejściu z `1` do `0` aplikacja pyta, czy dodać produkt do listy zakupów,
- lista zakupów pokazuje, **do którego domu** brakuje danego produktu,
- możliwość ręcznego dodania produktu do listy zakupów dla konkretnego domu,
- 10 gotowych produktów z grafikami: mleko, jajka, chleb, masło, ser, makaron, ryż, cukier, kawa, woda,
- możliwość dodania własnego zdjęcia produktu,
- PWA: aplikację można dodać do ekranu głównego telefonu,
- czytelniejszy wygląd mobilny z przełączaniem `Spiżarnia / Zakupy`,
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
git add .
git commit -m "Improve mobile pantry app"
git push
```

Jeśli to pierwszy push do pustego repo:

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

## Jak dodać na ekran telefonu

### iPhone / Safari

1. Otwórz link aplikacji w Safari.
2. Kliknij ikonę udostępniania.
3. Wybierz `Do ekranu początkowego`.
4. Zapisz.

### Android / Chrome

1. Otwórz link aplikacji w Chrome.
2. Kliknij menu `⋮`.
3. Wybierz `Dodaj do ekranu głównego` albo `Zainstaluj aplikację`.
4. Zapisz.

## Ważne

To jest wersja bez logowania. Każdy, kto ma link do aplikacji, może zmieniać produkty i listę zakupów. Następny sensowny krok to dodanie prostego hasła rodzinnego albo kont użytkowników.
