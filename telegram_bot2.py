import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import requests
from bs4 import BeautifulSoup

# Настройка журналирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Определение состояний разговора
STATIONS_SELECTION, FINAL_STATION_SELECTION = range(2)

def start(update: Update, context: CallbackContext) -> int:
    """
    Обработка команды /start
    """
    update.message.reply_text(
        "Привет! Я помогу узнать расстояние в километрах от станции дислокации до станции назначения.\n"
        "Напиши свой запрос в форме:\n"
        "1. Забойщик\n"
        "2. Поздеевка\n"
        "И так далее..."
    )
    return STATIONS_SELECTION

def stations_selection(update: Update, context: CallbackContext) -> int:
    """
    Обработка ввода станций пользователем
    """
    stations = update.message.text.split('\n')
    stations = [station.strip() for station in stations if station.strip()]
    if not stations:
        update.message.reply_text("Пожалуйста, введите корректные станции")
        return STATIONS_SELECTION
    context.user_data['stations'] = stations
    update.message.reply_text(
        "Теперь выбери конечную станцию:",
        reply_markup=ReplyKeyboardMarkup([["Электроугли", "Чик"]], one_time_keyboard=True)
    )
    return FINAL_STATION_SELECTION

def final_station_selection(update: Update, context: CallbackContext) -> int:
    """
    Обработка ввода конечной станции пользователем
    """
    final_station = update.message.text.strip()
    if final_station not in ["Электроугли", "Чик"]:
        update.message.reply_text("Пожалуйста, выберите конечную станцию из предложенного списка")
        return FINAL_STATION_SELECTION
    context.user_data['final_station'] = final_station
    distance = get_distance(context.user_data['stations'], final_station)
    update.message.reply_text(
        f"Расстояние до {final_station}:\n"
        f"{distance}",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def get_distance(stations, final_station):
    """
    Получение расстояния между станциями
    """
    url = "https://poisk-vagonov.ru/route.php#"
    params = {
        "from": "\n".join(stations),
        "to": final_station
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к {url}: {e}")
        return "Ошибка при запросе к веб-странице"
    soup = BeautifulSoup(response.text, 'html.parser')
    distance_elem = soup.find("span", class_="dist")
    if not distance_elem:
        logger.error("Элемент с расстоянием не найден на странице")
        return "Расстояние не найдено"
    distance = distance_elem.text.strip()
    return distance

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Команда отменена.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END