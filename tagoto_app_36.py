import streamlit as st
import pandas as pd
import io
# timedelta を追加
from datetime import datetime, time, date, timedelta
import uuid
# JavaScript埋め込みのために追加
import streamlit.components.v1 as components
# URLエンコードのために追加
import urllib.parse
import calendar
import re
from collections import Counter



# ページのレイアウトをワイドモードに設定
st.set_page_config(layout="wide")





# ここからがデザイン変更の核心部分
# カスタムCSSを定義して、アプリに適用する
st.markdown("""
<style>
/* Streamlitのプライマリボタン（デフォルトの青ボタン）の見た目を緑に変更 */
button[kind = "primary"] {
    background-color: #FF69A3 !important; /* 背景色を緑に */
    color: white !important;              /* 文字色を白に */
    border: 1px solid #FF0461 !important;/* 枠線を濃い緑に */
    font-weight: bold;                    /* 文字を太字に */
}

/* ボタンにカーソルを合わせたときの見た目 */
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #FF0461 !important;
    color: white !important;
    border: 1px solid #1e7e34 !important;
}



/* 通常のボタン（プライマリではないボタン） */
button:not([kind="primary"]) {
    background-color: #ffffff !important; /* 背景を白に */
    color: #495057 !important;            /* 文字を濃い灰色に */
    border: 1px solid #ced4da !important; /* 枠線を灰色に */
}

/* 通常のボタンにカーソルを合わせたとき */
div[data-testid="stButton"] button:not([kind="primary"]):hover {
    background-color: #f8f9fa !important; /* 背景を少しだけ灰色に */
    border: 1px solid #adb5bd !important; /* 枠線を少し濃い灰色に */
}



/* 無効化された（disabled）ボタンの見た目 */
button:disabled {
    background-color: #555555 !important; /* 灰色背景 */
    color: #adadad !important;            /* 文字色を薄い灰色に */
    border: 1px solid #d0d4e8 !important;
    cursor: not-allowed;                  /* カーソルは「禁止マーク」になる */
}
            
/* メニュー選択エリアのボタン */
.menu-container button {
    height: 50em !important;    /* ボタンの高さを変更 */
    font-size: 10em !important;    /* 文字の大きさを変更 */
}

/* アレルギー詳細入力欄のラベルを赤くするためのCSS */
.red-text {
    color: red !important;
}

</style>
""", unsafe_allow_html=True)




# アプリが期待するデータ構造（スキーマ）を定義
CUSTOMER_COLUMNS = {
    "顧客ID": "object", "名前": "object", "フリガナ": "object", "郵便番号": "object",
    "都道府県名": "object", "住所": "object", "メールアドレス": "object", "電話番号": "object",
    "FAX番号": "object", "領収書が必要な方はこちらをご選択ください": "object",
    "適格請求書をご希望の方は、同梱されている「納品書」も必要となりますこと、ご了承ください": "object",
    "ユーザー登録": "object", "備考": "object"
}
RESERVATION_COLUMNS = {
    '日付': 'str', '時間': 'str', '席番号': 'object',
    '名前': 'object', '電話番号': 'object', '人数': 'int64',
    '人数(大人)': 'int64', '人数(子供)': 'int64',
    '注文内容': 'object', '会席': 'object', 'バス': 'object', '担当バス運転手': 'object',
    'お迎え先住所': 'object', 'お迎え時間': 'object', '用途': 'object',
    'アレルギー': 'object', 'アレルギー詳細': 'object',
    '備考': 'object', '担当者': 'object', 'ステータス': 'object'
}


SEAT_MAP = {
    "first_floor": {
        "left_block": [["1-1", "1-2", "1-3"], ["1-6", "1-5", "1-4"]],
        "right_block": [["2-1", "2-2", "2-3"], ["2-6", "2-5", "2-4"]]
    },
    "second_floor": {
        "up_left_block":   [["4-1"], ["4-3", "4-2"]],
        "up_center_block": [["5-1"], ["5-3", "5-2"]],
        "up_right_block":  [["6-2", "6-1"]],
        "low_left_block":  [["8-2"], ["8-1"]],
        "low_right_block": [["7-2"], ["7-1"]]
    }
}


# メニューデータ、運転手リスト、用途リストを定義
MENU_DATA = {
    "煮込み": ["煮込み", "煮込み定食", "鍋焼き", "鍋焼き定食", "カレー煮込", "カレー煮込定食", "煮込み天", "煮込み天定食", "鍋焼き天", "鍋焼き天定食", "カレー煮込天", "カレー煮込天定食", "煮込み鶏もも", "煮込み鶏もも定食", "鍋焼き鶏もも", "鍋焼き鶏もも定食", "カレー煮込鶏もも", "カレー煮込鶏もも定食", "煮込みもち", "煮込みもち定食", "鍋焼きもち", "鍋焼きもち定食", "カレー煮込もち", "カレー煮込もち定食", "煮込みブタ", "煮込みブタ定食", "鍋焼きブタ", "鍋焼きブタ定食", "カレー煮込ブタ", "カレー煮込ブタ定食", "特製煮込み", "特製煮込定食", "特製鍋焼き", "特製鍋焼き定食", "スタミナ牛もつ", "ピリ辛煮込み"],
    "丼・一品": ["★大海老天", "★豚肉", "★もち", "★鶏もも", "★玉子", "★チーズ", "★ヒレか(1枚)", "★ロースかつ", "★生かき(5粒)", "★牛モツ"],
    "温": ["牛鍋", "牛鍋定食"], "冷": ["冷やし中華", "ざるそば"],
    "定食・単": ["ご飯セット", "味噌汁"], "半期メニュー": ["季節の天ぷら"],
    "春・秋": ["たけのこご飯"], "夏・冬": ["おでん"],
    "持帰り": ["持ち帰り用煮込み"],
    "冷凍土産": ["冷凍もつ煮", "冷凍餃子"],
}
BUS_DRIVERS = ["未定", "坂倉　仁", "亀山　繁男", "金森　正親", "木田　豊"]
PURPOSE_OPTIONS = ["法事", "顔合わせ", "お食い初め", "お祝い", "歓迎会", "送別会", "町内会", "おひまち", "結納", "会食", "その他"]


# --- セッション状態の初期化 ---
if 'df_customer' not in st.session_state: st.session_state.df_customer = None
if 'df_reservation' not in st.session_state: st.session_state.df_reservation = pd.DataFrame(columns=RESERVATION_COLUMNS.keys()).astype(RESERVATION_COLUMNS)
if 'selected_time' not in st.session_state: st.session_state.selected_time = None
if 'selected_tables' not in st.session_state: st.session_state.selected_tables = []
if 'active_keypad' not in st.session_state: st.session_state.active_keypad = None
if 'current_page' not in st.session_state: st.session_state.current_page = '予約登録'

if 'name_input' not in st.session_state: st.session_state.name_input = ""
if 'tel_input' not in st.session_state: st.session_state.tel_input = ""
if 'pax_input' not in st.session_state: st.session_state.pax_input = ""
if 'pax_adult_input' not in st.session_state: st.session_state.pax_adult_input = "" # <-- この行を追加
if 'pax_child_input' not in st.session_state: st.session_state.pax_child_input = "" # <-- この行を追加
if 'memo_input_area' not in st.session_state: st.session_state.memo_input_area = ""

if 'search_name_input' not in st.session_state: st.session_state.search_name_input = ""
if 'search_tel_input' not in st.session_state: st.session_state.search_tel_input = ""

if 'editing_reservation_index' not in st.session_state: st.session_state.editing_reservation_index = None
if 'edit_name_input' not in st.session_state: st.session_state.edit_name_input = ""
if 'edit_pax_input' not in st.session_state: st.session_state.edit_pax_input = ""
if 'edit_pax_adult_input' not in st.session_state: st.session_state.edit_pax_adult_input = "" # <-- この行を追加
if 'edit_pax_child_input' not in st.session_state: st.session_state.edit_pax_child_input = "" # <-- この行を追加
if 'edit_tel_input' not in st.session_state: st.session_state.edit_tel_input = ""
if 'edit_memo_input' not in st.session_state: st.session_state.edit_memo_input = ""
if 'edit_selected_date' not in st.session_state: st.session_state.edit_selected_date = date.today()

if 'selected_menu_category' not in st.session_state: st.session_state.selected_menu_category = "煮込み"
if 'order_items' not in st.session_state: st.session_state.order_items = {}
if 'is_kaiseki' not in st.session_state: st.session_state.is_kaiseki = "いいえ"
if 'bus_required' not in st.session_state: st.session_state.bus_required = "不要"
if 'bus_driver' not in st.session_state: st.session_state.bus_driver = "未定"
if 'bus_address' not in st.session_state: st.session_state.bus_address = ""
if 'bus_time' not in st.session_state: st.session_state.bus_time = ""
if 'purpose' not in st.session_state: st.session_state.purpose = "会食"
if 'has_allergies' not in st.session_state: st.session_state.has_allergies = "無し"
if 'allergy_details' not in st.session_state: st.session_state.allergy_details = ""
if 'allergy_list_of_people' not in st.session_state: st.session_state.allergy_list_of_people = []
if 'staff_in_charge' not in st.session_state: st.session_state.staff_in_charge = ""
if 'edit_staff_in_charge' not in st.session_state: st.session_state.edit_staff_in_charge = ""
if 'scroll_to_time' not in st.session_state: st.session_state.scroll_to_time = False
if 'scroll_to_pax' not in st.session_state: st.session_state.scroll_to_pax = False
if 'scroll_to_seat' not in st.session_state: st.session_state.scroll_to_seat = False

if 'show_calendar_in_search' not in st.session_state: st.session_state.show_calendar_in_search = False
if 'search_selected_date' not in st.session_state: st.session_state.search_selected_date = date.today()

