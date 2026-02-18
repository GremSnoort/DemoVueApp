# DEMOEXAM HOWTO MAKE CUSTOMIZATIONS

## ❓ **КАК И ЧТО КОПИРОВАТЬ? (frontend)**

‼️**НЕ ТРОГАТЬ ФАЙЛЫ:**
- `package.json`
- `package-lock.json`
- `index.html`
- `.gitignore`

‼️**НЕ ТРОГАТЬ ПАПКУ:**
- `node_modules`

### CSS style

Берем из прототипа **DemoVueApp**:
```
frontend/CUSTOMIZATIONS/trivial/src/styles/__fonted.css
```
и помещаем его в **СВОЙ ПРОЕКТ**:
```
frontend/src/styles/base.css
```

❗️**Остальные файлы из** `frontend/CUSTOMIZATIONS/trivial/src/styles/` **копировать НЕ НУЖНО!**


## ❓ **ИСПРАВЛЯЕМ НАЗВАНИЕ ПРОЕКТА!!!**

❗️**Исходное название проекта - DemoVueApp. Его НЕОБХОДИМО заменить на название проекта из .pdf доки с ТЗ!**

В **VSCode** открываем **СВОЙ ПРОЕКТ**, слева на вертикальной панели ищем значок "лупа" - поиск.

Вбиваем в поиск `DemoVueApp`. Открываем файл `AppHeader.vue` с найденным вхождением.

‼️**ЗАМЕНЯЕМ вхождение DemoVueApp на СКОПИРОВАННОЕ ИЗ .pdf доки с ТЗ НАЗВАНИЕ ПРОЕКТА**

‼️**Проверяем web-морду на предмет корректного отображение названия в верхней части страницы!**


## ❓ **Как засунуть картинки в слайдер?**

ℹ️ **На Рабочем столе в день экзамена будет лежать папка с заданием и приложениями к нему.**

Необходимо зайти в папку задания, разархивировать приложения, найти в них папку с картинками (их много) и выбрать себе **4 картинки**.

При помощи Проводника скопировать выбранные **4 картинки** вот в эту папку **СВОЕГО ПРОЕКТА**:
```bash
frontend/public/slider/
```
❗️Если этой папки не существует - создать ее.

Далее поправить имена картинок в коде:
- открываем файл `frontend/src/components/TopSlider.vue`
- ищем в нем фаргмент:
```js
const slides = [
  { src: "/slider/image07.jpg", alt: "Slide 1" },
  { src: "/slider/image08.webp", alt: "Slide 2" },
  { src: "/slider/image10.webp", alt: "Slide 3" },
  { src: "/slider/image13.webp", alt: "Slide 4" },
];
```
- исправляем имена картинок на те, которые по факту лежат в папке `slider`

‼️**Проверяем web-морду на предмет появления выбранных картинок в слайдере!**


## ❓ **Как подключить fonts?**

ℹ️ **На Рабочем столе в день экзамена будет лежать папка с заданием и приложениями к нему.**

Необходимо зайти в папку задания, разархивировать приложения, найти в них папку `fonts`. Внутри этой папки должна быть папка с шрифтом, например: `Roboto`.

❗️**Папка с шрифтом - это ИМЕННО папка, а НЕ архив!** Если не так - разархивировать.

При помощи Проводника скопировать себе папку с шрифтом вот в эту папку **СВОЕГО ПРОЕКТА**:
```bash
frontend/src/assets/fonts/
```
❗️Если какой-либо из промежуточных папкок не существует - создать их.

Далее поправить пути до шрифта и имена шрифта в стилях:
- открываем файл `frontend/src/styles/base.css`
- ищем в нем фаргмент:
```css
@font-face {
  font-family: "Roboto";
  src: url("../assets/fonts/Roboto/static/Roboto-Light.ttf") format("truetype");
  font-weight: 300;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Roboto";
  src: url("../assets/fonts/Roboto/static/Roboto-Regular.ttf") format("truetype");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Roboto";
  src: url("../assets/fonts/Roboto/static/Roboto-Medium.ttf") format("truetype");
  font-weight: 600;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Roboto";
  src: url("../assets/fonts/Roboto/static/Roboto-Bold.ttf") format("truetype");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```
- имя `Roboto` заменяем на имя своего шрифта и ПРОВЕРЯЕМ ПУТИ до `.ttf` - необходимо убедиться, что эти файлы существуют и корректно переименованы
