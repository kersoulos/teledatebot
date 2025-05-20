import asyncio
import datetime
from telethon import TelegramClient
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TELEGRAM_TOKEN, API_ID, API_HASH, SPREADSHEET_ID
import re

CHANNELS = [
    ['rodzvuk', 'artfactproducts', 'befree_community', 'mesomatrix', 'pro_dermatit', 'thescandalist_official', 'boom_sports', 'naidimenyatomsk2', 'realmerussia', 'indiespotlight', 'moskva_tretiy_rim', 'dddOutlet', 'luxecosmetics_ru', 'theactlabs', 'themackers', 'Garage54official', 'autovkp', 'apichru', 'texnoprosto', 'fakin_krakin', 'Gorenje_Rus', 'klientvsprav', 'joskayatelega', 'Blackie_Di', 'cosmetics_19lab', 'mskgigs', 'lostmaryru', 'raffleblog', 'klmcollective', 'podrygka_ru', 'moskvichca', 'etolizochka', 'gurupc_sv', 'GoldApple_BOX', 'laroutine', 'info_greenwashing', 'moscowachplus', 'chistie_auto36', 'thgkru', 'okmarketofficial', 'dubrovskiy_444', 'dionisjew', 'wave_of_vintage', 'liubov_dermatalog', 'bigati_fest', 'mixit_mood', 'gubinhojr', 'zortelad', 'topor_ul', 'famila_offprice', 'Romancev768', 'mvideoandeldorado', 'proboknet', 'chulpan_library', 'hirecomend', 'sheff_camelot', 'GORDEYLIVE', 'gazetaru', 'mayotfamm', 'DigitalBeautyyy', 'renovvatio', 'booksunday', 'rbc_news', 'RuslanEfremov', 'utrotnt', 'betboompoker', 'radisson_cruise', 'b_retail', 'turkhakassia', 'castoreumgr', 'vitameal_brand', 'attache_brand', 'alioiahes', 'cybersvibe', 'nhlvk', 'verybadreview', 'adamasru', 'anderstoreru', 'otkrytaya_kuhnya', 'igropapka', 'evelone192gg', 'mia_cara_home', 'ai_machinelearning_big_data', 'conflict_in', 'OnesysPS', 'goldapple', 'afishadaily', 'histore_ru', 'rozygryshit', 'elsedaa', 'afisharestaurants', 'rbtshki', 'Wylsared', 'timzhur', 'afishanovosibirsk', 'koreanbutik_ru', 'pristavok100', 'tutu_travel', 'juvedel', 'frankypark_hogwarts', 'viikablackberry', 'sesderma_russia', 'kingstoreshop', 'Maryanaro', 'pultrussia', 'zveronutie', 'obshakstaya', 'avocado_grocery_stores', 'winline_cs', 'vskinsur', 'oiani_style', 'karcherru', 'hack_less', 'ozonru', 'uchmanenews', 'centrclimatru', 'mvideomgame', 'treygolnikx', 'vserozigrishi', 'vprok_official', 'lichi', 'sneakerbox_official', 'Bezprovodov174', 'techmedia', 'technopark_ru', 'istyagina', 'onlinetradeshopru', 'King_Store_Balakovo', 'hpcseller', 'compshop_ru', 'katrina_karma', 'planto_club', 'alanhadash', 'polyandria', 'raffle_vn', 'nicegirlsclub', 'trendybox_ru', 'chp_159_59', 'octave999', 'astwineshop', 'sberboost', 'moscowtinderr', 'kinomax_cinema', 'yandex_travel', 'teronlyone', 'chromos0ma', 'lentadnya', 'araikcryptovolk', 'push_auto163', 'askona_official', 'technodeus2023', 'TSpiritCS', 'podarki_ot_nk', 'lizzerin_Run', 'PrizeTech', 'nechetoff', 'enzzai', 'grandchef_retaste', 'ispovd', 'mskevents_ru', 'gl_vibes', 'overheardatraves', 'Pavel_Rubcov', 'mademanrussia', 'porshee_auto', 'romanavtov', 'spadreamru', 'winline_mlbb', 'inspireshopru', 'gangstersaleie', 'yandex_realty_msk_spb', 'the_sortage', 'sneakershot24', 'pharmacosmetica_ru', 'biggeekru']
]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RANGE_NAME = "Лист1!A:J"

creds = Credentials.from_service_account_file("creds.json", scopes=SCOPES)
sheets_service = build("sheets", "v4", credentials=creds)
sheet = sheets_service.spreadsheets()

def parse_deadline(text):
    match = re.search(r"(до|итоги|результаты)[^\d]*(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})(\s*в\s*\d{1,2}:\d{2})?", text, re.IGNORECASE)
    if match:
        date_str = match.group(2).replace("/", ".").replace("-", ".")
        time_str = match.group(3).strip() if match.group(3) else "00:00"
        try:
            dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
            return dt
        except:
            return None
    return None

def extract_prize(text):
    lines = text.strip().split("\n")
    for line in lines:
        if any(keyword in line.lower() for keyword in ["выиграй", "приз", "розыгрыш", "дарим", "разыгрываем", "получи"]):
            return line.strip()
    return "приз"

def already_exists(url):
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])
    return any(url in row for row in values)

async def scan():
    async with TelegramClient("session_name", API_ID, API_HASH) as client:
        for channel in CHANNELS:
            try:
                async for message in client.iter_messages(channel, limit=20):
                    if not message.message:
                        continue
                    text = message.message
                    deadline = parse_deadline(text)
                    if not deadline:
                        continue
                    if deadline < datetime.datetime.now() + datetime.timedelta(hours=2):
                        continue
                    url = f"https://t.me/{channel}/{message.id}"
                    if already_exists(url):
                        continue
                    prize = extract_prize(text)
                    now = datetime.datetime.now().strftime("%d.%m.%Y")
                    deadline_str = deadline.strftime("%d.%m.%Y %H:%M")
                    new_row = [now, url, prize, deadline_str, "Подписка", "Да", "", "", "Идёт", ""]
                    sheet.values().append(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME, valueInputOption="USER_ENTERED", body={"values": [new_row]}).execute()
            except Exception as e:
                print(f"Ошибка при обработке канала {channel}: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(scan()), "interval", hours=1)
    scheduler.start()
    asyncio.get_event_loop().run_forever()