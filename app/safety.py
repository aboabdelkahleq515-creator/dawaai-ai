"""
Structured safety summary for Dawaa'i AI.

Turns the free-text safety fields of a VERIFIED database record (or, as a clearly-labelled
fallback, the structured hints of an AI report) into a UI-ready profile:
  - minimum age
  - pregnancy / children / elderly level: safe | caution | avoid | unknown

Design rule: when the text is ambiguous the answer is "unknown" (never "safe").
"""
import re
from typing import Optional, Tuple

from app.models import PopulationSafety, SafetyProfile

LEVELS = ("safe", "caution", "avoid", "unknown")

_LABELS = {
    "pregnancy": {
        "safe": ("آمن نسبياً للحمل (بإشراف الطبيب)", "Generally considered acceptable in pregnancy (under medical supervision)"),
        "caution": ("استشر الطبيب قبل الاستخدام أثناء الحمل", "Consult a doctor before use in pregnancy"),
        "avoid": ("غير آمن أثناء الحمل - تجنبه", "Not safe in pregnancy - avoid"),
        "unknown": ("غير محدد - اسأل الصيدلي أو الطبيب", "Unknown - ask a pharmacist or doctor"),
    },
    "children": {
        "safe": ("مناسب للأطفال بالجرعة المحسوبة بالوزن", "Suitable for children with weight-based dosing"),
        "caution": ("للأطفال فقط بإشراف الطبيب", "Children only under medical supervision"),
        "avoid": ("غير مناسب للأطفال", "Not suitable for children"),
        "unknown": ("غير محدد - اسأل الصيدلي أو طبيب الأطفال", "Unknown - ask a pharmacist or pediatrician"),
    },
    "elderly": {
        "safe": ("مناسب لكبار السن", "Suitable for elderly patients"),
        "caution": ("لكبار السن بحذر وبجرعة مناسبة", "Use with caution in the elderly"),
        "avoid": ("يُفضّل تجنبه لكبار السن", "Best avoided in the elderly"),
        "unknown": ("غير محدد - اسأل الصيدلي أو الطبيب", "Unknown - ask a pharmacist or doctor"),
    },
}


# --------------------------------------------------------------------------- age
_AGE_PATTERNS = [
    # "12 years and older", "12+ years", "12 years or older", "aged 12 years", "from 6 years"
    (re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:and|or)?\s*(?:older|above|and over|\+)?", re.I), "year"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:months?)\s*(?:and|or)?\s*(?:older|above)?", re.I), "month"),
    (re.compile(r"(?:من سن|فوق|اكبر من|أكبر من|فما فوق|سن)\s*(\d+(?:\.\d+)?)\s*(?:سنة|سنوات|عاما|عاماً|سنه)", re.I), "year"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:سنة|سنوات|عاما|عاماً|سنه)\s*(?:فما فوق|فأكثر|فاكثر)", re.I), "year"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:شهر|أشهر|اشهر|شهور)", re.I), "month"),
]


def extract_min_age_years(pediatric_text_en: str = "", pediatric_text_ar: str = "") -> Optional[float]:
    """
    Best-effort minimum age (years) for THIS product from the pediatric text.
    Conservative: when several limits appear, the HIGHEST one wins. None when it cannot be determined.
    """
    text_en = (pediatric_text_en or "").strip()
    low = text_en.lower()

    # "not established / not approved ... under 18"  -> adults only
    has_positive = "approved for" in low or "authorized" in low
    if "not been established" in low or "not established" in low or (re.search(r"\bnot approved\b", low) and not has_positive):
        return 18.0
    if re.search(r"(strictly )?contraindicated in (all )?(pediatric|children|paediatric)\b", low) and "under" not in low:
        return 18.0

    limits = []
    # restrictions: "under 12", "not for children under 12 years", "< 40 kg" (kg is ignored)
    for m in re.finditer(r"(?:under|below)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", low):
        if any(k in low for k in ("contraindicated", "not recommended", "not for", "not suitable", "not intended")):
            limits.append(float(m.group(1)))
    if limits:
        return max(limits)

    # positive statements: "12+", "12 years and older", "children 6 to 17 years" (-> first number), ">= 12 years"
    for m in re.finditer(r"(?:>=?\s*)?(\d+(?:\.\d+)?)\s*(?:\+|(?:to|-|–)\s*\d+\s*)?\s*(years?|yrs?|months?)?", low):
        # only accept numbers that are clearly ages
        span = low[max(0, m.start() - 25): m.end() + 25]
        if not re.search(r"children|adolescents|aged|from|age|years|months|\+", span):
            continue
        unit = (m.group(2) or "").lower()
        is_age = bool(unit) or "+" in m.group(0)
        if not is_age:
            continue
        val = float(m.group(1))
        return round(val / 12, 2) if unit.startswith("month") else val

    text_ar = (pediatric_text_ar or "").strip()
    for pat, unit in _AGE_PATTERNS[2:]:
        m = pat.search(text_ar)
        if m:
            val = float(m.group(1))
            return round(val / 12, 2) if unit == "month" else val
    return None


def age_labels(min_age: Optional[float]) -> Tuple[str, str]:
    if min_age is None:
        return ("السن الأدنى غير محدد - اسأل الصيدلي", "Minimum age not specified - ask a pharmacist")
    if min_age >= 18:
        return ("للبالغين فقط (18 سنة فأكثر)", "Adults only (18+ years)")
    if min_age < 1:
        months = max(1, int(round(min_age * 12)))
        return (f"من عمر {months} شهر", f"From {months} months of age")
    n = int(min_age) if float(min_age).is_integer() else min_age
    return (f"من سن {n} سنة فأكثر", f"From {n} years of age")


