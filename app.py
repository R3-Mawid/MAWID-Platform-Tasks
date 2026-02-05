import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText

# --- 1. قائمة الإيميلات المصرح لها بالدخول ---
EMAILS_MAP = {
    "د.عادل الحربي": "adilalharby@gmail.com",
    "بريده المطيري": "buraida990@gmail.com",
    "منى العتيبي": "muna@example.com",
    "هويدي الصنقر": "hwidii@gmail.com",
    "المسؤول": "r3-mawid@gmail.com"
}

# --- 2. نظام تسجيل الدخول ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 تسجيل الدخول لبرنامج موعد")
    user_email = st.text_input("أدخل بريدك الإلكتروني الشخصي:")
    if st.button("دخول"):
        if user_email.lower() in [e.lower() for e in EMAILS_MAP.values()]:
            st.session_state.authenticated = True
            st.session_state.user_email = user_email
            st.rerun()
        else:
            st.error("البريد غير مسجل، يرجى التواصل مع مسؤول النظام.")
    st.stop()

# --- 3. دالة إرسال الإيميل الآمنة ---
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

# --- 4. الربط مع Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)
url = st.secrets["gsheets"]["spreadsheet_url"]

# قراءة البيانات الحالية من الجدول
df = conn.read(spreadsheet=url, usecols=[0, 1, 2, 3, 4, 5])

# --- 5. واجهة التطبيق ---
st.title("🩻 نظام إدارة مهام برنامج موعد")
st.write(f"المستخدم الحالي: {st.session_state.user_email}")

# ميزة إضافة مهمة جديدة
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        col1, col2 = st.columns(2)
        with col1:
            t_due_date = st.date_input("تاريخ التسليم", datetime.date.today())
        with col2:
            t_due_time = st.time_input("وقت التسليم", datetime.time(9, 0))
        
        t_days = st.number_input("الأيام المتوقعة للإنجاز", min_value=1, step=1)
        
        submitted = st.form_submit_button("حفظ المهمة وتنبيه الزملاء")
        
        if submitted and t_name:
            # تجهيز الصف الجديد
            new_row = pd.DataFrame([{
                "المهمة": t_name,
                "المسؤول": t_member,
                "التاريخ": str(t_due_date),
                "وقت التسليم": str(t_due_time),
                "الأيام المتوقعة": t_days,
                "الحالة": "قيد التنفيذ"
            }])
            # تحديث الجدول في جوجل شيتس
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(spreadsheet=url, data=updated_df)
            
            # التنبيهات
            body = f"تم إضافة مهمة جديدة: {t_name}\nالموعد: {t_due_date} الساعة {t_due_time}\nالمدة المتوقعة: {t_days} أيام"
            send_email("🔔 مهمة جديدة - نظام موعد", body, EMAILS_MAP[t_member])
            send_email("⚠️ تحديث نظام موعد", f"تم إضافة مهمة من قبل {st.session_state.user_email}", EMAILS_MAP["هويدي الصنقر"])
            
            st.success("✅ تم حفظ المهمة في Google Sheets وتنبيه الجميع")
            st.rerun()

# --- 6. لوحة المتابعة (قفل التعديل) ---
st.divider()
st.subheader("📊 لوحة المتابعة وتحديث الحالات")

if not df.empty:
    # القفل البرمجي: تعديل الحالة فقط
    edited_df = st.data_editor(
        df,
        column_config={
            "المهمة": st.column_config.Column(disabled=True),
            "المسؤول": st.column_config.Column(disabled=True),
            "التاريخ": st.column_config.Column(disabled=True),
            "وقت التسليم": st.column_config.Column(disabled=True),
            "الأيام المتوقعة": st.column_config.Column(disabled=True),
            "الحالة": st.column_config.SelectboxColumn(
                "الحالة",
                options=["قيد التنفيذ", "مكتمل", "جاري التواصل", "متأخر"],
                required=True,
            )
        },
        use_container_width=True,
        num_rows="fixed"
    )
    
    if st.button("حفظ التغييرات النهائية"):
        conn.update(spreadsheet=url, data=edited_df)
        # تنبيه هويدي
        send_email("⚠️ تعديل في حالات المهام", f"قام {st.session_state.user_email} بتحديث حالات المهام.", EMAILS_MAP["هويدي الصنقر"])
        st.success("✅ تم تحديث جدول جوجل شيتس وتنبيه هويدي")
        st.rerun()
else:
    st.info("لا توجد مهام مسجلة في الجدول.")
