import asyncio
import datetime
from telethon import TelegramClient
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_TOKEN, API_ID, API_HASH, SPREADSHEET_ID
import re
import json
import os

CHANNELS = [ 'rodzvuk', 'artfactproducts', 'befree_community', 'mesomatrix', 'pro_dermatit', 'thescandalist_official',
     'boom_sports', 'naidimenyatomsk2', 'realmerussia', 'indiespotlight', 'moskva_tretiy_rim', 'dddOutlet',
     'luxecosmetics_ru', 'theactlabs', 'themackers', 'Garage54official', 'autovkp', 'apichru', 'texnoprosto',
     'fakin_krakin', 'Gorenje_Rus', 'klientvsprav', 'joskayatelega', 'Blackie_Di', 'cosmetics_19lab', 'mskgigs',
     'lostmaryru', 'raffleblog', 'klmcollective', 'podrygka_ru', 'moskvichca', 'etolizochka', 'gurupc_sv',
     'GoldApple_BOX', 'laroutine', 'info_greenwashing', 'moscowachplus', 'chistie_auto36', 'thgkru',
     'okmarketofficial', 'dubrovskiy_444', 'dionisjew', 'wave_of_vintage', 'liubov_dermatalog', 'bigati_fest',
     'mixit_mood', 'gubinhojr', 'zortelad', 'topor_ul', 'famila_offprice', 'Romancev768', 'mvideoandeldorado',
     'proboknet', 'chulpan_library', 'hirecomend', 'sheff_camelot', 'GORDEYLIVE', 'gazetaru', 'mayotfamm',
     'DigitalBeautyyy', 'renovvatio', 'booksunday', 'rbc_news', 'RuslanEfremov', 'utrotnt', 'betboompoker',
     'radisson_cruise', 'b_retail', 'turkhakassia', 'castoreumgr', 'vitameal_brand', 'attache_brand', 'alioiahes',
     'cybersvibe', 'nhlvk', 'verybadreview', 'adamasru', 'anderstoreru', 'otkrytaya_kuhnya', 'igropapka',
     'evelone192gg', 'mia_cara_home', 'ai_machinelearning_big_data', 'conflict_in', 'OnesysPS', 'goldapple',
     'afishadaily', 'histore_ru', 'rozygryshit', 'elsedaa', 'afisharestaurants', 'rbtshki', 'Wylsared', 'timzhur',
     'afishanovosibirsk', 'koreanbutik_ru', 'pristavok100', 'tutu_travel', 'juvedel', 'frankypark_hogwarts',
     'viikablackberry', 'sesderma_russia', 'kingstoreshop', 'Maryanaro', 'pultrussia', 'zveronutie', 'obshakstaya',
     'avocado_grocery_stores', 'winline_cs', 'vskinsur', 'oiani_style', 'karcherru', 'hack_less', 'ozonru',
     'uchmanenews', 'centrclimatru', 'mvideomgame', 'treygolnikx', 'vserozigrishi', 'vprok_official', 'lichi',
     'sneakerbox_official', 'Bezprovodov174', 'techmedia', 'technopark_ru', 'istyagina', 'onlinetradeshopru',
     'King_Store_Balakovo', 'hpcseller', 'compshop_ru', 'katrina_karma', 'planto_club', 'alanhadash', 'polyandria',
     'raffle_vn', 'nicegirlsclub', 'trendybox_ru', 'chp_159_59', 'octave999', 'astwineshop', 'sberboost',
     'moscowtinderr', 'kinomax_cinema', 'yandex_travel', 'teronlyone', 'chromos0ma', 'lentadnya', 'araikcryptovolk',
     'push_auto163', 'askona_official', 'technodeus2023', 'TSpiritCS', 'podarki_ot_nk', 'lizzerin_Run', 'PrizeTech',
     'nechetoff', 'enzzai', 'grandchef_retaste', 'ispovd', 'mskevents_ru', 'gl_vibes', 'overheardatraves',
     'Pavel_Rubcov', 'mademanrussia', 'porshee_auto', 'romanavtov', 'spadreamru', 'winline_mlbb', 'inspireshopru',
     'gangstersaleie', 'yandex_realty_msk_spb', 'the_sortage', 'sneakershot24', 'pharmacosmetica_ru', 'biggeekru' ]  

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RANGE_NAME = "Лист1!A:J"

# Авторизация Google
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
sheets_service = build("sheets", "v4", credentials=creds)
sheet = sheets_service.spreadsheets()

# Кеш уже добавленных URL'ов
added_urls = set()

# Загрузка существующих ссылок
def load_existing_urls():
    global added_urls
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])
        added_urls = {cell for row in values for cell in row if "https://t.me/" in cell}
    except Exception as e:
        print(f"Ошибка при загрузке существующих URL: {e}")

# Парсинг дедлайна
def parse_deadline(text):
    match = re.search(r"(до|итоги|результаты)[^\d]*(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})(\s*в\s*\d{1,2}:\d{2})?", text, re.IGNORECASE)
    if match:
        date_str = match.group(2).replace("/", ".").replace("-", ".")
        time_str = match.group(3).strip() if match.group(3) else "00:00"
        try:
            dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
            return dt
        except Exception:
            return None
    return None

# Извлечение приза
def extract_prize(text):
    lines = text.strip().split("\n")
    for line in lines:
        if any(keyword in line.lower() for keyword in ["выиграй", "приз", "розыгрыш", "дарим", "разыгрываем", "получи"]):
            return line.strip()
    return "приз"

# Основной парсер
async def scan():
    print("🔍 Сканирование началось...")
    load_existing_urls()
    new_rows = []

    async with TelegramClient("session_name", API_ID, API_HASH) as client:
        for channel_group in CHANNELS:
            for channel in channel_group:
                try:
                    async for message in client.iter_messages(channel, limit=20):
                        if not message.message:
                            continue

                        text = message.message
                        deadline = parse_deadline(text)
                        if not deadline or deadline < datetime.datetime.now() + datetime.timedelta(hours=2):
                            continue

                        url = f"https://t.me/{channel}/{message.id}"
                        if url in added_urls:
                            continue

                        prize = extract_prize(text)
                        now = datetime.datetime.now().strftime("%d.%m.%Y")
                        deadline_str = deadline.strftime("%d.%m.%Y %H:%M")

                        row = [now, url, prize, deadline_str, "Подписка", "Да", "", "", "Идёт", ""]
                        new_rows.append(row)
                        added_urls.add(url)

                    await asyncio.sleep(0.5)  # защита от API rate limits
                except Exception as e:
                    print(f"⚠️ Ошибка в канале {channel}: {e}")

    if new_rows:
        try:
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body={"values": new_rows}
            ).execute()
            print(f"✅ Добавлено {len(new_rows)} новых записей.")
        except Exception as e:
            print(f"❌ Ошибка при добавлении в таблицу: {e}")
    else:
        print("📭 Новых розыгрышей не найдено.")

# Запуск планировщика
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scan, "interval", hours=1)
    scheduler.start()
    print("⏰ Планировщик запущен. Сканер будет запускаться каждый час.")
    while True:
        await asyncio.sleep(3600)
