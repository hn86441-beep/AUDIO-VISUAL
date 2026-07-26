# -*- coding: utf-8 -*-
"""
تطبيق ويب أكاديمي لإدارة وتحليل بيانات أطروحة دكتوراه:
"استراتيجيات وتحديات الترجمة السمعبصرية من العربية إلى الصينية
تطبيقًا على مسلسل (ما وراء الطبيعة)"

يشغَّل عبر:  streamlit run app.py
"""

import io
import json
import math
from datetime import datetime

import pandas as pd
import streamlit as st

# استيراد Plotly بأمان: إن لم تكن الحزمة مثبَّتة في بيئة النشر (خطأ شائع عند نسيان
# رفع requirements.txt أو وضعه في مسار غير جذر المستودع)، يتحوّل التطبيق تلقائيًا
# إلى رسوم بيانية بديلة مبنية داخليًا في Streamlit بدل أن يتعطل بالكامل.
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ModuleNotFoundError:
    PLOTLY_AVAILABLE = False

# ----------------------------------------------------------------------------
# إعدادات الصفحة العامة
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="الترجمة السمعبصرية | ما وراء الطبيعة",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# قوائم ثابتة: استراتيجيات الترجمة السمعبصرية (بناءً على أدبيات جوتليب وديريز وغيرهم)
# ----------------------------------------------------------------------------
TRANSLATION_STRATEGIES = [
    "الترجمة الحرفية (Literal Translation)",
    "التكييف الثقافي (Cultural Adaptation)",
    "الحذف (Omission / Deletion)",
    "الإضافة (Addition/Explicitation)",
    "التكثيف (Condensation)",
    "إعادة الصياغة (Paraphrase)",
    "الاقتراض (Borrowing/Transliteration)",
    "التعويض (Compensation)",
    "التعميم (Generalization)",
    "المعادلة الوظيفية (Functional Equivalence)",
]

CHALLENGE_TYPES = [
    "تحديات لغوية (تركيبية/نحوية)",
    "تحديات ثقافية (عادات، تعابير اصطلاحية)",
    "تحديات دينية/عقائدية (مفاهيم إسلامية-صينية)",
    "قيود تقنية (زمن العرض/عدد الأحرف)",
    "تحديات صوتية (تزامن الشفاه/الإيقاع)",
    "تحديات أسلوبية (نبرة، سخرية، عامية)",
    "أسماء أعلام ومصطلحات خاصة بالمسلسل",
    "تحديات دلالية (تعدد المعنى/الغموض)",
]

AI_THEORY_NOTES = {
    "جوتليب": "يصنّف Gottlieb (1992) استراتيجيات الترجمة السمعبصرية إلى عشر استراتيجيات "
               "أبرزها: التوسيع، الإدغام، النقل المباشر، التكثيف، الحذف، والفك. "
               "يمكن الاستشهاد به عند تحليل التكثيف والحذف في مشاهد الحوار السريع.",
    "ديريز": "تُميّز Díaz-Cintas & Remael (2007) بين القيود الرسمية (الزمانية والمكانية) "
              "والقيود اللغوية-النصية في الترجمة عبر السترجة والدبلجة، وهو إطار مناسب "
              "لتحليل التحديات التقنية في مسلسل ما وراء الطبيعة.",
    "نيومارك": "يميّز Newmark بين الترجمة الدلالية (Semantic) والترجمة التواصلية "
                "(Communicative)؛ مناسب لتفسير اختيارك بين الحرفية والتكييف الثقافي.",
    "فينوتي": "مفهوما 'الاستئناس' (Domestication) و'التغريب' (Foreignization) عند "
                "Venuti يفيدان في مناقشة كيفية تعامل المترجم مع العناصر الثقافية "
                "والدينية العربية عند نقلها إلى القارئ الصيني.",
    "بيرم": "تشير Berman إلى 'الميول التشويهية' (Deforming Tendencies) في الترجمة، وهي "
             "مفيدة لتحليل حالات فقدان الإيقاع أو التلاعب اللفظي بين العربية والصينية.",
}

