"""
Medicine Box & Packaging Scanner router for Dawaa'i AI  (v2 - safety-first pipeline).

Pipeline
  1. READ   : Gemini transcribes ONLY what is printed on the package (no guessing, no monograph).
  2. MATCH  : strict, scored matching against the VERIFIED medicines table
              (brand + strength + dosage form, ambiguity detection).
  3. DECIDE : confirmed_db       -> report is built from the verified DB record (no LLM involved)
              needs_confirmation -> candidates are returned, the user confirms, then /scan/confirm
              ai_unverified      -> not in DB: LLM report, clearly labelled, queued for pharmacist review
              unreadable         -> ask for a clearer photo
  4. NEVER  : auto-save LLM output as "verified", invent confidence, or fall back to template text.
"""
from typing import Optional, List, Tuple, Dict, Any
import difflib
import hashlib
import uuid
import json
import re
import base64
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import httpx
from app.models import (
    ScanRequest, ScanResponse, ScannedMatch, MedicineSummary, MedicineDetail,
    AIDrugReport, AIScanResponse, ScanCandidate
)
from app.database import get_db, normalize_arabic
from app.auth import get_optional_current_user
from app.config import settings
from app.ai_provider import ai_provider
from app.ml_engine import predict_drug_ml, predict_packaging_cnn
from app.safety import profile_from_db_row, profile_from_ai_report

router = APIRouter(prefix="/scan", tags=["Scanner"])

# ----------------------------------------------------------------------------- constants
DEFAULT_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]  # override with settings.GEMINI_MODELS
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

CONFIRM_THRESHOLD = 0.75     # minimum score to auto-confirm a DB match
CONFIRM_MARGIN = 0.15        # minimum gap to the runner-up (otherwise ambiguous)
CANDIDATE_MIN_SCORE = 0.40   # minimum score to be offered as a candidate

DISCLAIMER_AR = "هذه المعلومات إرشادية وتثقيفية ولا تغني عن استشارة الطبيب المعالج أو الصيدلي المرخص."
DISCLAIMER_EN = "This information is educational and does not replace a doctor or licensed pharmacist."
UNSURE_AR = "غير متأكد - اسأل الصيدلي"
UNSURE_EN = "Not sure - ask a pharmacist"

UNREADABLE_AR = "الصورة غير واضحة أو لا تحتوي على علامة تجارية واضحة لدواء، يرجى إعادة التقاط الصورة بوضوح للاسم والتركيز"
UNREADABLE_EN = "The image is unclear or does not show a clear medicine brand. Please retake the photo clearly showing the name and strength."

GENERIC_PHARMA_STOPWORDS = {
    "tablet", "tablets", "capsule", "capsules", "syrup", "suspension",
    "solution", "injection", "cream", "ointment", "drops", "spray", "gel", "topical",
    "mg", "ml", "mcg", "film", "coated", "oral", "dose", "daily", "gm", "g",
    "gsk", "pfizer", "novartis", "sanofi", "bayer", "roche", "merck", "abbott",
    "for", "and", "the", "with", "box", "pack", "pharma", "lab", "labs",
    "حبوب", "اقراص", "كبسولات", "شراب", "محلول", "حقن", "مرهم", "كريم", "قطره", "بخاخ", "جل",
    "ملغ", "مل", "غرام", "جم", "فموي", "معلق", "علبه", "شريط"
}

# words that never identify a product (dosage forms, salts, units ...)
NAME_STOP = GENERIC_PHARMA_STOPWORDS | {
    "hydrochloride", "hcl", "sodium", "potassium", "calcium", "magnesium", "trihydrate", "dihydrate",
    "fumarate", "besylate", "maleate", "phosphate", "bisulfate", "oxalate", "sulfate", "acid", "complex",
    "pre", "filled", "pen", "gastro", "resistant", "hard", "soft", "slow", "release", "metered", "dry",
    "powder", "inhaler", "oral", "nasal", "topical", "subcutaneous", "plus", "of", "in", "per", "by",
    "usp", "bp", "ep", "ph", "eur", "tab", "tabs", "cap", "caps", "fct", "fctabs", "amp", "vial", "pack",
    "fc", "f", "c", "gm", "g", "gel",
}
SALT_WORDS = {
    "hydrochloride", "hcl", "sodium", "potassium", "calcium", "magnesium", "trihydrate", "dihydrate",
    "fumarate", "besylate", "maleate", "phosphate", "bisulfate", "oxalate", "sulfate", "acid", "complex",
    "vitamin", "rdna", "origin", "bromide", "butyl", "propionate", "dihydrochloride",
}


# ----------------------------------------------------------------------------- text helpers
def norm_text(text: str) -> str:
    """lowercase + Arabic normalisation + keep only letters/digits."""
    t = normalize_arabic(text or "")
    return re.sub(r"[^0-9a-z؀-ۿ]+", " ", t.lower()).strip()


def tokenize(text: str) -> List[str]:
    return [w for w in norm_text(text).split() if w]


