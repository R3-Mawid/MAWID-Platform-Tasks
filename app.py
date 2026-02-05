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

# --- 3. إدارة البيانات ---
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
st.title("🩻 نظام إدارة مهام برنامج موعد")
df = load_data()

with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        t_days = st.number_input("عدد الأيام المتوقعة للإنجاز", min_value=1, step=1)
        
        if st.form_submit_button("حفظ وإرسال التنبيهات"):
            if t_name:
                # تسجيل الوقت والتاريخ الحالي تلقائياً
                now = datetime.datetime.now()
                current_date = now.date()
                current_time = now.strftime("%H:%M:%S")
                due_date = current_date + datetime.timedelta(days=t_days)
                
                new_row = {
                    "المهمة": t_name, 
                    "المسؤول": t_member, 
                    "تاريخ التسجيل": str(current_date), 
                    "وقت الإدخال": current_time, 
                    "الأيام المتوقعة": t_days, 
                    "تاريخ الإنجاز المتوقع": str(due_date),
                    "الحالة": "قيد التنفيذ"
                }
                
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                
                # إرسال الإيميلات
                email_body = (f"تفاصيل المهمة المسجلة:\n\n"
                              f"اسم المهمة: {t_name}\n"
                              f"المسؤول عنها: {t_member}\n"
                              f"تاريخ التسجيل: {current_date}\n"
                              f"وقت الإدخال: {current_time}\n"
                              f"المدة المحددة: {t_days} أيام\n"
                              f"تاريخ الإنجاز المطلوب: {due_date}")
                
                # 1. تنبيه للشخص المكلف
                send_email("🔔 مهمة جديدة مكلف بها", email_body, EMAILS_MAP[t_member])
                # 2. تنبيه لهويدي
                send_email("⚠️ إحاطة: مهمة جديدة في النظام", f"قام {st.session_state.user_email} بإضافة مهمة جديدة.\n\n{email_body}", EMAILS_MAP["هويدي الصنقر"])
                # 3. تنبيه لك (المسؤول)
                send_email("✅ تم تأكيد حفظ المهمة", f"تم تسجيل المهمة التالية بنجاح في قاعدة البيانات:\n\n{email_body}", EMAILS_MAP["المسؤول"])
                
                st.success(f"✅ تم الحفظ وتنبيه جميع الأطراف. موعد الإنجاز: {due_date}")
                st.rerun()

# --- لوحة المتابعة ---
st.divider()
st.subheader("📊 لوحة المتابعة")
if not df.empty:
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
        send_email("⚠️ تحديث حالات المهام", f"قام {st.session_state.user_email} بتحديث حالات العمل في الجدول.", EMAILS_MAP["هويدي الصنقر"])
        st.success("✅ تم تحديث البيانات بنجاح!")
        st.rerun()

    st.download_button(label="📥 تحميل النسخة الاحتياطية", data=df.to_csv(index=False).encode('utf-8-sig'), 
                       file_name=f"mawid_backup_{datetime.date.today()}.csv", mime='text/csv')
else:
    st.info("لا توجد مهام حالية.")
