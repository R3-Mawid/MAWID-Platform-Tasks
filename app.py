import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText

# --- 1. إعدادات الأمان والدخول ---
EMAILS_MAP = {
    "د.عادل الحربي": "adilalharby@gmail.com",
    "بريده المطيري": "buraida990@gmail.com",
    "منى العتيبي": "muna@example.com",
    "هويدي الصنقر": "hwidii@gmail.com",
    "المسؤول": "r3-mawid@gmail.com"
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 دخول نظام موعد")
    u_email = st.text_input("أدخل بريدك الإلكتروني:")
    if st.button("دخول"):
        if u_email.lower() in [e.lower() for e in EMAILS_MAP.values()]:
            st.session_state.authenticated = True
            st.session_state.user_email = u_email
            st.rerun()
        else:
            st.error("البريد غير مسجل.")
    st.stop()

# --- 2. دالة إرسال الإيميل ---
def send_email(subject, body, receiver):
    try:
        sender = st.secrets["email_settings"]["sender_email"]
        password = st.secrets["email_settings"]["app_password"]
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = receiver
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except: return False

# --- 3. الربط مع Google Sheets ---
# ملاحظة: يستخدم الرابط الموجود في Secrets تحت [gsheets] spreadsheet_url
conn = st.connection("gsheets", type=GSheetsConnection)
url = st.secrets["gsheets"]["spreadsheet_url"]

# قراءة البيانات
df = conn.read(spreadsheet=url)

# --- 4. واجهة التطبيق ---
st.title("🩻 نظام إدارة مهام برنامج موعد")
st.caption(f"متصل بقاعدة بيانات Google Sheets | المستخدم: {st.session_state.user_email}")

# نموذج الإضافة
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        col1, col2 = st.columns(2)
        with col1: t_due_date = st.date_input("التاريخ", datetime.date.today())
        with col2: t_due_time = st.time_input("الوقت", datetime.time(9, 0))
        t_days = st.number_input("الأيام المتوقعة", min_value=1, step=1)
        
        if st.form_submit_button("حفظ وإرسال تنبيه"):
            if t_name:
                new_row = pd.DataFrame([{
                    "المهمة": t_name, "المسؤول": t_member, 
                    "التاريخ": str(t_due_date), "وقت التسليم": str(t_due_time), 
                    "الأيام المتوقعة": t_days, "الحالة": "قيد التنفيذ"
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=url, data=updated_df)
                
                # التنبيهات
                send_email("🔔 مهمة جديدة", f"تم تكليفك بمهمة: {t_name}", EMAILS_MAP[t_member])
                send_email("⚠️ تحديث نظام", f"إضافة مهمة بواسطة {st.session_state.user_email}", EMAILS_MAP["هويدي الصنقر"])
                st.success("✅ تم الحفظ في Google Sheets وتنبيه الجميع")
                st.rerun()

# --- 5. لوحة المتابعة (قفل التعديل) ---
st.divider()
st.subheader("📊 المتابعة (تعديل الحالة فقط)")

if not df.empty:
    edited_df = st.data_editor(
        df,
        column_config={
            "المهمة": st.column_config.Column(disabled=True),
            "المسؤول": st.column_config.Column(disabled=True),
            "التاريخ": st.column_config.Column(disabled=True),
            "وقت التسليم": st.column_config.Column(disabled=True),
            "الأيام المتوقعة": st.column_config.Column(disabled=True),
            "الحالة": st.column_config.SelectboxColumn("الحالة", options=["قيد التنفيذ", "مكتمل", "جاري التواصل", "متأخر"], required=True)
        },
        use_container_width=True, num_rows="fixed"
    )
    
    if st.button("حفظ التغييرات النهائية"):
        conn.update(spreadsheet=url, data=edited_df)
        send_email("⚠️ تعديل حالات", f"قام {st.session_state.user_email} بتحديث الجدول.", EMAILS_MAP["هويدي الصنقر"])
        st.success("✅ تم التحديث بنجاح!")
        st.rerun()
else:
    st.info("الجدول فارغ حالياً.")