if 'calendar_year' not in st.session_state:
    st.session_state.calendar_year = date.today().year
if 'calendar_month' not in st.session_state:
    st.session_state.calendar_month = date.today().month
if 'selected_date_custom' not in st.session_state:
    # 編集モードで初期値があればそれを、なければ今日の日付を使う
    if st.session_state.get('editing_reservation_index') is not None and 'edit_selected_date' in st.session_state:
        st.session_state.selected_date_custom = st.session_state.edit_selected_date
    else:
        st.session_state.selected_date_custom = date.today()



# ===================================================================
# ===== アプリケーション全体で使用する関数（ヘルパー関数）の定義 =====
# ===================================================================

def to_katakana(hiragana_string): return "".join([chr(ord(char) + 96) if "ぁ" <= char <= "ん" else char for char in hiragana_string])
def to_half_width(text): return text.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

def convert_text_callback(session_state_key, conversion_type):
    text = st.session_state[session_state_key]
    
    # --- ▼▼▼ ここから修正 ▼▼▼ ---
    if conversion_type == 'kana':
        # ひらがな(ぁ-ん)、カタカナ(ァ-ン)、長音符(ー) 以外をすべて除去
        filtered_text = re.sub(r'[^ぁ-んァ-ンー]', '', text)
        # フィルター後のテキストをカタカナに変換
        converted_text = to_katakana(filtered_text)
    # --- ▲▲▲ 修正ここまで ▲▲▲ ---

    elif conversion_type == 'digit': converted_text = "".join(filter(str.isdigit, to_half_width(text)))
    else: converted_text = text
    
    st.session_state[session_state_key] = converted_text
    
    # 人数(大人・子供)の入力が変更されたら、合計人数を更新する
    if 'pax_adult' in session_state_key or 'pax_child' in session_state_key:
        update_total_pax(is_edit_mode=('edit' in session_state_key))

def update_total_pax(is_edit_mode=False):
    """大人と子供の人数から合計人数を計算してsession_stateを更新する"""
    if is_edit_mode:
        adult_key = 'edit_pax_adult_input'
        child_key = 'edit_pax_child_input'
        total_key = 'edit_pax_input'
    else:
        adult_key = 'pax_adult_input'
        child_key = 'pax_child_input'
        total_key = 'pax_input'
    
    try:
        # .get()でキーが存在しなくてもエラーにならないようにする
        adult_str = st.session_state.get(adult_key, "0")
        child_str = st.session_state.get(child_key, "0")
        
        adults = int(adult_str) if adult_str else 0
        children = int(child_str) if child_str else 0
        total = adults + children
        st.session_state[total_key] = str(total)
    except (ValueError, TypeError):
        st.session_state[total_key] = "0"


def generate_time_slots(is_lunch):
    slots = []
    if is_lunch:
        start_time = time(11, 0)
        end_time = time(15, 0) # 15:00 含まない
        current_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        while current_dt < end_dt:
            slots.append(current_dt.time())
            current_dt += timedelta(minutes=5)
    else:
        start_time = time(17, 0)
        end_time = time(22, 0) # 22:00 含まない
        current_dt = datetime.combine(date.today(), start_time)
        end_dt = datetime.combine(date.today(), end_time)
        while current_dt < end_dt:
            slots.append(current_dt.time())
            current_dt += timedelta(minutes=5)
    return slots

def toggle_seat_selection(seat):
    if seat in st.session_state.selected_tables: st.session_state.selected_tables.remove(seat)
    else: st.session_state.selected_tables.append(seat)

def set_active_keypad(target): st.session_state.active_keypad = target

# ★★★★★ 住所キーパッドがなくなったため、元のシンプルな作りに戻す ★★★★★
def append_char(char):
    if st.session_state.active_keypad:
        key = st.session_state.active_keypad + "_input"
        st.session_state[key] += char

def delete_char():
    if st.session_state.active_keypad:
        key = st.session_state.active_keypad + "_input"
        st.session_state[key] = st.session_state[key][:-1]

def clear_input():
    if st.session_state.active_keypad:
        key = st.session_state.active_keypad + "_input"
        st.session_state[key] = ""

def apply_diacritic(diacritic):
    if st.session_state.active_keypad and "name" in st.session_state.active_keypad:
        key = st.session_state.active_keypad + "_input"
        if not st.session_state[key]: return
        dakuten_map = {'カ':'ガ','キ':'ギ','ク':'グ','ケ':'ゲ','コ':'ゴ','サ':'ザ','シ':'ジ','ス':'ズ','セ':'ゼ','ソ':'ゾ','タ':'ダ','チ':'ヂ','ツ':'ヅ','テ':'デ','ト':'ド','ハ':'バ','ヒ':'ビ','フ':'ブ','ヘ':'ベ','ホ':'ボ'}
        handakuten_map = {'ハ':'パ','ヒ':'ピ','フ':'プ','ヘ':'ペ','ホ':'ポ'}
        last_char = st.session_state[key][-1]
        if diacritic == '゛' and last_char in dakuten_map: st.session_state[key] = st.session_state[key][:-1] + dakuten_map[last_char]
        elif diacritic == '゜' and last_char in handakuten_map: st.session_state[key] = st.session_state[key][:-1] + handakuten_map[last_char]

def start_editing(index):
    st.session_state.editing_reservation_index = index
    reservation_to_edit = st.session_state.df_reservation.loc[index]
    st.session_state.edit_name_input = reservation_to_edit['名前']
    st.session_state.edit_pax_input = str(reservation_to_edit['人数'])

    # .get()を使い、古いデータに列がなくてもエラーにならないようにする
    st.session_state.edit_pax_adult_input = str(reservation_to_edit.get('人数(大人)', ''))
    st.session_state.edit_pax_child_input = str(reservation_to_edit.get('人数(子供)', ''))
    
    # 古いデータ（大人・子供が未入力）の場合、合計人数を「大人」に入れ、「子供」を0にする
    if not st.session_state.edit_pax_adult_input and not st.session_state.edit_pax_child_input and st.session_state.edit_pax_input:
        st.session_state.edit_pax_adult_input = st.session_state.edit_pax_input
        st.session_state.edit_pax_child_input = "0"
    if not st.session_state.edit_pax_adult_input: st.session_state.edit_pax_adult_input = "0"
    if not st.session_state.edit_pax_child_input: st.session_state.edit_pax_child_input = "0"

    st.session_state.edit_tel_input = str(reservation_to_edit['電話番号'])
    st.session_state.edit_memo_input = str(reservation_to_edit['備考'])
    st.session_state.edit_selected_date = datetime.strptime(reservation_to_edit['日付'], '%Y-%m-%d').date()
    st.session_state.selected_time = datetime.strptime(reservation_to_edit['時間'], '%H:%M').time()
    st.session_state.selected_tables = [s.strip() for s in reservation_to_edit['席番号'].split(',')]
# --- ▼▼▼ 以下のブロックを修正 ▼▼▼ ---
    # st.session_state.order_items = reservation_to_edit.get('注文内容', '').split(', ') if reservation_to_edit.get('注文内容') else []
    
    # 文字列 (例: "煮込み, 煮込み, ご飯セット") をパースして辞書 (例: {"煮込み": 2, "ご飯セット": 1}) にする
    order_string = reservation_to_edit.get('注文内容', '')
    if order_string:
        # Counterを使ってアイテムごとの数をカウントし、辞書に変換
        order_list = [item.strip() for item in order_string.split(',') if item.strip()] # 空白を除去
        st.session_state.order_items = dict(Counter(order_list))
    else:
        st.session_state.order_items = {}


    st.session_state.is_kaiseki = reservation_to_edit.get('会席', 'いいえ')
    st.session_state.bus_required = reservation_to_edit.get('バス', '不要')
    st.session_state.bus_driver = reservation_to_edit.get('担当バス運転手', '未定')
    st.session_state.bus_address = reservation_to_edit.get('お迎え先住所', '')
    st.session_state.bus_time = reservation_to_edit.get('お迎え時間', '')
    st.session_state.purpose = reservation_to_edit.get('用途', '会食')
    st.session_state.has_allergies = reservation_to_edit.get('アレルギー', '無し')

    # --- ▼▼▼ 以下のブロックを置き換え ▼▼▼ ---
    # st.session_state.allergy_details = reservation_to_edit.get('アレルギー詳細', '')
    
    # "アレルギー詳細" 文字列 (例: "Aさん: 卵 / Bさん: 小麦") をパースしてリストに戻す
    allergy_detail_str = reservation_to_edit.get('アレルギー詳細', '')
    st.session_state.allergy_list_of_people = [] # いったんリセット
    
    # アレルギー "有り" かつ 詳細文字列が存在する場合のみパース
    if st.session_state.has_allergies == "有り" and allergy_detail_str:
        try:
            # " / " (スペース・スラッシュ・スペース) で人ごとに分割
            people_allergies = allergy_detail_str.split(' / ')
            for entry in people_allergies:
                if ':' in entry:
                    # "名前: 詳細" に分割
                    name, details = entry.split(':', 1)
                    st.session_state.allergy_list_of_people.append({
                        'id': str(uuid.uuid4()), # 編集時は新しいIDを振る
                        'name': name.strip(),
                        'details': details.strip()
                    })
                elif entry.strip(): # : がないデータ (古い形式やパース失敗)
                    st.session_state.allergy_list_of_people.append({
                        'id': str(uuid.uuid4()),
                        'name': '（詳細）', # 名前が不明なアレルギー
                        'details': entry.strip()
                    })
            
            # パース結果が空だが、元の文字列が空でなかった場合 (救済措置)
            if not st.session_state.allergy_list_of_people and allergy_detail_str.strip():
                 st.session_state.allergy_list_of_people.append({
                        'id': str(uuid.uuid4()),
                        'name': '（全体）',
                        'details': allergy_detail_str.strip()
                    })
        except Exception as e:
            # 万が一パースに失敗したら、そのまま詳細に入れる (古いデータ救済)
            st.session_state.allergy_list_of_people = [{
                'id': str(uuid.uuid4()),
                'name': '（全体）',
                'details': allergy_detail_str
            }]
    
    # 互換性のため、古い allergy_details も一応セットしておく (UIでは使わない)
    st.session_state.allergy_details = allergy_detail_str 
    # --- ▲▲▲ 修正ここまで ▲▲▲ ---



    st.session_state.edit_staff_in_charge = reservation_to_edit.get('担当者', '')
    st.session_state.active_keypad = None
    st.session_state.current_page = '予約登録'

