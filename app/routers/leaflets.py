"""
Patient Information Leaflet (PIL) Reader & Simplifier router for Dawaa'i AI.
"""
from typing import Optional, List
import uuid
import json
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.models import LeafletParseRequest, LeafletParseResponse, LeafletSection
from app.database import get_db
from app.auth import get_optional_current_user

router = APIRouter(prefix="/leaflets", tags=["Leaflets"])

# Medical jargon glossary to simplify complex medical terminology
JARGON_MAP_AR = {
    "عسر الهضم": "ألم أو انزعاج في رأس المعدة بعد تناول الطعام",
    "خلل وظيفي كبدي": "تأثر كفاءة الكبد في تنقية الجسم، ويتطلب فحص إنزيمات الكبد",
    "الحماض اللبني": "تراكم نادر لحمض اللاكتيك في الدم يسبب إرهاقاً شديداً وصعوبة في التنفس",
    "تشنج القصبات": "تضيق مفاجئ في ممرات الهواء بالرئتين يسبب صفيراً وضيقاً في التنفس",
    "نقص الصفائح الدموية": "انخفاض في خلايا تجلط الدم مما يزيد قابلية النزيف والكدمات",
    "مثبطات مضخة البروتون": "أدوية تقلل بشكل قوي إنتاج حمض المعدة لعلاج القرحة والارتجاع",
    "مضادات الالتهاب غير الستيرويدية": "مسكنات ومضادات تورم شائعة مثل الإيبوبروفين والبروفين",
    "قصور كلوي": "ضعف قدرة الكليتين على تصفية السوائل والسموم",
    "ارتجاع المريء": "صعود أحماض المعدة إلى المريء مما يسبب حُرقة شديدة في الصدر",
    "متلازمة زولينجر": "حالة تؤدي إلى إفراز مفرط لحمض المعدة مسببة قرحات متكررة"
}

JARGON_MAP_EN = {
    "dyspepsia": "upset stomach, indigestion, or pain in the upper abdomen",
    "hepatic dysfunction": "reduced liver ability to process toxins, requires blood monitoring",
    "lactic acidosis": "rare buildup of acid in bloodstream causing weakness and deep rapid breathing",
    "bronchospasm": "tightening of the airway muscles causing wheezing and shortness of breath",
    "thrombocytopenia": "lower than normal platelet count making bruising or bleeding easier",
    "proton pump inhibitors": "medications that significantly reduce stomach acid production",
    "nsaids": "common anti-inflammatory painkillers such as ibuprofen",
    "renal impairment": "decreased kidney filtration efficiency",
    "gerd": "acid reflux causing persistent heartburn and throat irritation"
}

def simplify_text(text: str, lang: str = "ar") -> str:
    simplified = text
    if lang == "ar":
        for term, explanation in JARGON_MAP_AR.items():
            if term in simplified:
                simplified = simplified.replace(term, f"**{term}** ({explanation})")
    else:
        for term, explanation in JARGON_MAP_EN.items():
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            simplified = pattern.sub(f"**{term}** ({explanation})", simplified)
    return simplified

