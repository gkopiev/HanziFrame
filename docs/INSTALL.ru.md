# Установка HanziFrame

[English version](INSTALL.md)

Эта инструкция поможет установить HanziFrame на LILYGO T5 4,7″ и подключить
его к Home Assistant. Home Assistant будет хранить слова и создавать изображение
карточки, а дисплей — загружать и показывать его.

Проект проверен с **Home Assistant Core 2026.8.1**, **Pyscript 2.0.1** и
**ESPHome 2026.7.4**. Если сборка не проходит на другой версии ESPHome, сначала
попробуйте 2026.7.4.

> Если вы добавляете HanziFrame в уже настроенный Home Assistant, сначала
> сделайте резервную копию. Дополняйте существующие `configuration.yaml` и
> `automations.yaml`, а не заменяйте их целиком.

## Что понадобится

- LILYGO T5 4.7″ на ESP32-S3;
- работающий Home Assistant и доступ к каталогу `/config`;
- HACS для установки Pyscript;
- ESPHome Device Builder или ESPHome CLI;
- USB-C-кабель с передачей данных и стабильное питание;
- Wi-Fi 2,4 ГГц, из которого дисплей может открыть Home Assistant.

Драйвер дисплея `t547`, шрифты и остальные файлы уже находятся в репозитории.
Отдельно скачивать драйвер не нужно.

## 1. Скачайте проект

Клонируйте репозиторий:

```console
git clone https://github.com/gkopiev/HanziFrame.git
cd HanziFrame
```

Либо выберите на GitHub **Code → Download ZIP** и распакуйте архив. Для переноса
файлов в Home Assistant можно использовать, например, Studio Code Server,
File editor или Samba.

Если вам помогает ИИ-агент, дайте ему ссылку на репозиторий: правила проекта он
найдёт в `AGENTS.md`. Пароли и ключи вводите самостоятельно и не отправляйте в
чат.

## 2. Настройте Home Assistant

### 2.1. Установите Pyscript и скопируйте файлы

1. Установите **Pyscript** через HACS и добавьте интеграцию в Home Assistant.
2. Скопируйте всё содержимое каталога `pyscript/` из репозитория в
   `/config/pyscript/`. Должны попасть `word_generator.py`, `requirements.txt`,
   CSV, оба шрифта и файлы их лицензий.
3. Создайте каталог `/config/www/`, если его ещё нет. В нём будет появляться
   файл `word.png`.
4. В настройках интеграции Pyscript включите **Allow all imports**. Если Pyscript
   настроен через YAML, добавьте параметр в существующую секцию:

```yaml
pyscript:
  allow_all_imports: true
```

Перезапустите Home Assistant. В **Инструменты разработчика → Действия** должны
появиться:

- `pyscript.generate_word_image`;
- `pyscript.add_chinese_word`;
- `pyscript.bulk_import_words`;
- `pyscript.import_words_from_csv`.

### 2.2. Создайте список слов и вспомогательные сущности

Добавьте официальную интеграцию **Local to-do**, создайте список `Chinese words`
и задайте ему точный ID:

```text
todo.chinese_words
```

Слова хранятся в виде `иероглифы | пиньинь | перевод`. Основной словарь — этот
Todo-список; встроенный CSV нужен для первого наполнения и импорта.

Добавьте следующий блок в `/config/configuration.yaml`. Если секции
`input_button:` или `input_text:` уже существуют, добавьте в них только
вложенные элементы — второй одноимённый верхнеуровневый ключ создавать нельзя.

<details>
<summary>Готовый YAML для вспомогательных сущностей</summary>

```yaml
input_button:
  hanziframe_next_word:
    name: "HanziFrame — Next word"
    icon: mdi:skip-next
  hanziframe_add_word:
    name: "HanziFrame — Add word"
    icon: mdi:plus
  hanziframe_import_words:
    name: "HanziFrame — Import pasted words"
    icon: mdi:playlist-plus
  hanziframe_import_csv_file:
    name: "HanziFrame — Import CSV file"
    icon: mdi:file-import

input_text:
  hanziframe_new_chinese:
    name: "HanziFrame — Chinese"
    max: 100
  hanziframe_new_pinyin:
    name: "HanziFrame — Pinyin"
    max: 100
  hanziframe_new_translation:
    name: "HanziFrame — Translation"
    max: 100
  hanziframe_csv_import_words:
    name: "HanziFrame — Pasted CSV"
    max: 255
```

</details>

Проверьте конфигурацию Home Assistant и перезапустите его. Сенсор
`sensor.current_hanzi_word` появится позже, после создания первой картинки.

### 2.3. Создайте первую карточку

В **Инструменты разработчика → Действия** последовательно вызовите:

1. `pyscript.import_words_from_csv` — добавит в Todo десять стартовых слов;
2. `pyscript.generate_word_image` — выберет слово и создаст картинку.

Проверьте, что в Home Assistant появился `sensor.current_hanzi_word`, а адрес
`http://АДРЕС_HOME_ASSISTANT:8123/local/word.png` показывает карточку. Если это
работает, часть Home Assistant готова.

## 3. Подготовьте и прошейте дисплей

### 3.1. Скопируйте конфигурацию ESPHome

Скопируйте в рабочий каталог ESPHome:

- `esphome/lilygo-display.yaml`;
- весь каталог `esphome/custom_components/t547/` без исключений;
- `esphome/secrets.example.yaml` как основу для секретов.

В Home Assistant это обычно выглядит так:

```text
/config/esphome/
├── lilygo-display.yaml
├── secrets.yaml
└── custom_components/
    └── t547/
```