def handle_pax_input_done():
    st.session_state.active_keypad = None
    is_edit_mode = st.session_state.editing_reservation_index is not None
    pax_value = st.session_state.edit_pax_input if is_edit_mode else st.session_state.pax_input
    if pax_value:
        st.session_state.scroll_to_seat = True
    
# ★★★★★ 住所キーパッドが不要になったため、ロジックを削除 ★★★★★
def draw_keypads():
    if st.session_state.active_keypad:
        with st.container(border=True):
            if "name" in st.session_state.active_keypad:
                st.subheader("名前を入力してください")
                kana_rows = ["ア","カ","サ","タ","ナ","ハ","マ","ヤ","ラ","ワ","イ","キ","シ","チ","ニ","ヒ","ミ","","リ","ン","ウ","ク","ス","ツ","ヌ","フ","ム","ユ","ル","ー","エ","ケ","セ","テ","ネ","ヘ","メ","","レ","゛","オ","コ","ソ","ト","ノ","ホ","モ","ヨ","ロ","゜"]
                kana_cols = st.columns(10)
                for i, char in enumerate(kana_rows):
                    with kana_cols[i % 10]:
                        if char in ["゛", "゜"]: st.button(char, key=f"key_{char}_{st.session_state.active_keypad}", on_click=apply_diacritic, args=(char,), use_container_width=True)
                        elif char: st.button(char, key=f"key_{char}_{st.session_state.active_keypad}", on_click=append_char, args=(char,), use_container_width=True)
                op_cols = st.columns(2)
                with op_cols[0]: st.button("一文字削除", key=f"delete_{st.session_state.active_keypad}", on_click=delete_char, use_container_width=True)
                with op_cols[1]: st.button("クリア", key=f"clear_{st.session_state.active_keypad}", on_click=clear_input, use_container_width=True)
                st.button("入力完了", on_click=set_active_keypad, args=(None,), use_container_width=True, type="primary")

            elif st.session_state.active_keypad in [
                'pax_adult', 'pax_child', 'tel', 
                'edit_pax_adult', 'edit_pax_child', 'edit_tel', 
                'search_tel'
            ]:
                # 押されたボタンに応じて、キーパッドのタイトルを動的に変更
                if 'pax_adult' in st.session_state.active_keypad:
                    target_label = "大人（人数）"
                elif 'pax_child' in st.session_state.active_keypad:
                    target_label = "子供（人数）"
                else:
                    target_label = "電話番号"
                
                st.subheader(f"{target_label}を入力してください")
                k_cols = st.columns(3)
                for i in range(1, 10):
                    with k_cols[(i-1)%3]: st.button(str(i), key=f"key_{i}_{st.session_state.active_keypad}", on_click=append_char, args=(str(i),), use_container_width=True)
                with k_cols[0]: st.button("C", key=f"key_clear_{st.session_state.active_keypad}", on_click=clear_input, use_container_width=True)
                with k_cols[1]: st.button("0", key=f"key_0_{st.session_state.active_keypad}", on_click=append_char, args=("0",), use_container_width=True)
                with k_cols[2]: st.button("←", key=f"key_delete_{st.session_state.active_keypad}", on_click=delete_char, use_container_width=True)

                if 'pax' in st.session_state.active_keypad:
                    st.button("入力完了", on_click=handle_pax_input_done, use_container_width=True, type="primary")
                else:
                    st.button("入力完了", on_click=set_active_keypad, args=(None,), use_container_width=True, type="primary")

def handle_reservation_upload(uploader_key):
    st.info("予約データがありません。過去の予約データをCSVファイルから読み込んでください。")
    uploaded_file = st.file_uploader("予約データCSVをアップロード", type=['csv'], key=uploader_key, help=f"CSVファイルには、次の列が必要です: {', '.join(RESERVATION_COLUMNS.keys())}")
    if uploaded_file:
        try:
            csv_dtypes = {'席番号': str, '電話番号': str}
            df_to_load = pd.read_csv(uploaded_file, encoding='utf-8-sig', dtype=csv_dtypes)
            for col, default in [
                ('ステータス', '予約済み'), ('注文内容', ''), ('会席', 'いいえ'), ('バス', '不要'), 
                ('担当バス運転手', ''), ('お迎え先住所', ''), ('お迎え時間', ''), ('用途', '会食'), 
                ('アレルギー', '無し'), ('アレルギー詳細', ''), ('担当者', ''),
                ('人数(大人)', 0), ('人数(子供)', 0)
            ]:
                if col not in df_to_load.columns: df_to_load[col] = default
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df_to_load = pd.read_csv(uploaded_file, encoding='shift-jis', dtype=csv_dtypes)
            for col, default in [
                ('ステータス', '予約済み'), ('注文内容', ''), ('会席', 'いいえ'), ('バス', '不要'), 
                ('担当バス運転手', ''), ('お迎え先住所', ''), ('お迎え時間', ''), ('用途', '会食'), 
                ('アレルギー', '無し'), ('アレルギー詳細', ''), ('担当者', ''),
                ('人数(大人)', 0), ('人数(子供)', 0)
            ]:
                if col not in df_to_load.columns: df_to_load[col] = default
        if not all(col in df_to_load.columns for col in RESERVATION_COLUMNS.keys()):
            st.error(f"ファイルの列が正しくありません。必要な列: {', '.join(RESERVATION_COLUMNS.keys())}")
            st.info(f"ファイルに含まれる列: {', '.join(df_to_load.columns)}")
        else:
            st.session_state.df_reservation = df_to_load.astype(RESERVATION_COLUMNS)
            st.success("予約データを読み込みました。")
            st.rerun()