SAMPLE_DATA = [
    {
        "رقم المشهد": 1,
        "الحوار بالعربية": "الحمد لله رب العالمين، ما شاء الله عليك يا ولدي.",
        "الترجمة الصينية": "感谢真主，愿真主保佑你，我的孩子。",
        "استراتيجية الترجمة": "التكييف الثقافي (Cultural Adaptation)",
        "نوع التحدي": "تحديات دينية/عقائدية (مفاهيم إسلامية-صينية)",
        "ملاحظات": "تعبير ديني شائع لا مقابل مباشر له في الثقافة الصينية.",
    },
    {
        "رقم المشهد": 2,
        "الحوار بالعربية": "يا رب استرها علينا، إحنا ما لنا حد غيرك.",
        "الترجمة الصينية": "主啊，求你保佑我们，我们别无依靠。",
        "استراتيجية الترجمة": "المعادلة الوظيفية (Functional Equivalence)",
        "نوع التحدي": "تحديات ثقافية (عادات، تعابير اصطلاحية)",
        "ملاحظات": "استبدال الصيغة الدعائية بمكافئ وظيفي يحافظ على القصدية.",
    },
    {
        "رقم المشهد": 3,
        "الحوار بالعربية": "قال الشيخ: هذا مسّ من الجن، لازم رقية شرعية.",
        "الترجمة الصينية": "长老说：这是精灵附体，需要念经驱邪。",
        "استراتيجية الترجمة": "التعميم (Generalization)",
        "نوع التحدي": "تحديات لغوية (تركيبية/نحوية)",
        "ملاحظات": "تعميم مفهوم 'الرقية الشرعية' إلى مايقابله تقريبًا في الثقافة الصينية الشعبية.",
    },
    {
        "رقم المشهد": 4,
        "الحوار بالعربية": "والله ما هذا إلا شغل شيطاني، خبروا الجيران بسرعة!",
        "الترجمة الصينية": "这绝对是恶魔的把戏，快去告诉邻居们！",
        "استراتيجية الترجمة": "الحذف (Omission / Deletion)",
        "نوع التحدي": "قيود تقنية (زمن العرض/عدد الأحرف)",
        "ملاحظات": "حذف القسم 'والله' نظرًا لضيق زمن ظهور الترجمة على الشاشة.",
    },
    {
        "رقم المشهد": 5,
        "الحوار بالعربية": "يا خرابي عليك، وين رايح بهالوقت المتأخر؟",
        "الترجمة الصينية": "你这是要害死自己啊，这么晚了你要去哪儿？",
        "استراتيجية الترجمة": "إعادة الصياغة (Paraphrase)",
        "نوع التحدي": "تحديات أسلوبية (نبرة، سخرية، عامية)",
        "ملاحظات": "إعادة صياغة تعبير عامي بلهجة تحذيرية إلى ما يقابله دلاليًا.",
    },
]

# ----------------------------------------------------------------------------
# إدارة الحالة (Session State)
# ----------------------------------------------------------------------------
if "corpus_df" not in st.session_state:
    st.session_state.corpus_df = pd.DataFrame(SAMPLE_DATA)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "theme" not in st.session_state:
    st.session_state.theme = "فاتح (Light)"


