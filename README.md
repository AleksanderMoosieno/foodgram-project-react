![example workflow](https://github.com/AleksanderMoosieno/foodgram-project-react/actions/workflows/main.yml/badge.svg)

### Описание проекта Foodgram:

Foodgram - «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

Проект реализован через RESTful API (включая Django и Django REST Framework).

Поддерживает методы GET, POST, PUT, PATCH, DELETE

Предоставляет данные в JSON

### Как запустить проект:

Убедитесь, что у вас установлен Docker командой:

```
* docker -v
```

Клонируйте репозиторий:

```
* https://github.com/AleksanderMoosieno/foodgram-project-react

```

Перейдите в папку с проектом и создайте и активируйте виртуальное окружение:

```
* cd foodgram-project-react
* python3 -m venv env
```

```
* source venv/Scripts/activate
```

```
* python3 -m pip install --upgrade pip
```

Установите зависимости из файла requirements.txt:

```
* pip install -r requirements.txt
```

Перейдите в папку с файлом docker-compose.yaml:

```
* cd infra
```

Разверните контейнеры:

```
* docker-compose up -d --build
```

Выполните миграции, создайте суперпользователя, соберите статику:

```
* docker-compose exec backend python manage.py migrate
* docker-compose exec backend python manage.py createsuperuser
* docker-compose exec backend python manage.py collectstatic --no-input
```


Создайте дамп (резервную копию) базы:

```
* docker-compose exec backend python manage.py dumpdata > fixtures.json
```

### Автор проекта Foodgram:
***
* Aleksander Musienko  https://github.com/AleksanderMoosieno

Сайт доступен по ссылке http://84.201.137.139/

Админка Логин : fedokanez@mail.com
        Пароль : 444 999
