import os
import random
import requests
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator


# Конфигурация из переменных окружения
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Порог качества модели для деплоя
ACCURACY_THRESHOLD = 0.8


def train_model(**context):
    """
    Обучение ML-модели.

    В реальном сценарии здесь происходит:
    - Загрузка данных
    - Предобработка
    - Обучение модели
    - Сохранение артефактов
    """
    print(f"Запуск обучения модели версии {MODEL_VERSION}")
    print("Загрузка данных...")
    print("Предобработка данных...")
    print("Обучение модели...")
    print(f"Модель {MODEL_VERSION} успешно обучена!")

    return {"status": "trained", "version": MODEL_VERSION}


def evaluate_model(**context):
    print(f"Оценка модели версии {MODEL_VERSION}")
    accuracy = random.uniform(0.75, 0.95)
    precision = random.uniform(0.70, 0.92)
    recall = random.uniform(0.72, 0.94)
    f1_score = 2 * (precision * recall) / (precision + recall)

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4)
    }

    print(f"Метрики модели: {metrics}")

    # Сохраняем метрики в XCom
    context['ti'].xcom_push(key='metrics', value=metrics)

    return metrics


def check_metrics(**context):
    ti = context['ti']
    metrics = ti.xcom_pull(task_ids='evaluate_model', key='metrics')

    accuracy = metrics.get('accuracy', 0)

    print(f"Проверка метрик: accuracy={accuracy}, порог={ACCURACY_THRESHOLD}")

    if accuracy >= ACCURACY_THRESHOLD:
        print(f"Метрики удовлетворительные (accuracy >= {ACCURACY_THRESHOLD}). Деплой разрешен.")
        return 'deploy_model'
    else:
        print(f"Метрики ниже порога (accuracy < {ACCURACY_THRESHOLD}). Деплой отклонен.")
        return 'skip_deploy'


def deploy_model(**context):
    ti = context['ti']
    metrics = ti.xcom_pull(task_ids='evaluate_model', key='metrics')

    print(f"Развертывание модели версии {MODEL_VERSION}")
    print(f"Метрики: accuracy={metrics['accuracy']}, f1={metrics['f1_score']}")
    print("Загрузка артефактов...")
    print("Обновление конфигурации...")
    print(f"Модель {MODEL_VERSION} успешно развернута в продакшен!")

    # Сохраняем информацию о деплое для уведомления
    context['ti'].xcom_push(key='deploy_info', value={
        "version": MODEL_VERSION,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    })

    return {"status": "deployed", "version": MODEL_VERSION}


def skip_deploy(**context):
    """
    Задача-заглушка при пропуске деплоя.
    """
    ti = context['ti']
    metrics = ti.xcom_pull(task_ids='evaluate_model', key='metrics')

    print(f"Деплой модели {MODEL_VERSION} пропущен")
    print(f"Причина: accuracy={metrics['accuracy']} < {ACCURACY_THRESHOLD}")
    print("Требуется доработка модели или сбор дополнительных данных")

    return {"status": "skipped", "reason": "metrics_below_threshold"}


def send_telegram_notification(**context):
    ti = context['ti']
    deploy_info = ti.xcom_pull(task_ids='deploy_model', key='deploy_info')

    if not deploy_info:
        print("Информация о деплое не найдена. Уведомление не отправлено.")
        return

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_TOKEN или TELEGRAM_CHAT_ID не настроены")
        print(f"Уведомление (симуляция): Модель {MODEL_VERSION} успешно развернута!")
        return

    metrics = deploy_info.get('metrics', {})

    # Формируем текст сообщения
    message = (
        f"*[DEPLOY] Model {MODEL_VERSION}*\n\n"
        f"Metrics:\n"
        f"  - Accuracy: `{metrics.get('accuracy', 'N/A')}`\n"
        f"  - Precision: `{metrics.get('precision', 'N/A')}`\n"
        f"  - Recall: `{metrics.get('recall', 'N/A')}`\n"
        f"  - F1-score: `{metrics.get('f1_score', 'N/A')}`\n\n"
        f"Timestamp: {deploy_info.get('timestamp', 'N/A')}\n"
        f"Status: OK"
    )

    # Отправка через Telegram Bot API
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"Уведомление успешно отправлено в Telegram")
        else:
            print(f"Ошибка отправки уведомления: {response.text}")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")


# Аргументы по умолчанию для всех задач
default_args = {
    'owner': 'mlops',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Определение DAG
with DAG(
    dag_id="ml_retrain_pipeline",
    default_args=default_args,
    description="Конвейер переобучения ML-модели с уведомлениями",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["ml", "retrain", "notification"],
) as dag:

    # Задача 1: Обучение модели
    train = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
        provide_context=True,
    )

    # Задача 2: Оценка модели
    evaluate = PythonOperator(
        task_id="evaluate_model",
        python_callable=evaluate_model,
        provide_context=True,
    )

    # Задача 3: Проверка метрик (ветвление)
    check = BranchPythonOperator(
        task_id="check_metrics",
        python_callable=check_metrics,
        provide_context=True,
    )

    # Задача 4a: Деплой модели (при хороших метриках)
    deploy = PythonOperator(
        task_id="deploy_model",
        python_callable=deploy_model,
        provide_context=True,
    )

    # Задача 4b: Пропуск деплоя (при плохих метриках)
    skip = PythonOperator(
        task_id="skip_deploy",
        python_callable=skip_deploy,
        provide_context=True,
    )

    # Задача 5: Уведомление о успешном деплое
    notify = PythonOperator(
        task_id="notify_success",
        python_callable=send_telegram_notification,
        provide_context=True,
        trigger_rule="none_failed_min_one_success",
    )

    # Точка соединения веток
    join = EmptyOperator(
        task_id="join",
        trigger_rule="none_failed_min_one_success",
    )

    # Определение зависимостей (порядок выполнения)
    train >> evaluate >> check
    check >> deploy >> notify
    check >> skip >> join
    notify >> join