# ----------------------------------------------------------------------------
# التنسيق البصري (CSS) — دعم العربية RTL + الخط الصيني + الوضع الليلي/النهاري
# ----------------------------------------------------------------------------
def inject_css(dark: bool):
    bg = "#0e1117" if dark else "#f7f5f2"
    card_bg = "#1b1f27" if dark else "#ffffff"
    text_color = "#eaeaea" if dark else "#1a1a1a"
    accent = "#c9a227"  # ذهبي أكاديمي
    accent2 = "#6b4f9e"  # بنفسجي هادئ

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;600;700&family=Noto+Sans+SC:wght@400;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Noto Naskh Arabic', 'Noto Sans SC', sans-serif !important;
        }}

        .stApp {{
            background-color: {bg};
            color: {text_color};
        }}

        /* دعم النص العربي RTL بشكل عام */
        .rtl-text {{
            direction: rtl;
            text-align: right;
            font-family: 'Noto Naskh Arabic', sans-serif;
        }}

        /* دعم عرض النص الصيني بخط واضح */
        .zh-text {{
            direction: ltr;
            text-align: left;
            font-family: 'Noto Sans SC', sans-serif;
        }}

        .main-card {{
            background-color: {card_bg};
            padding: 1.4rem 1.6rem;
            border-radius: 14px;
            border: 1px solid rgba(201,162,39,0.25);
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
        }}

        h1, h2, h3 {{
            color: {accent} !important;
        }}

        .badge {{
            display: inline-block;
            background-color: {accent2};
            color: white;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            margin-inline-end: 6px;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {card_bg};
        }}

        .chat-bubble-user {{
            background-color: {accent2};
            color: white;
            padding: 10px 14px;
            border-radius: 14px 14px 2px 14px;
            margin: 6px 0;
            direction: rtl;
            text-align: right;
        }}
        .chat-bubble-ai {{
            background-color: rgba(201,162,39,0.15);
            color: {text_color};
            padding: 10px 14px;
            border-radius: 14px 14px 14px 2px;
            margin: 6px 0;
            direction: rtl;
            text-align: right;
            border: 1px solid rgba(201,162,39,0.35);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# محرك المساعد الذكي الأكاديمي (قائم على القواعد + نظريات الترجمة السمعبصرية)
# لا يتطلب أي مفتاح API خارجي — مبني على أدبيات AVT المعروفة، ليعمل مباشرة على
# Streamlit Cloud دون إعدادات إضافية.
# ----------------------------------------------------------------------------
def ai_assistant_reply(user_text: str, df: pd.DataFrame) -> str:
    text = user_text.strip()
    lower = text.lower()

    # أسئلة عن نظرية معينة
    for key, note in AI_THEORY_NOTES.items():
        if key in text:
            return f"📚 **{key}**: {note}"

    # طلب إحصائية سريعة
    if any(k in text for k in ["إحصائ", "نسبة", "توزيع", "كم عدد"]):
        if len(df) == 0:
            return "لا توجد بيانات بعد في المدوّنة (Corpus) لتحليلها. أضف بعض الأمثلة أولًا في صفحة قاعدة البيانات."
        top_strategy = df["استراتيجية الترجمة"].value_counts().idxmax()
        top_challenge = df["نوع التحدي"].value_counts().idxmax()
        return (
            f"📊 بناءً على {len(df)} مثالًا مُسجَّلًا حاليًا:\n\n"
            f"- الاستراتيجية الأكثر استخدامًا: **{top_strategy}**\n"
            f"- التحدي الأكثر تكرارًا: **{top_challenge}**\n\n"
            "يمكنك مراجعة صفحة 'لوحة الإحصائيات' لرؤية الرسوم البيانية الكاملة."
        )

    # اقتراح خطة كتابة / هيكلة فصل
    if any(k in text for k in ["خطة", "هيكل", "فصل", "كيف أكتب", "منهجية"]):
        return (
            "✍️ **مقترح لهيكلة الفصل التحليلي:**\n\n"
            "1) تمهيد نظري موجز عن الترجمة السمعبصرية (AVT) وخصائصها.\n"
            "2) عرض تصنيف الاستراتيجيات المعتمد (جوتليب / ديريز-ريمايل).\n"
            "3) تحليل كمي: نسب استخدام كل استراتيجية عبر الحلقات المختارة.\n"
            "4) تحليل كيفي: نماذج مختارة (مشاهد دينية، مشاهد عامية، مشاهد رعب).\n"
            "5) تصنيف التحديات (لغوية/ثقافية/دينية/تقنية) مع أمثلة موازية عربي-صيني.\n"
            "6) مناقشة النتائج في ضوء ثنائية الاستئناس/التغريب عند فينوتي.\n"
            "7) خاتمة الفصل وربطها بإشكالية الأطروحة العامة.\n\n"
            "💡 فكرة إبداعية: خصّص جدولًا مقارنًا لكل مشهد ديني يوضح كيف عومل "
            "المصطلح الإسلامي (تكييف/تعميم/حذف) — هذا يميّز أطروحتك لأن المسلسل "
            "مشحون بمفردات دينية-شعبية نادرًا ما دُرست في الترجمة نحو الصينية."
        )

    # اقتراح عنوان فرعي أو زاوية بحثية جديدة
    if any(k in text for k in ["فكرة", "أفكار", "زاوية", "إضافة", "إبداع"]):
        return (
            "💡 **أفكار إبداعية لإثراء الأطروحة:**\n\n"
            "- مقارنة نسخة الدبلجة بنسخة السترجة (إن وُجدت) لنفس المشاهد الدينية.\n"
            "- دراسة استقبال الجمهور الصيني عبر تعليقات منصات البث (تحليل خطاب مصغّر).\n"
            "- بناء 'معجم مصغّر' للمصطلحات الدينية والشعبية العربية ومقابلاتها الصينية "
            "المقترحة، كملحق للأطروحة.\n"
            "- تتبع تطور استراتيجية الحذف عبر المواسم: هل يتزايد الحذف كلما زاد "
            "الكثافة الحوارية؟\n"
            "- مقارنة ذاتية بين مترجمين مختلفين إن توفرت أكثر من نسخة ترجمة للمسلسل.\n"
            "- ربط النتائج الكمية بنظرية 'قواعد الترجمة الابتدائية والثانوية' عند Toury."
        )

    # ترحيب عام / إرشاد
    if any(k in text for k in ["مرحبا", "السلام", "أهلا", "hello"]):
        return (
            "أهلًا بك 👋 أنا مساعدك الأكاديمي لتحليل الترجمة السمعبصرية. "
            "يمكنك سؤالي عن: نظريات AVT (جوتليب، ديريز، نيومارك، فينوتي، بيرم)، "
            "إحصائيات المدوّنة الحالية، أفكار إبداعية للأطروحة، أو مقترح لهيكلة فصل."
        )

    # افتراضي: تحليل نصي عام لأي حوار يُلصق في المحادثة
    if len(text) > 15:
        detected = []
        if any(w in text for w in ["الله", "رب", "دين", "شيخ", "رقية", "جن"]):
            detected.append("مضمون ديني/عقائدي محتمل → فكّر في التكييف الثقافي أو التعميم.")
        if any(w in text for w in ["يا خرابي", "والله", "شو", "ليش", "وين"]):
            detected.append("أسلوب عامي/لهجي → قد يتطلب إعادة الصياغة أو التعويض الأسلوبي.")
        if len(text) > 120:
            detected.append("النص طويل نسبيًا → احتمال الحاجة إلى التكثيف (Condensation) بسبب قيود الشاشة.")
        if not detected:
            detected.append("لم يظهر نمط لغوي أو ديني واضح؛ يمكن تصنيفه ضمن الترجمة الحرفية أو المعادلة الوظيفية.")
        return "🔎 **تحليل مبدئي للنص المُدخل:**\n\n" + "\n".join(f"- {d}" for d in detected)

    return (
        "يمكنك سؤالي عن نظرية ترجمة (اكتب مثلاً: جوتليب)، أو طلب 'إحصائيات'، "
        "أو 'أفكار' لإثراء الأطروحة، أو 'خطة' لهيكلة فصل تحليلي."
    )


# ----------------------------------------------------------------------------
# الشريط الجانبي: التنقل + إعدادات المظهر
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎬 أطروحة الترجمة السمعبصرية")
    st.markdown("##### *ما وراء الطبيعة* — عربي ⇄ صيني")
    st.divider()

    page = st.radio(
        "التنقل بين الصفحات",
        [
            "🏠 الصفحة الرئيسية",
            "📚 قاعدة البيانات والتحليل",
            "📊 لوحة الإحصائيات",
            "🤖 المساعد الذكي",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.session_state.theme = st.selectbox(
        "🎨 المظهر", ["فاتح (Light)", "داكن (Dark)"],
        index=0 if st.session_state.theme == "فاتح (Light)" else 1,
    )
    st.caption("تطبيق أكاديمي مُعدّ لدعم أطروحة الدكتوراه — جاهز للنشر على Streamlit Cloud.")

inject_css(dark=(st.session_state.theme == "داكن (Dark)"))

if not PLOTLY_AVAILABLE:
    st.warning(
        "⚠️ حزمة `plotly` غير مثبَّتة في هذه البيئة، لذلك تعمل الرسوم البيانية "
        "حاليًا بوضع بديل (Streamlit Charts). للتفعيل الكامل: تأكد أن ملف "
        "`requirements.txt` موجود في **جذر المستودع** بجانب `app.py` مباشرة "
        "(وليس داخل مجلد فرعي)، ثم من لوحة التطبيق على Streamlit Cloud اضغط "
        "على 'Manage app' ← ⋮ ← 'Reboot app' لإعادة تثبيت الحزم.",
        icon="⚠️",
    )

# ----------------------------------------------------------------------------
# الصفحة 1: الصفحة الرئيسية
# ----------------------------------------------------------------------------
if page == "🏠 الصفحة الرئيسية":
    st.markdown('<div class="rtl-text">', unsafe_allow_html=True)
    st.title("📖 استراتيجيات وتحديات الترجمة السمعبصرية من العربية إلى الصينية")
    st.subheader("دراسة تطبيقية على مسلسل «ما وراء الطبيعة»")

    st.markdown(
        """
        <div class="main-card rtl-text">
        <h3>🎯 أهداف الأطروحة</h3>
        <ul>
        <li>رصد أبرز استراتيجيات الترجمة السمعبصرية المستخدمة في نقل حوارات المسلسل من العربية إلى الصينية.</li>
        <li>تصنيف التحديات (اللغوية، الثقافية، الدينية، التقنية) التي تواجه المترجم في هذا السياق.</li>
        <li>تحليل العلاقة بين طبيعة المحتوى الديني/الشعبي في المسلسل وخيارات المترجم الاستراتيجية.</li>
        <li>الإسهام في سد فجوة بحثية في دراسات الترجمة السمعبصرية بين العربية والصينية، وهو زوج لغوي أقل درسًا مقارنة بأزواج أوروبية.</li>
        <li>اقتراح إطار تحليلي مُهجّن يجمع بين تصنيف جوتليب للاستراتيجيات وثنائية الاستئناس/التغريب عند فينوتي.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    df = st.session_state.corpus_df
    with col1:
        st.metric("عدد الأمثلة المسجّلة", len(df))
    with col2:
        st.metric("عدد الاستراتيجيات المرصودة", df["استراتيجية الترجمة"].nunique() if len(df) else 0)
    with col3:
        st.metric("عدد أنواع التحديات", df["نوع التحدي"].nunique() if len(df) else 0)

    st.markdown(
        """
        <div class="main-card rtl-text">
        <h3>💡 لماذا هذا الموضوع مهم؟</h3>
        <p>مسلسل «ما وراء الطبيعة» يتميّز بكثافة المفردات الدينية والشعبية العربية
        (الاستعاذة، الأدعية، مصطلحات الجن والرقية)، وهو ما يجعله مادة غنية لاختبار
        قدرة الترجمة السمعبصرية على نقل هذه الطبقة الثقافية إلى جمهور صيني لا يمتلك
        بالضرورة الخلفية الدينية الإسلامية أو الشعبية العربية نفسها. هذا التطبيق
        يتيح لك توثيق كل مشهد، وتصنيفه، وتحليله إحصائيًا بشكل منهجي ومباشر.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-card rtl-text"><h3>🧭 دليل الاستخدام السريع</h3>'
        '<span class="badge">١</span> أضف أمثلة المشاهد في «قاعدة البيانات والتحليل» &nbsp;'
        '<span class="badge">٢</span> راجع الرسوم البيانية في «لوحة الإحصائيات» &nbsp;'
        '<span class="badge">٣</span> استشر «المساعد الذكي» لأفكار كتابة وتحليل &nbsp;'
        '<span class="badge">٤</span> صدّر بياناتك بصيغة CSV أو JSON لإرفاقها بالأطروحة'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# الصفحة 2: قاعدة البيانات والتحليل
# ----------------------------------------------------------------------------
elif page == "📚 قاعدة البيانات والتحليل":
    st.markdown('<div class="rtl-text">', unsafe_allow_html=True)
    st.title("📚 قاعدة البيانات والتحليل (Corpus & Analysis)")
    st.write("يمكنك هنا تعديل الجدول مباشرة، إضافة صفوف جديدة، حذف صفوف، أو استيراد/تصدير البيانات.")
    st.markdown("</div>", unsafe_allow_html=True)

    edited_df = st.data_editor(
        st.session_state.corpus_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "رقم المشهد": st.column_config.NumberColumn("رقم المشهد", min_value=1, step=1),
            "الحوار بالعربية": st.column_config.TextColumn("الحوار بالعربية", width="large"),
            "الترجمة الصينية": st.column_config.TextColumn("الترجمة الصينية", width="large"),
            "استراتيجية الترجمة": st.column_config.SelectboxColumn(
                "استراتيجية الترجمة", options=TRANSLATION_STRATEGIES
            ),
            "نوع التحدي": st.column_config.SelectboxColumn(
                "نوع التحدي", options=CHALLENGE_TYPES
            ),
            "ملاحظات": st.column_config.TextColumn("ملاحظات", width="large"),
        },
        key="corpus_editor",
    )
    st.session_state.corpus_df = edited_df

    st.divider()
    st.markdown('<div class="rtl-text"><h3>⬇️⬆️ الاستيراد والتصدير</h3></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        csv_bytes = edited_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 تصدير CSV",
            data=csv_bytes,
            file_name=f"corpus_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        json_bytes = edited_df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "📥 تصدير JSON",
            data=json_bytes,
            file_name=f"corpus_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with c3:
        uploaded = st.file_uploader("📤 استيراد بيانات (CSV / JSON)", type=["csv", "json"])
        if uploaded is not None:
            try:
                if uploaded.name.endswith(".csv"):
                    new_df = pd.read_csv(uploaded)
                else:
                    new_df = pd.read_json(uploaded)
                st.session_state.corpus_df = new_df
                st.success("✅ تم استيراد البيانات بنجاح. انتقل بين الصفحات لرؤية التحديث.")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ حدث خطأ أثناء الاستيراد: {e}")

# ----------------------------------------------------------------------------
# الصفحة 3: لوحة الإحصائيات
# ----------------------------------------------------------------------------
elif page == "📊 لوحة الإحصائيات":
    st.markdown('<div class="rtl-text">', unsafe_allow_html=True)
    st.title("📊 لوحة الإحصائيات (Analytics & Charts)")
    st.markdown("</div>", unsafe_allow_html=True)

    df = st.session_state.corpus_df

    if len(df) == 0:
        st.warning("لا توجد بيانات بعد. أضف أمثلة في صفحة «قاعدة البيانات والتحليل».")
    else:
        col1, col2 = st.columns(2)

        strat_counts = df["استراتيجية الترجمة"].value_counts().reset_index()
        strat_counts.columns = ["الاستراتيجية", "التكرار"]
        chall_counts = df["نوع التحدي"].value_counts().reset_index()
        chall_counts.columns = ["نوع التحدي", "التكرار"]

        with col1:
            st.markdown('<div class="rtl-text"><h4>توزيع استراتيجيات الترجمة</h4></div>', unsafe_allow_html=True)
            if PLOTLY_AVAILABLE:
                fig1 = px.pie(
                    strat_counts, names="الاستراتيجية", values="التكرار",
                    hole=0.45, color_discrete_sequence=px.colors.sequential.Sunset,
                )
                fig1.update_layout(legend=dict(orientation="h"), margin=dict(t=10, b=10))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.bar_chart(strat_counts.set_index("الاستراتيجية"))

        with col2:
            st.markdown('<div class="rtl-text"><h4>توزيع أنواع التحديات</h4></div>', unsafe_allow_html=True)
            if PLOTLY_AVAILABLE:
                fig2 = px.bar(
                    chall_counts, x="التكرار", y="نوع التحدي", orientation="h",
                    color="التكرار", color_continuous_scale="Purples",
                )
                fig2.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=10, b=10))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.bar_chart(chall_counts.set_index("نوع التحدي"))

        st.divider()
        st.markdown('<div class="rtl-text"><h4>العلاقة بين الاستراتيجية ونوع التحدي</h4></div>', unsafe_allow_html=True)
        cross = df.groupby(["استراتيجية الترجمة", "نوع التحدي"]).size().reset_index(name="التكرار")
        if PLOTLY_AVAILABLE:
            fig3 = px.sunburst(
                cross, path=["نوع التحدي", "استراتيجية الترجمة"], values="التكرار",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig3.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig3, use_container_width=True)
        else:
            pivot = cross.pivot_table(
                index="نوع التحدي", columns="استراتيجية الترجمة",
                values="التكرار", fill_value=0,
            )
            st.dataframe(pivot, use_container_width=True)
            st.caption("عرض جدولي بديل (Cross-tabulation) — سيتحول تلقائيًا إلى مخطط Sunburst بمجرد تثبيت plotly.")

        st.markdown('<div class="rtl-text"><h4>عدد المشاهد المُحلَّلة تراكميًا</h4></div>', unsafe_allow_html=True)
        df_sorted = df.sort_values("رقم المشهد").copy()
        df_sorted["تراكمي"] = range(1, len(df_sorted) + 1)
        if PLOTLY_AVAILABLE:
            fig4 = px.line(df_sorted, x="رقم المشهد", y="تراكمي", markers=True)
            fig4.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.line_chart(df_sorted.set_index("رقم المشهد")["تراكمي"])

        # ------------------------------------------------------------------
        # لمسة إبداعية جديدة: "مؤشر التوازن الاستراتيجي" — مقياس مبسّط يقيس
        # مدى تنوّع استراتيجيات الترجمة المستخدمة (مؤشر Shannon للتنوع)،
        # وهو رقم يمكنك الاستشهاد به مباشرة في فصل التحليل الكمي بالأطروحة.
        # ------------------------------------------------------------------
        st.divider()
        st.markdown('<div class="rtl-text"><h4>🧮 مؤشر التنوع الاستراتيجي (Shannon Diversity Index)</h4></div>', unsafe_allow_html=True)
        probs = (strat_counts["التكرار"] / strat_counts["التكرار"].sum()).values
        shannon = -sum(p * math.log(p) for p in probs if p > 0)
        max_shannon = math.log(len(TRANSLATION_STRATEGIES))
        normalized = (shannon / max_shannon) if max_shannon > 0 else 0
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("مؤشر التنوع (0–1)", f"{normalized:.2f}")
        with c2:
            st.markdown(
                '<div class="rtl-text">'
                "قيمة قريبة من <b>1</b> تعني أن المترجم استخدم استراتيجيات متنوعة "
                "دون هيمنة واضحة لاستراتيجية واحدة، بينما قيمة قريبة من <b>0</b> "
                "تعني اعتمادًا شبه حصري على استراتيجية واحدة. هذا مؤشر إحصائي "
                "بسيط يمكن ذكره في فصل النتائج كدليل كمّي على 'مرونة' أو 'تحفظ' "
                "المترجم في التعامل مع النص."
                "</div>",
                unsafe_allow_html=True,
            )

# ----------------------------------------------------------------------------
# الصفحة 4: المساعد الذكي
# ----------------------------------------------------------------------------
elif page == "🤖 المساعد الذكي":
    st.markdown('<div class="rtl-text">', unsafe_allow_html=True)
    st.title("🤖 المساعد الذكي للبحث الأكاديمي")
    st.write(
        "اسأل عن نظريات الترجمة السمعبصرية، أو اطلب إحصائيات سريعة عن مدوّنتك، "
        "أو استشره في أفكار إبداعية وخطة كتابة الفصول."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("💡 أمثلة على أسئلة يمكن طرحها"):
        st.markdown(
            """
            - "حدثني عن جوتليب"
            - "أعطني إحصائيات عن المدوّنة الحالية"
            - "أفكار لإثراء الأطروحة"
            - "اقترح لي خطة لكتابة فصل التحليل"
            - أو الصق حوارًا عربيًا وسأحلل لك نمطه اللغوي/الديني المحتمل
            """
        )

    for msg in st.session_state.chat_history:
        css_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
        prefix = "🧑‍🎓 أنت" if msg["role"] == "user" else "🤖 المساعد"
        st.markdown(
            f'<div class="{css_class}"><b>{prefix}:</b><br>{msg["content"]}</div>',
            unsafe_allow_html=True,
        )

    user_input = st.chat_input("اكتب سؤالك هنا...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        reply = ai_assistant_reply(user_input, st.session_state.corpus_df)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ مسح المحادثة"):
            st.session_state.chat_history = []
            st.rerun()

# ----------------------------------------------------------------------------
# تذييل الصفحة
# ----------------------------------------------------------------------------
st.divider()
st.caption(
    "© مشروع أكاديمي مُعدّ كأداة مساعدة لأطروحة دكتوراه في الترجمة السمعبصرية — "
    "قابل للتعديل والتخصيص الكامل حسب حاجة الباحث."
)
