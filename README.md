# MLOps Домашнее задание №5

**Автор:** Мартиросова Анастасия Гургеновна  
**Модуль 5:** Продвинутая оркестрация и инфраструктура как код

## 1. Цель задания

Реализация автоматизированного конвейера переобучения ML-модели в Apache Airflow:
- Настройка DAG с обучением, оценкой и условным деплоем
- Интеграция уведомлений через Telegram Bot API
- Конфигурация через переменные окружения

## 2. Структура проекта

```
mlops_hw5_Martirosova_Anastasia/
├── dags/
│   └── ml_retrain_pipeline.py
├── screenshots/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

## 3. Архитектура DAG

**Последовательность выполнения:**
1. `train_model` — обучение модели
2. `evaluate_model` — расчёт метрик (accuracy, precision, recall, F1)
3. `check_metrics` — проверка качества:
   - accuracy >= 0.8 → `deploy_model` → `notify_success`
   - accuracy < 0.8 → `skip_deploy`

## 4. Переменные окружения

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_TOKEN` | Токен Telegram бота |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений |
| `MODEL_VERSION` | Версия модели (default: v1.0.0) |

## 5. Запуск

```bash
# Инициализация
docker-compose up airflow-init

# Запуск сервисов
docker-compose up -d
```

**Доступ к сервисам:**
- Airflow UI: http://localhost:8080 (airflow/airflow)

## 7. Скриншоты

| Скриншот | Описание |
|----------|----------|
| `dag_graph.png` | Граф DAG |
| `dag_gantt.png` | Диаграмма Ганта |
| `telegram.png` | Уведомление |
