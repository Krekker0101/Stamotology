import config

# Centralized translations for the application
# Keys are arbitrary identifiers used from UI code via tr("key")

def tr(key: str, **kwargs) -> str:
    """Translate key according to current language in config.config.current_language.
    Supports simple Python format placeholders like {count}.
    """
    lang = config.config.current_language
    translations = {
        config.Language.RUSSIAN: {
            # General
            "settings": "Настройки",
            "profile": "Профиль",
            "users": "Пользователи",
            "appearance": "Внешний вид",
            "database": "База данных",
            "save": "Сохранить",
            "close": "Закрыть",
            "error": "Ошибка",
            "success": "Успех",
            # Profile
            "username": "Имя пользователя",
            "full_name": "Полное имя",
            "role": "Роль",
            "current_password": "Текущий пароль",
            "new_password": "Новый пароль",
            "confirm_password": "Подтвердите пароль",
            "change_password": "Изменить пароль",
            "change_password_section": "— Изменение пароля —",
            "fill_all_password_fields": "Заполните все поля пароля",
            "passwords_mismatch": "Пароли не совпадают",
            "password_length_error": "Пароль должен быть не менее 6 символов",
            # Users
            "add_user": "➕ Добавить пользователя",
            "create_user": "Создать пользователя",
            "create": "Создать",
            "cancel": "Отмена",
            "user_created": "Пользователь создан",
            # Database
            "current_db_file": "Текущий файл БД",
            "select_db_file": "Выбрать файл БД",
            "create_new_db": "Создать новую БД",
            "apply": "Применить",
            "db_switched": "База данных переключена на {path}",
            "db_not_selected": "Файл базы данных не выбран",
            # Patients view
            "total_patients_count": "Всего пациентов: {count}",
            "search": "Поиск",
            "quick_search_placeholder": "Быстрый поиск...",
            "add_patient": "➕ Добавить",
            "export": "📤 Экспорт",
            "filter_by_status": "Фильтр по статусу",
            "disease_type": "Тип заболевания",
            "all_statuses": "Все статусы",
            "all_types": "Все типы",
            "sort": "Сортировка",
            "per_page": "На странице:",
            "page_label": "Страница {current} из {total}",
            # Table headers
            "hdr_id": "ID",
            "hdr_full_name": "ФИО",
            "hdr_phone": "Телефон",
            "hdr_birth_year": "Год рождения",
            "hdr_disease_type": "Тип заболевания",
            "hdr_disease_name": "Заболевание",
            "hdr_status": "Статус",
            "hdr_registration_date": "Дата регистрации",
            # Themes
            "theme": "Тема оформления",
            "theme_light": "Светлая",
            "theme_dark": "Темная",
        },
        config.Language.TAJIK: {
            # General
            "settings": "Танзимот",
            "profile": "Профил",
            "users": "Истифодабарандагон",
            "appearance": "Намоиш",
            "database": "Маълумоти БД",
            "save": "Сабт",
            "close": "Пӯшидан",
            "error": "Хато",
            "success": "Муфассал",
            # Profile
            "username": "Номи корбар",
            "full_name": "Номи пурра",
            "role": "Нақш",
            "current_password": "Рамзи ҳозира",
            "new_password": "Рамзи нав",
            "confirm_password": "Тасдиқи рамз",
            "change_password": "Тағир додани рамз",
            "change_password_section": "— Тағйири рамз —",
            "fill_all_password_fields": "Лутфан ҳамаи майдонҳои рамзро пур кунед",
            "passwords_mismatch": "Рамзҳо мувофиқ нестанд",
            "password_length_error": "Рамз ҳадди ақал 6 аломат бояд бошад",
            # Users
            "add_user": "➕ Илова кардани корбар",
            "create_user": "Эҷоди корбар",
            "create": "Эҷод",
            "cancel": "Бекор кардан",
            "user_created": "Корбар сохта шуд",
            # Database
            "current_db_file": "Файли ҷории БД",
            "select_db_file": "Интихоби файли БД",
            "create_new_db": "Созмони нави БД",
            "apply": "Паҳн кардан",
            "db_switched": "Базаи додаҳо ба {path} гузашт",
            "db_not_selected": "Файли БД интихоб нашудааст",
            # Patients view
            "total_patients_count": "Ҳамагӣ беморон: {count}",
            "search": "Ҷустуҷӯ",
            "quick_search_placeholder": "Ҷустуҷӯи зуд...",
            "add_patient": "➕ Илова",
            "export": "📤 Содирот",
            "filter_by_status": "Филтр по вазъ",
            "disease_type": "Навъи беморӣ",
            "all_statuses": "Ҳамаи ҳолатҳо",
            "all_types": "Ҳама чизҳо",
            "sort": "Тартиб",
            "per_page": "Дар саҳифа:",
            "page_label": "Саҳифа {current} аз {total}",
            # Table headers
            "hdr_id": "ID",
            "hdr_full_name": "Номи пурра",
            "hdr_phone": "Телефон",
            "hdr_birth_year": "Соли таввалуд",
            "hdr_disease_type": "Навъи беморӣ",
            "hdr_disease_name": "Номи беморӣ",
            "hdr_status": "Вазъ",
            "hdr_registration_date": "Санаи бақайдгирӣ",
            # Themes
            "theme": "Мавзӯъ",
            "theme_light": "Равшан",
            "theme_dark": "Торик",
        }
    }

    text = translations.get(lang, {}).get(key, key)
    try:
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return text