def extract_medicine_tokens(text: str) -> List[str]:
    """Meaningful medicine-specific tokens (kept for the legacy endpoint and logging)."""
    if not text:
        return []
    cleaned = [w for w in tokenize(text) if len(w) > 2 and w not in GENERIC_PHARMA_STOPWORDS]
    return list(dict.fromkeys(cleaned))


_STRENGTH_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|ug|g|ml|iu|%|ملغ|ملجم|مجم|مل|غرام|جم|وحده)", re.I)
_UNIT_MAP = {"mg": "mg", "ملغ": "mg", "ملجم": "mg", "مجم": "mg", "g": "g", "غرام": "g", "جم": "g",
             "mcg": "mcg", "µg": "mcg", "ug": "mcg", "ml": "ml", "مل": "ml", "iu": "iu", "وحده": "iu", "%": "%"}


def parse_strengths(text: str) -> set:
    """All (value, unit) strengths in a text, normalised to mg when possible."""
    out = set()
    for num, unit in _STRENGTH_RE.findall(normalize_arabic(text or "").lower() if text else ""):
        try:
            val = float(num.replace(",", "."))
        except ValueError:
            continue
        unit = _UNIT_MAP.get(unit.lower(), unit.lower())
        if unit == "g":
            val, unit = val * 1000, "mg"
        out.add((round(val, 3), unit))
    return out


def form_category(text: str) -> Optional[str]:
    low = (text or "").lower()
    low_ar = normalize_arabic(text or "")
    checks = [
        ("inhaler", ["inhaler", "evohaler", "turbuhaler", "spray", "بخاخ", "استنشاق"]),
        ("injection", ["injection", "ampoule", "vial", "syringe", "pen", "حقن", "امبول"]),
        ("drops", ["drops", "قطره", "نقط"]),
        ("liquid", ["syrup", "suspension", "solution", "liquid", "شراب", "معلق", "محلول"]),
        ("topical", ["cream", "ointment", "gel", "مرهم", "كريم", "جل"]),
        ("capsule", ["capsule", "كبسول"]),
        ("tablet", ["tablet", "caplet", "اقراص", "قرص", "حبوب"]),
    ]
    for cat, keys in checks:
        if any(k in low or k in low_ar for k in keys):
            return cat
    return None


def _split_image(image_b64: str) -> Tuple[str, str]:
    mime_type, clean = "image/jpeg", image_b64
    if "," in image_b64:
        header, clean = image_b64.split(",", 1)
        if "png" in header:
            mime_type = "image/png"
        elif "webp" in header:
            mime_type = "image/webp"
    return mime_type, clean


# ----------------------------------------------------------------------------- Gemini
def _gemini_models() -> List[str]:
    configured = getattr(settings, "GEMINI_MODELS", None)
    if isinstance(configured, str):
        configured = [m.strip() for m in configured.split(",") if m.strip()]
    return list(configured) if configured else DEFAULT_GEMINI_MODELS


async def _gemini_json(parts: List[dict], timeout: float = 40.0, max_tokens: int = 4096) -> Tuple[Optional[dict], Optional[str]]:
    """Calls Gemini asking for strict JSON at temperature 0. Returns (parsed_dict, error_code)."""
    if not settings.GEMINI_API_KEY:
        return None, "no_key"
    headers = {"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"}
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "maxOutputTokens": max_tokens,
        },
    }
    last_err = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for model in _gemini_models():
            try:
                res = await client.post(f"{GEMINI_BASE}/{model}:generateContent", headers=headers, json=body)
                if res.status_code == 429:
                    print(f"Gemini ({model}) Rate Limit 429")
                    last_err = "rate_limit"
                    continue
                if res.status_code == 503:
                    print(f"Gemini ({model}) Service Unavailable 503")
                    last_err = "service_unavailable"
                    continue
                if res.status_code != 200:
                    print(f"Gemini ({model}) HTTP {res.status_code}")
                    last_err = "http_error"
                    continue
                cands = res.json().get("candidates", [])
                if not cands or "content" not in cands[0]:
                    continue
                raw = "".join(p.get("text", "") for p in cands[0]["content"].get("parts", [])).strip()
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data, None
            except Exception as e:  # network / JSON errors -> try next model
                print(f"Gemini ({model}) error: {e}")
                last_err = "network_error"
                continue
    return None, (last_err or "failed")


EXTRACTION_PROMPT = """You are an OCR transcriber for medicine packaging (box, blister, bottle, tube, ampoule, sachet, inhaler).
Transcribe ONLY what is physically printed and legible in the photo.
RULES:
- Never guess, never complete partial words, never use your own knowledge to decide what the product "probably" is.
- If a field is not clearly visible, use null.
- If the photo is blurry or does not show a medicine package, set is_medicine=false or legibility="unreadable".
Return ONE JSON object with exactly these keys:
{
  "is_medicine": true|false,
  "legibility": "clear" | "partial" | "unreadable",
  "brand_name_en": string|null,
  "brand_name_ar": string|null,
  "generic_name": string|null,
  "active_ingredients": [{"name": string, "strength": string|null}],
  "strength": string|null,
  "dosage_form": string|null,
  "manufacturer": string|null,
  "raw_text": "all visible text, verbatim"
}"""