def draw_menu_selection():
    st.markdown('<div class="menu-container">', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("##### 5. メニューを選択")
    categories = list(MENU_DATA.keys())
    cols = st.columns(5)
    for i, category in enumerate(categories):
        with cols[i % 5]:
            button_type = "primary" if st.session_state.selected_menu_category == category else "secondary"
            if st.button(category, key=f"cat_{category}", use_container_width=True, type=button_type):
                st.session_state.selected_menu_category = category
                st.rerun()
    st.markdown("---")
    
    # --- ▼▼▼ ここからUIとロジックを大幅修正 ▼▼▼ ---
    if st.session_state.selected_menu_category:
        items = MENU_DATA.get(st.session_state.selected_menu_category, [])
        cols = st.columns(6)
        
        for i, item in enumerate(items):
            with cols[i % 6]:
                # 注文辞書から現在の個数を取得
                item_count = st.session_state.order_items.get(item, 0)
                
                # 個数に応じてラベルとボタンタイプを変更
                if item_count > 0:
                    button_label = f"{item} ({item_count})"
                    button_type = "primary" # 選択されているので色を変える
                else:
                    button_label = item
                    button_type = "secondary"

                # ボタンがクリックされたら、個数を+1する
                if st.button(button_label, key=f"item_{item}", use_container_width=True, type=button_type):
                    st.session_state.order_items[item] = item_count + 1
                    st.rerun()

    if st.session_state.order_items: # 辞書が空でない場合
        st.markdown("---")
        st.write("**現在の注文リスト**")
        
        # 注文リストをアイテムごとに表示 (辞書をループ)
        # (注: Python 3.7+ では辞書の順序は挿入順に保持される)
        items_to_iterate = list(st.session_state.order_items.keys()) # 途中で削除してもエラーにならないようキーのリストを先に作成
        
        for item in items_to_iterate:
            count = st.session_state.order_items.get(item)
            if not count or count <= 0: # 万が一カウントが0以下ならスキップ
                if item in st.session_state.order_items: # 念のため削除
                    del st.session_state.order_items[item]
                continue
                
            item_cols = st.columns([0.6, 0.4]) # レイアウト変更
            with item_cols[0]:
                st.write(f"- {item} (数量: {count})")
            
            # 数量変更ボタン ( - / + / 削除 )
            with item_cols[1]:
                btn_cols = st.columns(3)
                with btn_cols[0]: # マイナスボタン
                    if st.button("－", key=f"dec_{item}", use_container_width=True):
                        st.session_state.order_items[item] = count - 1
                        if st.session_state.order_items[item] <= 0:
                            del st.session_state.order_items[item] # 0個になったら辞書から削除
                        st.rerun()
                with btn_cols[1]: # プラスボタン
                    if st.button("＋", key=f"inc_{item}", use_container_width=True):
                        st.session_state.order_items[item] = count + 1
                        st.rerun()
                with btn_cols[2]: # 削除ボタン (アイテム自体をリストから削除)
                    if st.button("削除", key=f"del_{item}", use_container_width=True, type="secondary"):
                        del st.session_state.order_items[item]
                        st.rerun()

        if st.button("注文を全てクリア", use_container_width=True, type="secondary"):
            st.session_state.order_items = {} # 辞書をクリア
            st.rerun()
    # --- ▲▲▲ 修正ここまで ▲▲▲ ---
            
    st.markdown('</div>', unsafe_allow_html=True)

def set_page():
    destination_page = st.session_state.radio_selector
    if destination_page == '予約登録':
        st.session_state.name_input = st.session_state.get('search_name_input', '')
        st.session_state.tel_input = st.session_state.get('search_tel_input', '')
    st.session_state.current_page = destination_page
    st.session_state.editing_reservation_index = None

def handle_date_change():
    """日付が変更された（カスタムカレンダーで日付がクリックされた）時の処理"""
    
    # 選択された日付を取得
    selected_dt = st.session_state.get('selected_date_custom')

    # 予約登録ページの場合のみ、時間リセットやスクロールを行う
    if st.session_state.get('current_page') == '予約登録':
        st.session_state.selected_time = None
        st.session_state.selected_tables = []
        st.session_state.scroll_to_time = True
    
    # 予約確認・検索ページの場合、選択された日付を専用キーに保存
    if st.session_state.get('current_page') == '予約確認・検索' and selected_dt:
        st.session_state.search_selected_date = selected_dt

    # 共通処理：カレンダーの表示年月を選択日に合わせる
    if selected_dt:
        st.session_state.calendar_year = selected_dt.year
        st.session_state.calendar_month = selected_dt.month
    
    st.rerun() # 時間選択肢などを更新するために必要

def handle_time_selection(slider_key, other_slider_key):
    """st.select_sliderの値が変更されたときに呼ばれるコールバック"""
    selected_slot = st.session_state[slider_key]
    
    # 選択が解除された場合 (Noneが選ばれた)
    if selected_slot is None:
        # 既に両方Noneなら何もしない
        if st.session_state.selected_time is None and (other_slider_key not in st.session_state or st.session_state[other_slider_key] is None):
            return
        # 選択を解除する
        st.session_state.selected_time = None
        st.session_state.selected_tables = []
        # 他方のスライダーもNoneにする (念のため)
        if other_slider_key in st.session_state:
            st.session_state[other_slider_key] = None
        st.rerun() # 画面を更新
        return

    # 新しい時間が選択された場合
    if st.session_state.selected_time != selected_slot:
        st.session_state.selected_time = selected_slot
        st.session_state.selected_tables = []
        st.session_state.scroll_to_pax = True
        
        # もう一方のスライダーの選択を解除(Noneに)する
        st.session_state[other_slider_key] = None
        st.rerun() # 画面を更新

# ==================================
# ===== カスタムカレンダー関数 =====
# ==================================
def draw_custom_calendar(calendar_key_prefix="cal"):
    """カスタムカレンダーを表示し、選択された日付を返す"""

# --- 年月ナビゲーション (スクロール選択式) ---
    
    # 年月が変更されたときにセッション状態を更新するコールバック
    def update_calendar_display():
        st.session_state.calendar_year = st.session_state[f"{calendar_key_prefix}_year_select"]
        st.session_state.calendar_month = st.session_state[f"{calendar_key_prefix}_month_select"]
        # 年月を変更しただけでは日付選択はリセットしない

    header_cols = st.columns([1, 1]) # 2列に変更 (年用, 月用)

    # 年選択
    current_year = st.session_state.calendar_year
    # 現在の年から前後5年の範囲をリストにする
    year_options = list(range(current_year - 5, current_year + 6))
    if current_year not in year_options: # 念のため現在の年がリストに含まれるように
        year_options.append(current_year)
        year_options.sort()
    
    with header_cols[0]:
        st.selectbox(
            "年",
            options=year_options,
            index=year_options.index(current_year), # 現在の年をデフォルト選択
            key=f"{calendar_key_prefix}_year_select",
            on_change=update_calendar_display, # 年変更時にコールバック
            label_visibility="collapsed" # "年"というラベルを非表示
        )

    # 月選択
    month_options = list(range(1, 13))
    current_month = st.session_state.calendar_month

    with header_cols[1]:
        st.selectbox(
            "月",
            options=month_options, # 内部的な値は 1, 2, ...
            format_func=lambda m: f"{m}月", # 表示は "1月", "2月", ...
            index=month_options.index(current_month), # 現在の月をデフォルト選択
            key=f"{calendar_key_prefix}_month_select",
            on_change=update_calendar_display, # 月変更時にコールバック
            label_visibility="collapsed" # "月"というラベルを非表示
        )

    # --- 曜日ヘッダー ---
    days = ["月", "火", "水", "木", "金", "土", "日"]
    cols = st.columns(7)
    for i, day_name in enumerate(days):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold;'>{day_name}</div>", unsafe_allow_html=True)

    st.markdown("---", unsafe_allow_html=True) # 細い線

    # --- 日付ボタン ---
    cal = calendar.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
    selected_dt = st.session_state.get('selected_date_custom')

    for week in cal:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            if day_num == 0:
                cols[i].write("") # 月外の日付は空白
            else:
                current_date = date(st.session_state.calendar_year, st.session_state.calendar_month, day_num)
                is_selected = (selected_dt == current_date)
                button_type = "primary" if is_selected else "secondary"
                button_label = str(day_num)

                # 日付ボタンクリック時の処理
                if cols[i].button(button_label, key=f"{calendar_key_prefix}_day_{day_num}", type=button_type, use_container_width=True):
                    st.session_state.selected_date_custom = current_date
                    handle_date_change() # 日付が選択されたら時間などをリセット
                    # st.rerun() # handle_date_change内でrerunされることが多いので不要かも

    return st.session_state.selected_date_custom # 選択されている日付を返す
# ==================================
# ===== カスタムカレンダー関数ここまで =====
# ==================================


st.sidebar.title("メニュー")
page_options = ['予約登録', '予約確認・検索', '顧客管理', '分析ページ']
st.sidebar.radio("ページを選択してください", page_options, key='radio_selector', on_change=set_page, index=page_options.index(st.session_state.current_page))
page = st.session_state.current_page

if page == '顧客管理':
    st.title('顧客管理')
    if st.session_state.df_customer is None:
        uploaded_file = st.file_uploader("顧客データCSVファイルをアップロードしてください", type=['csv'], key="file_uploader", help=f"CSVファイルには、次の列が必要です: {', '.join(CUSTOMER_COLUMNS.keys())}")
        if uploaded_file is not None:
            try:
                df_to_load = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df_to_load = pd.read_csv(uploaded_file, encoding='shift-jis')
            if not all(col in df_to_load.columns for col in CUSTOMER_COLUMNS.keys()):
                st.error(f"ファイルの列が正しくありません。必要な列: {', '.join(CUSTOMER_COLUMNS.keys())}")
                st.info(f"ファイルに含まれる列: {', '.join(df_to_load.columns)}")
            else:
                st.session_state.df_customer = df_to_load.astype(CUSTOMER_COLUMNS)
                st.rerun()
    else:
        df = st.session_state.df_customer
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader('新しいデータを追加')
            with st.form(key='add_customer_form', clear_on_submit=True):
                name_input = st.text_input('名前*')
                furigana_input = st.text_input('フリガナ*')
                email_input = st.text_input('メールアドレス*')
                tel_input = st.text_input('電話番号')
                submit_button = st.form_submit_button(label='追加')
                if submit_button:
                    try:
                        if df.empty:
                            new_id_num = 1
                        else:
                            numeric_ids = pd.to_numeric(df['顧客ID'].str.replace('C', '', regex=False), errors='coerce').dropna()
                            max_id = numeric_ids.max() if not numeric_ids.empty else 0
                            new_id_num = int(max_id + 1)
                        new_id = f"C{new_id_num:04d}"
                        new_row_dict = {"顧客ID": new_id, "名前": str(name_input), "フリガナ": str(furigana_input), "郵便番号": "", "都道府県名": "", "住所": "", "メールアドレス": str(email_input), "電話番号": str(tel_input), "FAX番号": "", "領収書が必要な方はこちらをご選択ください": "いいえ", "適格請求書をご希望の方は、同梱されている「納品書」も必要となりますこと、ご了承ください": "いいえ", "ユーザー登録": "未登録", "備考": ""}
                        new_row_df = pd.DataFrame([new_row_dict])
                        df_updated = pd.concat([df, new_row_df], ignore_index=True)
                        st.session_state.df_customer = df_updated.astype(CUSTOMER_COLUMNS)
                        st.success('データを追加しました！')
                        st.rerun()
                    except Exception as e:
                        st.error(f"予期せぬエラーが発生しました: {e}")
            st.markdown("---")
            st.subheader('データをCSVで保存')
            csv_string = st.session_state.df_customer.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label="CSVファイルをダウンロード", data=csv_string, file_name='updated_customers.csv', mime='text/csv')
        with col2:
            st.subheader('データ検索')
            search_word = st.text_input('検索キーワードを入力してください（全列対象）', key="search_input")
            display_df = st.session_state.df_customer
            if search_word:
                display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search_word, na=False)).any(axis=1)]
            st.subheader('現在のデータ')
            st.dataframe(display_df, use_container_width=True)
        st.markdown("---")
        if st.button("別のファイルをアップロード（リセット）"):
            st.session_state.df_customer = None
            st.rerun()

