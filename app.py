import streamlit as st
import pandas as pd
import datetime
import smtplib
import os
import pytz 
from email.mime.text import MIMEText

# --- 1. إعدادات المنطقة الزمنية ---
KSA = pytz.timezone('Asia/Riyadh')

def get_ksa_now():
    return datetime.datetime.now(KSA)

# --- 2. قائمة الإيميلات ---
EMAILS_MAP = {
    "د.عادل الحربي": "adilalharby@gmail.com",
    "بريده المطيري": "buraida990@gmail.com",
    "منى العتيبي": "muna@example.com",
    "هويدي الصنقر": "hwidii@gmail.com",
    "المسؤول": "r3-mawid@gmail.com"
}

# --- 3. نظام تسجيل الدخول ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 دخول نظام ادارة مهام برنامج موعد")
    u_email = st.text_input("أدخل بريدك الإلكتروني:")
    if st.button("دخول"):
        if u_email.lower() in [e.lower() for e in EMAILS_MAP.values()]:
            st.session_state.authenticated = True
            st.session_state.user_email = u_email.lower()
            st.rerun()
        else:
            st.error("البريد غير مسجل.")
    st.stop()

# --- 4. إدارة البيانات ---
DB_FILE = "radiology_tasks.csv"
COLUMNS = [
    "المهمة", "المسؤول", "تاريخ البدء", "وقت البدء", 
    "الأيام المتوقعة", "الموعد النهائي", "الحالة",
    "تاريخ الإنجاز الفعلي", "وقت الإنجاز الفعلي"
]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE).fillna("")

def save_data(df_to_save):
    df_to_save.to_csv(DB_FILE, index=False)

# --- 5. دالة إرسال الإيميل ---
def send_email(subject, body, receiver):
    try:
        sender = st.secrets["email_settings"]["sender_email"]
        password = st.secrets["email_settings"]["app_password"]
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = receiver
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except: return False

# --- 6. واجهة التطبيق الرئيسية ---
st.set_page_config(page_title="نظام مهام موعد", layout="wide")
st.title(" نظام إدارة مهام برنامج موعد")
df = load_data()

with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        t_days = st.number_input("عدد الأيام المتوقعة للإنجاز", min_value=1, step=1)
        
        # الحساب التلقائي للتاريخ ليظهر للمستخدم قبل الحفظ
        current_ksa_date = get_ksa_now().date()
        calculated_finish_date = current_ksa_date + datetime.timedelta(days=t_days)
        st.info(f"📅 الموعد النهائي الذي سيتم تسجيله: **{calculated_finish_date}**")
        
        if st.form_submit_button("حفظ وإرسال التنبيهات"):
            if t_name:
                now_ksa = get_ksa_now()
                # التأكد من حساب التاريخ هنا أيضاً لحظة الضغط على الزر
                final_expected_date = now_ksa.date() + datetime.timedelta(days=t_days)
                
                new_row = {
                    "المهمة": t_name, 
                    "المسؤول": t_member, 
                    "تاريخ البدء": str(now_ksa.date()), 
                    "وقت البدء": now_ksa.strftime("%I:%M:%S %p"), 
                    "الأيام المتوقعة": t_days, 
                    "الموعد النهائي": str(final_expected_date), # هذا السطر هو الأهم
                    "الحالة": "قيد التنفيذ",
                    "تاريخ الإنجاز الفعلي": "", 
                    "وقت الإنجاز الفعلي": ""
                }
                
                new_df = pd.DataFrame([new_row])
                df = pd.concat([df, new_df], ignore_index=True)
                save_data(df)
                
                # التنبيهات
                email_content = f"مهمة جديدة: {t_name}\nالموعد النهائي: {final_expected_date}"
                send_email("🔔 مهمة جديدة", email_content, EMAILS_MAP[t_member])
                send_email("⚠️ إحاطة", f"أضاف {st.session_state.user_email} مهمة جديدة لـ {t_member}", EMAILS_MAP["هويدي الصنقر"])
                
                st.success(f"✅ تم تسجيل المهمة بنجاح بموعد نهائي: {final_expected_date}")
                st.rerun()

# --- 7. لوحة المتابعة ---
st.divider()
st.subheader("📊 لوحة المتابعة المباشرة")
if not df.empty:
    # إعادة ترتيب الأعمدة للتأكد من ظهور الموعد النهائي في مكانه الصحيح
    df = df[COLUMNS] 
    
    edited_df = st.data_editor(
        df,
        column_config={
            "المهمة": st.column_config.Column(disabled=True),
            "المسؤول": st.column_config.Column(disabled=True),
            "تاريخ البدء": st.column_config.Column(disabled=True),
            "وقت البدء": st.column_config.Column(disabled=True),
            "الأيام المتوقعة": st.column_config.Column(disabled=True),
            "الموعد النهائي": st.column_config.Column(disabled=True),
            "تاريخ الإنجاز الفعلي": st.column_config.Column(disabled=True),
            "وقت الإنجاز الفعلي": st.column_config.Column(disabled=True),
            "الحالة": st.column_config.SelectboxColumn("الحالة", options=["قيد التنفيذ", "مكتمل", "متأخر"], required=True)
        },
        use_container_width=True
    )
    
    if st.button("تحديث وحفظ الحالات"):
        now_ksa = get_ksa_now()
        for index, row in edited_df.iterrows():
            if row["الحالة"] == "مكتمل" and (row["تاريخ الإنجاز الفعلي"] == "" or pd.isna(row["تاريخ الإنجاز الفعلي"])):
                edited_df.at[index, "تاريخ الإنجاز الفعلي"] = str(now_ksa.date())
                edited_df.at[index, "وقت الإنجاز الفعلي"] = now_ksa.strftime("%I:%M:%S %p")
            elif row["الحالة"] == "قيد التنفيذ":
                edited_df.at[index, "تاريخ الإنجاز الفعلي"] = ""
                edited_df.at[index, "وقت الإنجاز الفعلي"] = ""
        
        save_data(edited_df)
        st.success("✅ تم تحديث الحالات.")
        st.rerun()

# --- 8. لوحة المسؤول ---
if st.session_state.user_email == "r3-mawid@gmail.com":
    st.sidebar.title("🛠️ لوحة تحكم المسؤول")
    with st.sidebar.expander("🗑️ إدارة المهام والحذف"):
        if not df.empty:
            to_del = st.selectbox("اختر مهمة لحذفها:", df["المهمة"].tolist())
            if st.button("حذف المهمة المختارة"):
                df = df[df["المهمة"] != to_del]
                save_data(df)
                st.rerun()
            
            st.divider()
            if st.button("⚠️ مسح جميع البيانات (إفراغ الجدول)"):
                if st.checkbox("أؤكد رغبتي في الحذف الكامل"):
                    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, index=False)
                    st.rerun()
    
    st.sidebar.download_button(
        label="📥 تحميل النسخة الاحتياطية",
        data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"mawid_tasks_{get_ksa_now().date()}.csv",
        mime='text/csv'
    )

