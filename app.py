import streamlit as st
import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText

# --- 1. دالة إرسال الإيميل الآمنة ---
def send_email(task_name, assignee, due_date):
    try:
        sender = st.secrets["email_settings"]["sender_email"]
        password = st.secrets["email_settings"]["app_password"]
        
        # خريطة الإيميلات (هنا قمنا بربط كل اسم بإيميله الحقيقي)
        emails_map = {
            "د.عادل الحربي": "adilalharby@gmail.com",
            "بريده المطيري": "buraida990@gmail.com",
            "منى العتيبي": "muna@example.com",
            "هويدي الصنقر": "hwidii@gmail.com"
        }
        
        receiver = emails_map.get(assignee, sender)
        
        msg = MIMEText(f"مرحباً {assignee}، تم تكليفك بمهمة جديدة في نظام موعد: {task_name}. الموعد النهائي: {due_date}")
        msg['Subject'] = '🔔 تنبيه مهمة جديدة - برنامج موعد'
        msg['From'] = sender
        msg['To'] = receiver

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        return False

# --- 2. إدارة قاعدة البيانات (CSV) ---
if not os.path.exists("tasks.csv"):
    df_init = pd.DataFrame(columns=["المهمة", "المسؤول", "الموعد النهائي", "الحالة"])
    df_init.to_csv("tasks.csv", index=False)

# --- 3. واجهة التطبيق ---
st.set_page_config(page_title="نظام موعد الذكي", page_icon="📅")
st.title("🩻 نظام إدارة مهام برنامج موعد")

# نموذج الإضافة
with st.form("task_form", clear_on_submit=True):
    st.subheader("➕ إضافة مهمة جديدة")
    t_name = st.text_input("اسم المهمة")
    t_member = st.selectbox("المسؤول", ["د.عادل الحربي", "بريده المطيري", "منى العتيبي", "هويدي الصنقر"])
    t_due = st.date_input("الموعد النهائي المتوقع", datetime.date.today())
    
    submitted = st.form_submit_button("إرسال التنبيه وحفظ المهمة")
    
    if submitted:
        if t_name:
            # حفظ في CSV
            new_row = [t_name, t_member, str(t_due), "قيد التنفيذ"]
            df_new = pd.DataFrame([new_row], columns=["المهمة", "المسؤول", "الموعد النهائي", "الحالة"])
            df_new.to_csv("tasks.csv", mode='a', header=False, index=False)
            
            # إرسال الإيميل الحقيقي
            if send_email(t_name, t_member, t_due):
                st.success(f"✅ تم الحفظ وإرسال إيميل إلى: {t_member}")
            else:
                st.warning("✅ تم حفظ المهمة، ولكن تعذر إرسال الإيميل (تأكد من إعدادات Secrets)")
        else:
            st.error("يرجى كتابة اسم المهمة")

# --- 4. لوحة المتابعة التفاعلية ---
st.divider()
st.subheader("📊 لوحة متابعة سير العمل (تفاعلية)")
if os.path.exists("tasks.csv"):
    df_display = pd.read_csv("tasks.csv")
    if not df_display.empty:
        # جدول يسمح بتعديل الحالة مباشرة
        edited_df = st.data_editor(df_display, use_container_width=True)
        
        if st.button("حفظ التغييرات في الجدول"):
            edited_df.to_csv("tasks.csv", index=False)
            st.success("✅ تم تحديث البيانات بنجاح!")
            st.rerun()
    else:
        st.info("لا توجد مهام حالياً.")