@router.post("/parse", response_model=LeafletParseResponse)
async def parse_medicine_leaflet(
    request: LeafletParseRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Parses medicine leaflet text, categorizes information into patient-centric sections,
    and simplifies difficult pharmaceutical terms into easily understood guidance.
    """
    raw_text = request.text.strip()
    if not raw_text or len(raw_text) < 20:
        raise HTTPException(status_code=400, detail="Leaflet content is too short to extract medical sections.")
        
    is_ar = request.language == "ar"
    
    # Section pattern discovery
    sections: List[LeafletSection] = []
    
    # Check for known medicines in the text
    detected_med = None
    if "panadol" in raw_text.lower() or "بنادول" in raw_text or "paracetamol" in raw_text.lower() or "باراسيتامول" in raw_text:
        detected_med = "Panadol (Paracetamol)"
    elif "augmentin" in raw_text.lower() or "أوجمنتين" in raw_text:
        detected_med = "Augmentin (Amoxicillin/Clavulanate)"
    elif "brufen" in raw_text.lower() or "بروفين" in raw_text:
        detected_med = "Brufen (Ibuprofen)"
    elif "glucophage" in raw_text.lower() or "جلوكوفاج" in raw_text:
        detected_med = "Glucophage (Metformin)"
    elif "losec" in raw_text.lower() or "لوسيك" in raw_text:
        detected_med = "Losec (Omeprazole)"
        
    # Standard medical leaflet sections
    sec_1_title_ar = "1. دواعي الاستعمال والغرض الطبي"
    sec_1_title_en = "1. Indications & Medical Purpose"
    sec_2_title_ar = "2. الجرعة وطريقة الاستعمال الآمنة"
    sec_2_title_en = "2. Recommended Dosage & Administration"
    sec_3_title_ar = "3. موانع الاستعمال والتحذيرات الهامة"
    sec_3_title_en = "3. Contraindications & Important Warnings"
    sec_4_title_ar = "4. الآثار الجانبية المحتملة وكيفية التعامل معها"
    sec_4_title_en = "4. Potential Side Effects & Management"
    sec_5_title_ar = "5. ظروف الحفظ والتخزين السليم"
    sec_5_title_en = "5. Proper Storage & Handling"
    
    # If the text has natural markers or paragraphs, extract them, otherwise structure it
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    
    p1 = paragraphs[0] if len(paragraphs) > 0 else raw_text
    p2 = paragraphs[1] if len(paragraphs) > 1 else (
        "تناول الجرعة بدقة حسب تعليمات الطبيب أو الصيدلي مع كوب كامل من الماء." if is_ar else
        "Take exactly as directed by your doctor or pharmacist with a full glass of water."
    )
    p3 = paragraphs[2] if len(paragraphs) > 2 else (
        "يحظر الاستخدام في حال وجود حساسية سابقة للمادة الفعالة أو أمراض الكبد الحادة." if is_ar else
        "Do not use if you have known hypersensitivity to the active ingredients or severe hepatic impairment."
    )
    p4 = paragraphs[3] if len(paragraphs) > 3 else (
        "قد يسبب اضطراباً خفيفاً في المعدة أو نعاساً. في حال ظهور طفح جلدي، أوقف الدواء واستشر الطبيب فوراً." if is_ar else
        "May cause mild stomach upset or drowsiness. If severe allergic rash occurs, discontinue and consult your doctor."
    )
    p5 = paragraphs[4] if len(paragraphs) > 4 else (
        "يحفظ في درجة حرارة أقل من 25 درجة مئوية بعيداً عن متناول الأطفال وأشعة الشمس." if is_ar else
        "Store below 25°C away from moisture, direct sunlight, and reach of children."
    )
    
    sections = [
        LeafletSection(
            title_ar=sec_1_title_ar,
            title_en=sec_1_title_en,
            content=p1,
            simplified_content=simplify_text(p1, "ar" if is_ar else "en") if request.simplify else None,
            icon="pill"
        ),
        LeafletSection(
            title_ar=sec_2_title_ar,
            title_en=sec_2_title_en,
            content=p2,
            simplified_content=simplify_text(p2, "ar" if is_ar else "en") if request.simplify else None,
            icon="clock"
        ),
        LeafletSection(
            title_ar=sec_3_title_ar,
            title_en=sec_3_title_en,
            content=p3,
            simplified_content=simplify_text(p3, "ar" if is_ar else "en") if request.simplify else None,
            icon="alert-triangle"
        ),
        LeafletSection(
            title_ar=sec_4_title_ar,
            title_en=sec_4_title_en,
            content=p4,
            simplified_content=simplify_text(p4, "ar" if is_ar else "en") if request.simplify else None,
            icon="activity"
        ),
        LeafletSection(
            title_ar=sec_5_title_ar,
            title_en=sec_5_title_en,
            content=p5,
            simplified_content=simplify_text(p5, "ar" if is_ar else "en") if request.simplify else None,
            icon="archive"
        ),
    ]
    
    precautions = [
        "لا تتجاوز الجرعة المقررة لتفادي سمية الكبد أو الكلى." if is_ar else "Never exceed the maximum daily dose to prevent liver or kidney toxicity.",
        "استشر الطبيب قبل الاستخدام أثناء فترات الحمل أو الرضاعة." if is_ar else "Consult a healthcare professional before taking during pregnancy or breastfeeding.",
        "أخبر الطبيب بجميع الأدوية والمكملات الغذائية الأخرى التي تتناولها." if is_ar else "Inform your pharmacist of all other medications and supplements you are taking."
    ]
    
    now_iso = datetime.now(timezone.utc).isoformat()
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # Save into processed_documents table
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO processed_documents (
            id, user_id, doc_type, file_name, extracted_text, structured_data_json, is_successful, created_at
        ) VALUES (?, ?, 'leaflet', 'patient_leaflet', ?, ?, 1, ?);
        """, (
            doc_id,
            current_user["id"] if current_user else None,
            raw_text[:500],
            json.dumps({"sections_count": len(sections), "detected_medicine": detected_med}),
            now_iso
        ))
        
        # Log meaningful use if user is authenticated
        if current_user:
            activity_id = f"act_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
            INSERT INTO user_activities (
                id, user_id, event_type, target_id, target_name, is_successful, metadata_json, created_at
            ) VALUES (?, ?, 'leaflet_processed', ?, ?, 1, ?, ?);
            """, (
                activity_id,
                current_user["id"],
                doc_id,
                detected_med or "General Leaflet",
                json.dumps({"language": request.language, "simplified": request.simplify}),
                now_iso
            ))
            
    return LeafletParseResponse(
        document_title="Patient Information Leaflet (PIL) / النشرة الطبية المعتمدة",
        detected_medicine=detected_med,
        sections=sections,
        identified_precautions=precautions,
        is_successful=True
    )