elif page == '予約登録':
    df_reservations = st.session_state.df_reservation
    is_edit_mode = st.session_state.editing_reservation_index is not None
    st.title('予約の変更' if is_edit_mode else '新規予約登録')
    
    if df_reservations.empty and not is_edit_mode:
        handle_reservation_upload(uploader_key='upload_on_register_page')
        st.stop()

    if is_edit_mode:
        idx = st.session_state.editing_reservation_index
        original_reservation = df_reservations.loc[idx]
        st.info(f"以下の予約を編集中です： {original_reservation['日付']} {original_reservation['時間']} - {original_reservation['名前']}様")
    
    if not is_edit_mode and st.session_state.get("clear_form_on_next_run"):
        st.session_state.update(
            name_input="", tel_input="", pax_input="", 
            pax_adult_input="", pax_child_input="",  # <-- この2つを追加
            memo_input_area="", selected_tables=[], selected_time=None, 
            order_items={}, is_kaiseki="いいえ", bus_required="不要", bus_driver="未定", 
            bus_address="", bus_time="", purpose="会食", has_allergies="無し", 
            allergy_details="", staff_in_charge="", clear_form_on_next_run=False
        )

    # --- 1. 日付を選択 ---
    st.markdown("##### 1. 日付を選択")
    # 編集モードの場合、カレンダーの初期表示年月を選択中の日付に合わせる
    if is_edit_mode and st.session_state.get('edit_selected_date'):
         # edit_selected_date が存在する初回のみカレンダー年月を更新
         if st.session_state.calendar_year != st.session_state.edit_selected_date.year or \
            st.session_state.calendar_month != st.session_state.edit_selected_date.month:
               st.session_state.calendar_year = st.session_state.edit_selected_date.year
               st.session_state.calendar_month = st.session_state.edit_selected_date.month
               st.session_state.selected_date_custom = st.session_state.edit_selected_date # selected_date_customも更新
               # st.rerun() # ここでrerunすると無限ループの可能性があるので避ける

    # カスタムカレンダーを描画し、選択された日付を取得
    selected_date = draw_custom_calendar(calendar_key_prefix="reg")
    # 編集モードの場合、edit_selected_date も更新しておく（保存時に使うため）
    if is_edit_mode:
        st.session_state.edit_selected_date = selected_date

    st.markdown("---")

    # --- 2. 時間を選択 ---
    st.markdown('<div id="time-selection-anchor"></div>', unsafe_allow_html=True)
    st.markdown("##### 2. 時間を選択")

# --- ▼▼▼ 以下の時間選択ブロック（スライダーの部分）を丸ごと置き換え ▼▼▼ ---

    # ドロップダウン用のセッションSTATEキーを定義
    LUNCH_SELECT_KEY = 'lunch_time_select' # キー名を変更
    DINNER_SELECT_KEY = 'dinner_time_select' # キー名を変更

    # ドロップダウンの選択肢（リスト）を生成
    # [None] を追加して「未選択」状態を作れるようにする
    lunch_slots = [None] + generate_time_slots(True)
    dinner_slots = [None] + generate_time_slots(False)

    # 予約データフレームを取得
    df_for_check = df_reservations.drop(st.session_state.editing_reservation_index) if is_edit_mode else df_reservations
    day_reservations = df_for_check[(df_for_check['日付'] == selected_date.strftime('%Y-%m-%d')) & (df_for_check['ステータス'] == '予約済み')]
    
    # 時間ごとの予約数をカウントする辞書を作成
    booked_counts = day_reservations['時間'].value_counts().to_dict()

    MAX_BOOKINGS_PER_TIME = 28 # 同時予約数の上限

    # ドロップダウンのフォーマット（表示）用関数
    def format_time_select(slot): # 関数名を変更
        if slot is None:
            # プレースホルダーテキストを返す
            return "--- 時間を選択してください ---"
        
        slot_str = slot.strftime('%H:%M')
        count = booked_counts.get(slot_str, 0)
        
        if count >= MAX_BOOKINGS_PER_TIME:
            # 満席の場合、ラベルで明確に示す
            return f"{slot_str} (満席)"
        else:
            return slot_str
        
    # 昼の部 ドロップダウン
    st.selectbox(
        "☀️ **昼の部 (11:00 ~ 15:00)**",
        options=lunch_slots,
        key=LUNCH_SELECT_KEY,
        format_func=format_time_select,
        on_change=handle_time_selection, # 以前のスライダー用コールバックをそのまま使えます
        args=(LUNCH_SELECT_KEY, DINNER_SELECT_KEY),
        index=0 # デフォルトで 0番目 (None) を指す
    )
    
    # 夜の部 ドロップダウン
    st.selectbox(
        "🌙 **夜の部 (17:00 ~ 21:00)**",
        options=dinner_slots,
        key=DINNER_SELECT_KEY,
        format_func=format_time_select,
        on_change=handle_time_selection, # 以前のスライダー用コールバックをそのまま使えます
        args=(DINNER_SELECT_KEY, LUNCH_SELECT_KEY),
        index=0 # デフォルトで 0番目 (None) を指す
    )
    
    # --- ▲▲▲ 置き換えここまで ▲▲▲ ---
    
    # --- ▲▲▲ 置き換えここまで ▲▲▲ ---

    
    # st.write("☀️ **昼の部 (11:00 ~ 15:00)**")
    # cols_lunch = st.columns(4)
    # for i, slot in enumerate(generate_time_slots(True)):
    #     with cols_lunch[i % 4]:
    #         booked_count = len(df_reservations[(df_reservations['日付'] == selected_date.strftime('%Y-%m-%d')) & (df_reservations['時間'] == slot.strftime('%H:%M')) & (df_reservations['ステータス'] == '予約済み')])
    #         is_full = booked_count >= 28
    #         button_type = "primary" if st.session_state.selected_time == slot else "secondary"
    #         st.button(slot.strftime('%H:%M'), key=f"btn_lunch_{slot.strftime('%H%M')}_{is_edit_mode}", on_click=handle_time_selection, args=(slot,), type=button_type, disabled=is_full, use_container_width=True)
    
    # st.write("🌙 **夜の部 (17:00 ~ 21:00)**")
    # cols_dinner = st.columns(4)
    # for i, slot in enumerate(generate_time_slots(False)):
    #     with cols_dinner[i % 4]:
    #         booked_count = len(df_reservations[(df_reservations['日付'] == selected_date.strftime('%Y-%m-%d')) & (df_reservations['時間'] == slot.strftime('%H:%M')) & (df_reservations['ステータス'] == '予約済み')])
    #         is_full = booked_count >= 28
    #         button_type = "primary" if st.session_state.selected_time == slot else "secondary"
    #         st.button(slot.strftime('%H:%M'), key=f"btn_dinner_{slot.strftime('%H%M')}_{is_edit_mode}", on_click=handle_time_selection, args=(slot,), type=button_type, disabled=is_full, use_container_width=True)

    # --- スクロールを実行するJavaScript ---
    if st.session_state.get('scroll_to_time', False):
        components.html('<script>window.parent.document.getElementById("time-selection-anchor").scrollIntoView({ behavior: "smooth", block: "start" });</script>', height=0)
        st.session_state.scroll_to_time = False
    
    if st.session_state.get('scroll_to_pax', False):
        components.html('<script>window.parent.document.getElementById("pax-input-anchor").scrollIntoView({ behavior: "smooth", block: "start" });</script>', height=0)
        st.session_state.scroll_to_pax = False

    if st.session_state.get('scroll_to_seat', False):
        components.html('<script>window.parent.document.getElementById("seat-selection-anchor").scrollIntoView({ behavior: "smooth", block: "start" });</script>', height=0)
        st.session_state.scroll_to_seat = False

    if st.session_state.selected_time:
        st.markdown("---")
        
        # --- 3. 人数を入力 ---
        st.markdown('<div id="pax-input-anchor"></div>', unsafe_allow_html=True)
        st.markdown("##### 3. 人数を入力")
        # 編集モードかどうかに応じて、使用するセッションキーを決定
        if is_edit_mode:
            adult_key, adult_keypad_target = "edit_pax_adult", "edit_pax_adult"
            child_key, child_keypad_target = "edit_pax_child", "edit_pax_child"
            total_key = "edit_pax_input"
        else:
            adult_key, adult_keypad_target = "pax_adult", "pax_adult"
            child_key, child_keypad_target = "pax_child", "pax_child"
            total_key = "pax_input"

        # カラムを3分割（大人用、子供用、合計用）
        pax_cols = st.columns([0.4, 0.4, 0.2]) 
        
        with pax_cols[0]: # 大人
            pax_inner_cols = st.columns([3, 1])
            with pax_inner_cols[0]: 
                st.text_input(
                    "大人 (人数)", 
                    key=f"{adult_key}_input", 
                    on_change=convert_text_callback, # 変更時に関数を呼び出す
                    args=(f"{adult_key}_input", 'digit')
                )
            with pax_inner_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{adult_key}_keypad_btn", on_click=set_active_keypad, args=(adult_keypad_target,), use_container_width=True)

        with pax_cols[1]: # 子供
            pax_inner_cols = st.columns([3, 1])
            with pax_inner_cols[0]: 
                st.text_input(
                    "子供 (人数)", 
                    key=f"{child_key}_input", 
                    on_change=convert_text_callback, # 変更時に関数を呼び出す
                    args=(f"{child_key}_input", 'digit')
                )
            with pax_inner_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{child_key}_keypad_btn", on_click=set_active_keypad, args=(child_keypad_target,), use_container_width=True)
        
        with pax_cols[2]: # 合計
            # 合計欄は自動計算されるため、編集不可(disabled=True)にする
            st.text_input("合計", key=total_key, disabled=True)
            
        # 「大人」または「子供」の入力ボタンが押されたらキーパッドを表示
        if st.session_state.active_keypad in [adult_keypad_target, child_keypad_target]:
            draw_keypads()
        
        st.markdown("---")

        # --- 4. 席を選択 ---
        st.markdown('<div id="seat-selection-anchor"></div>', unsafe_allow_html=True)
        st.markdown(f"##### 4. 席を選択 ({st.session_state.selected_time.strftime('%H:%M')} の予約)")
        df_for_check = df_reservations.drop(st.session_state.editing_reservation_index) if is_edit_mode else df_reservations
        day_reservations = df_for_check[(df_for_check['日付'] == selected_date.strftime('%Y-%m-%d')) & (df_for_check['ステータス'] == '予約済み')]
        booked_tables_set = set()
        new_res_time = st.session_state.selected_time
        for index, reservation in day_reservations.iterrows():
            try:
                reservation_time = datetime.strptime(reservation['時間'], '%H:%M').time()
                is_overlapping = False
                if reservation['会席'] == 'はい':
                    is_new_res_lunch = new_res_time.hour < 15
                    is_reservation_lunch = reservation_time.hour < 15
                    if is_new_res_lunch == is_reservation_lunch: is_overlapping = True
                else:
                    res_start_dt = datetime.combine(date.today(), reservation_time)
                    res_end_dt = res_start_dt + timedelta(minutes=90)
                    new_res_dt = datetime.combine(date.today(), new_res_time)
                    if res_start_dt <= new_res_dt < res_end_dt: is_overlapping = True
                if is_overlapping:
                    seats = [s.strip() for s in str(reservation['席番号']).split(',')]
                    booked_tables_set.update(seats)
            except (ValueError, TypeError): continue
        booked_tables = list(booked_tables_set)

        st.subheader("1階")
        with st.container(border=True):
            map_cols = st.columns([0.5, 2, 0.2, 2])
            with map_cols[1]:
                with st.container(border=True):
                    block_cols = st.columns(2)
                    for i, col_seats in enumerate(SEAT_MAP["first_floor"]["left_block"]):
                        with block_cols[i]:
                            for seat in reversed(col_seats): st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
            with map_cols[3]:
                with st.container(border=True):
                    block_cols = st.columns(2)
                    for i, col_seats in enumerate(SEAT_MAP["first_floor"]["right_block"]):
                        with block_cols[i]:
                            for seat in reversed(col_seats): st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
        
        st.subheader("2階")
        with st.container(border=True):
            st.write("上段")
            up_cols = st.columns(3)
            up_blocks = ["up_left_block", "up_center_block", "up_right_block"]
            for i, block_name in enumerate(up_blocks):
                with up_cols[i]:
                    with st.container(border=True):
                        seat_cols = st.columns(len(SEAT_MAP["second_floor"][block_name]))
                        for j, seat_col in enumerate(SEAT_MAP["second_floor"][block_name]):
                            with seat_cols[j]:
                                for seat in reversed(seat_col): st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
            st.divider()
            st.write("下段")
            low_cols = st.columns([0.5, 1, 0.2, 1, 0.5])
            with low_cols[1]:
                with st.container(border=True):
                    block_name = "low_left_block"
                    seat_cols = st.columns(len(SEAT_MAP["second_floor"][block_name]))
                    for j, seat_col in enumerate(SEAT_MAP["second_floor"][block_name]):
                        with seat_cols[j]:
                            for seat in reversed(seat_col): st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
            with low_cols[3]:
                with st.container(border=True):
                    block_name = "low_right_block"
                    seat_cols = st.columns(len(SEAT_MAP["second_floor"][block_name]))
                    for j, seat_col in enumerate(SEAT_MAP["second_floor"][block_name]):
                        with seat_cols[j]:
                            for seat in reversed(seat_col): st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))

    if st.session_state.selected_tables:
        
        draw_menu_selection()

        st.markdown("---")
        st.markdown(f"##### 6. お客様情報と詳細を入力")
        
        st.write("**会席料理のご予約ですか？**")
        kaiseki_cols = st.columns(2)
        with kaiseki_cols[0]:
            if st.button("はい", key="kaiseki_yes", use_container_width=True, type="primary" if st.session_state.is_kaiseki == "はい" else "secondary"):
                st.session_state.is_kaiseki = "はい"; st.rerun()
        with kaiseki_cols[1]:
            if st.button("いいえ", key="kaiseki_no", use_container_width=True, type="primary" if st.session_state.is_kaiseki == "いいえ" else "secondary"):
                st.session_state.is_kaiseki = "いいえ"; st.rerun()

        st.markdown("---")
        
        name_key, name_keypad_target = ("edit_name", "edit_name") if is_edit_mode else ("name", "name")
        tel_key, tel_keypad_target = ("edit_tel", "edit_tel") if is_edit_mode else ("tel", "tel")
        
        cust_info_cols = st.columns(2)
        with cust_info_cols[0]:
            name_cols = st.columns([3, 1])
            with name_cols[0]: st.text_input("お名前（カタカナ）*", key=f"{name_key}_input", on_change=convert_text_callback, args=(f"{name_key}_input", 'kana'))
            with name_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{name_key}_keypad_btn", on_click=set_active_keypad, args=(name_keypad_target,), use_container_width=True)
            if st.session_state.active_keypad == name_keypad_target:
                draw_keypads()

        with cust_info_cols[1]:
            tel_cols = st.columns([3, 1])
            with tel_cols[0]: st.text_input("電話番号*", key=f"{tel_key}_input", on_change=convert_text_callback, args=(f"{tel_key}_input", 'digit'))
            with tel_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{tel_key}_keypad_btn", on_click=set_active_keypad, args=(tel_keypad_target,), use_container_width=True)
            if st.session_state.active_keypad == tel_keypad_target:
                draw_keypads()
        
        st.markdown("---")

        pax_str = st.session_state.edit_pax_input if is_edit_mode else st.session_state.pax_input
        pax_count = int(pax_str) if pax_str.isdigit() else 0
        
        if st.session_state.is_kaiseki == "はい" and pax_count >= 10:
            st.write("**送迎バスは必要ですか？**")
            bus_cols = st.columns(2)
            with bus_cols[0]:
                if st.button("必要", key="bus_yes", use_container_width=True, type="primary" if st.session_state.bus_required == "必要" else "secondary"):
                    st.session_state.bus_required = "必要"; st.rerun()
            with bus_cols[1]:
                if st.button("不要", key="bus_no", use_container_width=True, type="primary" if st.session_state.bus_required == "不要" else "secondary"):
                    st.session_state.bus_required = "不要"; st.rerun()
            
            if st.session_state.bus_required == "必要":
                st.selectbox("担当バス運転手を選択してください", options=BUS_DRIVERS, key='bus_driver')
                
                # ★★★★★ 住所入力の代替案UI ★★★★★
                st.text_input("お迎え先住所", key="bus_address", help="スマートフォンのマイク機能や、地図アプリからのコピー＆ペーストが便利です。")
                
                with st.expander("住所の入力方法について"):
                    st.info("##### **方法1：音声入力を使う（推奨）**\n1. 上の住所入力欄をタップします。\n2. スマートフォンやタブレットのキーボードに表示されるマイクのボタン 🎤 を押します。\n3. 住所をはっきりと話すと、自動で漢字に変換されて入力されます。")
                    st.info("##### **方法2：地図アプリからコピーする**\n1. 下の「地図アプリで検索」ボタンを押して、Google マップを開きます。\n2. 目的地を検索し、表示された住所を長押ししてコピーします。\n3. この画面に戻り、上の住所入力欄に貼り付けます。")

                address_button_cols = st.columns(2)
                with address_button_cols[0]:
                    st.link_button("🗺️ 地図アプリで検索", url="http://googleusercontent.com/maps", use_container_width=True)
                with address_button_cols[1]:
                    address_to_show = st.session_state.bus_address
                    if address_to_show:
                        encoded_address = urllib.parse.quote(address_to_show)
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
                        st.link_button("入力した住所を確認", url=maps_url, use_container_width=True)
                    else:
                        st.button("入力した住所を確認", disabled=True, use_container_width=True, help="住所を入力すると有効になります")
                
                st.text_input("お迎え時間", key="bus_time")

        else:
            st.session_state.bus_required = "不要"
            st.session_state.bus_driver = "未定"
            st.session_state.bus_address = ""
            st.session_state.bus_time = ""
        
        st.selectbox("ご利用用途を選択してください", options=PURPOSE_OPTIONS, key='purpose')
        
        st.write("**アレルギーの有無**")
        allergy_cols = st.columns(2)
        with allergy_cols[0]:
            if st.button("有り", key="allergy_yes", use_container_width=True, type="primary" if st.session_state.has_allergies == "有り" else "secondary"):
                st.session_state.has_allergies = "有り"; st.rerun()
        with allergy_cols[1]:
            if st.button("無し", key="allergy_no", use_container_width=True, type="primary" if st.session_state.has_allergies == "無し" else "secondary"):
                st.session_state.has_allergies = "無し"
                st.session_state.allergy_details = ""; st.rerun()

