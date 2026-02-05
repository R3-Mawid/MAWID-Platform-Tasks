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
    st.title("🔐 دخول لوحة تحكم مهام نظام موعد")
    u_email = st.text_input(" أدخل بريدك الإلكتروني:")
    if st.button("دخول"):
        if u_email.lower() in [e.lower() for e in EMAILS_MAP.values()]:
            st.session_state.authenticated = True
            st.session_state.user_email = u_email.lower()
            st.rerun()
        else:
            st.error("البريد غير مسجل.")
    st.stop()

# --- 3. إدارة البيانات ---
DB_FILE = "radiology_tasks.csv"
COLUMNS = ["المهمة", "المسؤول", "تاريخ البدء", "وقت البدء", "الأيام المتوقعة", "الموعد النهائي", "الحالة", "تاريخ الإنجاز الفعلي", "وقت الإنجاز الفعلي"]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE).fillna("")

def save_data(df_to_save):
    df_to_save.to_csv(DB_FILE, index=False)

# --- 4. واجهة التطبيق ---
st.title(" نظام إدارة مهام برنامج موعد")
df = load_data()

# [قسم إضافة المهمة - يبقى كما هو]
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        t_days = st.number_input("المدة المتوقعة (بالأيام)", min_value=1, step=1)
        if st.form_submit_button("حفظ وحماية"):
            if t_name:
                now = datetime.datetime.now()
                due_date = now.date() + datetime.timedelta(days=t_days)
                new_row = {"المهمة": t_name, "المسؤول": t_member, "تاريخ البدء": str(now.date()), "وقت البدء": now.strftime("%H:%M:%S"), "الأيام المتوقعة": t_days, "الموعد النهائي": str(due_date), "الحالة": "قيد التنفيذ", "تاريخ الإنجاز الفعلي": "", "وقت الإنجاز الفعلي": ""}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("✅ تم الحفظ")
                st.rerun()

# --- 5. لوحة المتابعة (التعديل) ---
st.divider()
st.subheader("📊 لوحة المتابعة")
if not df.empty:
    edited_df = st.data_editor(df, use_container_width=True, disabled=["المهمة", "المسؤول", "تاريخ البدء", "وقت البدء", "الأيام المتوقعة", "الموعد النهائي", "تاريخ الإنجاز الفعلي", "وقت الإنجاز الفعلي"])
    if st.button("تحديث الحالات"):
        save_data(edited_df)
        st.success("✅ تم التحديث")
        st.rerun()

# --- 6. لوحة تحكم المسؤول (للحذف) ---
# تظهر فقط إذا كان المستخدم هو المسؤول r3-mawid@gmail.com
if st.session_state.user_email == "r3-mawid@gmail.com":
    st.sidebar.divider()
    with st.sidebar.expander("🗑️ إدارة وحذف المهام"):
        st.warning("هذه المنطقة مخصصة للمسؤول فقط")
        if not df.empty:
            task_to_delete = st.selectbox("اختر المهمة المراد حذفها:", df["المهمة"].unique())
            if st.button("حذف المهمة المختارة نهائياً"):
                df = df[df["المهمة"] != task_to_delete]
                save_data(df)
                st.error(f"❌ تم حذف مهمة: {task_to_delete}")
                st.rerun()
            
            if st.button("⚠️ مسح جميع المهام (إفراغ الجدول)"):
                if st.checkbox("أؤكد رغبتي في مسح قاعدة البيانات بالكامل"):
                    df = pd.DataFrame(columns=COLUMNS)
                    save_data(df)
                    st.success("🧹 تم تنظيف الجدول بالكامل")
                    st.rerun()

    st.download_button(label="📥 تحميل نسخة احتياطية", data=df.to_csv(index=False).encode('utf-8-sig'), file_name=f"backup_{datetime.date.today()}.csv")

