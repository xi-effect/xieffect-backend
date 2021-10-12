# Xi-Effect-Backend

## Работа над проектом
1. Скачать репозиторий (через `git clone` или PyCharm)
2. Временно сменить ветку на `prod`, далее см. [Раздел про GIT](#GIT)
3. Настроить виртуальное окружение или глобальный интерпретатор python. Используется [**3.9.7**](https://www.python.org/downloads/release/python-397/) ради совместимости с хостингом
4. Установить все библиотеки через `pip install -r requirements.txt`

### Для PyCharm
1. Пометить папки `xieffect` и `blueprints` как *Sources Root*
2. Открыть `api.py` и запустить его. Возможно, придётся поменять working directory на `path/to/project/xieffect`
3. Проверить доступность [http://localhost:5000/doc/](http://localhost:5000/doc/). Затем `api.py` можно останавливать
4. Создать конфигурацию `pytest` для папки `xieffect`. Также поменять working directory на `path/to/project/xieffect`. Проверить, что всё работает


### GIT
1. Никогда не работать в ветках `master` или `prod`
2. Создавать ответвления (feature-branches) от `prod` для работы над проектом
3. По окончании работы над фичей, отправлять PR из своей *feature-branch* в `prod`
4. В PR нужно отмечать issues, над которыми работали и призывать кого-то на review
5. Если во время работы над фичей произошло обновление в `prod`, необходимо обновить собственную ветку
