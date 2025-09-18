import streamlit as st
import pandas as pd
import io
# timedelta を追加
from datetime import datetime, time, date, timedelta
import uuid

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
    height: 50em !important;     /* ボタンの高さを変更 */
    font-size: 10em !important;    /* 文字の大きさを変更 */
}

</style>
""", unsafe_allow_html=True)




# アプリが期待するデータ構造（スキーマ）を定義 
# 顧客データ用
CUSTOMER_COLUMNS = {
    "顧客ID": "object", "名前": "object", "フリガナ": "object", "郵便番号": "object",
    "都道府県名": "object", "住所": "object", "メールアドレス": "object", "電話番号": "object",
    "FAX番号": "object", "領収書が必要な方はこちらをご選択ください": "object",
    "適格請求書をご希望の方は、同梱されている「納品書」も必要となりますこと、ご了承ください": "object",
    "ユーザー登録": "object", "備考": "object"
}
# ★★★★★ ここからが修正箇所 ★★★★★
# 予約データ用に「担当者」列を追加
RESERVATION_COLUMNS = {
    '日付': 'str', '時間': 'str', '席番号': 'object', 
    '名前': 'object', '電話番号': 'object', '人数': 'int64', 
    '注文内容': 'object', '会席': 'object', 'バス': 'object', '担当バス運転手': 'object',
    'お迎え先住所': 'object', 'お迎え時間': 'object', '用途': 'object',
    'アレルギー': 'object', 'アレルギー詳細': 'object',
    '備考': 'object', '担当者': 'object', 'ステータス': 'object'
}


SEAT_MAP = {
    "first_floor": {
        "left_block": [["1-1", "1-2", "1-3"], ["1-4", "1-5", "1-6"]],
        "right_block": [["2-1", "2-2", "2-3"], ["2-4", "2-5", "2-6"]]
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
if 'memo_input_area' not in st.session_state: st.session_state.memo_input_area = ""

if 'search_name_input' not in st.session_state: st.session_state.search_name_input = ""
if 'search_tel_input' not in st.session_state: st.session_state.search_tel_input = ""

if 'editing_reservation_index' not in st.session_state: st.session_state.editing_reservation_index = None
if 'edit_name_input' not in st.session_state: st.session_state.edit_name_input = ""
if 'edit_pax_input' not in st.session_state: st.session_state.edit_pax_input = ""
if 'edit_tel_input' not in st.session_state: st.session_state.edit_tel_input = ""
if 'edit_memo_input' not in st.session_state: st.session_state.edit_memo_input = ""
if 'edit_selected_date' not in st.session_state: st.session_state.edit_selected_date = date.today()

if 'selected_menu_category' not in st.session_state: st.session_state.selected_menu_category = "煮込み" 
if 'order_items' not in st.session_state: st.session_state.order_items = []
if 'is_kaiseki' not in st.session_state: st.session_state.is_kaiseki = "いいえ"
if 'bus_required' not in st.session_state: st.session_state.bus_required = "不要"
if 'bus_driver' not in st.session_state: st.session_state.bus_driver = "未定"
if 'bus_address' not in st.session_state: st.session_state.bus_address = ""
if 'bus_time' not in st.session_state: st.session_state.bus_time = ""
if 'purpose' not in st.session_state: st.session_state.purpose = "会食"
if 'has_allergies' not in st.session_state: st.session_state.has_allergies = "無し"
if 'allergy_details' not in st.session_state: st.session_state.allergy_details = ""
# ★★★★★ 担当者用のセッション状態 ★★★★★
if 'staff_in_charge' not in st.session_state: st.session_state.staff_in_charge = ""
if 'edit_staff_in_charge' not in st.session_state: st.session_state.edit_staff_in_charge = ""


def to_katakana(hiragana_string): return "".join([chr(ord(char) + 96) if "ぁ" <= char <= "ん" else char for char in hiragana_string])
def to_half_width(text): return text.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

def convert_text_callback(session_state_key, conversion_type):
    text = st.session_state[session_state_key]
    if conversion_type == 'kana': converted_text = to_katakana(text)
    elif conversion_type == 'digit': converted_text = "".join(filter(str.isdigit, to_half_width(text)))
    else: converted_text = text
    st.session_state[session_state_key] = converted_text

def generate_time_slots(is_lunch):
    slots = []
    if is_lunch:
        for hour in range(11, 15):
            for minute in (0, 30):
                if hour == 14 and minute == 30: break
                slots.append(time(hour, minute))
    else:
        for hour in range(17, 22):
            for minute in (0, 30):
                if hour == 21 and minute == 30: break
                slots.append(time(hour, minute))
    return slots

def toggle_seat_selection(seat):
    if seat in st.session_state.selected_tables: st.session_state.selected_tables.remove(seat)
    else: st.session_state.selected_tables.append(seat)

def set_active_keypad(target): st.session_state.active_keypad = target

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
    st.session_state.edit_tel_input = str(reservation_to_edit['電話番号'])
    st.session_state.edit_memo_input = str(reservation_to_edit['備考'])
    st.session_state.edit_selected_date = datetime.strptime(reservation_to_edit['日付'], '%Y-%m-%d').date()
    st.session_state.selected_time = datetime.strptime(reservation_to_edit['時間'], '%H:%M').time()
    st.session_state.selected_tables = [s.strip() for s in reservation_to_edit['席番号'].split(',')]
    st.session_state.order_items = []
    st.session_state.is_kaiseki = reservation_to_edit.get('会席', 'いいえ')
    st.session_state.bus_required = reservation_to_edit.get('バス', '不要')
    st.session_state.bus_driver = reservation_to_edit.get('担当バス運転手', '未定')
    st.session_state.bus_address = reservation_to_edit.get('お迎え先住所', '')
    st.session_state.bus_time = reservation_to_edit.get('お迎え時間', '')
    st.session_state.purpose = reservation_to_edit.get('用途', '会食')
    st.session_state.has_allergies = reservation_to_edit.get('アレルギー', '無し')
    st.session_state.allergy_details = reservation_to_edit.get('アレルギー詳細', '')
    st.session_state.edit_staff_in_charge = reservation_to_edit.get('担当者', '')
    st.session_state.active_keypad = None
    st.session_state.current_page = '予約登録'
    
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
            elif st.session_state.active_keypad in ['pax', 'tel', 'edit_pax', 'edit_tel', 'search_tel']:
                target_label = "人数" if "pax" in st.session_state.active_keypad else "電話番号"
                st.subheader(f"{target_label}を入力してください")
                k_cols = st.columns(3)
                for i in range(1, 10):
                    with k_cols[(i-1)%3]: st.button(str(i), key=f"key_{i}_{st.session_state.active_keypad}", on_click=append_char, args=(str(i),), use_container_width=True)
                with k_cols[0]: st.button("C", key=f"key_clear_{st.session_state.active_keypad}", on_click=clear_input, use_container_width=True)
                with k_cols[1]: st.button("0", key=f"key_0_{st.session_state.active_keypad}", on_click=append_char, args=("0",), use_container_width=True)
                with k_cols[2]: st.button("←", key=f"key_delete_{st.session_state.active_keypad}", on_click=delete_char, use_container_width=True)
            st.button("入力完了", on_click=set_active_keypad, args=(None,), use_container_width=True, type="primary")

def handle_reservation_upload(uploader_key):
    st.info("予約データがありません。過去の予約データをCSVファイルから読み込んでください。")
    uploaded_file = st.file_uploader("予約データCSVをアップロード", type=['csv'], key=uploader_key, help=f"CSVファイルには、次の列が必要です: {', '.join(RESERVATION_COLUMNS.keys())}")
    if uploaded_file:
        try:
            csv_dtypes = {'席番号': str, '電話番号': str}
            df_to_load = pd.read_csv(uploaded_file, encoding='utf-8-sig', dtype=csv_dtypes)
            for col, default in [('ステータス', '予約済み'), ('注文内容', ''), ('会席', 'いいえ'), ('バス', '不要'), ('担当バス運転手', ''), ('お迎え先住所', ''), ('お迎え時間', ''), ('用途', '会食'), ('アレルギー', '無し'), ('アレルギー詳細', ''), ('担当者', '')]:
                if col not in df_to_load.columns: df_to_load[col] = default
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df_to_load = pd.read_csv(uploaded_file, encoding='shift-jis', dtype=csv_dtypes)
            for col, default in [('ステータス', '予約済み'), ('注文内容', ''), ('会席', 'いいえ'), ('バス', '不要'), ('担当バス運転手', ''), ('お迎え先住所', ''), ('お迎え時間', ''), ('用途', '会食'), ('アレルギー', '無し'), ('アレルギー詳細', ''), ('担当者', '')]:
                if col not in df_to_load.columns: df_to_load[col] = default
        if not all(col in df_to_load.columns for col in RESERVATION_COLUMNS.keys()):
            st.error(f"ファイルの列が正しくありません。必要な列: {', '.join(RESERVATION_COLUMNS.keys())}")
            st.info(f"ファイルに含まれる列: {', '.join(df_to_load.columns)}")
        else:
            st.session_state.df_reservation = df_to_load.astype(RESERVATION_COLUMNS)
            st.success("予約データを読み込みました。")
            st.rerun()

def draw_menu_selection():
        # ▼▼▼ この行を追加 ▼▼▼
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
    if st.session_state.selected_menu_category:
        items = MENU_DATA.get(st.session_state.selected_menu_category, [])
        cols = st.columns(6)
        for i, item in enumerate(items):
            with cols[i % 6]:
                if st.button(item, key=f"item_{item}", use_container_width=True):
                    st.session_state.order_items.append(item)
                    st.rerun()
    if st.session_state.order_items:
        st.markdown("---")
        st.write("**現在の注文リスト**")
        for i, item in enumerate(st.session_state.order_items):
            item_cols = st.columns([0.8, 0.2])
            with item_cols[0]: st.write(f"- {item}")
            with item_cols[1]:
                if st.button("削除", key=f"del_{i}_{item}", use_container_width=True):
                    st.session_state.order_items.pop(i)
                    st.rerun()
        if st.button("注文を全てクリア", use_container_width=True, type="secondary"):
            st.session_state.order_items = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def set_page():
    destination_page = st.session_state.radio_selector
    if destination_page == '予約登録':
        st.session_state.name_input = st.session_state.get('search_name_input', '')
        st.session_state.tel_input = st.session_state.get('search_tel_input', '')
    st.session_state.current_page = destination_page
    st.session_state.editing_reservation_index = None

st.sidebar.title("メニュー")
page_options = ['予約登録', '予約確認・検索', '顧客管理', '分析ページ']
st.sidebar.radio("ページを選択してください", page_options, key='radio_selector', on_change=set_page, index=page_options.index(st.session_state.current_page))
page = st.session_state.current_page

# (顧客管理ページ、分析ページのコードは変更なしのため省略)
# =====================================================================================
# 顧客管理ページ
# =====================================================================================
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



# (顧客管理ページ、分析ページのコードは変更なし)
# ====================================================================================
# 予約登録ページ（編集機能もここに統合）
# =====================================================================================
elif page == '予約登録':
    df_reservations = st.session_state.df_reservation
    is_edit_mode = st.session_state.editing_reservation_index is not None
    st.title('予約の変更' if is_edit_mode else '新規予約登録')
    if is_edit_mode:
        idx = st.session_state.editing_reservation_index
        original_reservation = df_reservations.loc[idx]
        st.info(f"以下の予約を編集中です： {original_reservation['日付']} {original_reservation['時間']} - {original_reservation['名前']}様")
        st.markdown("##### 1. 日付を選択")
        selected_date = st.date_input("日付", key='edit_date', value=st.session_state.edit_selected_date, on_change=lambda: st.session_state.update(selected_time=None, selected_tables=[]))
    else:
        if st.session_state.df_reservation.empty:
            handle_reservation_upload(uploader_key='upload_on_register_page')
            st.stop() 
        if st.session_state.get("clear_form_on_next_run"):
            st.session_state.update(name_input="", tel_input="", pax_input="", memo_input_area="", selected_tables=[], selected_time=None, order_items=[], is_kaiseki="いいえ", bus_required="不要", bus_driver="未定", bus_address="", bus_time="", purpose="会食", has_allergies="無し", allergy_details="", staff_in_charge="", clear_form_on_next_run=False)
        st.markdown("##### 1. お客様情報を入力")
        c1, c2 = st.columns(2)
        with c1:
            name_cols = st.columns([3, 1])
            with name_cols[0]: st.text_input("お名前（カタカナ）*", key="name_input", on_change=convert_text_callback, args=("name_input", 'kana'))
            with name_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key="new_name_keypad_btn", on_click=set_active_keypad, args=('name',), use_container_width=True)
        with c2:
            tel_cols = st.columns([3, 1])
            with tel_cols[0]: st.text_input("電話番号", key="tel_input", on_change=convert_text_callback, args=("tel_input", 'digit'))
            with tel_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key="new_tel_keypad_btn", on_click=set_active_keypad, args=('tel',), use_container_width=True)
        pax_cols = st.columns([0.5, 0.5]) 
        with pax_cols[0]:
            pax_inner_cols = st.columns([3, 1])
            with pax_inner_cols[0]: st.text_input("人数", key="pax_input", on_change=convert_text_callback, args=("pax_input", 'digit'))
            with pax_inner_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key="new_pax_keypad_btn", on_click=set_active_keypad, args=('pax',), use_container_width=True)


        if st.session_state.active_keypad in ['name', 'tel', 'pax', 'edit_name', 'edit_pax', 'edit_tel']:
            draw_keypads()



        st.markdown("---")
        st.markdown("##### 2. 日付を選択")
        selected_date = st.date_input("日付を選択", label_visibility="collapsed", on_change=lambda: st.session_state.update(selected_time=None, selected_tables=[]))
    st.markdown("##### 3. 時間を選択")
    st.write("☀️ **昼の部 (11:00 ~ 15:00)**")
    cols_lunch = st.columns(4)
    for i, slot in enumerate(generate_time_slots(True)):
        with cols_lunch[i % 4]:
            booked_count = len(df_reservations[(df_reservations['日付'] == selected_date.strftime('%Y-%m-%d')) & (df_reservations['時間'] == slot.strftime('%H:%M')) & (df_reservations['ステータス'] == '予約済み')])
            is_full = booked_count >= 28
            button_type = "primary" if st.session_state.selected_time == slot else "secondary"
            st.button(slot.strftime('%H:%M'), key=f"btn_lunch_{slot.strftime('%H%M')}_{is_edit_mode}", on_click=lambda s=slot: st.session_state.update(selected_time=s, selected_tables=[]), type=button_type, disabled=is_full, use_container_width=True)
    st.write("🌙 **夜の部 (17:00 ~ 21:00)**")
    cols_dinner = st.columns(4)
    for i, slot in enumerate(generate_time_slots(False)):
        with cols_dinner[i % 4]:
            booked_count = len(df_reservations[(df_reservations['日付'] == selected_date.strftime('%Y-%m-%d')) & (df_reservations['時間'] == slot.strftime('%H:%M')) & (df_reservations['ステータス'] == '予約済み')])
            is_full = booked_count >= 28
            button_type = "primary" if st.session_state.selected_time == slot else "secondary"
            st.button(slot.strftime('%H:%M'), key=f"btn_dinner_{slot.strftime('%H%M')}_{is_edit_mode}", on_click=lambda s=slot: st.session_state.update(selected_time=s, selected_tables=[]), type=button_type, disabled=is_full, use_container_width=True)
    if st.session_state.selected_time:
        st.markdown("---")
        st.markdown(f"##### 4. 席を選択 ({st.session_state.selected_time.strftime('%H:%M')} の予約)")

        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ▼▼▼▼▼▼▼▼▼▼▼▼▼ 予約席の判定ロジックをここから変更 ▼▼▼▼▼▼▼▼▼▼▼▼
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

        df_for_check = df_reservations.drop(st.session_state.editing_reservation_index) if is_edit_mode else df_reservations
        
        # 選択日の予約済みデータのみを抽出
        day_reservations = df_for_check[
            (df_for_check['日付'] == selected_date.strftime('%Y-%m-%d')) &
            (df_for_check['ステータス'] == '予約済み')
        ]

        booked_tables_set = set()
        new_res_time = st.session_state.selected_time

        # 1件ずつ予約を確認し、席が利用可能かを判定
        for index, reservation in day_reservations.iterrows():
            try:
                reservation_time = datetime.strptime(reservation['時間'], '%H:%M').time()
                is_overlapping = False
                
                # ★★★ ここを「会席」の判定に変更 ★★★
                if reservation['会席'] == 'はい':
                    # 同じ時間帯（昼/夜）に予約があれば、その席は利用不可
                    is_new_res_lunch = new_res_time.hour < 15
                    is_reservation_lunch = reservation_time.hour < 15
                    if is_new_res_lunch == is_reservation_lunch:
                        is_overlapping = True
                
                # 「会席」でない場合
                else:
                    # 既存の予約の開始時刻と終了時刻を計算
                    res_start_dt = datetime.combine(date.today(), reservation_time)
                    res_end_dt = res_start_dt + timedelta(minutes=90)
                    
                    # 新規予約の希望時刻を計算
                    new_res_dt = datetime.combine(date.today(), new_res_time)
                    
                    # 90分間の利用時間内に新規予約の希望時刻が含まれていれば、席は利用不可
                    if res_start_dt <= new_res_dt < res_end_dt:
                        is_overlapping = True

                # 重複がある場合、その予約の席番号を予約不可リストに追加
                if is_overlapping:
                    seats = [s.strip() for s in str(reservation['席番号']).split(',')]
                    booked_tables_set.update(seats)
            except (ValueError, TypeError):
                # 時間の形式が正しくないなどのデータエラーはスキップ
                continue
        
        booked_tables = list(booked_tables_set)

        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲ 予約席の判定ロジックの変更はここまで ▲▲▲▲▲▲▲▲▲▲▲▲
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

        st.subheader("1階")
        with st.container(border=True):
            map_cols = st.columns([0.5, 2, 0.2, 2])
            with map_cols[1]:
                with st.container(border=True):
                    block_cols = st.columns(2)
                    for i, col_seats in enumerate(SEAT_MAP["first_floor"]["left_block"]):
                        with block_cols[i]:
                            for seat in reversed(col_seats):
                                st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
            with map_cols[3]:
                with st.container(border=True):
                    block_cols = st.columns(2)
                    for i, col_seats in enumerate(SEAT_MAP["first_floor"]["right_block"]):
                        with block_cols[i]:
                            for seat in reversed(col_seats):
                                st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
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
                                for seat in reversed(seat_col):
                                    st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
            st.divider()
            st.write("下段")
            low_cols = st.columns([0.5, 1, 0.2, 1, 0.5])
            with low_cols[1]:
                with st.container(border=True):
                    block_name = "low_left_block"
                    seat_cols = st.columns(len(SEAT_MAP["second_floor"][block_name]))
                    for j, seat_col in enumerate(SEAT_MAP["second_floor"][block_name]):
                        with seat_cols[j]:
                            for seat in reversed(seat_col):
                                st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
            with low_cols[3]:
                with st.container(border=True):
                    block_name = "low_right_block"
                    seat_cols = st.columns(len(SEAT_MAP["second_floor"][block_name]))
                    for j, seat_col in enumerate(SEAT_MAP["second_floor"][block_name]):
                        with seat_cols[j]:
                            for seat in reversed(seat_col):
                                st.button(seat, key=f"seat_{seat}_{is_edit_mode}", on_click=toggle_seat_selection, args=(seat,), disabled=(seat in booked_tables), use_container_width=True, type=("primary" if seat in st.session_state.selected_tables else "secondary"))
    if is_edit_mode or st.session_state.selected_tables:
        draw_menu_selection()
        st.markdown("---")
        st.markdown(f"##### {'6. 詳細情報と最終確認' if not is_edit_mode else '4. 予約情報を編集'}")
        seats_are_selected = bool(st.session_state.selected_tables)
        if seats_are_selected:
            selected_seats_str = ", ".join(sorted(st.session_state.selected_tables))
            st.info(f"【選択中の予約内容】 {selected_date.strftime('%m/%d')} {st.session_state.selected_time.strftime('%H:%M')} - 席: {selected_seats_str}")
        else:
            selected_seats_str = "" 
            if is_edit_mode: st.warning("席が選択されていません。変更を保存するには、少なくとも1つの席を選択してください。")
        

        
        st.write("**会席料理のご予約ですか？**")
        kaiseki_cols = st.columns(2)
        with kaiseki_cols[0]:
            if st.button("はい", key="kaiseki_yes", use_container_width=True, type="primary" if st.session_state.is_kaiseki == "はい" else "secondary"):
                st.session_state.is_kaiseki = "はい"
                st.rerun()
        with kaiseki_cols[1]:
            if st.button("いいえ", key="kaiseki_no", use_container_width=True, type="primary" if st.session_state.is_kaiseki == "いいえ" else "secondary"):
                st.session_state.is_kaiseki = "いいえ"
                st.rerun()
        
        pax_str = st.session_state.edit_pax_input if is_edit_mode else st.session_state.pax_input
        pax_count = int(pax_str) if pax_str.isdigit() else 0
        
        if st.session_state.is_kaiseki == "はい" and pax_count >= 10:
            st.write("**送迎バスは必要ですか？**")
            bus_cols = st.columns(2)
            with bus_cols[0]:
                if st.button("必要", key="bus_yes", use_container_width=True, type="primary" if st.session_state.bus_required == "必要" else "secondary"):
                    st.session_state.bus_required = "必要"
                    st.rerun()
            with bus_cols[1]:
                if st.button("不要", key="bus_no", use_container_width=True, type="primary" if st.session_state.bus_required == "不要" else "secondary"):
                    st.session_state.bus_required = "不要"
                    st.rerun()
            if st.session_state.bus_required == "必要":
                st.selectbox("担当バス運転手を選択してください", options=BUS_DRIVERS, key='bus_driver')
                st.text_input("お迎え先住所", key="bus_address")
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
                st.session_state.has_allergies = "有り"
                st.rerun()
        with allergy_cols[1]:
            if st.button("無し", key="allergy_no", use_container_width=True, type="primary" if st.session_state.has_allergies == "無し" else "secondary"):
                st.session_state.has_allergies = "無し"
                st.session_state.allergy_details = ""
                st.rerun()

        if st.session_state.has_allergies == "有り":
            st.text_area("アレルギーの詳細を記入してください", key="allergy_details")
        
        
        st.markdown("---")

        # ★★★★★ ここからが修正箇所 ★★★★★
        if is_edit_mode:
            # 編集モードでは、各入力欄を個別に表示
            name_key, pax_key, tel_key, keypad_prefix = ("edit_name", "edit_pax", "edit_tel", "edit")
            name_cols = st.columns([3, 1])
            with name_cols[0]: st.text_input("お名前（カタカナ）*", key=f"{name_key}_input", on_change=convert_text_callback, args=(f"{name_key}_input", 'kana'))
            with name_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{keypad_prefix}_name_keypad_btn", on_click=set_active_keypad, args=(name_key,), use_container_width=True)
            tel_cols = st.columns([3, 1])
            with tel_cols[0]: st.text_input("電話番号", key=f"{tel_key}_input", on_change=convert_text_callback, args=(f"{tel_key}_input", 'digit'))
            with tel_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{keypad_prefix}_tel_keypad_btn", on_click=set_active_keypad, args=(tel_key,), use_container_width=True)
            pax_cols = st.columns([3, 1])
            with pax_cols[0]: st.text_input("人数", key=f"{pax_key}_input", on_change=convert_text_callback, args=(f"{pax_key}_input", 'digit'))
            with pax_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key=f"{keypad_prefix}_pax_keypad_btn", on_click=set_active_keypad, args=(pax_key,), use_container_width=True)
            st.text_area("備考", key="edit_memo_input")
            st.text_input("担当者", key="edit_staff_in_charge")
        else:
            # 新規モードでは備考と担当者のみ
            st.text_area("備考", key="memo_input_area")
            st.text_input("担当者", key="staff_in_charge")

        st.markdown("---")
        order_string = ", ".join(st.session_state.order_items)
        bus_driver_to_save = st.session_state.bus_driver if st.session_state.bus_required == "必要" else ""
        bus_address_to_save = st.session_state.bus_address if st.session_state.bus_required == "必要" else ""
        bus_time_to_save = st.session_state.bus_time if st.session_state.bus_required == "必要" else ""
        allergy_details_to_save = st.session_state.allergy_details if st.session_state.has_allergies == "有り" else ""

        if is_edit_mode:
            form_cols = st.columns(2)
            with form_cols[0]:
                if st.button("変更を保存", use_container_width=True, type="primary", disabled=not seats_are_selected):
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
                    new_reservation = {'日付': selected_date.strftime('%Y-%m-%d'), '時間': st.session_state.selected_time.strftime('%H:%M'), '席番号': selected_seats_str, '名前': st.session_state.name_input, '電話番号': st.session_state.tel_input, '人数': int(st.session_state.pax_input) if st.session_state.pax_input else 0, '注文内容': order_string, '会席': st.session_state.is_kaiseki, 'バス': st.session_state.bus_required, '担当バス運転手': bus_driver_to_save, 'お迎え先住所': bus_address_to_save, 'お迎え時間': bus_time_to_save, '用途': st.session_state.purpose, 'アレルギー': st.session_state.has_allergies, 'アレルギー詳細': allergy_details_to_save, '備考': st.session_state.memo_input_area, '担当者': st.session_state.staff_in_charge, 'ステータス': '予約済み'}
                    new_row_df = pd.DataFrame([new_reservation])
                    df_updated = pd.concat([df_reservations, new_row_df], ignore_index=True)
                    st.session_state.df_reservation = df_updated.sort_values(by=['日付', '時間']).astype(RESERVATION_COLUMNS)
                    st.session_state.clear_form_on_next_run = True
                    st.success("新しい予約を追加しました。")
                    st.rerun()

    # if st.session_state.active_keypad in ['name', 'tel', 'pax', 'edit_name', 'edit_pax', 'edit_tel']:
    #     draw_keypads()

# =====================================================================================
# 予約確認・検索ページ
# =====================================================================================
elif page == '予約確認・検索':
    st.title('予約確認・検索')
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
        with search_cols[1]:
            tel_search_cols = st.columns([3,1])
            with tel_search_cols[0]:
                st.text_input("電話番号で検索", key="search_tel_input", on_change=convert_text_callback, args=('search_tel_input', 'digit'))
            with tel_search_cols[1]:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button("入力", key="search_tel_keypad_btn", on_click=set_active_keypad, args=('search_tel',), use_container_width=True)
        
        if st.session_state.active_keypad in ['search_name', 'search_tel']:
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
        selected_date = st.date_input("日付を選択", label_visibility="collapsed")
        st.subheader(f"【 {selected_date.strftime('%Y年%m月%d日')} の予約一覧 】")
        daily_display_df = df_reservations[df_reservations['日付'] == selected_date.strftime('%Y-%m-%d')]
        if daily_display_df.empty:
            st.info("この日の予約はありません。")
        else:
            for index, row in daily_display_df.iterrows():
                is_cancelled = row.get('ステータス') == 'キャンセル'
                display_text = f"{row['時間']} - {row['名前']}様 - {row['人数']}名 - 席:{row['席番号']}"
                if is_cancelled: display_text = f"~~{display_text}~~ (キャンセル済み)"
                with st.expander(display_text):
                    st.write(f"**電話番号:** {row['電話番号']}")
                    if row.get('注文内容'):
                        st.write(f"**注文内容:** {row['注文内容']}")
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

# =====================================================================================
# 分析ページ
# =====================================================================================
elif page == '分析ページ':
    st.title('データ分析')
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