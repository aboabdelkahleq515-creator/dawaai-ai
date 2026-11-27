"""
Medicines catalog and search router for Dawaa'i AI.
"""
from typing import Optional, List
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models import (
    MedicineSummary, MedicineDetail, MedicineSearchResponse,
    InteractionCheckRequest, InteractionCheckResponse
)
from app.database import get_db
from app.auth import get_optional_current_user

router = APIRouter(prefix="/medicines", tags=["Medicines"])

def normalize_arabic(text: str) -> str:
    """Normalizes Arabic characters for flexible searching."""
    if not text:
        return ""
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي")
    return text.lower().strip()

def _row_to_summary(r) -> MedicineSummary:
    keys = r.keys()
    has_ped = bool(r["has_pediatric_data"]) if "has_pediatric_data" in keys and r["has_pediatric_data"] is not None else False
    has_preg = bool(r["has_pregnancy_data"]) if "has_pregnancy_data" in keys and r["has_pregnancy_data"] is not None else False
    has_ger = bool(r["has_geriatric_data"]) if "has_geriatric_data" in keys and r["has_geriatric_data"] is not None else False
    
    return MedicineSummary(
        id=r["id"],
        slug=r["slug"],
        trade_name_en=r["trade_name_en"],
        trade_name_ar=r["trade_name_ar"] or r["trade_name_en"],
        generic_name=r["generic_name"] or "",
        active_ingredient_en=r["active_ingredient_en"] or "",
        active_ingredient_ar=r["active_ingredient_ar"] or "",
        category_en=r["category_en"] or "",
        category_ar=r["category_ar"] or "",
        dosage_form_en=r["dosage_form_en"] or "",
        dosage_form_ar=r["dosage_form_ar"] or "",
        strength=r["strength"] or "",
        is_verified=bool(r["is_verified"]),
        source_authority=r["source_authority"] or "EDA / DailyMed",
        pediatric_safety_en=r["pediatric_safety_en"] if has_ped and "pediatric_safety_en" in keys else None,
        pediatric_safety_ar=r["pediatric_safety_ar"] if has_ped and "pediatric_safety_ar" in keys else None,
        pregnancy_safety_en=r["pregnancy_safety_en"] if has_preg and "pregnancy_safety_en" in keys else None,
        pregnancy_safety_ar=r["pregnancy_safety_ar"] if has_preg and "pregnancy_safety_ar" in keys else None,
        geriatric_safety_en=r["geriatric_safety_en"] if has_ger and "geriatric_safety_en" in keys else None,
        geriatric_safety_ar=r["geriatric_safety_ar"] if has_ger and "geriatric_safety_ar" in keys else None,
        price=r["price"] if "price" in keys else None,
        manufacturer=r["manufacturer"] if "manufacturer" in keys else None,
        data_origin=r["data_origin"] if "data_origin" in keys and r["data_origin"] else "official_registry",
        classification=r["classification"] if "classification" in keys and r["classification"] else "registered_drug",
        clean_strength=r["clean_strength"] if "clean_strength" in keys else None,
        clean_dosage_form=r["clean_dosage_form"] if "clean_dosage_form" in keys else None,
        clean_route=r["clean_route"] if "clean_route" in keys else None,
        atc_code=r["atc_code"] if "atc_code" in keys else None,
        pharmacological_class_en=r["pharmacological_class_en"] if "pharmacological_class_en" in keys else None,
        pharmacological_class_ar=r["pharmacological_class_ar"] if "pharmacological_class_ar" in keys else None,
        has_pediatric_data=has_ped,
        has_pregnancy_data=has_preg,
        has_geriatric_data=has_ger,
        monograph_coverage=r["monograph_coverage"] if "monograph_coverage" in keys and r["monograph_coverage"] else "none",
        is_hidden=bool(r["is_hidden"]) if "is_hidden" in keys else False
    )