# --- ▼▼▼ 以下のブロック (アレルギー詳細UI) を丸ごと置き換え ▼▼▼ ---
        if st.session_state.has_allergies == "有り":
            st.markdown('<p class="red-text">アレルギーの詳細を人ごとに入力してください</p>', unsafe_allow_html=True)
            
            # --- アレルゲンボタン用のコールバック関数を定義 ---
            def append_allergen_to_person(allergen, person_id, person_index):
                """特定の人（person_id）にアレルゲンを追加するコールバック"""
                if person_index < len(st.session_state.allergy_list_of_people):
                    person_data = st.session_state.allergy_list_of_people[person_index]
                    if person_data['id'] == person_id:
                        details_key = f"allergy_details_{person_id}"
                        current_details = st.session_state.get(details_key, person_data.get('details', ''))
                        if current_details:
                            new_details = f"{current_details}、{allergen}"
                        else:
                            new_details = allergen
                        person_data['details'] = new_details
                        st.session_state[details_key] = new_details

            st.markdown("---")

            # --- 人ごとの入力欄 ---
            for i, person_data in enumerate(st.session_state.allergy_list_of_people):
                person_id = person_data['id']

                # --- ▼▼▼ ここは前回の修正のまま（正しい）▼▼▼ ---
                name_key = f"allergy_name_{person_id}"
                details_key = f"allergy_details_{person_id}"
                if name_key not in st.session_state:
                    st.session_state[name_key] = person_data.get('name', '')
                if details_key not in st.session_state:
                    st.session_state[details_key] = person_data.get('details', '')
                # --- ▲▲▲ ここまで ▲▲▲ ---

                with st.container(border=True):
                    cols = st.columns([0.7, 0.3])
                    with cols[0]:
                        st.write(f"**対象者 {i + 1} 人目**")
                    with cols[1]:
                        if st.button("削除", key=f"del_allergy_person_{person_id}", use_container_width=True):
                            st.session_state.allergy_list_of_people = [p for p in st.session_state.allergy_list_of_people if p['id'] != person_id]
                            st.rerun()
                    
                    # --- ▼▼▼ ★★★ ここを修正 (value= を削除) ★★★ ▼▼▼ ---
                    st.text_input(
                        "お名前（Aさん、Bさん など）", 
                        # value=... の行を削除
                        key=name_key,
                        on_change=lambda key=name_key, i=i: st.session_state.allergy_list_of_people[i].update({'name': st.session_state[key]})
                    )
                    
                    # --- ▼▼▼ ★★★ ここを修正 (value= を削除) ★★★ ▼▼▼ ---
                    st.text_area(
                        "アレルギーの詳細", 
                        # value=... の行を削除
                        key=details_key,
                        on_change=lambda key=details_key, i=i: st.session_state.allergy_list_of_people[i].update({'details': st.session_state[key]})
                    )

                    st.write("**よくあるアレルゲン（クリックしてこの人に追加）**")
                    ALLERGENS_TOP10 = ["卵", "乳", "小麦", "えび", "かに", "そば", "落花生", "大豆", "ごま", "くるみ"]
                    allergen_cols = st.columns(5)
                    
                    for j, allergen in enumerate(ALLERGENS_TOP10):
                        with allergen_cols[j % 5]:
                            st.button(allergen, 
                                      key=f"allergen_{allergen}_{person_id}", 
                                      use_container_width=True, 
                                      on_click=append_allergen_to_person, 
                                      args=(allergen, person_id, i)
                                     )

            if st.button("＋ アレルギーのある人を追加する", use_container_width=True, type="secondary"):
                new_person_id = str(uuid.uuid4())
                st.session_state.allergy_list_of_people.append({
                    'id': new_person_id,
                    'name': '',
                    'details': ''
                })
                st.rerun()

        else:
             if st.session_state.allergy_list_of_people:
                 st.session_state.allergy_list_of_people = []
             st.session_state.allergy_details = ""
        
        # --- ▲▲▲ 置き換えここまで ▲▲▲ ---
        
        memo_key, staff_key = ("edit_memo_input", "edit_staff_in_charge") if is_edit_mode else ("memo_input_area", "staff_in_charge")
        st.text_area("備考", key=memo_key)
        st.text_input("担当者", key=staff_key)

        st.markdown("---")
        st.markdown("##### 最終確認")
        selected_seats_str = ", ".join(sorted(st.session_state.selected_tables))
        #st.info(f"**【選択中の予約内容】**\n- **日時:** {selected_date.strftime('%Y/%m/%d')} {st.session_state.selected_time.strftime('%H:%M')}\n- **席:** {selected_seats_str}")
        date_display = selected_date.strftime('%Y/%m/%d') if selected_date else "日付未選択"
        time_display = st.session_state.selected_time.strftime('%H:%M') if st.session_state.selected_time else "時間未選択"
        st.info(f"**【選択中の予約内容】**\n- **日時:** {date_display} {time_display}\n- **席:** {selected_seats_str if selected_seats_str else '席未選択'}")



