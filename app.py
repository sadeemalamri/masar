import os
import json
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse

import streamlit as st
import google.generativeai as genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# 1) PAGE CONFIGURATION & CSS
# ============================================================
st.set_page_config(
    page_title="Masar",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
.stApp {
    background-color: #F7FBF8;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.header-container { text-align: center; margin-bottom: 20px; }
.header-title { color: #005A36; font-size: 32px; font-weight: bold; }
.header-subtitle { color: #555; font-size: 16px; }
.card-box {
    background-color: #F0F8F4;
    border: 1px solid #D6EADF;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,90,54,0.06);
}
.section-title { font-size: 18px; font-weight: bold; color: #1a202c; margin-bottom: 15px; }
.match-circle {
    width: 100px; height: 100px; border-radius: 50%; border: 6px solid #005A36;
    display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 auto 10px auto;
}
.match-percentage { font-size: 26px; font-weight: bold; color: #005A36; }
.match-label { font-size: 12px; color: #666; }
.skill-row { margin-bottom: 10px; }
.skill-label { display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 4px; }
.skill-bar-bg { background-color: #DDEFE4; border-radius: 4px; height: 7px; width: 100%; }
.skill-bar-fill { background-color: #005A36; height: 100%; border-radius: 4px; }
.badge { display: inline-block; background-color: #DFF2E6; color: #005A36; padding: 4px 12px; border-radius: 16px; font-size: 13px; margin: 3px; }
.timeline-card { background-color: #F8FCF9; border: 1px solid #D6EADF; border-radius: 10px; padding: 12px; text-align: center; }
.timeline-step {
    background-color: #005A36; color: white; width: 24px; height: 24px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center; font-size: 12px; margin-bottom: 8px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# 2) API KEY CONFIGURATION (GOOGLE GEMINI)
# ============================================================
def get_secret(name: str) -> str:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, "")

GEMINI_API_KEY = get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY was not found. Please add it to Streamlit Secrets or environment variables.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)


# ============================================================
# 3) TRANSLATIONS
# ============================================================
TRANSLATIONS = {
    "en": {
        "app_title": "Masar",
        "app_subtitle": "Discover the career path that fits your future in Saudi Arabia",
        "start_here": "Start Here",
        "label_major": "Preferred major",
        "label_edu": "Educational level",
        "label_interests": "Interests",
        "label_goal": "Your goal of development",
        "label_duration": "Time available for learning",
        "label_skills": "Your skills",
        "skills_placeholder": "e.g. Python, SQL, Excel",
        "analyze_btn": "Discover My Path",
        "system_status": "System Status",
        "status_waiting_input": "Waiting for user input.",
        "skills_needed": "Skills You Need",
        "waiting_input_short": "Waiting for your input...",
        "why_path": "Why This Path?",
        "suggested_path": "Your Suggested Path",
        "best_jobs": "Best Jobs For You",
        "dev_plan": "Development Plan",
        "hitl_title": "Confirm Your Approval",
        "hitl_desc": "Educational resources will be generated after your approval.",
        "approve_btn": "Approve Path",
        "reject_btn": "I Want to Edit My Data",
        "resources_title": "Suggested Educational Resources",
        "resources_waiting": "Waiting for user approval...",
        "memory_title": "Memory / Context",
        "memory_empty": "No recommendations saved in this session yet.",
        "match_label": "Match percentage",
        "verified_link": "Verified link",
        "no_resources": "No verified links were found at this time.",
        "month_label": "Month",
        "hitl_checkpoint": "HITL Checkpoint: The recommendation has been created. Review the path, then click 'Approve Path' to generate educational resources, or 'I Want to Edit My Data' to change your inputs.",
        "awaiting_approval": "Waiting for user approval...",
        "guardrail_stopped": "Request stopped by the protection system (Guardrail).",
        "analysis_error": "An error occurred during analysis:",
        "approved_status": "The recommendation was approved by the user, then Agent 3 ran to fetch learning resources.",
        "memory_saved": "Memory: The latest recommendation has been saved in the session memory. Saved path: {path}. Number of saved recommendations: {count}",
        "reset_message": "Edit your data, then click 'Discover My Path' again.",
        "required_msg": "Please enter your {field}.",
        "too_long_msg": "Your {field} entry is too long. Maximum {max} characters.",
    },
    "ar": {
        "app_title": "مسار",
        "app_subtitle": "اكتشف المسار المهني المناسب لمستقبلك في المملكة العربية السعودية",
        "start_here": "ابدأ من هنا",
        "label_major": "التخصص المفضل",
        "label_edu": "المستوى التعليمي",
        "label_interests": "الاهتمامات",
        "label_goal": "هدفك التطويري",
        "label_duration": "الوقت المتاح للتعلم",
        "label_skills": "مهاراتك الحالية",
        "skills_placeholder": "مثل: بايثون، SQL، إكسل",
        "analyze_btn": "اكتشف مساري",
        "system_status": "حالة النظام",
        "status_waiting_input": "في انتظار إدخال البيانات من المستخدم.",
        "skills_needed": "المهارات المطلوبة",
        "waiting_input_short": "في انتظار الإدخال...",
        "why_path": "لماذا هذا المسار؟",
        "suggested_path": "المسار المقترح",
        "best_jobs": "أفضل الوظائف لك",
        "dev_plan": "خطة التطوير",
        "hitl_title": "تأكيد الموافقة",
        "hitl_desc": "سيتم توليد المصادر التعليمية بعد موافقتك على المسار.",
        "approve_btn": "موافقة على المسار",
        "reject_btn": "أريد تعديل بياناتي",
        "resources_title": "المصادر التعليمية المقترحة",
        "resources_waiting": "في انتظار موافقة المستخدم...",
        "memory_title": "الذاكرة / السياق",
        "memory_empty": "لم يتم حفظ أي توصيات في هذه الجلسة حتى الآن.",
        "match_label": "نسبة التوافق",
        "verified_link": "رابط موثق",
        "no_resources": "لم يتم العثور على روابط موثقة في الوقت الحالي.",
        "month_label": "شهر",
        "hitl_checkpoint": "نقطة التحقق البشرية: تم إنشاء التوصية. راجع المسار ثم اضغط على 'موافقة على المسار' لتوليد المصادر التعليمية، أو 'أريد تعديل بياناتي' لتغيير المدخلات.",
        "awaiting_approval": "في انتظار موافقة المستخدم...",
        "guardrail_stopped": "تم إيقاف الطلب بواسطة نظام الحماية (Guardrail).",
        "analysis_error": "حدث خطأ أثناء التحليل:",
        "approved_status": "تمت الموافقة على التوصية من قبل المستخدم، وتم تشغيل الوكيل الثالث لجلب مصادر التعلم.",
        "memory_saved": "الذاكرة: تم حفظ التوصية الأخيرة في ذاكرة الجلسة. المسار المحفوظ: {path}. عدد التوصيات المحفوظة: {count}",
        "reset_message": "قم بتعديل بياناتك ثم اضغط على 'اكتشف مساري' مرة أخرى.",
        "required_msg": "الرجاء إدخال حقل {field}.",
        "too_long_msg": "النص المدخل في حقل {field} طويل جداً. الحد الأقصى {max} حرفاً.",
    },
}

LANGUAGE_NAME = {"en": "English", "ar": "العربية"}

# Initialize Session State
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "pending_state" not in st.session_state:
    st.session_state.pending_state = None
if "memory_state" not in st.session_state:
    st.session_state.memory_state = {"history": []}
if "status_msg" not in st.session_state:
    st.session_state.status_msg = "status_waiting_input"
if "resources_data" not in st.session_state:
    st.session_state.resources_data = None
if "recommendation_data" not in st.session_state:
    st.session_state.recommendation_data = None


def tr(key, **kwargs):
    lang = st.session_state.lang
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


# Language Selector Sidebar / Top
lang_choice = st.selectbox(
    "Language / اللغة",
    options=["English", "Arabic"],
    index=0 if st.session_state.lang == "en" else 1
)
new_lang = "ar" if lang_choice == "Arabic" else "en"
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    st.rerun()

# Apply Direction
direction = "rtl" if st.session_state.lang == "ar" else "ltr"
st.markdown(f'<div style="direction: {direction};">', unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="header-container">
    <div class="header-title">{tr("app_title")}</div>
    <div class="header-subtitle">{tr("app_subtitle")}</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 4) GUARDRAILS AND SAFETY
# ============================================================
MAX_TEXT_LENGTH = 500
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous",
    r"ignore\s+instructions",
    r"system\s+prompt",
    r"reveal\s+(the\s+)?prompt",
    r"developer\s+message",
    r"jailbreak",
    r"bypass\s+(the\s+)?rules",
]

def contains_prompt_injection(text: str) -> bool:
    text = (text or "").lower()
    return any(re.search(pattern, text) for pattern in INJECTION_PATTERNS)

def validate_inputs(major, edu_level, interests, goal, duration, skills):
    required = {
        tr("label_major"): major,
        tr("label_edu"): edu_level,
        tr("label_interests"): interests,
        tr("label_goal"): goal,
        tr("label_duration"): duration,
        tr("label_skills"): skills,
    }
    for field, value in required.items():
        if not value or not str(value).strip():
            return False, tr("required_msg", field=field)
        if len(str(value)) > MAX_TEXT_LENGTH:
            return False, tr("too_long_msg", field=field, max=MAX_TEXT_LENGTH)
        if contains_prompt_injection(str(value)):
            return False, tr("guardrail_stopped")
    return True, ""


def extract_months(duration):
    match = re.search(r"\d+", str(duration))
    if match:
        return int(match.group())
    return 1


def is_valid_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return 200 <= response.status < 400
        except urllib.error.HTTPError as e:
            if e.code in (403, 405):
                return True
            return False
    except Exception:
        return False


# ============================================================
# 5) AGENTS (GEMINI 3.6-FLASH)
# ============================================================
def agent_1_analysis(major, edu_level, interests, goal, duration, skills):
    months = extract_months(duration)
    language_name = LANGUAGE_NAME.get(st.session_state.lang, "English")

    prompt = f"""
You are Agent 1: Profile & Career Alignment Analyst.
Analyze this Saudi university student profile:
- Major: {major}
- Educational Level: {edu_level}
- Interests: {interests}
- Development Goal: {goal}
- Time Available: {duration}
- Existing Skills: {skills}

Return strict JSON with:
- match_percentage: integer
- path_title: string
- path_desc: string (in {language_name})
- badges: array of 3 short strings (in {language_name})
- reasons: array of 4 strings (in {language_name})
- skills_required: array of objects {{"name": "Python", "level": "Good level", "percentage": 85}}
- top_jobs: array of objects {{"title": "Data Analyst", "match": "92%"}}
- roadmap: array of exactly {months} objects {{"month": "1", "icon": "Step", "title": "Python Foundations"}}
"""
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction="You are a safe career analysis agent. Return only valid JSON."
    )
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(response.text)


def agent_2_evaluation(agent1_data, duration):
    months = extract_months(duration)
    language_name = LANGUAGE_NAME.get(st.session_state.lang, "English")

    prompt = f"""
You are Agent 2: Recommendation Refiner & Career Strategist.
Evaluate and refine: {json.dumps(agent1_data, ensure_ascii=False)}
Duration: {duration}
Write all narrative text fields in {language_name}. Roadmap must contain exactly {months} months.
Return identical strict JSON format.
"""
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction="You are a quality-control agent. Return only valid JSON."
    )
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    result = json.loads(response.text)
    roadmap = result.get("roadmap", [])
    if len(roadmap) != months:
        result["roadmap"] = roadmap[:months]
    for index, step in enumerate(result.get("roadmap", []), 1):
        step["month"] = str(index)
    return result


def agent_3_url_finder(evaluated_data):
    path_title = evaluated_data.get("path_title", "Career Development")
    prompt = f"""
You are Agent 3: Educational Resource Hunter.
Career path: {path_title}
Suggest up to 8 well-known educational resources relevant to this career path.
Return strict JSON:
{{
  "resources": [
    {{
      "provider": "Coursera",
      "course": "Relevant course or learning catalog",
      "url": "https://www.coursera.org"
    }}
  ]
}}
"""
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction="You provide educational resources. Return only valid JSON and avoid fabricated URLs."
    )
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    data = json.loads(response.text)
    valid_res = [r for r in data.get("resources", []) if is_valid_url(r.get("url", ""))]
    data["resources"] = valid_res
    return data


# ============================================================
# 6) INPUT FORM
# ============================================================
worldwide_majors = [
    "Computer Science", "Artificial Intelligence", "Data Science", "Software Engineering",
    "Cybersecurity", "Information Technology", "Information Systems", "Computer Engineering",
    "Business Administration", "Finance", "Accounting", "Marketing", "Supply Chain Management",
    "Mathematics", "Statistics", "Medicine & Surgery", "Nursing", "Public Health",
    "Health Informatics", "Graphic Design", "UI/UX Design", "Architecture", "Psychology", "Education & Pedagogy"
]
learning_durations = [f"{i} Month" if i == 1 else f"{i} Months" for i in range(1, 25)]

with st.container():
    st.markdown(f'<div class="card-box"><div class="section-title">{tr("start_here")}</div>', unsafe_allow_html=True)
    with st.form("path_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pref_major = st.selectbox(tr("label_major"), options=worldwide_majors)
        with col2:
            edu_level = st.selectbox(tr("label_edu"), options=["Diploma", "Bachelor's Degree", "Master's Degree"])
        with col3:
            interests = st.text_input(tr("label_interests"))

        col4, col5, col6 = st.columns(3)
        with col4:
            dev_goal = st.text_input(tr("label_goal"))
        with col5:
            avail_time = st.selectbox(tr("label_duration"), options=learning_durations)
        with col6:
            skills_input = st.text_input(tr("label_skills"), placeholder=tr("skills_placeholder"))

        submitted = st.form_submit_button(tr("analyze_btn"))
    st.markdown('</div>', unsafe_allow_html=True)

if submitted:
    is_valid, message = validate_inputs(pref_major, edu_level, interests, dev_goal, avail_time, skills_input)
    if not is_valid:
        st.error(message)
        st.session_state.status_msg = tr("guardrail_stopped")
    else:
        try:
            with st.spinner("Analyzing profile..."):
                agent1 = agent_1_analysis(pref_major, edu_level, interests, dev_goal, avail_time, skills_input)
                agent2 = agent_2_evaluation(agent1, avail_time)
                st.session_state.recommendation_data = agent2
                st.session_state.pending_state = {
                    "profile": {"major": pref_major, "edu_level": edu_level, "interests": interests, "goal": dev_goal, "duration": avail_time, "skills": skills_input},
                    "recommendation": agent2,
                    "lang": st.session_state.lang,
                }
                st.session_state.status_msg = tr("hitl_checkpoint")
                st.session_state.resources_data = None
        except Exception as e:
            st.error(f"{tr('analysis_error')} {str(e)}")


# ============================================================
# 7) SYSTEM STATUS
# ============================================================
st.markdown(f'<div class="card-box"><div class="section-title">{tr("system_status")}</div>', unsafe_allow_html=True)
st.info(st.session_state.status_msg)
st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 8) DISPLAY RESULTS
# ============================================================
rec = st.session_state.recommendation_data

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(f'<div class="card-box"><div class="section-title">{tr("skills_needed")}</div>', unsafe_allow_html=True)
    if rec:
        for skill in rec.get("skills_required", []):
            pct = max(0, min(100, int(skill.get("percentage", 70))))
            st.markdown(f"""
            <div class="skill-row">
                <div class="skill-label">
                    <span>{skill.get("name", "")}</span>
                    <span style="color:#718096;font-weight:normal;">{skill.get("level", "")}</span>
                </div>
                <div class="skill-bar-bg">
                    <div class="skill-bar-fill" style="width:{pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write(tr("waiting_input_short"))
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown(f'<div class="card-box"><div class="section-title">{tr("why_path")}</div>', unsafe_allow_html=True)
    if rec:
        for r in rec.get("reasons", []):
            st.markdown(f"<div style='margin-bottom: 12px;'>[OK] {r}</div>", unsafe_allow_html=True)
    else:
        st.write(tr("waiting_input_short"))
    st.markdown('</div>', unsafe_allow_html=True)

with col_c:
    st.markdown(f'<div class="card-box"><div class="section-title">{tr("suggested_path")}</div>', unsafe_allow_html=True)
    if rec:
        badges_html = "".join([f'<span class="badge">{b}</span>' for b in rec.get("badges", [])])
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="match-circle">
                <div class="match-percentage">{rec.get("match_percentage", 0)}%</div>
                <div class="match-label">{tr("match_label")}</div>
            </div>
            <h2 style="color: #005A36; margin: 5px 0;">{rec.get("path_title", "")}</h2>
            <p style="color: #4a5568; font-size: 13px;">{rec.get("path_desc", "")}</p>
            <div>{badges_html}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.write(tr("waiting_input_short"))
    st.markdown('</div>', unsafe_allow_html=True)


col_d, col_e = st.columns(2)

with col_d:
    st.markdown(f'<div class="card-box"><div class="section-title">{tr("best_jobs")}</div>', unsafe_allow_html=True)
    if rec:
        for job in rec.get("top_jobs", []):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:8px; border-bottom:1px solid #dceee3;">
                <span>{job.get("title", "")}</span>
                <span class="badge">{job.get("match", "")}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write(tr("waiting_input_short"))
    st.markdown('</div>', unsafe_allow_html=True)

with col_e:
    st.markdown(f'<div class="card-box"><div class="section-title">{tr("dev_plan")}</div>', unsafe_allow_html=True)
    if rec:
        roadmap_cols = st.columns(len(rec.get("roadmap", [1])))
        for idx, step in enumerate(rec.get("roadmap", [])):
            with roadmap_cols[idx]:
                st.markdown(f"""
                <div class="timeline-card">
                    <div class="timeline-step">{idx+1}</div>
                    <div style="font-size:14px; font-weight:bold;">{step.get("icon", "Step")}</div>
                    <div style="font-size:11px; color:#718096;">{tr("month_label")} {step.get("month", idx+1)}</div>
                    <div style="font-size:12px; font-weight:bold;">{step.get("title", "")}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write(tr("waiting_input_short"))
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 9) HITL APPROVAL & RESOURCES
# ============================================================
st.markdown(f'<div class="card-box"><div class="section-title">{tr("hitl_title")}</div><p>{tr("hitl_desc")}</p>', unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    approve_clicked = st.button(tr("approve_btn"), type="primary")
with col_btn2:
    reject_clicked = st.button(tr("reject_btn"))

if approve_clicked:
    if st.session_state.pending_state and st.session_state.pending_state.get("recommendation"):
        try:
            with st.spinner("Fetching resources..."):
                recommendation = st.session_state.pending_state["recommendation"]
                res_data = agent_3_url_finder(recommendation)
                st.session_state.resources_data = res_data
                
                # Update memory
                rec_record = {
                    "profile": st.session_state.pending_state["profile"],
                    "approved_path": recommendation.get("path_title"),
                    "match_percentage": recommendation.get("match_percentage"),
                    "skills": recommendation.get("skills_required", []),
                }
                st.session_state.memory_state["latest"] = rec_record
                st.session_state.memory_state["history"].append(rec_record)
                st.session_state.memory_state["history"] = st.session_state.memory_state["history"][-5:]
                
                st.session_state.status_msg = tr("approved_status")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("No pending recommendation to approve.")

if reject_clicked:
    st.session_state.pending_state = None
    st.session_state.recommendation_data = None
    st.session_state.resources_data = None
    st.session_state.status_msg = tr("reset_message")
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Resources display
st.markdown(f'<div class="card-box"><div class="section-title">{tr("resources_title")}</div>', unsafe_allow_html=True)
if st.session_state.resources_data and st.session_state.resources_data.get("resources"):
    res_cols = st.columns(min(len(st.session_state.resources_data["resources"]), 4))
    for idx, res in enumerate(st.session_state.resources_data["resources"]):
        with res_cols[idx % len(res_cols)]:
            st.markdown(f"""
            <a href="{res.get("url", "#")}" target="_blank" style="text-type:none; text-decoration:none; color:inherit;">
                <div style="border:1px solid #D6EADF; border-radius:8px; padding:12px; background:#F8FCF9; height:100%;">
                    <div style="font-weight:bold; color:#005A36;">{res.get("provider", "")}</div>
                    <div style="font-size:12px; color:#555;">{res.get("course", "")}</div>
                    <div style="font-size:11px; margin-top:5px; color:#4F7A62;">{tr("verified_link")}</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
else:
    st.write(tr("resources_waiting"))
st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 10) MEMORY
# ============================================================
st.markdown(f'<div class="card-box"><div class="section-title">{tr("memory_title")}</div>', unsafe_allow_html=True)
mem_history = st.session_state.memory_state.get("history", [])
if mem_history:
    st.write(tr("memory_saved", path=mem_history[-1].get("approved_path"), count=len(mem_history)))
    for h in mem_history:
        st.text(f"- {h.get('approved_path')} ({h.get('match_percentage')}%)")
else:
    st.write(tr("memory_empty"))
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
