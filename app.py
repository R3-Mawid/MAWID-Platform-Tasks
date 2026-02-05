import streamlit as st
import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText

# --- دالة إرسال الإيميل الآمنة ---
def send_email(task_name, assignee, due_date):
    # هنا نقوم بجلب البيانات من Secrets بدلاً من كتابتها في الكود
    try:
        sender = st.secrets["email_settings"]["sender_email"]
        password = st.secrets["email_settings"]["app_password"]
        
        # مصفوفة إيميلات الزملاء (يمكنك تحديثها بإيميلاتهم الحقيقية)
        emails = {
            "د.عادل الحربي": "adilalharby@gmail.com",
            "بريده المطيري": "buraida990@gmail.com",
            "منى العتيبي": "muna@example.com",
            "هويدي الصنقر": "hwidii@gmail.com"
        }
        receiver = emails.get(assignee, sender) # إذا لم يجد الإيميل يرسل لنفسه
        
        msg = MIMEText(f"مرحباً {assignee}، تم تكليفك بمهمة: {task_name}. الموعد النهائي: {due_date}")
        msg['Subject'] = 'تنبيه مهمة جديدة - برنامج موعد'
        msg['From'] = sender
        msg['To'] = receiver

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        return False

# --- إدارة قاعدة البيانات البسيطة (CSV) ---
if not os.path.exists("tasks.csv"):
    df_init = pd.DataFrame(columns=["المهمة", "المسؤول", "الموعد النهائي", "الحالة"])
    df_init.to_csv("tasks.csv", index=False)

# --- واجهة التطبيق ---
st.set_page_config(page_title="نظام موعد", page_icon="📅")
st.title("🩻 نظام إدارة مهام برنامج موعد")

with st.form("task_form", clear_on_submit=True):
    st.subheader("➕ إضافة مهمة جديدة")
    t_name = st.text_input("اسم المهمة")
    t_member = st.selectbox("المسؤول", ["د.عادل الحربي", "بريده المطيري", "منى العتيبي", "هويدي الصنقر"])
    t_due = st.date_input("الموعد النهائي المتوقع", datetime.date.today())
    
    submitted = st.form_submit_button("إضافة المهمة وتنبيه الزميل")
    
    if submitted:
        if t_name:
            # حفظ المهمة في الملف
            new_data = pd.DataFrame([[t_name, t_member, t_due, "قيد التنفيذ"]], 
                                    columns=["المهمة", "المسؤول", "الموعد النهائي", "الحالة"])
            new_data.to_csv("tasks.csv", mode='a', header=False, index=False)
            
            # محاولة إرسال الإيميل
            if send_email(t_name, t_member, t_due):
                st.success(f"✅ تم حفظ المهمة وإرسال إيميل لـ {t_member}")
            else:
                st.warning("✅ تم حفظ المهمة، ولكن فشل إرسال الإيميل (تأكد من إعدادات Secrets)")
        else:
            st.error("يرجى كتابة اسم المهمة")

# --- عرض المهام من الملف ---
st.divider()
st.subheader("📊 جدول متابعة المهام الحقيقي")
df_display = pd.read_csv("tasks.csv")
st.dataframe(df_display, use_container_width=True)
