# Estructura del Proyecto

```
.
├── .env
├── .gitignore
├── db_dev.sqlite3
├── generate_structure.py
├── manage.py
├── project_structure.md
├── pyproject.toml
├── README.md
├── requirements.txt
├── config
│   ├── __init__.py
│   ├── asgi.py
│   ├── urls.py
│   ├── wsgi.py
│   └── settings
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
├── mediafiles_dev_local
└── src
    ├── __init__.py
    ├── core
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── middlewares.py
    │   ├── models
    │   │   ├── __init__.py
    │   │   ├── audit.py
    │   │   ├── notification.py
    │   │   ├── role.py
    │   │   ├── tenant.py
    │   │   └── user.py
    │   ├── permissions.py
    │   ├── signals.py
    │   ├── tests.py
    │   ├── urls.py
    │   ├── views
    │   │   └── __init__.py
    │   ├── migrations
    │   │   └── __init__.py
    │   │   └── 0001_initial.py
    │   ├── serializers
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── role.py
    │   │   ├── tenant.py
    │   │   └── user.py
    │   └── services
    │       ├── __init__.py
    │       ├── auth_service.py
    │       └── tenant_service.py
    ├── ds_owari
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── permissions.py
    │   ├── signals.py
    │   ├── urls.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models
    │   │   └── __init__.py
    │   ├── serializers
    │   │   └── __init__.py
    │   ├── services
    │   │   └── __init__.py
    │   ├── tests
    │   │   └── __init__.py
    │   └── views
    │       └── __init__.py
    ├── modules
    │   ├── __init__.py
    │   ├── crm
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views
    │   │       └── __init__.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   ├── dashboard_module
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views
    │   │       └── __init__.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   ├── finances
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views
    │   │       └── __init__.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   ├── project_management
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models
    │   │   │   └── __init__.py
    │   │   ├── models.py
    │   │   ├── permissions.py
    │   │   ├── serializers
    │   │   │   └── __init__.py
    │   │   ├── services
    │   │   │   └── __init__.py
    │   │   ├── signals.py
    │   │   ├── tests.py
    │   │   ├── urls.py
    │   │   └── views
    │   │       └── __init__.py
    │   │   ├── migrations
    │   │   │   └── __init__.py
    │   └── service_catalog_management
    │       ├── __init__.py
    │       ├── admin.py
    │       ├── apps.py
    │       ├── models
    │       │   └── __init__.py
    │       ├── models.py
    │       ├── permissions.py
    │       ├── serializers
    │       │   └── __init__.py
    │       ├── services
    │       │   └── __init__.py
    │       ├── signals.py
    │       ├── tests.py
    │       ├── urls.py
    │       └── views
    │           └── __init__.py
    │       ├── migrations
    │       │   └── __init__.py
    └── shared_utils
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── models
        │   └── __init__.py
        ├── models.py
        ├── permissions.py
        ├── serializers
        │   └── __init__.py
        ├── services
        │   └── __init__.py
        ├── signals.py
        ├── tests.py
        ├── urls.py
        └── views
            └── __init__.py
        ├── migrations
        │   └── __init__.py