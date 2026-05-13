# Установка словаря в macOS

Это версия кыргызско-русского словаря Юдахина для стандартного приложения **Dictionary** в macOS. После установки словарь работает локально, открывается через системный поиск Dictionary.app и не требует интернета.

## Скачать

Скачайте архив:

https://github.com/xinatanil/udahin_corpus/releases/download/apple-dictionary-2026-05-13/kg_ru_udahin_apple_dictionary.zip

## Установить

1. Распакуйте архив `kg_ru_udahin_apple_dictionary.zip`.
2. В Finder откройте папку:

```text
~/Library/Dictionaries
```

Если папки `Dictionaries` нет, создайте её.

3. Перетащите распакованный файл словаря с расширением `.dictionary` в `~/Library/Dictionaries`.
4. Откройте приложение **Dictionary**.
5. В меню выберите **Dictionary → Settings...** или **Dictionary → Preferences...**.
6. Найдите кыргызско-русский словарь Юдахина в списке и включите его галочкой.

## Использовать

После включения словарь появится в приложении **Dictionary** рядом с другими словарями macOS. Можно искать кыргызские слова напрямую в Dictionary.app.

Если словарь не появился, полностью закройте Dictionary.app и откройте его снова. Иногда macOS подхватывает новые словари только после перезапуска приложения.

## Удалить

Удалите файл `.dictionary` из:

```text
~/Library/Dictionaries
```

После этого перезапустите Dictionary.app.