Если `secrets.yaml` уже существует, не заменяйте его: добавьте в него четыре
ключа из `secrets.example.yaml`. Если файла нет, скопируйте пример под именем
`secrets.yaml`. Укажите Wi-Fi, ключ шифрования API и пароль OTA. Файл с реальными
значениями не публикуйте и не добавляйте в Git.

Ключ `api_encryption_key` — это 32 случайных байта в Base64. При необходимости
его и пароль OTA можно создать локально:

```console
openssl rand -base64 32
openssl rand -hex 24
```

Первый результат используйте для `api_encryption_key`, второй — для
`ota_password`.

В `lilygo-display.yaml` указан адрес картинки:

```text
http://homeassistant.local:8123/local/word.png
```

Если `homeassistant.local` не открывается с других устройств вашей сети,
замените только имя хоста на локальный IP-адрес Home Assistant.

### 3.2. Соберите и установите прошивку

Самый простой путь — через ESPHome Device Builder:

1. Откройте `lilygo-display.yaml` и выполните **Validate**.
2. Подключите LILYGO к USB-C-кабелю с передачей данных.
3. Нажмите **Install** и выберите подходящий USB-способ установки.

Если вы используете ESPHome CLI, сначала создайте `esphome/secrets.yaml` в
клоне, а затем из корня репозитория выполните:

```console
esphome run esphome/lilygo-display.yaml
```

Перед записью убедитесь, что выбран именно дисплей LILYGO, а не другое
USB-устройство. После первой загрузки Home Assistant предложит добавить новое
ESPHome-устройство. Добавьте его и введите тот же `api_encryption_key` через
интерфейс Home Assistant. Если устройство не обнаружилось автоматически,
добавьте интеграцию **ESPHome** вручную и укажите его имя или IP-адрес.

Устройство должно появиться под именем `hanzi-frame`, а среди его сущностей —
кнопка `button.hanzi_frame_refresh_chinese_word`.

## 4. Добавьте автоматизации

Файл `homeassistant/automation.yaml` содержит три автоматизации:

- смена слова при запуске Home Assistant и каждые 10 минут;
- смена слова по кнопке;
- добавление и импорт слов через вспомогательные сущности.

Откройте существующий `/config/automations.yaml` и добавьте в его конец три
элемента из файла репозитория. **Не заменяйте свой `automations.yaml` целиком.**
После этого проверьте конфигурацию Home Assistant и перезагрузите автоматизации.

## 5. Добавьте дашборд

Для первого запуска достаточно четырёх карточек:

- Markdown-карточка с изображением;
- Tile-карточка для `input_button.hanziframe_next_word`;
- Tile-карточка для `button.hanzi_frame_refresh_chinese_word`;
- To-do List для `todo.chinese_words`.

В Markdown-карточку вставьте:

```yaml
type: markdown
content: >-
  <img src="/local/word.png?v={{ state_attr('sensor.current_hanzi_word', 'image_version') | int(0) }}"
       style="width:100%;border-radius:8px;" alt="HanziFrame preview">
entity_id:
  - sensor.current_hanzi_word
```

Параметр `image_version` нужен, чтобы браузер не показывал старую картинку из
кэша. Для управления словарём с телефона по желанию добавьте:

- поля `input_text.hanziframe_new_chinese`,
  `input_text.hanziframe_new_pinyin`,
  `input_text.hanziframe_new_translation` и кнопку
  `input_button.hanziframe_add_word`;
- поле `input_text.hanziframe_csv_import_words` и кнопки
  `input_button.hanziframe_import_words` и
  `input_button.hanziframe_import_csv_file`.

Формат быстрой вставки — `汉字,hànzì,перевод`; несколько строк разделяются
`;;`.

## 6. Проверьте результат

Установка завершена, если:

- в `todo.chinese_words` есть стартовые слова;
- `/local/word.png` открывается и показывает карточку;
- устройство `hanzi-frame` доступно в Home Assistant;
- кнопка обновления дисплея загружает картинку на E-Ink-экран;
- кнопка «Следующее слово» меняет и предпросмотр, и изображение на дисплее.

## Если что-то не работает

| Проблема | Что проверить |
|---|---|
| Нет действий Pyscript | Файлы находятся в `/config/pyscript/`, включён `allow_all_imports`, Home Assistant перезапущен, Pillow установился из `requirements.txt`. |
| `no_active_todo_words` | Список Todo пуст. Импортируйте стартовый CSV или добавьте слово вручную. |
| Нет `/local/word.png` | Вызовите `pyscript.generate_word_image` и проверьте, что `/config/www/` существует и доступен для записи. |
| ESPHome не находит `t547` | Скопируйте весь `custom_components/t547/` рядом с YAML и выполните Clean build. |
| Картинка есть, но экран не обновляется | Проверьте кнопку обновления и доступность URL картинки с другого устройства в той же сети. При необходимости замените `homeassistant.local` на IP-адрес HA. |
| Дашборд показывает старую картинку | Проверьте наличие `image_version` и `entity_id` в Markdown-карточке. |
| USB-прошивка не начинается | Проверьте кабель с передачей данных, выбранный порт и при необходимости переведите плату в boot mode. |
| Цвета на экране перепутаны | Не добавляйте вторую инверсию в ESPHome: картинка уже инвертируется в Pyscript. |

## Официальные инструкции

- [Установка Pyscript](https://hacs-pyscript.readthedocs.io/en/latest/installation.html)
- [Настройка Pyscript и `allow_all_imports`](https://hacs-pyscript.readthedocs.io/en/latest/configuration.html)
- [Local to-do в Home Assistant](https://www.home-assistant.io/integrations/local_todo/)
- [Начало работы с ESPHome](https://esphome.io/guides/)
