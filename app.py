import streamlit as st
import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText

# --- 1. قائمة الإيميلات ---
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

# --- 3. إدارة البيانات (هيكل نظيف بدون تكرار) ---
DB_FILE = "radiology_tasks.csv"
# الأعمدة الأساسية فقط
COLUMNS = [
    "المهمة", "المسؤول", "تاريخ البدء", "وقت البدء", 
    "الأيام المتوقعة", "الموعد النهائي", "الحالة",
    "تاريخ الإنجاز الفعلي", "وقت الإنجاز الفعلي"
]

if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=COLUMNS)
    df_init.to_csv(DB_FILE, index=False)

def load_data():
    # fillna("") تضمن أن الخانات الفارغة لا تظهر كـ NaN المزعجة
    return pd.read_csv(DB_FILE).fillna("")

def save_data(df_to_save):
    df_to_save.to_csv(DB_FILE, index=False)

# --- 4. دالة إرسال الإيميل ---
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

# --- 5. واجهة التطبيق ---
st.title("🩻 نظام إدارة مهام برنامج موعد")
df = load_data()

with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        t_days = st.number_input("المدة المتوقعة (بالأيام)", min_value=1, step=1)
        
        if st.form_submit_button("حفظ وإرسال التنبيهات"):
            if t_name:
                now = datetime.datetime.now()
                due_date = now.date() + datetime.timedelta(days=t_days)
                
                new_row = {
                    "المهمة": t_name, 
                    "المسؤول": t_member, 
                    "تاريخ البدء": str(now.date()), 
                    "وقت البدء": now.strftime("%H:%M:%S"), 
                    "الأيام المتوقعة": t_days, 
                    "الموعد النهائي": str(due_date),
                    "الحالة": "قيد التنفيذ",
                    "تاريخ الإنجاز الفعلي": "", 
                    "وقت الإنجاز الفعلي": ""
                }
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success(f"✅ تم الحفظ! الموعد النهائي هو {due_date}")
                st.rerun()

# --- لوحة المتابعة ---
st.divider()
st.subheader("📊 لوحة المتابعة")

if not df.empty:
    # عرض الجدول وتفعيل التعديل للحالة فقط
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
            "الحالة": st.column_config.SelectboxColumn(
                "الحالة", 
                options=["قيد التنفيذ", "مكتمل", "متأخر"], 
                required=True
            )
        },
        use_container_width=True, num_rows="fixed"
    )
    
    if st.button("تحديث الحالات"):
        now = datetime.datetime.now()
        # تحديث تلقائي لوقت الإنجاز الفعلي عند اختيار "مكتمل"
        for index, row in edited_df.iterrows():
            if row["الحالة"] == "مكتمل" and (row["تاريخ الإنجاز الفعلي"] == ""):
                edited_df.at[index, "تاريخ الإنجاز الفعلي"] = str(now.date())
                edited_df.at[index, "وقت الإنجاز الفعلي"] = now.strftime("%H:%M:%S")
            elif row["الحالة"] == "قيد التنفيذ":
                edited_df.at[index, "تاريخ الإنجاز الفعلي"] = ""
                edited_df.at[index, "وقت الإنجاز الفعلي"] = ""

        save_data(edited_df)
        send_email("⚠️ تحديث نظام", f"تعديل جديد بواسطة {st.session_state.user_email}", EMAILS_MAP["هويدي الصنقر"])
        st.success("✅ تم التحديث وتوثيق الوقت الفعلي!")
        st.rerun()

    st.download_button(label="📥 تحميل السجل الكامل", data=df.to_csv(index=False).encode('utf-8-sig'), 
                       file_name=f"mawid_report_{datetime.date.today()}.csv", mime='text/csv')
else:
    st.info("لا توجد مهام حالية.")