# --- ▼▼▼ 以下のブロックを修正 (注文文字列の作成) ▼▼▼ ---
        # order_string = ", ".join(st.session_state.order_items)
        
        # 辞書を文字列に変換 (例: {"煮込み": 2} -> "煮込み, 煮込み")
        order_list = []
        # st.session_state.order_items が存在し、辞書であることを確認
        if isinstance(st.session_state.order_items, dict):
            for item, count in st.session_state.order_items.items():
                if count > 0:
                    order_list.extend([item] * count) # itemをcount回繰り返したリストを生成
        
        order_string = ", ".join(sorted(order_list)) # 保存時にソートしておくと見やすい
        # --- ▲▲▲ 修正ここまで ▲▲▲ ---



        bus_driver_to_save = st.session_state.bus_driver if st.session_state.bus_required == "必要" else ""
        bus_address_to_save = st.session_state.bus_address if st.session_state.bus_required == "必要" else ""
        bus_time_to_save = st.session_state.bus_time if st.session_state.bus_required == "必要" else ""
        # --- ▼▼▼ 以下の1行を置き換え ▼▼▼ ---
        # allergy_details_to_save = st.session_state.allergy_details if st.session_state.has_allergies == "有り" else ""
        
        # allergy_list_of_people を "名前: 詳細 / 名前: 詳細" の形式の文字列にシリアライズする
        allergy_details_to_save = ""
        if st.session_state.has_allergies == "有り" and st.session_state.allergy_list_of_people:
            entries = []
            for person in st.session_state.allergy_list_of_people:
                name = person.get('name', '').strip()
                details = person.get('details', '').strip()
                
                # 名前か詳細が入力されている場合のみ保存対象とする
                if name or details:
                    # 名前がない場合は（詳細）とし、詳細がない場合は（要確認）とする
                    entries.append(f"{name or '（詳細）'}: {details or '（要確認）'}")
            
            # " / " (スペース・スラッシュ・スペース) で区切る
            allergy_details_to_save = " / ".join(entries) 
        # --- ▲▲▲ 修正ここまで ▲▲▲ ---

        if is_edit_mode:
            form_cols = st.columns(2)
            with form_cols[0]:
                if st.button("変更を保存", use_container_width=True, type="primary"):
                    if not st.session_state.edit_name_input or not st.session_state.edit_tel_input:
                        st.warning("お名前と電話番号は必須項目です。")
                    else:
                        idx = st.session_state.editing_reservation_index
                        df_reservations.loc[idx, '日付'] = selected_date.strftime('%Y-%m-%d')
                        df_reservations.loc[idx, '時間'] = st.session_state.selected_time.strftime('%H:%M')
                        df_reservations.loc[idx, '席番号'] = selected_seats_str
                        df_reservations.loc[idx, '名前'] = st.session_state.edit_name_input
                        df_reservations.loc[idx, '電話番号'] = st.session_state.edit_tel_input
                        df_reservations.loc[idx, '人数'] = int(st.session_state.edit_pax_input) if st.session_state.edit_pax_input.isdigit() else 0
                        df_reservations.loc[idx, '人数(大人)'] = int(st.session_state.edit_pax_adult_input) if st.session_state.edit_pax_adult_input.isdigit() else 0
                        df_reservations.loc[idx, '人数(子供)'] = int(st.session_state.edit_pax_child_input) if st.session_state.edit_pax_child_input.isdigit() else 0
                        df_reservations.loc[idx, '注文内容'] = order_string
                        df_reservations.loc[idx, '会席'] = st.session_state.is_kaiseki
                        df_reservations.loc[idx, 'バス'] = st.session_state.bus_required
                        df_reservations.loc[idx, '担当バス運転手'] = bus_driver_to_save
                        df_reservations.loc[idx, 'お迎え先住所'] = bus_address_to_save
                        df_reservations.loc[idx, 'お迎え時間'] = bus_time_to_save
                        df_reservations.loc[idx, '用途'] = st.session_state.purpose
                        df_reservations.loc[idx, 'アレルギー'] = st.session_state.has_allergies
                        df_reservations.loc[idx, 'アレルギー詳細'] = allergy_details_to_save
                        df_reservations.loc[idx, '備考'] = st.session_state.edit_memo_input
                        df_reservations.loc[idx, '担当者'] = st.session_state.edit_staff_in_charge
                        st.session_state.df_reservation = df_reservations.sort_values(by=['日付', '時間'])
                        st.session_state.editing_reservation_index = None
                        st.success("予約内容を変更しました。")
                        st.session_state.current_page = '予約確認・検索'
                        st.rerun()
            with form_cols[1]:
                if st.button("変更をやめる", use_container_width=True):
                    st.session_state.editing_reservation_index = None
                    st.session_state.current_page = '予約確認・検索'
                    st.rerun()
            st.markdown("---")
            if st.button("この予約をキャンセルする", use_container_width=True, type="secondary"):
                idx = st.session_state.editing_reservation_index
                df_reservations.loc[idx, 'ステータス'] = 'キャンセル'
                st.session_state.df_reservation = df_reservations
                st.session_state.editing_reservation_index = None
                st.success("予約をキャンセルしました。")
                st.session_state.current_page = '予約確認・検索'
                st.rerun()
        else:
            if st.button("この内容で予約を確定する", use_container_width=True, type="primary"):
                if not st.session_state.name_input or not st.session_state.tel_input:
                    st.warning("お名前と電話番号は必須項目です。")
                else:
                    new_reservation = {
                        '日付': selected_date.strftime('%Y-%m-%d'), 
                        '時間': st.session_state.selected_time.strftime('%H:%M'), 
                        '席番号': selected_seats_str, 
                        '名前': st.session_state.name_input, 
                        '電話番号': st.session_state.tel_input, 
                        '人数': int(st.session_state.pax_input) if st.session_state.pax_input else 0, 
                        # --- ▼▼▼ 以下の2行を追加 ▼▼▼ ---
                        '人数(大人)': int(st.session_state.pax_adult_input) if st.session_state.pax_adult_input else 0,
                        '人数(子供)': int(st.session_state.pax_child_input) if st.session_state.pax_child_input else 0,
                        # --- ▲▲▲ 追加ここまで ▲▲▲ ---
                        '注文内容': order_string, 
                        '会席': st.session_state.is_kaiseki, 
                        'バス': st.session_state.bus_required, 
                        '担当バス運転手': bus_driver_to_save, 
                        'お迎え先住所': bus_address_to_save, 
                        'お迎え時間': bus_time_to_save, 
                        '用途': st.session_state.purpose, 
                        'アレルギー': st.session_state.has_allergies, 
                        'アレルギー詳細': allergy_details_to_save, 
                        '備考': st.session_state.memo_input_area, 
                        '担当者': st.session_state.staff_in_charge, 
                        'ステータス': '予約済み'
                    }
                    new_row_df = pd.DataFrame([new_reservation])
                    df_updated = pd.concat([df_reservations, new_row_df], ignore_index=True)
                    st.session_state.df_reservation = df_updated.sort_values(by=['日付', '時間']).astype(RESERVATION_COLUMNS)
                    st.session_state.clear_form_on_next_run = True
                    st.success("新しい予約を追加しました。")
                    st.rerun()

