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

# --- 3. إدارة البيانات (إضافة العمود الجديد للهيكل) ---
DB_FILE = "radiology_tasks.csv"
COLUMNS = ["المهمة", "المسؤول", "تاريخ التسجيل", "وقت الإدخال", "الأيام المتوقعة", "تاريخ الإنجاز المتوقع", "الحالة"]

if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=COLUMNS)
    df_init.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

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
st.title(" نظام إدارة مهام برنامج موعد")
df = load_data()

# نموذج الإضافة
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        col1, col2 = st.columns(2)
        with col1: t_start_date = st.date_input("تاريخ تسجيل المهمة", datetime.date.today())
        with col2: t_start_time = st.time_input("وقت إدخال المهمة", datetime.time(9, 0))
        
        t_days = st.number_input("الأيام المتوقعة لإنهاء المهمة", min_value=1, step=1)
        
        # الحساب التلقائي لتاريخ الإنجاز
        t_due_date = t_start_date + datetime.timedelta(days=t_days)
        st.info(f"💡 تاريخ الإنجاز المتوقع سيكون في: {t_due_date}")

        if st.form_submit_button("حفظ وإرسال تنبيه"):
            if t_name:
                new_row = {
                    "المهمة": t_name, 
                    "المسؤول": t_member, 
                    "تاريخ التسجيل": str(t_start_date), 
                    "وقت الإدخال": str(t_start_time), 
                    "الأيام المتوقعة": t_days, 
                    "تاريخ الإنجاز المتوقع": str(t_due_date),
                    "الحالة": "قيد التنفيذ"
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                
                # تحديث نص الإيميل ليشمل التاريخ المحسوب
                email_body = f"تم تكليفك بمهمة جديدة:\n\nالمهمة: {t_name}\nتاريخ التسجيل: {t_start_date}\nالأيام المتاحة: {t_days}\nتاريخ الإنجاز النهائي المطلوب: {t_due_date}"
                
                send_email("🔔 مهمة جديدة - موعد", email_body, EMAILS_MAP[t_member])
                send_email("⚠️ تحديث نظام", f"تم إضافة مهمة جديدة بواسطة {st.session_state.user_email}", EMAILS_MAP["هويدي الصنقر"])
                
                st.success(f"✅ تم الحفظ! موعد الإنجاز: {t_due_date}")
                st.rerun()

# --- 6. لوحة المتابعة ---
st.divider()
st.subheader("📊 لوحة المتابعة")
if not df.empty:
    # قفل جميع الأعمدة عدا الحالة
    edited_df = st.data_editor(
        df,
        column_config={
            "المهمة": st.column_config.Column(disabled=True),
            "المسؤول": st.column_config.Column(disabled=True),
            "تاريخ التسجيل": st.column_config.Column(disabled=True),
            "وقت الإدخال": st.column_config.Column(disabled=True),
            "الأيام المتوقعة": st.column_config.Column(disabled=True),
            "تاريخ الإنجاز المتوقع": st.column_config.Column(disabled=True),
            "الحالة": st.column_config.SelectboxColumn("الحالة", options=["قيد التنفيذ", "مكتمل", "متأخر"], required=True)
        },
        use_container_width=True, num_rows="fixed"
    )
    
    if st.button("حفظ التغييرات"):
        save_data(edited_df)
        send_email("⚠️ تعديل حالات", f"قام {st.session_state.user_email} بتحديث الحالات.", EMAILS_MAP["هويدي الصنقر"])
        st.success("✅ تم تحديث البيانات!")
        st.rerun()

    st.download_button(label="📥 تحميل نسخة احتياطية (Excel/CSV)", data=df.to_csv(index=False).encode('utf-8-sig'), 
                       file_name=f"tasks_backup_{datetime.date.today()}.csv", mime='text/csv')
else:
    st.info("لا توجد مهام حالية.")