def _row_to_detail(r) -> MedicineDetail:
    keys = r.keys()
    summary = _row_to_summary(r)
    has_mono = summary.monograph_coverage == "official_label"

    dump = summary.model_dump()
    # Exclude safety keys to allow the detailed fallback values below
    for k in [
        "pediatric_safety_en", "pediatric_safety_ar",
        "pregnancy_safety_en", "pregnancy_safety_ar",
        "geriatric_safety_en", "geriatric_safety_ar"
    ]:
        dump.pop(k, None)

    return MedicineDetail(
        **dump,
        indications_en=r["indications_en"] or ("Available via pharmacist consultation." if not has_mono else ""),
        indications_ar=r["indications_ar"] or ("راجع الصيدلي أو الطبيب المختص لمعرفة دواعي الاستعمال." if not has_mono else ""),
        dosage_instructions_en=r["dosage_instructions_en"] or ("Dosage instructions not available in official registry; consult physician." if not has_mono else ""),
        dosage_instructions_ar=r["dosage_instructions_ar"] or ("الجرعة غير متوفرة في السجل الرسمي؛ استشر الطبيب أو الصيدلي." if not has_mono else ""),
        contraindications_en=r["contraindications_en"] or ("Hypersensitivity to any component." if not has_mono else ""),
        contraindications_ar=r["contraindications_ar"] or ("الحساسية تجاه أي من مكونات المستحضر." if not has_mono else ""),
        side_effects_en=r["side_effects_en"] or ("Refer to package insert for full adverse reactions." if not has_mono else ""),
        side_effects_ar=r["side_effects_ar"] or ("راجع النشرة الداخلية المرفقة بالعبوة." if not has_mono else ""),
        interactions_en=r["interactions_en"] or ("Consult pharmacist before concurrent medication use." if not has_mono else ""),
        interactions_ar=r["interactions_ar"] or ("استشر الصيدلي قبل تناول أدوية أخرى بالتزامن." if not has_mono else ""),
        pregnancy_safety_en=r["pregnancy_safety_en"] if summary.has_pregnancy_data else "Not available in official source label. Consult doctor.",
        pregnancy_safety_ar=r["pregnancy_safety_ar"] if summary.has_pregnancy_data else "غير متوفر في النشرة الرسمية للمستحضر. استشيري الطبيب.",
        pediatric_safety_en=r["pediatric_safety_en"] if summary.has_pediatric_data else "Not available in official source label. Consult pediatrician.",
        pediatric_safety_ar=r["pediatric_safety_ar"] if summary.has_pediatric_data else "غير متوفر في النشرة الرسمية للمستحضر. استشر طبيب الأطفال.",
        geriatric_safety_en=r["geriatric_safety_en"] if summary.has_geriatric_data else "Not available in official source label. Consult physician.",
        geriatric_safety_ar=r["geriatric_safety_ar"] if summary.has_geriatric_data else "غير متوفر في النشرة الرسمية للمستحضر. استشر الطبيب.",
        storage_en=r["storage_en"] or "Store below 30°C in a dry place.",
        storage_ar=r["storage_ar"] or "يحفظ في درجة حرارة أقل من 30 مئوية في مكان جاف.",
        source_url=r["source_url"] or r.get("monograph_url") or "",
        verified_at=r["verified_at"] if "verified_at" in keys else None,
        adult_dosage_frequency=r["adult_dosage_frequency"] if "adult_dosage_frequency" in keys else None,
        adult_dosage_interval=r["adult_dosage_interval"] if "adult_dosage_interval" in keys else None,
        adult_dosage_max_daily=r["adult_dosage_max_daily"] if "adult_dosage_max_daily" in keys else None,
        adult_dosage_duration=r["adult_dosage_duration"] if "adult_dosage_duration" in keys else None,
        pediatric_min_age=r["pediatric_min_age"] if "pediatric_min_age" in keys else None,
        pediatric_max_age=r["pediatric_max_age"] if "pediatric_max_age" in keys else None,
        pediatric_dose_by_weight=r["pediatric_dose_by_weight"] if "pediatric_dose_by_weight" in keys else None,
        pediatric_status=r["pediatric_status"] if "pediatric_status" in keys else None,
        pregnancy_category=r["pregnancy_category"] if "pregnancy_category" in keys else None,
        pregnancy_status=r["pregnancy_status"] if "pregnancy_status" in keys else None,
        lactation_status=r["lactation_status"] if "lactation_status" in keys else None,
        geriatric_status=r["geriatric_status"] if "geriatric_status" in keys else None,
        geriatric_warnings=r["geriatric_warnings"] if "geriatric_warnings" in keys else None,
        monograph_source=r["monograph_source"] if "monograph_source" in keys else None,
        monograph_url=r["monograph_url"] if "monograph_url" in keys else None,
        monograph_version_date=r["monograph_version_date"] if "monograph_version_date" in keys else None
    )

