import datetime as dt
import hashlib
import math
import re
from typing import Dict, Optional, Tuple

import requests
import streamlit as st

st.set_page_config(page_title="فالِ فان", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');
:root { --ink:#17212b; --muted:#66727e; --cream:#fbfaf7; --paper:#ffffff; --mint:#dff4ee; --coral:#ff7b6b; --gold:#f5c86a; --line:#e8e5df; }
* { font-family:'Vazirmatn', Tahoma, sans-serif; }
html, body, [class*="css"] { direction:rtl; }
.stApp { background:linear-gradient(145deg,#fbfaf7 0%,#f1f7f5 100%); color:var(--ink); }
.block-container { max-width:1180px; padding:2rem 1.2rem 4rem; }
.hero { background:var(--ink); color:#fff; border-radius:18px; padding:2.2rem 2.4rem; margin-bottom:1.4rem; position:relative; overflow:hidden; }
.hero:after { content:'✦'; position:absolute; left:2rem; top:1rem; color:var(--gold); font-size:5rem; opacity:.4; }
.hero h1 { margin:0 0 .45rem; font-size:clamp(2rem,5vw,3.5rem); letter-spacing:0; }
.hero p { color:#d9e4e6; max-width:690px; margin:0; line-height:2; font-size:1.02rem; }
.eyebrow { color:var(--gold); font-weight:700; font-size:.82rem; margin-bottom:.4rem; }
.card { background:var(--paper); border:1px solid var(--line); border-radius:12px; padding:1.1rem 1.25rem; margin:.6rem 0; box-shadow:0 5px 18px rgba(23,33,43,.045); }
.card h3 { margin:.1rem 0 .6rem; font-size:1.12rem; }
.tag { display:inline-block; background:var(--mint); border-radius:999px; padding:.18rem .7rem; margin:.18rem; font-size:.82rem; color:#225d56; }
.big-symbol { font-size:3.1rem; line-height:1; }
.reading { background:#fff7e4; border-right:4px solid var(--gold); border-radius:8px; padding:1rem 1.1rem; line-height:2.05; }
.small-note { color:var(--muted); font-size:.84rem; line-height:1.8; }
.metric { font-size:2rem; font-weight:800; color:var(--coral); }
div[data-testid="stTabs"] button { font-weight:700; }
.stButton button { border-radius:8px; font-weight:700; }
[data-testid="stSidebar"] { background:#eff7f4; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- Data and calculations ----------
ZODIAC = [
    ("حمل", "♈", (3,21), (4,19), "پرانرژی، پیش‌قدم و صریح"),
    ("ثور", "♉", (4,20), (5,20), "با‌ثبات، خوش‌ذوق و صبور"),
    ("جوزا", "♊", (5,21), (6,20), "کنجکاو، اجتماعی و منعطف"),
    ("سرطان", "♋", (6,21), (7,22), "حساس، مراقبت‌گر و خیال‌پرداز"),
    ("اسد", "♌", (7,23), (8,22), "گرم، خلاق و اهل درخشش"),
    ("سنبله", "♍", (8,23), (9,22), "دقیق، عمل‌گرا و منظم"),
    ("میزان", "♎", (9,23), (10,22), "متعادل، خوش‌برخورد و زیبایی‌دوست"),
    ("عقرب", "♏", (10,23), (11,21), "عمیق، پرشور و رازدار"),
    ("قوس", "♐", (11,22), (12,21), "ماجراجو، امیدوار و صریح"),
    ("جدی", "♑", (12,22), (1,19), "هدفمند، مسئول و استوار"),
    ("دلو", "♒", (1,20), (2,18), "مستقل، نوآور و انسان‌دوست"),
    ("حوت", "♓", (2,19), (3,20), "همدل، هنرمند و شهودی"),
]
CHINESE = ["موش", "گاو", "ببر", "خرگوش", "اژدها", "مار", "اسب", "بز", "میمون", "خروس", "سگ", "خوک"]
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
PERSIAN_LETTERS = str.maketrans({
    "آ": "ا",
    "أ": "ا",
    "إ": "ا",
    "ٱ": "ا",
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ۀ": "ه",
    "ة": "ه",
    "ؤ": "و",
})
TRAITS = {
    "حمل":"امروز برای شروعی کوچک و شجاعانه انرژی خوبی داری.", "ثور":"یک انتخاب ساده و باحوصله می‌تواند حال امروزت را بهتر کند.",
    "جوزا":"گفت‌وگویی کوتاه شاید ایده‌ای تازه به ذهنت بیاورد.", "سرطان":"به حس آرامش خودت توجه کن و برای استراحت جا باز کن.",
    "اسد":"وقت آن است استعدادت را در یک کار خلاقانه نشان بدهی.", "سنبله":"مرتب کردن یک گوشه کوچک، ذهن تو را هم سبک می‌کند.",
    "میزان":"یک تعامل دوستانه می‌تواند تعادل دلپذیری به روزت بدهد.", "عقرب":"کنجکاوی‌ات را دنبال کن، اما برای نتیجه‌گیری کمی مکث کن.",
    "قوس":"تغییر مسیر کوتاه یا تجربه‌ای تازه روزت را رنگی می‌کند.", "جدی":"پیشرفت‌های کوچک امروز، پایه یک نتیجه خوب در آینده‌اند.",
    "دلو":"یک نگاه متفاوت به موضوعی معمولی، جرقه ایده تازه‌ای می‌شود.", "حوت":"موسیقی، تصویر یا خیال‌پردازی می‌تواند منبع انرژی تو باشد."
}
COMPAT = {"حمل":["اسد","قوس","دلو"],"ثور":["سرطان","سنبله","جدی"],"جوزا":["میزان","دلو","حمل"],"سرطان":["عقرب","حوت","ثور"],"اسد":["حمل","قوس","میزان"],"سنبله":["ثور","جدی","سرطان"],"میزان":["جوزا","دلو","اسد"],"عقرب":["سرطان","حوت","جدی"],"قوس":["حمل","اسد","دلو"],"جدی":["ثور","سنبله","عقرب"],"دلو":["جوزا","میزان","قوس"],"حوت":["سرطان","عقرب","ثور"]}


def western_sign(date: dt.date) -> Dict[str, str]:
    for name, icon, start, end, traits in ZODIAC:
        if (start[0] == end[0] and (start[0], start[1]) <= (date.month, date.day) <= (end[0], end[1])) or (start[0] != end[0] and ((date.month, date.day) >= start or (date.month, date.day) <= end)):
            return {"name":name, "icon":icon, "traits":traits}
    return {"name":"جدی", "icon":"♑", "traits":"هدفمند، مسئول و استوار"}


def normalize_text(value: str) -> str:
    value = value.translate(PERSIAN_DIGITS).translate(PERSIAN_LETTERS)
    value = value.replace("‌", "")
    return re.sub(r"[^آ-یa-zA-Z]", "", value).lower()


def digit_sum(value: int) -> int:
    while value > 9 and value not in (11, 22, 33):
        value = sum(int(x) for x in str(value))
    return value


def life_path(date: dt.date) -> int:
    return digit_sum(sum(int(x) for x in date.strftime("%Y%m%d")))


def name_number(name: str) -> int:
    latin = {c: i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz", 1)}
    persian = dict(zip("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی", list(range(1, 33))))
    total = sum(latin.get(c, persian.get(c, 0)) for c in normalize_text(name))
    return digit_sum(total) if total else 0


def moon_phase(date: dt.date) -> Tuple[str, str]:
    days = (date - dt.date(2000, 1, 6)).days + 0.5
    phase = (days % 29.530588) / 29.530588
    phases = [(0.03,"ماه نو","🌑"),(0.22,"هلال افزاینده","🌒"),(0.28,"ربع اول","🌓"),(0.47,"کوژ افزاینده","🌔"),(0.53,"ماه کامل","🌕"),(0.72,"کوژ کاهنده","🌖"),(0.78,"ربع آخر","🌗"),(0.97,"هلال کاهنده","🌘")]
    return next((label, icon) for threshold, label, icon in phases if phase < threshold) if phase < .97 else ("ماه نو","🌑")


def seeded_reading(date, sign):
    options = ["یک فرصت کوچک برای یادگیری پیدا کن.", "امروز به یک پیام ساده و مهربانانه فکر کن.", "به جای کمال‌گرایی، یک قدم واقعی بردار.", "چند دقیقه دور شدن از صفحه‌نمایش به تو کمک می‌کند."]
    idx = int(hashlib.sha256(f"{date.isoformat()}-{sign}".encode()).hexdigest(), 16) % len(options)
    return options[idx]

# ---------- Internet helpers ----------
@st.cache_data(ttl=3600, show_spinner=False)
def geocode(city: str) -> Optional[Tuple[float, float, str]]:
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search", params={"q":city,"format":"json","limit":1}, headers={"User-Agent":"fal-e-fun/1.0 (entertainment app)"}, timeout=8)
        r.raise_for_status(); data = r.json()
        if data: return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", city)
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None
    return None

@st.cache_data(ttl=1800, show_spinner=False)
def sun_times(lat: float, lon: float, day: str) -> Optional[Dict[str, str]]:
    try:
        r = requests.get("https://api.sunrise-sunset.org/json", params={"lat":lat,"lng":lon,"date":day,"formatted":0}, timeout=8)
        r.raise_for_status(); data = r.json().get("results")
        return data if isinstance(data, dict) else None
    except (requests.RequestException, ValueError): return None

@st.cache_data(ttl=1800, show_spinner=False)
def time_context(city: str) -> str:
    try:
        r = requests.get("https://timeapi.io/api/Time/current/zone", params={"timeZone": "UTC"}, timeout=6)
        if r.ok: return "اتصال زمانی برقرار است؛ زمان محلی دقیق به منطقه زمانی شهر وابسته است."
    except requests.RequestException: pass
    return "سرویس زمان در دسترس نبود؛ زمان و وضعیت بالا تقریبی و محلی محاسبه شده‌اند."


def pretty_time(value):
    if not value: return "—"
    try: return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M") + " UTC"
    except ValueError: return str(value)

# ---------- UI ----------
st.markdown('<div class="hero"><div class="eyebrow">یک تجربه سبک و خیال‌انگیز</div><h1>فالِ فان ✨</h1><p>چند نگاه سرگرم‌کننده به آسمان، عددها و نشانه‌ها؛ برای لبخند و کنجکاوی، نه پیش‌بینی قطعی آینده.</p></div>', unsafe_allow_html=True)
with st.sidebar:
    st.markdown("## درباره فالِ فان")
    st.write("این برنامه صرفاً برای سرگرمی و خودشناسی سبک طراحی شده است. هیچ نتیجه‌ای قطعی یا علمی نیست و نباید مبنای تصمیم‌های پزشکی، حقوقی، مالی یا مهم زندگی قرار بگیرد.")
    st.divider()
    st.markdown("### حریم خصوصی")
    st.write("اطلاعات واردشده در این برنامه ذخیره نمی‌شود. برای بخش آسمان، تنها نام شهر به سرویس عمومی مکان‌یابی فرستاده می‌شود.")
    st.caption("منابع زنده: Nominatim و Sunrise-Sunset؛ در صورت خطا، برنامه با حالت تقریبی ادامه می‌دهد.")

with st.form("profile"):
    st.markdown("### مشخصات سرگرمی")
    c1, c2 = st.columns(2)
    with c1: name = st.text_input("نام یا نام مستعار", placeholder="مثلاً نازنین")
    with c2: birth_date = st.date_input("تاریخ تولد", value=dt.date(1995, 6, 15), min_value=dt.date(1900,1,1), max_value=dt.date.today())
    c3, c4 = st.columns(2)
    with c3: birth_time = st.time_input("ساعت تولد (اختیاری)", value=None)
    with c4: city = st.text_input("شهر (اختیاری، برای طلوع و غروب)", placeholder="مثلاً شیراز")
    submitted = st.form_submit_button("✨ نمایش فال سرگرمی", use_container_width=True)

if submitted or "result" not in st.session_state:
    st.session_state.result = True
if st.session_state.result:
    sign = western_sign(birth_date); lp = life_path(birth_date); nn = name_number(name)
    tabs = st.tabs(["برج غربی", "زودیاک چینی", "عددشناسی", "فال امروز", "هماهنگی", "آسمان زنده"])
    with tabs[0]:
        st.markdown(f'<div class="card"><div class="big-symbol">{sign["icon"]}</div><h3>برج {sign["name"]}</h3><p>{sign["traits"]}</p><span class="tag">عنصر نمادین: {"آتش" if sign["name"] in ["حمل","اسد","قوس"] else "خاک" if sign["name"] in ["ثور","سنبله","جدی"] else "هوا" if sign["name"] in ["جوزا","میزان","دلو"] else "آب"}</span></div>', unsafe_allow_html=True)
        st.info("این توصیف‌ها کلی و نمادین‌اند و قرار نیست شخصیت یا آینده را تعیین کنند.")
    with tabs[1]:
        animal = CHINESE[(birth_date.year - 4) % 12]
        st.markdown(f'<div class="card"><h3>سال {animal}</h3><p>در سنت زودیاک چینی، سال تولد با نماد <b>{animal}</b> همراه دانسته می‌شود؛ برداشتی فرهنگی و سرگرم‌کننده.</p></div>', unsafe_allow_html=True)
    with tabs[2]:
        st.markdown(f'<div class="card"><h3>عدد مسیر زندگی</h3><div class="metric">{lp}</div><p>جمع نمادین رقم‌های تاریخ تولد. عدد نام برای «{name or "مهمان"}»: <b>{nn or "—"}</b></p><p class="small-note">عددشناسی یک روش تفسیری سرگرمی است و اعتبار پیش‌بینی قطعی ندارد.</p></div>', unsafe_allow_html=True)
    with tabs[3]:
        st.markdown(f'<div class="card"><h3>پیام روز برای {name or "شما"}</h3><div class="reading">{TRAITS[sign["name"]]}<br><br>جرقه امروز: {seeded_reading(dt.date.today(), sign["name"])}</div><p class="small-note">این پیام با تاریخ امروز و برج انتخابی به‌صورت ثابت تولید شده است.</p></div>', unsafe_allow_html=True)
    with tabs[4]:
        second = st.selectbox("برج نفر دوم را انتخاب کنید", [z[0] for z in ZODIAC], index=0)
        score = 82 if second in COMPAT[sign["name"]] else (66 if second == sign["name"] else 54)
        st.markdown(f'<div class="card"><h3>{sign["name"]} و {second}</h3><div class="metric">{score}٪</div><p>{"ریتم نمادین این دو نشانه می‌تواند مکمل به نظر برسد." if score > 70 else "تفاوت‌ها می‌تواند فرصتی برای گفت‌وگو و شناخت بیشتر باشد."}</p><p class="small-note">این درصد صرفاً یک امتیاز بازی‌گونه است، نه سنجش واقعی رابطه.</p></div>', unsafe_allow_html=True)
    with tabs[5]:
        today = dt.date.today(); phase, icon = moon_phase(today)
        st.markdown(f'<div class="card"><h3>{icon} وضعیت تقریبی ماه</h3><p><b>{phase}</b> در تاریخ {today.strftime("%Y/%m/%d")}</p></div>', unsafe_allow_html=True)
        if city.strip():
            with st.spinner("در حال دریافت اطلاعات عمومی شهر..."):
                place = geocode(city.strip())
                if place:
                    lat, lon, display = place; solar = sun_times(lat, lon, today.isoformat())
                    st.markdown(f'<div class="card"><h3>طلوع و غروب برای {city.strip()}</h3><p class="small-note">مکان تقریبی: {display}</p><div style="display:flex;gap:3rem"><div><b>طلوع</b><br><span class="metric">{pretty_time(solar.get("sunrise") if solar else None)}</span></div><div><b>غروب</b><br><span class="metric">{pretty_time(solar.get("sunset") if solar else None)}</span></div></div></div>', unsafe_allow_html=True)
                else: st.warning("شهر پیدا نشد یا سرویس مکان‌یابی موقتاً در دسترس نیست.")
            st.caption(time_context(city.strip()))
        else: st.info("برای دیدن طلوع و غروب، نام شهر را در فرم بالا وارد کنید.")
        st.caption("همه زمان‌ها و فاز ماه تقریبی‌اند و این بخش نیز فقط جنبه سرگرمی دارد.")