# ----------------------------------------------------------------------- pregnancy
def classify_pregnancy(text_en: str = "", text_ar: str = "") -> str:
    low = (text_en or "").lower()
    ar = text_ar or ""
    if not low and not ar:
        return "unknown"

    # Strictest signals first
    if re.search(r"category\s*x\b", low) or "strictly contraindicated" in low or "contraindicated in pregnancy" in low \
            or "contraindicated during pregnancy" in low or "يمنع منعاً باتاً" in ar or "ممنوع في الحمل" in ar \
            or "ممنوع منعاً باتاً" in ar:
        return "avoid"
    if re.search(r"category\s*d\b", low):
        # Many NSAIDs are "Category D in 3rd trimester": treat as avoid-in-part -> caution is too soft.
        return "avoid"
    if "avoid" in low and "pregnan" in low and "unless" not in low and "trimester" not in low:
        return "avoid"
    if re.search(r"category\s*c\b", low) or "avoid" in low or "unless" in low or "only if" in low:
        return "caution"
    if re.search(r"category\s*(a|b)\b", low) or "safe in pregnancy" in low or "generally considered safe" in low:
        return "safe"
    if "يفضل تجنبه" in ar or "يستخدم فقط" in ar or "للضرورة" in ar:
        return "caution"
    if "آمن" in ar:
        return "safe"
    return "unknown"


# --------------------------------------------------------------------------- children
def classify_children(pediatric_text_en: str = "", pediatric_text_ar: str = "", min_age: Optional[float] = None) -> str:
    """avoid | caution | safe | unknown.  'safe' only when the record explicitly says so; age alone is never 'safe'."""
    low = (pediatric_text_en or "").lower()
    if not low and not (pediatric_text_ar or "").strip():
        return "unknown"
    if min_age is not None and min_age >= 18:
        return "avoid"
    has_positive = "approved for" in low or "authorized" in low
    if "not been established" in low or "not established" in low or ("not approved" in low and not has_positive):
        return "avoid"
    if "strictly contraindicated" in low and "under" not in low:
        return "avoid"
    safe_markers = ("first-line", "essential", "extremely safe", "universal supplementation")
    if any(k in low for k in safe_markers):
        return "safe"
    if min_age is not None or any(k in low for k in ("specialist", "off-label", "supervision", "guidance", "only")):
        return "caution"
    return "unknown"


# --------------------------------------------------------------------------- elderly
def classify_elderly(text_en: str = "", text_ar: str = "") -> str:
    low = (text_en or "").lower()
    if not low and not (text_ar or "").strip():
        return "unknown"
    avoid_markers = ("avoid in the elderly", "high risk", "significantly higher risk", "fatal", "heightened caution",
                     "high vulnerability", "higher vulnerability", "high risk of")
    if any(k in low for k in avoid_markers):
        return "caution"   # never auto-"avoid" the elderly from text alone: clinical call -> caution
    caution_markers = ("caution", "monitor", "adjust", "reduce", "lowest", "start with", "start at", "increased risk",
                       "renal", "dose reduction", "higher bleeding", "starting dose", "maximum", "minimum", "shortest",
                       "susceptible", "mandatory", "vulnerab", "co-prescribe", "develop", "sensitiv")
    if any(k in low for k in caution_markers):
        return "caution"
    if "safe" in low or "well tolerated" in low or "no dosage adjustment" in low or "preferred" in low \
            or "highly recommended" in low:
        return "safe"
    return "unknown"


def _pop(kind: str, level: str, detail: str) -> PopulationSafety:
    ar, en = _LABELS[kind][level]
    return PopulationSafety(level=level, label_ar=ar, label_en=en, detail=(detail or "")[:600])


# ------------------------------------------------------------------------ public API
def profile_from_db_row(med) -> SafetyProfile:
    """med: a MedicineDetail (verified DB record)."""
    ped_en = getattr(med, "pediatric_safety_en", "") or ""
    ped_ar = getattr(med, "pediatric_safety_ar", "") or ""
    min_age = extract_min_age_years(ped_en, ped_ar)

    preg = classify_pregnancy(getattr(med, "pregnancy_safety_en", ""), getattr(med, "pregnancy_safety_ar", ""))
    kids = classify_children(ped_en, ped_ar, min_age)
    old = classify_elderly(getattr(med, "geriatric_safety_en", ""), getattr(med, "geriatric_safety_ar", ""))
    ar_label, en_label = age_labels(min_age)
    return SafetyProfile(
        min_age_years=min_age,
        min_age_label_ar=ar_label,
        min_age_label_en=en_label,
        pregnancy=_pop("pregnancy", preg, getattr(med, "pregnancy_safety_ar", "")),
        children=_pop("children", kids, ped_ar),
        elderly=_pop("elderly", old, getattr(med, "geriatric_safety_ar", "")),
        source="verified_database",
    )


def profile_from_ai_report(report) -> SafetyProfile:
    """AI report: only trusts structured enum hints; everything else becomes 'unknown'."""
    def lvl(v):
        v = (v or "unknown").lower().strip()
        return v if v in LEVELS else "unknown"

    min_age = report.min_age_years if getattr(report, "min_age_years", None) is not None else None
    ar_label, en_label = age_labels(min_age)
    return SafetyProfile(
        min_age_years=min_age,
        min_age_label_ar=ar_label,
        min_age_label_en=en_label,
        pregnancy=_pop("pregnancy", lvl(report.pregnancy_level), report.pregnancy_safety),
        children=_pop("children", lvl(report.children_level), report.children_safety),
        elderly=_pop("elderly", lvl(report.elderly_level), report.elderly_safety),
        source="ai_unverified",
    )