elif page == '予約確認・検索':
    st.title('予約確認・検索')
    # (予約確認・検索ページのコード ... 変更なし)
    if st.session_state.df_reservation.empty:
        handle_reservation_upload(uploader_key='upload_on_confirm_page')
    else:
        df_reservations = st.session_state.df_reservation
        st.subheader("予約の検索")
        search_cols = st.columns(2)
        with search_cols[0]:
            name_search_cols = st.columns([3,1])
            with name_search_cols[0]:
                st.text_input("名前で検索", key="search_name_input", on_change=convert_text_callback, args=('search_name_input', 'kana'))
            with name_search_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key="search_name_keypad_btn", on_click=set_active_keypad, args=('search_name',), use_container_width=True)
            if st.session_state.active_keypad == 'search_name':
                draw_keypads()
        with search_cols[1]:
            tel_search_cols = st.columns([3,1])
            with tel_search_cols[0]:
                st.text_input("電話番号で検索", key="search_tel_input", on_change=convert_text_callback, args=('search_tel_input', 'digit'))
            with tel_search_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key="search_tel_keypad_btn", on_click=set_active_keypad, args=('search_tel',), use_container_width=True)
            if st.session_state.active_keypad == 'search_tel':
                draw_keypads()

        search_name = st.session_state.search_name_input
        search_tel = st.session_state.search_tel_input
        is_searching = search_name or search_tel

        if is_searching:
            st.markdown("---")
            st.subheader("検索結果")
            search_result_df = df_reservations
            if search_name: search_result_df = search_result_df[search_result_df['名前'].str.contains(search_name, na=False)]
            if search_tel: search_result_df = search_result_df[search_result_df['電話番号'].str.contains(search_tel, na=False)]
            st.dataframe(search_result_df, use_container_width=True, height=250)

        st.markdown("---")
        st.subheader("日付を選択して一覧表示")



        if st.session_state.show_calendar_in_search:
                    
            # カレンダーが表示されている場合
            if st.button("カレンダーを非表示にする", use_container_width=True, type="secondary"):
                st.session_state.show_calendar_in_search = False
                st.rerun()
                    
            # 描画の前に、カレンダーが使う日付キー(selected_date_custom)を
            # 検索ページ用の日付キー(search_selected_date)と同期させる
            if st.session_state.search_selected_date != st.session_state.selected_date_custom:
                st.session_state.selected_date_custom = st.session_state.search_selected_date
                # カレンダーの表示年月も同期
                st.session_state.calendar_year = st.session_state.search_selected_date.year
                st.session_state.calendar_month = st.session_state.search_selected_date.month
                st.rerun() 
                    
            # カスタムカレンダーを描画 (キープレフィックスを "search_cal" などに変える)
            # 日付がクリックされると handle_date_change が呼ばれ、
            # st.session_state.search_selected_date が更新された後に rerun されます。
            draw_custom_calendar(calendar_key_prefix="search_cal")

        else:
            # カレンダーが非表示の場合
            if st.button("カレンダーで日付を選択する", use_container_width=True):
                st.session_state.show_calendar_in_search = True
                st.rerun()
                
         # どの道でも、一覧表示に使う日付は search_selected_date から取得
        selected_date = st.session_state.search_selected_date


        st.subheader(f"【 {selected_date.strftime('%Y年%m月%d日')} の予約一覧 】")
        daily_display_df = df_reservations[df_reservations['日付'] == selected_date.strftime('%Y-%m-%d')]
        if daily_display_df.empty:
            st.info("この日の予約はありません。")
        else:
            for index, row in daily_display_df.iterrows():
                is_cancelled = row.get('ステータス') == 'キャンセル'
                pax_adult = row.get('人数(大人)', 0)
                pax_child = row.get('人数(子供)', 0)
                
                # 大人・子供のデータがある場合のみ内訳を表示
                if pax_adult > 0 or pax_child > 0:
                    pax_display = f"{row['人数']}名 (大人:{pax_adult}名, 子供:{pax_child}名)"
                else:
                    pax_display = f"{row['人数']}名" # 古いデータ用の表示
                
                display_text = f"{row['時間']} - {row['名前']}様 - {pax_display} - 席:{row['席番号']}"
                if is_cancelled: display_text = f"~~{display_text}~~ (キャンセル済み)"
                with st.expander(display_text):
                    st.write(f"**電話番号:** {row['電話番号']}")


                    # --- ▼▼▼ 以下のブロックを修正・置き換え ▼▼▼ ---
                    order_string = row.get('注文内容')

                    # [修正点]
                    # order_string が存在し (True)、かつ pd.isna で NaN でないことを確認
                    if order_string and not pd.isna(order_string):
                        
                        # [修正点]
                        # 実行前に str() で明示的に文字列にキャスト(変換)する
                        order_list = [item.strip() for item in str(order_string).split(',') if item.strip()]
                        
                        # リストが空でなければ (例: " , " だけで中身がなかった場合)
                        if order_list:
                            from collections import Counter
                            order_counts = Counter(order_list)
                            
                            display_order_string = ", ".join([f"{item} ({count})" for item, count in sorted(order_counts.items())])
                            
                            st.write(f"**注文内容:** {display_order_string}")
                        # else: 
                            # order_listが空 (例: ", ,") だった場合は何も表示しない
                    
                    # --- ▲▲▲ 置き換えここまで ▲▲▲ ---                



                    st.write(f"**用途:** {row.get('用途', '未選択')}")
                    st.write(f"**会席:** {row.get('会席', 'いいえ')}")
                    if row.get('バス') == '必要':
                        driver = row.get('担当バス運転手', '未定')
                        address = row.get('お迎え先住所', '未入力')
                        pickup_time = row.get('お迎え時間', '未入力')
                        st.write(f"**送迎バス:** 必要 (担当: {driver})")
                        st.write(f"**お迎え先:** {address} ({pickup_time})")
                    if row.get('アレルギー') == '有り':
                        details = row.get('アレルギー詳細', '詳細未入力')
                        st.write(f"**アレルギー:** 有り ({details})")
                    else:
                        st.write(f"**アレルギー:** 無し")
                    
                    st.write(f"**備考:** {row['備考']}")
                    if row.get('担当者'):
                        st.write(f"**担当者:** {row['担当者']}")

                    expander_cols = st.columns(2)
                    with expander_cols[0]: st.button("変更", key=f"edit_{index}", on_click=start_editing, args=(index,), use_container_width=True, disabled=is_cancelled)
                    with expander_cols[1]: st.button("キャンセル", key=f"cancel_{index}", on_click=start_editing, args=(index,), use_container_width=True, type="primary", disabled=is_cancelled)

        st.markdown("---")
        st.subheader("全予約データ管理")
        manage_cols = st.columns(2)
        with manage_cols[0]:
            csv_string_all = df_reservations.to_csv(index=False).encode('utf-8-sig')
            current_time_str = datetime.now().strftime('%Y_%m_%d_%H%M')
            st.download_button(label="全ての予約データをCSVでダウンロード", data=csv_string_all, file_name=f"all_reservations_{current_time_str}.csv", mime='text/csv', use_container_width=True)
        with manage_cols[1]:
            if st.button("予約データをリセットして再アップロード", use_container_width=True):
                st.session_state.df_reservation = pd.DataFrame(columns=RESERVATION_COLUMNS.keys()).astype(RESERVATION_COLUMNS)
                st.session_state.editing_reservation_index = None
                st.rerun()

elif page == '分析ページ':
    st.title('データ分析')
    # (分析ページのコード ... 変更なし)
    st.write('ここでは、顧客データや予約データの簡単な分析ができます。')
    st.subheader('顧客データの分析')
    if st.session_state.df_customer is not None:
        st.metric("総顧客数", len(st.session_state.df_customer))
        st.bar_chart(st.session_state.df_customer['都道府県名'].value_counts())
    else:
        st.warning('先に「顧客管理」ページでデータをアップロードしてください。')
    st.markdown("---")
    st.subheader('予約データの分析')
    if not st.session_state.df_reservation.empty:
        df_res = st.session_state.df_reservation
        col1_an, col2_an, col3_an = st.columns(3)
        with col1_an: st.metric("総予約組数 (キャンセル除く)", len(df_res[df_res['ステータス'] == '予約済み']))
        with col2_an: st.metric("総予約人数 (キャンセル除く)", int(df_res[df_res['ステータス'] == '予約済み']['人数'].sum()))
        with col3_an: st.metric("キャンセル組数", len(df_res[df_res['ステータス'] == 'キャンセル']))
        st.write("日別 予約組数 (キャンセル除く)")
        daily_counts = df_res[df_res['ステータス'] == '予約済み']['日付'].value_counts().sort_index()
        st.bar_chart(daily_counts)
        st.write("日別 予約人数 (キャンセル除く)")
        daily_guests = df_res[df_res['ステータス'] == '予約済み'].groupby('日付')['人数'].sum().sort_index()
        st.bar_chart(daily_guests)
    else:
        st.info("分析対象の予約データがありません。「予約登録」または「予約確認・検索」ページでデータを読み込んでください。")