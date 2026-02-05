import streamlit as st
import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText

# --- 1. دالة إرسال الإيميل ---
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
    except:
        return False

# --- 2. إدارة قاعدة البيانات ---
if not os.path.exists("tasks.csv"):
    df_init = pd.DataFrame(columns=["المهمة", "المسؤول", "الموعد النهائي", "الحالة"])
    df_init.to_csv("tasks.csv", index=False)

# --- 3. واجهة التطبيق ---
st.set_page_config(page_title="نظام موعد الذكي", page_icon="📅")
st.title(" نظام إدارة مهام برنامج موعد")

# خريطة الإيميلات
emails_map = {
    "د.عادل الحربي": "adilalharby@gmail.com",
    "بريده المطيري": "buraida990@gmail.com",
    "منى العتيبي": "muna@example.com",
    "هويدي الصنقر": "hwidii@gmail.com"
}

# نموذج الإضافة
with st.form("task_form", clear_on_submit=True):
    st.subheader("➕ إضافة مهمة جديدة")
    t_name = st.text_input("اسم المهمة")
    t_member = st.selectbox("المسؤول", list(emails_map.keys()))
    t_due = st.date_input("الموعد النهائي المتوقع", datetime.date.today())
    
    submitted = st.form_submit_button("حفظ وإرسال تنبيه")
    
    if submitted and t_name:
        new_row = [t_name, t_member, str(t_due), "قيد التنفيذ"]
        pd.DataFrame([new_row], columns=["المهمة", "المسؤول", "الموعد النهائي", "الحالة"]).to_csv("tasks.csv", mode='a', header=False, index=False)
        
        # تنبيه المسؤول عن المهمة
        body = f"تم تكليفك بمهمة: {t_name}\nالموعد: {t_due}"
        send_email("🔔 مهمة جديدة - نظام موعد", body, emails_map[t_member])
        st.success("✅ تم الحفظ وتنبيه الزميل")

# --- 4. لوحة المتابعة (التعديل الذكي) ---
st.divider()
st.subheader("📊 متابعة وتحديث الحالات")

df = pd.read_csv("tasks.csv")

if not df.empty:
    # إضافة القائمة المنسدلة للحالة داخل الجدول
    edited_df = st.data_editor(
        df,
        column_config={
            "الحالة": st.column_config.SelectboxColumn(
                "الحالة",
                options=["قيد التنفيذ", "مكتمل", "جاري التواصل", "متأخر"],
                required=True,
            )
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if st.button("تحديث وحفظ التغييرات"):
        edited_df.to_csv("tasks.csv", index=False)
        
        # تنبيه "هويدي الصنقر" عند كل تعديل في الجدول
        h_email = emails_map["هويدي الصنقر"]
        h_body = f"مرحباً هويدي، تم إجراء تعديل جديد على جدول المهام في الموقع بتاريخ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_email("⚠️ تحديث في نظام موعد", h_body, h_email)
        
        st.success("✅ تم التحديث وتنبيه هويدي بالبريد")
        st.rerun()
else:
    st.info("لا توجد مهام حالياً.")
