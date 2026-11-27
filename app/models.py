"""
Pydantic data models and schemas for Dawaa'i AI.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, model_validator
from datetime import datetime

# --- Auth & User Schemas ---
class GoogleAuthRequest(BaseModel):
    id_token: str
    preferred_language: Optional[str] = "ar"

class DemoAuthRequest(BaseModel):
    email: EmailStr
    full_name: str
    picture_url: Optional[str] = None
    preferred_language: Optional[str] = "ar"

class LocalLoginRequest(BaseModel):
    email: Optional[str] = Field("demo.patient@dawaai.local", description="User email address")
    password: Optional[str] = Field(None, description="Optional password for local auth")
    full_name: Optional[str] = Field(None, description="Optional user display name")
    role: Optional[str] = Field("user", description="User role (user, admin)")
    preferred_language: Optional[str] = "ar"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    picture_url: Optional[str] = None
    preferred_language: str
    role: str
    has_completed_onboarding: bool
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class OnboardingUpdateRequest(BaseModel):
    preferred_language: str
    has_completed_onboarding: bool = True

# --- Review Schemas ---
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional user review text")
    category: Optional[str] = Field("ease_of_use", description="Review category")
    consent_public: bool = Field(True, description="Consent to display review publicly")

class ReviewResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    category: Optional[str] = None
    review_type: str
    consent_public: bool
    is_published: bool
    moderation_status: str
    created_at: str

class ReviewStatusResponse(BaseModel):
    is_authenticated: bool
    has_meaningful_use: bool
    has_submitted_first_review: bool
    should_prompt_review: bool
    pending_review_event: Optional[str] = None

class RatingDistribution(BaseModel):
    star_1: int = 0
    star_2: int = 0
    star_3: int = 0
    star_4: int = 0
    star_5: int = 0

class ReviewsPublicResponse(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: RatingDistribution
    reviews: List[ReviewResponse]

class AdminModerationRequest(BaseModel):
    moderation_status: str = Field(..., pattern="^(approved|hidden)$")
    is_published: bool = True

# --- Activity Schemas ---
class ActivityLogCreate(BaseModel):
    event_type: str  # 'medicine_view', 'leaflet_processed', 'assistant_explanation', 'medicine_scanned'
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    is_successful: bool = True
    metadata: Optional[Dict[str, Any]] = None

# --- Medicine Schemas ---
class MedicineSummary(BaseModel):
    id: str
    slug: str
    trade_name_en: str
    trade_name_ar: str
    generic_name: str
    active_ingredient_en: str
    active_ingredient_ar: str
    category_en: str
    category_ar: str
    dosage_form_en: str
    dosage_form_ar: str
    strength: str
    is_verified: bool
    source_authority: str
    pediatric_safety_en: Optional[str] = None
    pediatric_safety_ar: Optional[str] = None
    pregnancy_safety_en: Optional[str] = None
    pregnancy_safety_ar: Optional[str] = None
    geriatric_safety_en: Optional[str] = None
    geriatric_safety_ar: Optional[str] = None
    price: Optional[float] = None
    manufacturer: Optional[str] = None
    data_origin: Optional[str] = "curated"
    classification: Optional[str] = "registered_drug"
    clean_strength: Optional[str] = None
    clean_dosage_form: Optional[str] = None
    clean_route: Optional[str] = None
    atc_code: Optional[str] = None
    pharmacological_class_en: Optional[str] = None
    pharmacological_class_ar: Optional[str] = None
    has_pediatric_data: Optional[bool] = False
    has_pregnancy_data: Optional[bool] = False
    has_geriatric_data: Optional[bool] = False
    monograph_coverage: Optional[str] = "none"
    is_hidden: Optional[bool] = False

class MedicineDetail(MedicineSummary):
    indications_en: str
    indications_ar: str
    dosage_instructions_en: str
    dosage_instructions_ar: str
    contraindications_en: str
    contraindications_ar: str
    side_effects_en: str
    side_effects_ar: str
    interactions_en: str
    interactions_ar: str
    pregnancy_safety_en: Optional[str] = None
    pregnancy_safety_ar: Optional[str] = None
    pediatric_safety_en: Optional[str] = None
    pediatric_safety_ar: Optional[str] = None
    geriatric_safety_en: Optional[str] = None
    geriatric_safety_ar: Optional[str] = None
    storage_en: str
    storage_ar: str
    source_url: str
    verified_at: Optional[str] = None
    adult_dosage_frequency: Optional[str] = None
    adult_dosage_interval: Optional[str] = None
    adult_dosage_max_daily: Optional[str] = None
    adult_dosage_duration: Optional[str] = None
    pediatric_min_age: Optional[float] = None
    pediatric_max_age: Optional[float] = None
    pediatric_dose_by_weight: Optional[str] = None
    pediatric_status: Optional[str] = None
    pregnancy_category: Optional[str] = None
    pregnancy_status: Optional[str] = None
    lactation_status: Optional[str] = None
    geriatric_status: Optional[str] = None
    geriatric_warnings: Optional[str] = None
    monograph_source: Optional[str] = None
    monograph_url: Optional[str] = None
    monograph_version_date: Optional[str] = None

class MedicineSearchResponse(BaseModel):
    query: str
    total: int
    results: List[MedicineSummary]

# --- Scan & OCR Schemas ---
class ScanRequest(BaseModel):
    image_base64: Optional[str] = None
    extracted_text: Optional[str] = None

class ScannedMatch(BaseModel):
    medicine: MedicineSummary
    confidence_score: float
    matched_term: str

class ScanResponse(BaseModel):
    detected_text: str
    extracted_keywords: List[str]
    matches: List[ScannedMatch]
    best_match: Optional[MedicineDetail] = None
    is_successful: bool

# --- AI-Powered Universal Drug Recognition ---
class AIDrugReport(BaseModel):
    drug_name: str = Field(..., description="Trade and scientific drug name")
    active_ingredient: str = Field(default="", description="Active pharmaceutical ingredient and strength/concentration")
    uses: str = Field(..., description="Detailed therapeutic indications and uses")
    dosage_and_usage: str = Field(default="", description="Standard dosage, administration method, and timing")
    dosage_instructions: Optional[str] = Field(default="", description="Dosage instructions (backward compatibility alias)")
    pregnancy_safety: str = Field(..., description="Safety during pregnancy and breastfeeding")
    children_safety: str = Field(..., description="Safety for children with allowed age")
    elderly_safety: str = Field(default="", description="Precautions for elderly and chronic illnesses")
    warnings: str = Field(..., description="Important warnings and contraindications")
    drug_interactions: str = Field(default="", description="Key drug-drug interactions")
    # Structured safety hints (filled by the AI only when no verified DB record exists)
    min_age_years: Optional[float] = Field(default=None, description="Minimum age in years, null if unknown")
    pregnancy_level: Optional[str] = Field(default=None, description="safe | caution | avoid | unknown")
    children_level: Optional[str] = Field(default=None, description="safe | caution | avoid | unknown")
    elderly_level: Optional[str] = Field(default=None, description="safe | caution | avoid | unknown")

    @model_validator(mode="after")
    def sync_dosages(self):
        if not self.dosage_and_usage and self.dosage_instructions:
            self.dosage_and_usage = self.dosage_instructions
        elif not self.dosage_instructions and self.dosage_and_usage:
            self.dosage_instructions = self.dosage_and_usage
        return self

class PopulationSafety(BaseModel):
    level: str = Field(default="unknown", description="safe | caution | avoid | unknown")
    label_ar: str = "غير محدد - اسأل الصيدلي"
    label_en: str = "Unknown - ask a pharmacist"
    detail: str = ""

class SafetyProfile(BaseModel):
    """Structured, UI-ready safety summary (age + special populations)."""
    min_age_years: Optional[float] = Field(default=None, description="Minimum age for THIS dosage form, null if unknown")
    min_age_label_ar: str = "السن الأدنى غير محدد - اسأل الصيدلي"
    min_age_label_en: str = "Minimum age not specified - ask a pharmacist"
    pregnancy: PopulationSafety = PopulationSafety()
    children: PopulationSafety = PopulationSafety()
    elderly: PopulationSafety = PopulationSafety()
    source: str = Field(default="ai_unverified", description="'verified_database' | 'ai_unverified'")

class ScanCandidate(BaseModel):
    slug: str
    trade_name_en: str
    trade_name_ar: str
    strength: str
    dosage_form_en: str
    score: float

class AIScanResponse(BaseModel):
    detected_text: str
    ai_report: Optional[AIDrugReport] = None
    db_matches: List[ScannedMatch] = []
    best_db_match: Optional[MedicineDetail] = None
    is_successful: bool
    source: str = Field(default="ai", description="'verified_database' | 'ai_unverified' | 'clinical_engine'")
    latency_ms: Optional[float] = Field(default=None, description="Processing latency in milliseconds")
    confidence_score: Optional[float] = Field(default=None, description="Real identification confidence 0-1, null if unknown")
    saved_to_db: bool = Field(default=False, description="Deprecated: AI results are no longer auto-saved as verified")
    saved_medicine_slug: Optional[str] = Field(default=None, description="Slug of matched verified medicine, if any")
    ml_insights: Optional[Dict[str, Any]] = Field(default=None, description="Secondary ML hints (NOT a safety verdict)")
    cnn_packaging: Optional[Dict[str, Any]] = Field(default=None, description="Secondary packaging-form hint from CNN")
    # --- new trust / safety fields ---
    identification_status: str = Field(default="uncertain", description="confirmed_db | needs_confirmation | ai_unverified | unreadable")
    needs_user_confirmation: bool = True
    candidates: List[ScanCandidate] = []
    extracted: Optional[Dict[str, Any]] = Field(default=None, description="Fields read from the package (brand, generic, strength, form)")
    safety_profile: Optional[SafetyProfile] = None
    data_origin: str = Field(default="ai_unverified", description="'verified_database' | 'ai_unverified'")
    warnings_for_user: List[str] = []

# --- Drug-Drug Interaction Checker Schemas ---
class InteractionCheckRequest(BaseModel):
    medicine_a: str = Field(..., description="First medicine name, trade name, or active ingredient")
    medicine_b: str = Field(..., description="Second medicine name, trade name, or active ingredient")
    language: Optional[str] = "ar"

class InteractionCheckResponse(BaseModel):
    medicine_a_name: str
    medicine_b_name: str
    has_interaction: bool
    severity: str = Field(..., description="'major' | 'moderate' | 'minor' | 'none'")
    headline_ar: str
    headline_en: str
    mechanism_ar: str
    mechanism_en: str
    recommendation_ar: str
    recommendation_en: str
    safe_alternatives_ar: List[str] = []
    safe_alternatives_en: List[str] = []
    source_authority: str = "Saudi FDA, US FDA & Micromedex Interactions Database"


# --- Leaflet Reader Schemas ---
class LeafletParseRequest(BaseModel):
    text: str
    language: str = "ar"
    simplify: bool = True

class LeafletSection(BaseModel):
    title_ar: str
    title_en: str
    content: str
    simplified_content: Optional[str] = None
    icon: str

class LeafletParseResponse(BaseModel):
    document_title: str
    detected_medicine: Optional[str] = None
    sections: List[LeafletSection]
    identified_precautions: List[str]
    is_successful: bool

# --- AI Assistant Schemas ---
class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class AssistantQueryRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    medicine_context_id: Optional[str] = None
    language: str = "ar"

class AssistantCitation(BaseModel):
    authority: str
    title: str
    url: str

class AssistantQueryResponse(BaseModel):
    reply: str
    citations: List[AssistantCitation]
    disclaimer: str
    is_grounded: bool

# --- Statistics Schemas ---
class PublicStatisticsResponse(BaseModel):
    registered_users: int
    verified_medicine_records: int
    successfully_processed_documents: int
    published_user_reviews: int
    average_user_rating: float
    calculated_at: str
    is_zero_state: bool
    registered_drugs_count: int = 0
    dietary_supplements_count: int = 0
    cosmetics_count: int = 0
    medical_devices_count: int = 0
    hidden_review_count: int = 0
    total_catalog_records: int = 0
    linked_monographs_count: int = 0
