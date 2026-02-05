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
    st.title("🔐 صفحة تسحيل الدخول لمهام إدارة موعد")
    u_email = st.text_input("أدخل بريدك الإلكتروني:")
    if st.button("دخول"):
        if u_email.lower() in [e.lower() for e in EMAILS_MAP.values()]:
            st.session_state.authenticated = True
            st.session_state.user_email = u_email.lower()
            st.rerun()
        else:
            st.error("البريد غير مسجل.")
    st.stop()

# --- 3. إدارة البيانات (هيكل نظيف بدون تكرار) ---
DB_FILE = "radiology_tasks.csv"
COLUMNS = [
    "المهمة", "المسؤول", "تاريخ البدء", "وقت البدء", 
    "الأيام المتوقعة", "تاريخ الإنجاز المتوقع", "الحالة",
    "تاريخ الإنجاز الفعلي", "وقت الإنجاز الفعلي"
]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE).fillna("")

def save_data(df_to_save):
    df_to_save.to_csv(DB_FILE, index=False)

# --- 4. واجهة التطبيق ---
st.title(" نظام إدارة مهام برنامج موعد")
df = load_data()

# نموذج الإضافة المطور
with st.expander("➕ إضافة مهمة جديدة"):
    with st.form("task_form", clear_on_submit=True):
        t_name = st.text_input("اسم المهمة")
        t_member = st.selectbox("تعيين إلى", list(EMAILS_MAP.keys()))
        t_days = st.number_input("عدد الأيام المتوقعة للإنجاز", min_value=1, step=1)
        
        # الحساب التلقائي يظهر هنا للمستخدم
        expected_date = datetime.date.today() + datetime.timedelta(days=t_days)
        st.write(f"📅 موعد الإنجاز المتوقع: **{expected_date}**")
        
        if st.form_submit_button("حفظ وإرسال التنبيهات"):
            if t_name:
                now = datetime.datetime.now()
                new_row = {
                    "المهمة": t_name, 
                    "المسؤول": t_member, 
                    "تاريخ البدء": str(now.date()), 
                    "وقت البدء": now.strftime("%H:%M:%S"), 
                    "الأيام المتوقعة": t_days, 
                    "تاريخ الإنجاز المتوقع": str(expected_date),
                    "الحالة": "قيد التنفيذ",
                    "تاريخ الإنجاز الفعلي": "", 
                    "وقت الإنجاز الفعلي": ""
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success(f"✅ تم الحفظ! الموعد المتوقع: {expected_date}")
                st.rerun()

# --- 5. لوحة المتابعة ---
st.divider()
st.subheader("📊 لوحة المتابعة")
if not df.empty:
    # عرض الجدول وتأمين الأعمدة
    edited_df = st.data_editor(
        df,
        column_config={
            "المهمة": st.column_config.Column(disabled=True),
            "المسؤول": st.column_config.Column(disabled=True),
            "تاريخ البدء": st.column_config.Column(disabled=True),
            "وقت البدء": st.column_config.Column(disabled=True),
            "الأيام المتوقعة": st.column_config.Column(disabled=True),
            "تاريخ الإنجاز المتوقع": st.column_config.Column(disabled=True),
            "تاريخ الإنجاز الفعلي": st.column_config.Column(disabled=True),
            "وقت الإنجاز الفعلي": st.column_config.Column(disabled=True),
            "الحالة": st.column_config.SelectboxColumn("الحالة", options=["قيد التنفيذ", "مكتمل", "متأخر"], required=True)
        },
        use_container_width=True
    )
    
    if st.button("تحديث وحفظ الحالات"):
        now = datetime.datetime.now()
        for index, row in edited_df.iterrows():
            if row["الحالة"] == "مكتمل" and row["تاريخ الإنجاز الفعلي"] == "":
                edited_df.at[index, "تاريخ الإنجاز الفعلي"] = str(now.date())
                edited_df.at[index, "وقت الإنجاز الفعلي"] = now.strftime("%H:%M:%S")
            elif row["الحالة"] == "قيد التنفيذ":
                edited_df.at[index, "تاريخ الإنجاز الفعلي"] = ""
                edited_df.at[index, "وقت الإنجاز الفعلي"] = ""
        
        save_data(edited_df)
        st.success("✅ تم توثيق الإنجاز الفعلي!")
        st.rerun()

# --- 6. لوحة المسؤول (الحذف) ---
if st.session_state.user_email == "r3-mawid@gmail.com":
    st.sidebar.title("🛠️ لوحة المسؤول")
    with st.sidebar.expander("🗑️ حذف المهام"):
        if not df.empty:
            to_delete = st.selectbox("اختر مهمة لحذفها:", df["المهمة"].tolist())
            if st.button("حذف نهائي"):
                df = df[df["المهمة"] != to_delete]
                save_data(df)
                st.error(f"تم حذف {to_delete}")
                st.rerun()
    
    st.sidebar.download_button("📥 تحميل النسخة الاحتياطية", df.to_csv(index=False).encode('utf-8-sig'), f"mawid_tasks_{datetime.date.today()}.csv")