async def gemini_extract_package(image_b64: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Extracts package details via unified AI Provider (with Circuit Breaker, caching, and rate limit resiliency).
    Returns (extracted_dict, error_code).
    """
    mime, data = _split_image(image_b64)
    ai_res = await ai_provider.extract_vision_json(
        prompt=EXTRACTION_PROMPT,
        image_b64=data,
        mime_type=mime,
        use_cache=True
    )
    if not ai_res.success:
        err_code = "rate_limit" if ai_res.error_code == "429" else (ai_res.error_code or "failed")
        return None, err_code

    parsed = ai_res.data
    if parsed is None:
        return None, "failed"
    if parsed.get("is_medicine") is False or parsed.get("legibility") == "unreadable":
        return None, "not_medicine"
    return parsed, None


def _extracted_summary(ex: dict) -> str:
    return json.dumps(
        {k: ex.get(k) for k in ("brand_name_en", "brand_name_ar", "generic_name", "active_ingredients",
                                "strength", "dosage_form", "manufacturer")},
        ensure_ascii=False,
    )


def report_from_unverified_extraction(extracted: dict, language: str = "ar") -> AIDrugReport:
    """
    Builds a strictly factual, grounded report for unverified packaging.
    Patient safety rule: NEVER hallucinate doses, contraindications or warnings for unverified products.
    """
    is_ar = language == "ar"
    not_avail = "غير متاح في قاعدة البيانات الموثّقة - راجع الصيدلي" if is_ar else "Not available in verified database - consult a pharmacist"
    
    brand = (extracted.get("brand_name_ar") if (is_ar and extracted.get("brand_name_ar")) else None) or extracted.get("brand_name_en") or extracted.get("generic_name") or (extracted.get("raw_text") or "").strip()[:50] or (UNSURE_AR if is_ar else UNSURE_EN)
    
    active_list = []
    for a in (extracted.get("active_ingredients") or []):
        if isinstance(a, dict) and a.get("name"):
            st = f" {a['strength']}" if a.get("strength") else ""
            active_list.append(f"{a['name']}{st}")
        elif isinstance(a, str):
            active_list.append(a)
    active = " + ".join(active_list) if active_list else (extracted.get("generic_name") or not_avail)
    
    strength = extracted.get("strength") or ""
    display_name = f"{brand} {strength}".strip()

    return AIDrugReport(
        drug_name=display_name,
        active_ingredient=active,
        uses=not_avail,
        dosage_and_usage=not_avail,
        dosage_instructions=not_avail,
        pregnancy_safety=not_avail,
        children_safety=not_avail,
        elderly_safety=not_avail,
        warnings=(
            f"⚠️ تنبيه سريري: هذا الدواء ({display_name}) غير مدرج في قاعدة بيانات الأدوية المعتمدة.\n\n"
            "تم استخراج الاسم والبيانات من العبوة فقط وإحالة السجل للمراجعة الصيدلانية.\n"
            "ممنوع تناول أي جرعة بناءً على معلومات غير موثقة، يرجى مراجعة الصيدلي أو الطبيب المختص."
        ) if is_ar else (
            f"⚠️ Clinical Warning: This medication ({display_name}) is not in the verified database.\n\n"
            "Packaging data has been transcribed and queued for pharmacist verification.\n"
            "Do not consume or adjust doses based on unverified data. Consult a licensed pharmacist or physician."
        ),
        drug_interactions=not_avail,
        min_age_years=None,
        pregnancy_level="unknown",
        children_level="unknown",
        elderly_level="unknown",
    )


# ----------------------------------------------------------------------------- DB row converters
def _clean(v):
    return v if v not in (None, "") else None


def row_to_summary(row) -> MedicineSummary:
    d = dict(row)
    extra = {k: _clean(d.get(k)) for k in (
        "pediatric_safety_en", "pediatric_safety_ar", "pregnancy_safety_en", "pregnancy_safety_ar",
        "geriatric_safety_en", "geriatric_safety_ar")}
    return MedicineSummary(
        id=d["id"], slug=d["slug"], trade_name_en=d["trade_name_en"], trade_name_ar=d["trade_name_ar"],
        generic_name=d["generic_name"], active_ingredient_en=d["active_ingredient_en"],
        active_ingredient_ar=d["active_ingredient_ar"], category_en=d["category_en"], category_ar=d["category_ar"],
        dosage_form_en=d["dosage_form_en"], dosage_form_ar=d["dosage_form_ar"], strength=d["strength"],
        is_verified=bool(d["is_verified"]), source_authority=d["source_authority"], **extra,
    )


def row_to_detail(row) -> MedicineDetail:
    """BUGFIX: the old code dropped pediatric/geriatric text and silently used generic defaults."""
    d = dict(row)
    kwargs = {}
    for k in ("pediatric_safety_en", "pediatric_safety_ar", "geriatric_safety_en", "geriatric_safety_ar"):
        if _clean(d.get(k)):
            kwargs[k] = d[k]
    return MedicineDetail(
        id=d["id"], slug=d["slug"], trade_name_en=d["trade_name_en"], trade_name_ar=d["trade_name_ar"],
        generic_name=d["generic_name"], active_ingredient_en=d["active_ingredient_en"],
        active_ingredient_ar=d["active_ingredient_ar"], category_en=d["category_en"], category_ar=d["category_ar"],
        dosage_form_en=d["dosage_form_en"], dosage_form_ar=d["dosage_form_ar"], strength=d["strength"],
        is_verified=bool(d["is_verified"]), source_authority=d["source_authority"],
        indications_en=d["indications_en"], indications_ar=d["indications_ar"],
        dosage_instructions_en=d["dosage_instructions_en"], dosage_instructions_ar=d["dosage_instructions_ar"],
        contraindications_en=d["contraindications_en"], contraindications_ar=d["contraindications_ar"],
        side_effects_en=d["side_effects_en"], side_effects_ar=d["side_effects_ar"],
        interactions_en=d["interactions_en"], interactions_ar=d["interactions_ar"],
        pregnancy_safety_en=d["pregnancy_safety_en"], pregnancy_safety_ar=d["pregnancy_safety_ar"],
        storage_en=d["storage_en"], storage_ar=d["storage_ar"],
        source_url=d["source_url"], verified_at=d["verified_at"], **kwargs,
    )


# ----------------------------------------------------------------------------- matching
def _fuzzy_hit(token: str, text_tokens: set) -> float:
    """1.0 exact whole-word, 0.85 OCR / typo tolerant variant, else 0."""
    if token in text_tokens:
        return 1.0
    if len(token) >= 4:
        for t in text_tokens:
            if t in GENERIC_PHARMA_STOPWORDS and token not in GENERIC_PHARMA_STOPWORDS:
                continue
            if len(t) >= 4:
                ratio = difflib.SequenceMatcher(None, token, t).ratio()
                if ratio >= 0.75:
                    return 0.85
                if len(token) >= 5 and (token[1:] in t or t[1:] in token or token[:4] == t[:4]):
                    return 0.80
    return 0.0


def _name_score(name: str, text_tokens: set) -> float:
    """0..0.70 : first (core) token is mandatory; descriptor tokens (Advance, Night ...) decide between variants."""
    toks = [t for t in tokenize(name) if t not in NAME_STOP and not t.isdigit() and len(t) > 1]
    if not toks:
        return 0.0
    core = _fuzzy_hit(toks[0], text_tokens)
    if core == 0.0:
        return 0.0
    extras = toks[1:]
    if not extras:
        return 0.70 * core
    matched = sum(1 for t in extras if _fuzzy_hit(t, text_tokens) > 0)
    return (0.50 + 0.20 * matched / len(extras)) * core


def _active_tokens(active_en: str) -> List[str]:
    return [t for t in tokenize(active_en) if t not in SALT_WORDS and t not in NAME_STOP and not t.isdigit() and len(t) > 3]


def are_clinically_equivalent(row_a, row_b) -> bool:
    """Checks whether two database records represent the exact same drug product & strength."""
    str_a = parse_strengths(row_a["strength"])
    str_b = parse_strengths(row_b["strength"])
    strength_compatible = bool(str_a & str_b) if (str_a and str_b) else True
    if not strength_compatible:
        return False
    
    brand_a = [t for t in tokenize(row_a["trade_name_en"]) if t not in NAME_STOP]
    brand_b = [t for t in tokenize(row_b["trade_name_en"]) if t not in NAME_STOP]
    core_a = brand_a[0] if brand_a else ""
    core_b = brand_b[0] if brand_b else ""
    
    if core_a and core_b and core_a == core_b:
        return True

    gen_a = norm_text(row_a["generic_name"] or row_a["active_ingredient_en"])
    gen_b = norm_text(row_b["generic_name"] or row_b["active_ingredient_en"])
    if gen_a and gen_b and (gen_a in gen_b or gen_b in gen_a):
        return True
    return False


def score_candidates(text: str, extracted: Optional[dict] = None) -> List[dict]:
    """Scores verified medicines with SQL pre-filtering and typo resilience."""
    text_tokens = set(tokenize(text))
    pkg_strengths = set()
    pkg_form = None
    if extracted:
        pkg_strengths = parse_strengths(" ".join(filter(None, [
            extracted.get("strength"),
            " ".join(f"{a.get('name','')} {a.get('strength') or ''}" for a in (extracted.get("active_ingredients") or [])
                     if isinstance(a, dict)),
        ])))
        pkg_form = form_category(extracted.get("dosage_form") or "")
    if not pkg_strengths:
        pkg_strengths = parse_strengths(text)
    if pkg_form is None:
        pkg_form = form_category(text)

    # Pre-filter query using extracted search tokens
    candidate_toks = [w for w in tokenize(text) if w not in NAME_STOP and not w.isdigit() and len(w) > 2]
    
    with get_db() as conn:
        cur = conn.cursor()
        if candidate_toks:
            conds = []
            params = []
            for t in candidate_toks:
                conds.append("(LOWER(trade_name_en) LIKE ? OR NORM_AR(trade_name_ar) LIKE ? OR LOWER(active_ingredient_en) LIKE ? OR LOWER(generic_name) LIKE ?)")
                params.extend([f"%{t}%", f"%{t}%", f"%{t}%", f"%{t}%"])
            sql = f"SELECT * FROM medicines WHERE is_verified = 1 AND is_hidden = 0 AND ({' OR '.join(conds)});"
            rows = cur.execute(sql, params).fetchall()
        else:
            rows = []

        # If too few matches or empty, fallback to full verified catalog
        if len(rows) < 5:
            rows = cur.execute("SELECT * FROM medicines WHERE is_verified = 1 AND is_hidden = 0;").fetchall()

    results = []
    for row in rows:
        name_s = max(_name_score(row["trade_name_en"], text_tokens), _name_score(row["trade_name_ar"], text_tokens))
        brand_matched = name_s > 0
        act = _active_tokens(row["active_ingredient_en"]) or _active_tokens(row["generic_name"])
        generic_matched = bool(act) and all(_fuzzy_hit(t, text_tokens) > 0 for t in act)

        score = name_s
        matched_term = row["trade_name_en"]
        if not brand_matched and generic_matched:
            score = 0.40
            matched_term = row["active_ingredient_en"]
        if score == 0:
            continue

        flags = []
        row_strengths = parse_strengths(row["strength"] or "") | parse_strengths(row["clean_strength"] or "") | parse_strengths(row["trade_name_en"] or "")
        strength_mismatch = False
        strength_matched = False
        if pkg_strengths and row_strengths:
            if pkg_strengths & row_strengths:
                score += 0.20
                strength_matched = True
            elif any(u in ("mg", "mcg", "iu", "%") for _, u in pkg_strengths):
                strength_mismatch = True
                score -= 0.30
                flags.append("strength_mismatch")

        form_conflict = False
        row_form = form_category(row["dosage_form_en"])
        if pkg_form and row_form:
            if pkg_form == row_form:
                score += 0.10
            else:
                form_conflict = True
                score -= 0.20
                flags.append("form_conflict")

        if not brand_matched:
            flags.append("generic_only")

        results.append({
            "row": row, "score": max(0.0, min(round(score, 3), 1.0)), "brand_matched": brand_matched,
            "strength_matched": strength_matched, "strength_mismatch": strength_mismatch, "form_conflict": form_conflict,
            "flags": flags, "matched_term": matched_term,
            "canonical": not row["id"].startswith("med-cat-") and not row["id"].startswith("eda-"),
        })

    results.sort(key=lambda r: (r["score"], r["canonical"]), reverse=True)
    return results


def decide(results: List[dict]) -> Tuple[str, Optional[dict]]:
    """Returns (status, best) with status in confirmed_db | needs_confirmation | none."""
    CONFIRM_THRESHOLD = 0.70
    cands = [r for r in results if r["score"] >= CANDIDATE_MIN_SCORE]
    if not cands:
        return "none", None
    best = cands[0]
    
    # Find the first candidate that is clinically DIFFERENT from best
    runner_up = None
    for c in cands[1:]:
        if not are_clinically_equivalent(best["row"], c["row"]):
            runner_up = c
            break

    clear_lead = runner_up is None or (best["score"] - runner_up["score"]) >= CONFIRM_MARGIN
    if (best["score"] >= CONFIRM_THRESHOLD and best["brand_matched"] and best["strength_matched"]
            and not best["strength_mismatch"] and not best["form_conflict"] and clear_lead):
        return "confirmed_db", best
    return "needs_confirmation", best


def match_against_database(text: str, tokens: Optional[List[str]] = None, extracted: Optional[dict] = None):
    """Backward-compatible wrapper -> (matches_list, best_match_detail_or_None)."""
    results = score_candidates(text, extracted)
    status, best = decide(results)
    matches = [
        ScannedMatch(medicine=row_to_summary(r["row"]), confidence_score=r["score"], matched_term=r["matched_term"])
        for r in results if r["score"] >= CANDIDATE_MIN_SCORE
    ][:5]
    best_detail = row_to_detail(best["row"]) if status == "confirmed_db" and best else None
    return matches, best_detail


# ----------------------------------------------------------------------------- report builders
def report_from_db(med: MedicineDetail, language: str = "ar") -> AIDrugReport:
    """Deterministic report from the verified record - no LLM involved."""
    profile = profile_from_db_row(med)
    if language == "ar":
        trade = med.trade_name_ar or med.trade_name_en
        return AIDrugReport(
            drug_name=f"{trade} ({med.trade_name_en}) - {med.strength}",
            active_ingredient=f"{med.active_ingredient_ar} ({med.strength})",
            uses=med.indications_ar, dosage_and_usage=med.dosage_instructions_ar,
            dosage_instructions=med.dosage_instructions_ar,
            pregnancy_safety=med.pregnancy_safety_ar, children_safety=med.pediatric_safety_ar,
            elderly_safety=med.geriatric_safety_ar,
            warnings=(f"موانع الاستعمال: {med.contraindications_ar}\n\n"
                      f"الآثار الجانبية: {med.side_effects_ar}\n\n⚠️ {DISCLAIMER_AR}"),
            drug_interactions=med.interactions_ar,
            min_age_years=profile.min_age_years, pregnancy_level=profile.pregnancy.level,
            children_level=profile.children.level, elderly_level=profile.elderly.level,
        )
    return AIDrugReport(
        drug_name=f"{med.trade_name_en} ({med.active_ingredient_en}) - {med.strength}",
        active_ingredient=f"{med.active_ingredient_en} ({med.strength})",
        uses=med.indications_en, dosage_and_usage=med.dosage_instructions_en,
        dosage_instructions=med.dosage_instructions_en,
        pregnancy_safety=med.pregnancy_safety_en, children_safety=med.pediatric_safety_en,
        elderly_safety=med.geriatric_safety_en,
        warnings=(f"Contraindications: {med.contraindications_en}\n\n"
                  f"Adverse reactions: {med.side_effects_en}\n\n⚠️ {DISCLAIMER_EN}"),
        drug_interactions=med.interactions_en,
        min_age_years=profile.min_age_years, pregnancy_level=profile.pregnancy.level,
        children_level=profile.children.level, elderly_level=profile.elderly.level,
    )


def _user_warnings(best: Optional[dict], extracted: Optional[dict], status: str, language: str) -> List[str]:
    ar = language == "ar"
    out: List[str] = []
    if status == "ai_unverified":
        out.append("هذا الدواء غير موجود في قاعدة الأدوية المعتمدة، والمعلومات مولّدة بالذكاء الاصطناعي ولم تُراجع من صيدلي. تأكد من الصيدلي قبل الاستخدام."
                   if ar else "This medicine is not in the verified database. The information is AI-generated and not pharmacist-reviewed.")
    if best:
        if best["strength_mismatch"]:
            _m = _STRENGTH_RE.search((extracted or {}).get("strength") or (extracted or {}).get("raw_text") or "")
            pkg = _m.group(0) if _m else "?"
            out.append(f"التركيز المقروء من العلبة ({pkg}) يختلف عن التركيز المسجل ({best['row']['strength']}). الجرعة المعروضة قد لا تنطبق على علبتك."
                       if ar else f"Strength on the box ({pkg}) differs from the recorded one ({best['row']['strength']}). Doses shown may not apply.")
        if best["form_conflict"]:
            out.append("الشكل الدوائي على العلبة يختلف عن المسجل. راجع الصيدلي." if ar
                       else "The dosage form on the box differs from the recorded one. Ask a pharmacist.")
        if not best["strength_matched"] and not best["strength_mismatch"]:
            out.append("لم نتمكن من قراءة التركيز على العلبة. تأكد من التركيز (مثلاً 500 ملغ) قبل الاعتماد على الجرعة." if ar
                       else "Could not read the strength on the box. Check it before relying on any dose.")
        if "generic_only" in best["flags"]:
            out.append("تم التعرف على المادة الفعالة فقط وليس الاسم التجاري." if ar
                       else "Only the active ingredient was matched, not the brand.")
    if status == "needs_confirmation":
        out.append("لم نتأكد من الدواء بنسبة كافية. اختر الدواء الصحيح من القائمة لعرض المعلومات." if ar
                   else "We are not sure which medicine this is. Please pick the correct one to see its information.")
    return out


def _queue_for_review(extracted: dict, report: Optional[AIDrugReport], detected_text: str) -> None:
    """Stores an unknown medicine in pending_medicines for a pharmacist - NEVER in the verified table."""
    try:
        key_src = "|".join([(extracted.get("brand_name_en") or "").lower(), (extracted.get("generic_name") or "").lower(),
                            (extracted.get("strength") or "").lower()])
        pid = "pend_" + hashlib.sha1(key_src.encode("utf-8")).hexdigest()[:16]
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM pending_medicines WHERE id = ?;", (pid,))
            if cur.fetchone():
                cur.execute("UPDATE pending_medicines SET scan_count = scan_count + 1, last_seen_at = ? WHERE id = ?;", (now, pid))
            else:
                cur.execute(
                    "INSERT INTO pending_medicines (id, detected_text, extracted_json, ai_report_json, created_at, last_seen_at) "
                    "VALUES (?, ?, ?, ?, ?, ?);",
                    (pid, detected_text[:500], json.dumps(extracted, ensure_ascii=False),
                     json.dumps(report.model_dump(), ensure_ascii=False) if report else None, now, now))
    except Exception as e:
        print(f"pending queue error: {e}")


def _log_scan(doc_payload: dict, user, detected_text: str, drug_name: str, ok: bool) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO processed_documents (id, user_id, doc_type, file_name, extracted_text, structured_data_json, "
                "is_successful, created_at) VALUES (?, ?, 'medicine_box', 'scanned_box_image', ?, ?, ?, ?);",
                (doc_id, user["id"] if user else None, detected_text[:500], json.dumps(doc_payload, ensure_ascii=False),
                 1 if ok else 0, now_iso))
            if user and ok:
                cur.execute(
                    "INSERT INTO user_activities (id, user_id, event_type, target_id, target_name, is_successful, metadata_json, "
                    "created_at) VALUES (?, ?, 'medicine_scanned', ?, ?, 1, ?, ?);",
                    (f"act_{uuid.uuid4().hex[:12]}", user["id"], doc_id, drug_name,
                     json.dumps({"status": doc_payload.get("status")}), now_iso))
    except Exception as e:
        print(f"scan log error: {e}")


# ----------------------------------------------------------------------------- endpoints
@router.post("/ai", response_model=AIScanResponse)
async def ai_scan_medicine(
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    extracted_text: Optional[str] = Form(None),
    language: Optional[str] = Form("ar"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Safety-first scan: read -> match -> decide (see module docstring)."""
    start = time.perf_counter()
    lang = language or "ar"
    unreadable = UNREADABLE_AR if lang == "ar" else UNREADABLE_EN

    img_b64 = None
    if image and image.filename:
        img_b64 = base64.b64encode(await image.read()).decode("utf-8")
    elif image_base64:
        img_b64 = image_base64

    typed_text = (extracted_text or "").strip()
    extracted: Optional[dict] = None

    if typed_text:
        extracted = {"raw_text": typed_text, "legibility": "clear", "brand_name_en": typed_text}
    elif img_b64:
        extracted, err = await gemini_extract_package(img_b64)
        if err == "rate_limit":
            raise HTTPException(status_code=429, detail="تم تجاوز حد الاستخدام لخدمة قراءة الصور (API Rate Limit). يرجى المحاولة بعد دقيقة." if lang == "ar" else "AI API rate limit exceeded. Please try again in a minute.")
        if err == "service_unavailable":
            raise HTTPException(status_code=503, detail="خدمة التعرف على الصور غير متاحة حالياً. يرجى المحاولة لاحقاً." if lang == "ar" else "Image recognition service is temporarily unavailable.")
        if err == "no_key":
            raise HTTPException(status_code=503, detail="خدمة التعرف الذكي غير مفعّلة حالياً (مفتاح API غير متوفر)." if lang == "ar" else "Image reading is not configured.")
        if err == "not_medicine":
            raise HTTPException(status_code=400, detail="الصورة غير واضحة أو لا تحتوي على علبة دواء يمكن قراءتها." if lang == "ar" else "The image is unclear or does not show a recognizable medicine box.")
        if err in ("failed", "network_error") or not extracted:
            raise HTTPException(status_code=400, detail=unreadable)
    else:
        raise HTTPException(
            status_code=400,
            detail="لم يتم التعرف على صورة واضحة. يرجى إرسال صورة واضحة لعلبة الدواء أو إدخال نص مقروء." if lang == "ar" else "Please provide a clear medicine packaging image or legible text."
        )

    search_text = " ".join(filter(None, [
        extracted.get("brand_name_en"), extracted.get("brand_name_ar"), extracted.get("generic_name"),
        " ".join(a.get("name", "") for a in (extracted.get("active_ingredients") or []) if isinstance(a, dict)),
        extracted.get("strength"), extracted.get("dosage_form"), extracted.get("raw_text"),
    ])).strip()
    has_identity = bool(extracted.get("brand_name_en") or extracted.get("brand_name_ar") or extracted.get("generic_name")
                        or extracted.get("active_ingredients") or typed_text)
    if not search_text or not has_identity:
        raise HTTPException(status_code=400, detail=unreadable)

    results = score_candidates(search_text, extracted)
    status, best = decide(results)
    tokens = extract_medicine_tokens(search_text)

    db_matches = [
        ScannedMatch(medicine=row_to_summary(r["row"]), confidence_score=r["score"], matched_term=r["matched_term"])
        for r in results if r["score"] >= CANDIDATE_MIN_SCORE
    ][:5]
    candidates = [
        ScanCandidate(slug=r["row"]["slug"], trade_name_en=r["row"]["trade_name_en"], trade_name_ar=r["row"]["trade_name_ar"],
                      strength=r["row"]["strength"], dosage_form_en=r["row"]["dosage_form_en"], score=r["score"])
        for r in results if r["score"] >= CANDIDATE_MIN_SCORE
    ][:4]

    ai_report: Optional[AIDrugReport] = None
    best_detail: Optional[MedicineDetail] = None
    safety = None
    confidence: Optional[float] = None
    needs_confirm = True
    source = "ai_unverified"

    if status == "confirmed_db":
        best_detail = row_to_detail(best["row"])
        ai_report = report_from_db(best_detail, lang)
        safety = profile_from_db_row(best_detail)
        confidence = best["score"]
        needs_confirm = False
        source = "verified_database"
    elif status == "needs_confirmation":
        # Do NOT attach medical advice for a guess. The client shows candidates; user confirms via /scan/confirm.
        confidence = best["score"] if best else None
        source = "verified_database"
    else:
        # Not in the verified DB -> clearly-labelled factual extraction, NO hallucinated doses or warnings
        status = "ai_unverified"
        ai_report = report_from_unverified_extraction(extracted, lang)
        if ai_report:
            safety = profile_from_ai_report(ai_report)
        _queue_for_review(extracted, ai_report, search_text)

    warnings = _user_warnings(best if status != "ai_unverified" else None, extracted, status, lang)
    if status == "ai_unverified" and not ai_report:
        warnings.append("تعذّر توليد معلومات موثوقة لهذا المنتج. اسأل الصيدلي." if lang == "ar"
                        else "Could not generate reliable information for this product. Ask a pharmacist.")

    cnn = predict_packaging_cnn(img_b64) if img_b64 else None
    ml = None
    if ai_report:
        ml = predict_drug_ml(
            name=ai_report.drug_name, active=ai_report.active_ingredient,
            form=(cnn or {}).get("predicted_form", "") if (cnn or {}).get("usable") else "",
            uses=ai_report.uses, side_effects=ai_report.warnings)

    ok = ai_report is not None or bool(candidates)
    _log_scan({"status": status, "best": best["row"]["trade_name_en"] if best else None,
               "score": best["score"] if best else None, "extracted": extracted}, current_user, search_text,
              (ai_report.drug_name if ai_report else (best["row"]["trade_name_en"] if best else "unknown")), ok)

    return AIScanResponse(
        detected_text=search_text, ai_report=ai_report, db_matches=db_matches, best_db_match=best_detail,
        is_successful=ok, source=source, latency_ms=round((time.perf_counter() - start) * 1000, 1),
        confidence_score=confidence, saved_to_db=False,
        saved_medicine_slug=best["row"]["slug"] if (best and status == "confirmed_db") else None,
        ml_insights=ml, cnn_packaging=cnn, identification_status=status, needs_user_confirmation=needs_confirm,
        candidates=candidates, extracted=extracted, safety_profile=safety,
        data_origin="verified_database" if status == "confirmed_db" else "ai_unverified",
        warnings_for_user=warnings,
    )


@router.post("/confirm", response_model=AIScanResponse)
async def confirm_medicine(
    slug: str = Form(...),
    language: Optional[str] = Form("ar"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """The user picked the right medicine from the candidates list -> return the VERIFIED record."""
    lang = language or "ar"
    with get_db() as conn:
        row = conn.cursor().execute("SELECT * FROM medicines WHERE slug = ? AND is_hidden = 0 AND is_verified = 1;", (slug,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="الدواء غير موجود في القاعدة المعتمدة" if lang == "ar" else "Medicine not found in the verified database.")
    detail = row_to_detail(row)
    report = report_from_db(detail, lang)
    _log_scan({"status": "user_confirmed", "best": detail.trade_name_en}, current_user, detail.trade_name_en, detail.trade_name_en, True)
    return AIScanResponse(
        detected_text=detail.trade_name_en, ai_report=report, db_matches=[], best_db_match=detail, is_successful=True,
        source="verified_database", confidence_score=1.0, saved_medicine_slug=detail.slug,
        identification_status="confirmed_db", needs_user_confirmation=False,
        safety_profile=profile_from_db_row(detail), data_origin="verified_database", warnings_for_user=[],
    )


# Legacy endpoint kept for backward compatibility
@router.post("", response_model=ScanResponse)
async def process_scanned_box(
    request: ScanRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Legacy endpoint: read text (OCR only, no guessing) and match against the verified database."""
    text = (request.extracted_text or "").strip()
    extracted = None
    if not text and not request.image_base64:
        raise HTTPException(status_code=400, detail="Please provide either scanned text or an image payload.")
    if not text and request.image_base64:
        extracted, _err = await gemini_extract_package(request.image_base64)
        if extracted:
            text = " ".join(filter(None, [extracted.get("brand_name_en"), extracted.get("brand_name_ar"),
                                          extracted.get("generic_name"), extracted.get("strength"),
                                          extracted.get("dosage_form"), extracted.get("raw_text")]))
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from the provided image. Please provide a clear medicine packaging image.")

    tokens = extract_medicine_tokens(text)
    db_matches, best_detail = match_against_database(text, tokens, extracted)
    _log_scan({"status": "legacy", "match_count": len(db_matches),
               "best_match": best_detail.trade_name_en if best_detail else None},
              current_user, text, best_detail.trade_name_en if best_detail else "scanned_medicine", len(db_matches) > 0)
    return ScanResponse(
        detected_text=text, extracted_keywords=tokens[:10], matches=db_matches, best_match=best_detail,
        is_successful=len(db_matches) > 0
    )