@router.get("/search", response_model=MedicineSearchResponse)
async def search_medicines(
    q: Optional[str] = Query(None, description="Search query (Arabic or English name, active ingredient, or symptom/condition)"),
    category: Optional[str] = Query(None, description="Category filter"),
    classification: Optional[str] = Query(None, description="Classification filter: registered_drug, dietary_supplement, cosmetic_care, medical_device"),
    dosage_form: Optional[str] = Query(None, description="Dosage form filter"),
    pediatric_only: Optional[bool] = Query(False, description="Filter items with verified pediatric dosing"),
    pregnancy_safe: Optional[bool] = Query(False, description="Filter items safe in pregnancy"),
    sort_by: Optional[str] = Query("relevance", description="Sort order: relevance, name_asc, price_asc, price_desc"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Searches the official medicine catalog by trade name, active ingredient,
    or approved medical indications/symptoms in both Arabic and English.
    Strictly excludes hidden / unapproved / cancelled entries.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Base filter: strictly exclude hidden / cancelled records
        query_sql = "SELECT * FROM medicines WHERE is_hidden = 0"
        count_sql = "SELECT COUNT(*) FROM medicines WHERE is_hidden = 0"
        params = []
        count_params = []
        
        # Safely extract parameter values if called directly or through FastAPI
        q_val = str(q).strip() if (q and isinstance(q, str)) else ""
        cat_val = str(category).strip() if (category and isinstance(category, str)) else ""
        class_val = str(classification).strip() if (classification and isinstance(classification, str)) else ""
        df_val = str(dosage_form).strip() if (dosage_form and isinstance(dosage_form, str)) else ""
        ped_val = bool(pediatric_only) if isinstance(pediatric_only, bool) else False
        preg_val = bool(pregnancy_safe) if isinstance(pregnancy_safe, bool) else False
        sort_val = str(sort_by).strip() if (sort_by and isinstance(sort_by, str)) else "relevance"
        offset_val = int(offset) if isinstance(offset, (int, str)) and str(offset).isdigit() else 0
        limit_val = int(limit) if isinstance(limit, (int, str)) and str(limit).isdigit() else 20

        if class_val:
            if class_val == "registered_drug":
                query_sql += " AND classification = 'registered_drug' AND is_verified = 1"
                count_sql += " AND classification = 'registered_drug' AND is_verified = 1"
            else:
                query_sql += " AND classification = ?"
                count_sql += " AND classification = ?"
                params.append(class_val)
                count_params.append(class_val)

        if cat_val:
            query_sql += " AND (LOWER(category_en) LIKE ? OR NORM_AR(category_ar) LIKE ?)"
            count_sql += " AND (LOWER(category_en) LIKE ? OR NORM_AR(category_ar) LIKE ?)"
            cat_p = [f"%{cat_val.lower()}%", f"%{normalize_arabic(cat_val)}%"]
            params.extend(cat_p)
            count_params.extend(cat_p)

        if df_val:
            query_sql += " AND (LOWER(dosage_form_en) LIKE ? OR LOWER(dosage_form_ar) LIKE ?)"
            count_sql += " AND (LOWER(dosage_form_en) LIKE ? OR LOWER(dosage_form_ar) LIKE ?)"
            df_p = [f"%{df_val.lower()}%", f"%{df_val.lower()}%"]
            params.extend(df_p)
            count_params.extend(df_p)

        if ped_val:
            query_sql += " AND has_pediatric_data = 1"
            count_sql += " AND has_pediatric_data = 1"

        if preg_val:
            query_sql += " AND pregnancy_status = 'safe'"
            count_sql += " AND pregnancy_status = 'safe'"
            
        if q_val:
            raw_q = q_val
            norm_q = normalize_arabic(raw_q)
            lower_q = raw_q.lower()
            
            # Check for symptom search or keyword matching via FTS5 first
            fts_ids = []
            try:
                # Sanitize search term for FTS5
                clean_term = re.sub(r'[^\w\s]', '', raw_q).strip()
                if clean_term:
                    fts_cursor = conn.cursor()
                    fts_cursor.execute("SELECT id FROM medicines_fts WHERE medicines_fts MATCH ? LIMIT 100;", (f'"{clean_term}"*',))
                    fts_ids = [row[0] for row in fts_cursor.fetchall()]
            except Exception:
                fts_ids = []

            like_raw = f"%{raw_q}%"
            like_lower = f"%{lower_q}%"
            like_norm = f"%{norm_q}%"
            
            if fts_ids:
                placeholders = ",".join(["?"] * len(fts_ids))
                query_sql += f"""
                    AND (
                        id IN ({placeholders}) OR
                        LOWER(trade_name_en) LIKE ? OR
                        NORM_AR(trade_name_ar) LIKE ? OR
                        trade_name_ar LIKE ? OR
                        LOWER(generic_name) LIKE ? OR
                        LOWER(active_ingredient_en) LIKE ? OR
                        NORM_AR(active_ingredient_ar) LIKE ? OR
                        active_ingredient_ar LIKE ? OR
                        LOWER(indications_en) LIKE ? OR
                        NORM_AR(indications_ar) LIKE ?
                    )
                """
                count_sql += f"""
                    AND (
                        id IN ({placeholders}) OR
                        LOWER(trade_name_en) LIKE ? OR
                        NORM_AR(trade_name_ar) LIKE ? OR
                        trade_name_ar LIKE ? OR
                        LOWER(generic_name) LIKE ? OR
                        LOWER(active_ingredient_en) LIKE ? OR
                        NORM_AR(active_ingredient_ar) LIKE ? OR
                        active_ingredient_ar LIKE ? OR
                        LOWER(indications_en) LIKE ? OR
                        NORM_AR(indications_ar) LIKE ?
                    )
                """
                clause_params = list(fts_ids) + [
                    like_lower, like_norm, like_raw,
                    like_lower, like_lower, like_norm, like_raw,
                    like_lower, like_norm
                ]
                params.extend(clause_params)
                count_params.extend(clause_params)
            else:
                query_sql += """
                    AND (
                        LOWER(trade_name_en) LIKE ? OR
                        NORM_AR(trade_name_ar) LIKE ? OR
                        trade_name_ar LIKE ? OR
                        LOWER(generic_name) LIKE ? OR
                        LOWER(active_ingredient_en) LIKE ? OR
                        NORM_AR(active_ingredient_ar) LIKE ? OR
                        active_ingredient_ar LIKE ? OR
                        LOWER(indications_en) LIKE ? OR
                        NORM_AR(indications_ar) LIKE ?
                    )
                """
                count_sql += """
                    AND (
                        LOWER(trade_name_en) LIKE ? OR
                        NORM_AR(trade_name_ar) LIKE ? OR
                        trade_name_ar LIKE ? OR
                        LOWER(generic_name) LIKE ? OR
                        LOWER(active_ingredient_en) LIKE ? OR
                        NORM_AR(active_ingredient_ar) LIKE ? OR
                        active_ingredient_ar LIKE ? OR
                        LOWER(indications_en) LIKE ? OR
                        NORM_AR(indications_ar) LIKE ?
                    )
                """
                clause_params = [
                    like_lower, like_norm, like_raw,
                    like_lower, like_lower, like_norm, like_raw,
                    like_lower, like_norm
                ]
                params.extend(clause_params)
                count_params.extend(clause_params)

        # Count total matches
        cursor.execute(count_sql, count_params)
        total_matches = cursor.fetchone()[0]

        # Log search activity for authenticated patient
        if q_val and current_user and offset_val == 0:
            try:
                act_id = f"act_{uuid.uuid4().hex[:12]}"
                cursor.execute("""
                    INSERT INTO user_activities (
                        id, user_id, event_type, target_name, is_successful, metadata_json, created_at
                    ) VALUES (?, ?, 'medicine_search', ?, 1, ?, ?);
                """, (
                    act_id,
                    current_user["id"],
                    q_val,
                    json.dumps({"total_found": total_matches, "category": cat_val}),
                    datetime.now(timezone.utc).isoformat()
                ))
            except Exception:
                pass

        # Order by
        if sort_val == "price_asc":
            query_sql += " ORDER BY price ASC NULLS LAST, trade_name_en ASC"
        elif sort_val == "price_desc":
            query_sql += " ORDER BY price DESC NULLS LAST, trade_name_en ASC"
        elif sort_val == "name_asc":
            query_sql += " ORDER BY trade_name_en ASC"
        else: # relevance
            q_order = q_val
            query_sql += """
                ORDER BY 
                    is_verified DESC,
                    monograph_coverage = 'official_label' DESC,
                    CASE 
                        WHEN LOWER(trade_name_en) = ? OR NORM_AR(trade_name_ar) = ? THEN 1
                        WHEN LOWER(trade_name_en) LIKE ? OR NORM_AR(trade_name_ar) LIKE ? THEN 2
                        WHEN LOWER(active_ingredient_en) LIKE ? THEN 3
                        ELSE 4
                    END,
                    trade_name_en ASC
            """
            params.extend([
                q_order.lower(),
                normalize_arabic(q_order),
                f"{q_order.lower()}%",
                f"{normalize_arabic(q_order)}%",
                f"{q_order.lower()}%"
            ])

        query_sql += " LIMIT ? OFFSET ?;"
        params.extend([limit_val, offset_val])
        
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()
        
        results = [_row_to_summary(r) for r in rows]

        return MedicineSearchResponse(
            query=q_val,
            total=total_matches,
            results=results
        )

@router.get("/categories")
async def get_categories():
    """
    Returns verified medicine categories with exact database counts and curated therapeutic groups.
    Strictly excludes hidden / unapproved records.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Curated Therapeutic Groups with live DB counts
        groups_def = [
            ("analgesics", "مسكنات الألم وخافضات الحرارة", "Analgesics & Antipyretics", "category_en LIKE '%Analgesic%' OR category_en LIKE '%Antipyretic%' OR category_ar LIKE '%مسكن%'", "Analgesic"),
            ("nsaids", "مضادات الالتهاب (NSAIDs)", "NSAIDs & Anti-inflammatory", "category_en LIKE '%NSAID%' OR category_en LIKE '%Anti-Inflammatory%' OR category_ar LIKE '%التهاب%'", "NSAID"),
            ("antibiotics", "مضادات حيوية وميكروبية", "Antibiotics & Antimicrobials", "category_en LIKE '%Antibiotic%' OR category_en LIKE '%Penicillin%' OR category_en LIKE '%Cephalosporin%' OR category_en LIKE '%Quinolone%' OR category_en LIKE '%Macrolide%'", "Antibiotic"),
            ("antidiabetics", "أدوية السكري", "Antidiabetic Agents", "category_en LIKE '%Antidiabetic%' OR category_en LIKE '%Biguanide%' OR category_en LIKE '%Sulfonylurea%' OR category_en LIKE '%Insulin%'", "Antidiabetic"),
            ("cardiovascular", "أدوية القلب والضغط", "Cardiovascular & Antihypertensives", "category_en LIKE '%Antihypertensive%' OR category_en LIKE '%Beta-Blocker%' OR category_en LIKE '%ACE%' OR category_en LIKE '%ARB%' OR category_en LIKE '%Calcium Channel%' OR category_en LIKE '%Cardio%'", "Antihypertensive"),
            ("statins", "أدوية الكوليسترول والدهون", "Statins & Lipid Lowering", "category_en LIKE '%Statin%' OR category_en LIKE '%Antihyperlipidemic%' OR category_en LIKE '%Lipid%'", "Statin"),
            ("peptic_ulcer", "قرحة وحموضة المعدة والجهاز الهضمي", "Peptic Ulcer & Gastrointestinal", "category_en LIKE '%Peptic%' OR category_en LIKE '%Proton Pump%' OR category_en LIKE '%Antacid%' OR category_en LIKE '%Gastro%'", "Peptic"),
            ("respiratory", "موسعات الشعب والجهاز التنفسي", "Respiratory & Bronchodilators", "category_en LIKE '%Respiratory%' OR category_en LIKE '%Bronchodilator%' OR category_en LIKE '%Cough%' OR category_en LIKE '%Asthma%'", "Respiratory"),
            ("antihistamines", "مضادات الحساسية والهيستامين", "Antihistamines & Allergy", "category_en LIKE '%Histamine%' OR category_en LIKE '%Allergy%' OR category_en LIKE '%Antihistamine%'", "Histamine"),
            ("psychiatric", "الأمراض العصبية والنفسية", "Psychiatric & Neurological", "category_en LIKE '%Psychiatric%' OR category_en LIKE '%Antidepressant%' OR category_en LIKE '%Antipsychotic%' OR category_en LIKE '%Epileptic%'", "Psychiatric"),
            ("supplements", "فيتامينات ومكملات غذائية", "Vitamins & Supplements", "category_en LIKE '%Vitamin%' OR category_en LIKE '%Supplement%' OR category_en LIKE '%Mineral%' OR category_en LIKE '%Iron%' OR category_en LIKE '%Calcium%'", "Supplement"),
            ("dermatology", "العناية بالبشرة والجلد", "Dermatology & Skin Care", "category_en LIKE '%Skin%' OR category_en LIKE '%Dermatolog%' OR category_en LIKE '%Hair%' OR category_en LIKE '%Cream%'", "Skin")
        ]

        therapeutic_groups = []
        for gid, ar_name, en_name, sql_cond, q_term in groups_def:
            cursor.execute(f"SELECT COUNT(*) FROM medicines WHERE is_hidden = 0 AND ({sql_cond});")
            cnt = cursor.fetchone()[0]
            therapeutic_groups.append({
                "id": gid,
                "name_ar": ar_name,
                "name_en": en_name,
                "count": cnt,
                "query": q_term
            })

        # 2. Individual top categories from DB with counts
        cursor.execute("""
            SELECT category_en, category_ar, COUNT(*) as cnt
            FROM medicines
            WHERE is_hidden = 0 AND category_en IS NOT NULL AND TRIM(category_en) != '' AND category_en != '.'
            GROUP BY category_en
            ORDER BY cnt DESC
            LIMIT 60;
        """)
        rows = cursor.fetchall()
        categories = []
        for r in rows:
            en = r["category_en"]
            ar = r["category_ar"]
            # Clean up default placeholder Arabic category if present
            if ar == "مستحضر دوائي معتمد" or not ar:
                # Provide intuitive Arabic fallback based on English name
                if "Multivitamin" in en:
                    ar = "فيتامينات متعددة"
                elif "Hair" in en:
                    ar = "عناية بالشعر"
                elif "Antineoplastic" in en:
                    ar = "علاجات أورام ومناعة"
                elif "Psychiatric" in en:
                    ar = "علاجات نفسية وعصبية"
                elif "Antibiotic" in en:
                    ar = "مضادات حيوية"
                elif "Skin" in en:
                    ar = "عناية بالبشرة"
                elif "Iron" in en:
                    ar = "مكملات حديد"
                elif "Calcium" in en:
                    ar = "مكملات كالسيوم"
                elif "Peptic" in en or "Proton Pump" in en:
                    ar = "أدوية قرحة وحموضة المعدة"
                elif "Statin" in en:
                    ar = "أدوية كوليسترول ودهون"
                elif "Anti-Histamine" in en:
                    ar = "مضادات حساسية"
                elif "Cough" in en:
                    ar = "أدوية السعال والكحة"
                elif "Dietary Supplement" in en:
                    ar = "مكمل غذائي"
                elif "Oral Care" in en:
                    ar = "صحة الفم والأسنان"
                else:
                    ar = en

            categories.append({
                "category_en": en,
                "category_ar": ar,
                "count": r["cnt"]
            })

        return {
            "therapeutic_groups": therapeutic_groups,
            "categories": categories
        }

# --- Academic ML & DL Evaluation Endpoints ---
@router.get("/academic-ml-report")
async def get_academic_ml_report():
    """
    Returns the comprehensive machine & deep learning academic report
    for university evaluation and doctor reference.
    Includes Decision Tree, Random Forest, and PyTorch CNN benchmark metrics.
    """
    import os
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "ml_academic_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "status": "in_training",
        "message": "Academic report being finalized"
    }

@router.get("/{slug_or_id}", response_model=MedicineDetail)
async def get_medicine_detail(
    slug_or_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Retrieves complete verified medicine information.
    If viewed by an authenticated user, logs a successful meaningful activity.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medicines WHERE id = ? OR slug = ?;", (slug_or_id, slug_or_id))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Medicine record not found in verified registry.")
            
        # Log meaningful use if user is authenticated
        if current_user:
            now_iso = datetime.now(timezone.utc).isoformat()
            activity_id = f"act_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
            INSERT INTO user_activities (
                id, user_id, event_type, target_id, target_name, is_successful, metadata_json, created_at
            ) VALUES (?, ?, 'medicine_view', ?, ?, 1, ?, ?);
            """, (
                activity_id,
                current_user["id"],
                row["id"],
                f"{row['trade_name_en']} / {row['trade_name_ar']}",
                json.dumps({"slug": row["slug"], "category": row["category_en"]}),
                now_iso
            ))
            
        return _row_to_detail(row)


@router.post("/check-interactions", response_model=InteractionCheckResponse)
async def check_drug_interactions(request: InteractionCheckRequest):
    """
    Clinically analyzes potential drug-drug interactions between two medications.
    Strictly grounded in official regulatory monographs (FDA / EMA / EDA) and authoritative clinical rules.
    If no documented interaction is recorded, strictly returns:
    'لا توجد بيانات تداخل موثّقة، اسأل الصيدلي' (NOT 'لا يوجد تداخل').
    Specifically recognizes non-drug products (probiotics, supplements) with dosing timing synergy instructions.
    """
    med_a_raw = request.medicine_a.strip().lower()
    med_b_raw = request.medicine_b.strip().lower()
    is_ar = request.language == "ar"

    # Search database for both medicines to get canonical records and monographs
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, trade_name_en, trade_name_ar, active_ingredient_en, active_ingredient_ar, 
                   category_en, classification, interactions_en, interactions_ar
            FROM medicines 
            WHERE is_hidden = 0;
        """)
        all_meds = cursor.fetchall()

    def find_match(term):
        norm = normalize_arabic(term)
        for m in all_meds:
            if (term in m["trade_name_en"].lower() or term in (m["active_ingredient_en"] or "").lower() or
                norm in normalize_arabic(m["trade_name_ar"] or "") or norm in normalize_arabic(m["active_ingredient_ar"] or "")):
                return m
        return None

    match_a = find_match(med_a_raw)
    match_b = find_match(med_b_raw)

    name_a = f"{match_a['trade_name_ar']} ({match_a['trade_name_en']})" if match_a else request.medicine_a
    name_b = f"{match_b['trade_name_ar']} ({match_b['trade_name_en']})" if match_b else request.medicine_b

    text_pair = f"{med_a_raw} {med_b_raw} {match_a['active_ingredient_en'].lower() if match_a and match_a['active_ingredient_en'] else ''} {match_b['active_ingredient_en'].lower() if match_b and match_b['active_ingredient_en'] else ''}"

    # -------------------------------------------------------------------------
    # SPECIAL CLINICAL CASE: Antibiotic (e.g. Augmentin) + Probiotic
    # Clinical timing synergy: Space doses by 2-3 hours to preserve live flora
    # -------------------------------------------------------------------------
    is_antibiotic = any(k in text_pair for k in ["augmentin", "amoxicillin", "clavulanate", "أوجمنتين", "اوجمنتين", "أموكسيسيلين", "اموكسيسيلين", "cipro", "cefixime", "ceftriaxone", "azithromycin", "antibiotic", "مضاد حيوي"]) or \
                    (match_a and "antibiotic" in (match_a["category_en"] or "").lower()) or \
                    (match_b and "antibiotic" in (match_b["category_en"] or "").lower())

    is_probiotic = any(k in text_pair for k in ["probiotic", "بروبيوتيك", "خمائر", "بكتيريا نافعة", "lactobacillus", "bifidobacterium", "saccharomyces", "enterogermina", "لاكتيول", "انتروجيرمينا"])

    if is_antibiotic and is_probiotic:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=True,
            severity="moderate",
            headline_ar="💡 توجيه زمني للاستخدام: فصل مواعيد الجرعات (تناغم علاجي)",
            headline_en="💡 Administration Timing Guidance: Separate Doses (Clinical Synergy)",
            mechanism_ar="المضاد الحيوي (مثل أوجمنتين) واسع المجال يقضي على البكتيريا الضارة والنافعة على حد سواء. عند تناول البروبيوتيك في نفس التوقيت المباشر، سيقوم المضاد بقتل بكتيريا البروبيوتيك الحية، مما يعطل فائدتها الداعمة للجهاز الهضمي.",
            mechanism_en="Broad-spectrum antibiotics eradicate both pathogenic and beneficial flora. Ingesting live probiotics simultaneously results in rapid antibiotic destruction of the beneficial cultures.",
            recommendation_ar="هذا ليس تعارضاً دوائياً خطيراً بل توجيه استخدام وتوقيت ذكي: يُنصح بالبروبيوتيك للوقاية من الإسهال والاضطرابات المعوية الناتجة عن المضادات، بشرط فصل موعد الجرعتين بساعتين إلى 3 ساعات على الأقل (مثلاً: تناول المضاد مع الطعام، وتناول البروبيوتيك بعد 2-3 ساعات).",
            recommendation_en="This is not a harmful drug toxicity but clinical timing synergy: probiotics are clinically encouraged to prevent antibiotic-associated diarrhea, provided you space doses by at least 2 to 3 hours.",
            safe_alternatives_ar=["فصل موعد الجرعتين بـ 2 إلى 3 ساعات كاملة", "الاستمرار في تناول البروبيوتيك لعدة أيام بعد انتهاء كورس المضاد الحيوي"],
            safe_alternatives_en=["Separate doses by at least 2 to 3 hours", "Continue probiotic regimen for a few days after finishing antibiotic course"]
        )

    # 1. NSAIDs + Anticoagulants / Antiplatelets (Major Risk)
    is_nsaid = any(k in text_pair for k in ["ibuprofen", "brufen", "diclofenac", "voltaren", "cataflam", "celecoxib", "celebrex", "ketoprofen", "بروفين", "إيبوبروفين", "ايبوبروفين", "فولتارين", "كاتافلام"])
    is_anticoag = any(k in text_pair for k in ["warfarin", "clopidogrel", "plavix", "enoxaparin", "clexane", "rivaroxaban", "xarelto", "aspirin", "وارفارين", "كومادين", "بلافيكس", "كلكسان", "زيلارتو", "أسبرين"])
    if is_nsaid and is_anticoag:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=True,
            severity="major",
            headline_ar="⚠️ تداخل دوائي شديد الخطورة (خطر نزيف هضمي حاد)",
            headline_en="⚠️ Severe Major Interaction (Acute Gastrointestinal Bleeding Risk)",
            mechanism_ar="الجمع بين مضادات الالتهاب غير الستيرويدية (NSAIDs) ومميعات الدم يضاعف تثبيط وظائف الصفائح الدموية ويهتك الغشاء المخاطي الواقي للمعدة، مما يسبب نزيفاً هضمياً وتقرحات خطيرة.",
            mechanism_en="Co-administration of NSAIDs and anticoagulants/antiplatelets synergistically impairs platelet aggregation and damages gastric mucosal lining, sharply increasing severe GI hemorrhage risk.",
            recommendation_ar="يمنع الجمع بينهما دون إشراف طبي صارم. يُوصى بالاعتماد على الباراسيتامول (بنادول أدفانس) كمسكن للألم وخافض للحرارة كبديل آمن لا يؤثر على سيولة الدم.",
            recommendation_en="Avoid combination unless under strict specialist supervision. Use Paracetamol (Panadol Advance) as a safe analgesic/antipyretic alternative that does not impair coagulation.",
            safe_alternatives_ar=["باراسيتامول (بنادول أدفانس 500 ملغ)", "كمادات موضعية مسكنة"],
            safe_alternatives_en=["Paracetamol (Panadol Advance 500mg)", "Topical non-systemic analgesics"]
        )

    # 2. Clopidogrel (Plavix) + Omeprazole / Esomeprazole (Major Risk)
    is_clopidogrel = any(k in text_pair for k in ["clopidogrel", "plavix", "بلافيكس"])
    is_omeprazole = any(k in text_pair for k in ["omeprazole", "losec", "esomeprazole", "nexium", "أوميبرازول", "لوسيك", "نيكسيوم"])
    if is_clopidogrel and is_omeprazole:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=True,
            severity="major",
            headline_ar="⚠️ تعارض رئيسي (إلغاء فاعلية مميع الدم بلافيكس)",
            headline_en="⚠️ Major Clinical Interaction (Reduced Clopidogrel Efficacy)",
            mechanism_ar="يثبط أوميبرازول/إيزوميبرازول إنزيم الكبد CYP2C19 الضروري لتحويل دواء بلافيكس إلى شكله النشط الفعال، مما يعطل مفعوله الواقي من التجلط ويزيد خطر انسداد الدعامات التاجية والسكتات القلبية.",
            mechanism_en="Omeprazole and esomeprazole inhibit hepatic CYP2C19, blocking the bioactivation of clopidogrel into its active metabolite, thereby increasing stent thrombosis and cardiovascular event risk.",
            recommendation_ar="استبدال أوميبرازول بدواء بانتوبرازول (كونترولوك) أو فاموتيدين لحماية المعدة دون التأثير على فاعلية بلافيكس.",
            recommendation_en="Switch from omeprazole to Pantoprazole (Controloc) or Famotidine, which exert minimal CYP2C19 inhibition.",
            safe_alternatives_ar=["بانتوبرازول (كونترولوك 40 ملغ)", "فاموتيدين (فاموتاك 20 ملغ)"],
            safe_alternatives_en=["Pantoprazole (Controloc 40mg)", "Famotidine 20mg"]
        )

    # 3. Statins (Lipitor/Crestor) + Macrolides (Klacid/Clarithromycin)
    is_statin = any(k in text_pair for k in ["atorvastatin", "lipitor", "rosuvastatin", "crestor", "ليبيتور", "كريستور", "ستاتين"])
    is_macrolide = any(k in text_pair for k in ["clarithromycin", "klacid", "كلاسيد", "كلاريثرومايسين"])
    if is_statin and is_macrolide:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=True,
            severity="major",
            headline_ar="⚠️ تداخل خطير (ارتفاع سمية العضلات وانحلالها)",
            headline_en="⚠️ High-Risk Interaction (Myopathy & Rhabdomyolysis Risk)",
            mechanism_ar="يثبط كلاريثرومايسين إنزيم CYP3A4 الكبدي، مما يؤدي لتراكم أدوية الكوليسترول (الستاتينات) في الدم بنسب مرتفعة وتسبب آلاماً عضلية حادة قد تتطور لانحلال الربيدات وتلف الكلى.",
            mechanism_en="Clarithromycin strongly inhibits CYP3A4, causing massive accumulation of statins and dramatically increasing the incidence of severe myopathy and life-threatening rhabdomyolysis.",
            recommendation_ar="إيقاف دواء الستاتين مؤقتاً طوال فترة تناول المضاد الحيوي، أو استبدال المضاد الحيوي بـ أزيثروميسين (زيثروماكس) أو أموكسيسيلين.",
            recommendation_en="Temporarily withhold statin therapy during the antibiotic course, or prescribe Azithromycin (Zithromax) or Amoxicillin.",
            safe_alternatives_ar=["أزيثروميسين (زيثروماكس 500 ملغ)", "أوجمنتين 1 غرام"],
            safe_alternatives_en=["Azithromycin (Zithromax 500mg)", "Augmentin 1g"]
        )

    # 4. Beta-Blockers (Concor) + Bronchodilators (Ventolin)
    is_beta_blocker = any(k in text_pair for k in ["bisoprolol", "concor", "propranolol", "كونكور", "بيسوبرولول"])
    is_bronchodilator = any(k in text_pair for k in ["salbutamol", "ventolin", "فنتولين", "سالبوتامول"])
    if is_beta_blocker and is_bronchodilator:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=True,
            severity="moderate",
            headline_ar="⚡ تداخل متوسط يستوجب الحذر (تعاكس دوائي على الشعب الهوائية)",
            headline_en="⚡ Moderate Interaction (Antagonistic Effect on Bronchial Smooth Muscle)",
            mechanism_ar="قد تعاكس حاصرات بيتا تأثير السالبوتامول الموسع للقصبات الهوائية وتؤدي لتشنج الشعب الهوائية لدى مرضى الربو.",
            mechanism_en="Beta-blockers can antagonize the bronchodilating effect of beta-2 agonists like salbutamol, potentially precipitating bronchospasm in asthmatic patients.",
            recommendation_ar="إذا كان المريض يعاني من الربو، يفضل استشارة طبيب القلب لاختيار دواء ضغط بديل لا يؤثر على الرئتين مثل أملوديبين (نورفاسك) أو لوسارتان.",
            recommendation_en="In asthmatic patients, consider calcium channel blockers (Amlodipine) or ARBs (Losartan) under cardiologist guidance.",
            safe_alternatives_ar=["أملوديبين (نورفاسك 5 ملغ)", "لوسارتان (كوزار 50 ملغ)"],
            safe_alternatives_en=["Amlodipine (Norvasc 5mg)", "Losartan (Cozaar 50mg)"]
        )

    # 5. Ciprofloxacin + Antacids / Multivitamins (Absorption Chelation)
    is_fluoroquinolone = any(k in text_pair for k in ["ciprofloxacin", "cipro", "سيبرو"])
    is_cation = any(k in text_pair for k in ["calcium", "magnesium", "osteocare", "gaviscon", "feroglobin", "iron", "أوستيوكير", "جافيسكون", "فيروجلوبين", "حديد", "كالسيوم"])
    if is_fluoroquinolone and is_cation:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=True,
            severity="moderate",
            headline_ar="⚡ تداخل امتصاص معوي (ارتباط كيميائي يضعف المضاد الحيوي)",
            headline_en="⚡ Moderate Absorption Chelation (Reduced Antibiotic Bioavailability)",
            mechanism_ar="ترتبط أيونات الكالسيوم والمغنيسيوم والحديد بجزيئات السيبروفلوكساسين وتشكل مركبات غير قابلة للامتصاص، مما يقلل فاعلية المضاد الحيوي بنسبة تفوق 75%.",
            mechanism_en="Multivalent metal cations chelate ciprofloxacin in the gastrointestinal tract, forming insoluble complexes that drastically diminish systemic absorption.",
            recommendation_ar="افصل بين موعد تناول الدواءين بساعتين قبل أو 4 ساعات بعد تناول المضاد الحيوي لضمان الامتصاص الكامل.",
            recommendation_en="Separate administration times: take the antibiotic at least 2 hours before or 4 hours after cation-containing supplements.",
            safe_alternatives_ar=["فصل مواعيد الجرعات بـ 3-4 ساعات كاملة"],
            safe_alternatives_en=["Space dosage by at least 3-4 hours"]
        )

    # -------------------------------------------------------------------------
    # 6. Non-Drug Products & Dietary Supplements Notice
    # If one or both items are classified as dietary supplement, cosmetic, device
    # -------------------------------------------------------------------------
    is_non_drug = (match_a and match_a["classification"] in ("dietary_supplement", "cosmetic_care", "medical_device")) or \
                   (match_b and match_b["classification"] in ("dietary_supplement", "cosmetic_care", "medical_device")) or \
                   any(k in text_pair for k in ["مكمل", "فيتامين", "عشبة", "herbal", "supplement", "vitamin"])

    if is_non_drug:
        return InteractionCheckResponse(
            medicine_a_name=name_a,
            medicine_b_name=name_b,
            has_interaction=False,
            severity="minor",
            headline_ar="ℹ️ مستحضر مكمل / غير دوائي: بيانات التداخل الرسمية محدودة",
            headline_en="ℹ️ Non-Drug / Supplement: Limited Regulatory Interaction Data",
            mechanism_ar="أحد المستحضرين مصنف كمكمل غذائي أو مستحضر عشبي وليس دواءً بشرياً مسجلاً، وبالتالي فإن بيانات التداخلات السريرية الرسمية محدودة في النشرات المعتمدة.",
            mechanism_en="One or both items are classified as dietary supplements or non-pharmaceuticals; formal regulatory interaction studies are naturally limited.",
            recommendation_ar="لا توجد بيانات تداخل موثّقة في النشرات الرسمية، يرجى استشارة الصيدلي أو الطبيب المعالج للتحقق من التوقيت الأمثل لتناول المكمل مع الأدوية.",
            recommendation_en="No documented interactions found in official monographs. Consult your pharmacist or physician before combining supplements with medications.",
            safe_alternatives_ar=["استشارة الصيدلي لتحديد فترات التباعد المناسبة بين المكملات والأدوية"],
            safe_alternatives_en=["Consult pharmacist for personalized spacing between supplements and drugs"]
        )

    # -------------------------------------------------------------------------
    # 7. Official Regulatory Monograph Check (Linked Leaflet data)
    # -------------------------------------------------------------------------
    if match_a and match_b:
        mono_a = (match_a["interactions_en"] or "") + " " + (match_a["interactions_ar"] or "")
        mono_b = (match_b["interactions_en"] or "") + " " + (match_b["interactions_ar"] or "")
        active_a = (match_a["active_ingredient_en"] or "").lower()
        active_b = (match_b["active_ingredient_en"] or "").lower()
        
        if active_b and active_b in mono_a.lower():
            return InteractionCheckResponse(
                medicine_a_name=name_a,
                medicine_b_name=name_b,
                has_interaction=True,
                severity="moderate",
                headline_ar="⚠️ تداخل مسجل في النشرة الرسمية المعتمدة",
                headline_en="⚠️ Interaction Documented in Official Regulatory Monograph",
                mechanism_ar=f"تنص النشرة الرسمية لدواء {match_a['trade_name_ar']} على الحذر عند تناوله بالتزامن مع {match_b['trade_name_ar']} لاحتمالية التأثير على التركيز الدوائي أو الفاعلية.",
                mechanism_en=f"Official regulatory monograph for {match_a['trade_name_en']} advises caution when co-administered with {match_b['trade_name_en']}.",
                recommendation_ar="راجع الطبيب أو الصيدلي لضبط الجرعات أو مراقبة الاستجابة السريرية.",
                recommendation_en="Consult your healthcare provider to adjust dosages or monitor clinical response.",
                safe_alternatives_ar=["مراجعة الصيدلي لتعديل الخطة الدوائية"],
                safe_alternatives_en=["Review regimen with pharmacist"]
            )

    # -------------------------------------------------------------------------
    # 8. Strict Clinical Default (No guessing, NO 'لا يوجد تداخل')
    # -------------------------------------------------------------------------
    return InteractionCheckResponse(
        medicine_a_name=name_a,
        medicine_b_name=name_b,
        has_interaction=False,
        severity="none",
        headline_ar="لا توجد بيانات تداخل موثّقة، اسأل الصيدلي",
        headline_en="No Documented Interactions Found, Consult Pharmacist",
        mechanism_ar="وفقاً للنشرات الدوائية المعتمدة وقواعد البيانات السريرية الرسمية، لم تُسجل بيانات تداخل موثّقة بين هذين المستحضرين. هذا لا ينفي احتمالية وجود تداخلات فردية غير مدرجة.",
        mechanism_en="According to official regulatory monographs and clinical databases, no documented interactions are recorded between these medications. This does not strictly exclude undocumented interactions.",
        recommendation_ar="استشر الصيدلي أو الطبيب المعالج للتحقق من الملاءمة السريرية للجمع بينهما وفقاً لحالتك الصحية الخاصة.",
        recommendation_en="Consult your pharmacist or physician to confirm clinical suitability based on your specific health status.",
        safe_alternatives_ar=["تناول كل دواء بموعده الموصوف واستشارة الصيدلي عند ظهور أي أعراض غير معتادة"],
        safe_alternatives_en=["Follow prescribed dosing schedules and notify your pharmacist of any unusual symptoms"]
    )

@router.get("/{slug_or_id}/ml-insights")
async def get_medicine_ml_insights(slug_or_id: str):
    """
    Calculates real-time Machine Learning inferences (Random Forest vs Decision Tree)
    for a specific medicine from the catalog.
    """
    from app.ml_engine import predict_drug_ml
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medicines WHERE slug = ? OR id = ? LIMIT 1;", (slug_or_id, slug_or_id))
        med = cursor.fetchone()
        if not med:
            raise HTTPException(status_code=404, detail="Medicine not found")

        insights = predict_drug_ml(
            name=med["trade_name_en"],
            active=med["active_ingredient_en"],
            form=med["dosage_form_en"],
            uses=med["indications_en"],
            side_effects=med["side_effects_en"]
        )
        return {
            "medicine_id": med["id"],
            "slug": med["slug"],
            "trade_name": med["trade_name_en"],
            "ml_insights": insights
        }

