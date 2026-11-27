"""
Public Statistics router for Dawaa'i AI.
Computes real database-backed aggregate metrics without fabricated values.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from app.models import PublicStatisticsResponse
from app.database import get_db

router = APIRouter(prefix="/public", tags=["Public Statistics"])

@router.get("/statistics", response_model=PublicStatisticsResponse)
async def get_public_statistics():
    """
    Returns authentic aggregate usage and verified catalog metrics from the live database.
    Strictly forbids fabricated or exaggerated values.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Registered Users Count
        cursor.execute("SELECT COUNT(*) FROM users;")
        registered_users = cursor.fetchone()[0]
        
        # 2. Verified Registered Drug Records (Excluding hidden, supplements, cosmetics)
        cursor.execute("SELECT COUNT(*) FROM medicines WHERE classification = 'registered_drug' AND is_verified = 1 AND is_hidden = 0;")
        registered_drugs = cursor.fetchone()[0]

        # 3. Dietary Supplements
        cursor.execute("SELECT COUNT(*) FROM medicines WHERE classification = 'dietary_supplement' AND is_hidden = 0;")
        dietary_supplements = cursor.fetchone()[0]

        # 4. Cosmetics & Care
        cursor.execute("SELECT COUNT(*) FROM medicines WHERE classification = 'cosmetic_care' AND is_hidden = 0;")
        cosmetics = cursor.fetchone()[0]

        # 5. Medical Devices
        cursor.execute("SELECT COUNT(*) FROM medicines WHERE classification = 'medical_device' AND is_hidden = 0;")
        medical_devices = cursor.fetchone()[0]

        # 6. Hidden / Under Review / Suspicious
        cursor.execute("SELECT COUNT(*) FROM medicines WHERE is_hidden = 1;")
        hidden_count = cursor.fetchone()[0]

        # 7. Total Catalog Records
        cursor.execute("SELECT COUNT(*) FROM medicines;")
        total_records = cursor.fetchone()[0]

        # 8. Linked Grounded Monographs
        cursor.execute("SELECT COUNT(*) FROM medicines WHERE monograph_coverage = 'official_label' AND is_hidden = 0;")
        linked_monographs = cursor.fetchone()[0]

        # 9. Successfully Processed Documents (Leaflets & Scanned Packages)
        cursor.execute("SELECT COUNT(*) FROM processed_documents WHERE is_successful = 1;")
        processed_docs = cursor.fetchone()[0]

        # 10. Published User Reviews
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE is_published = 1 AND moderation_status = 'approved';")
        published_reviews = cursor.fetchone()[0]

        # 11. Average User Rating
        cursor.execute("SELECT AVG(rating) FROM reviews WHERE is_published = 1 AND moderation_status = 'approved';")
        avg_row = cursor.fetchone()
        avg_rating = round(float(avg_row[0]), 1) if avg_row and avg_row[0] is not None else 0.0

        is_zero_state = registered_users == 0 and published_reviews == 0
        now_iso = datetime.now(timezone.utc).isoformat()

        return PublicStatisticsResponse(
            registered_users=registered_users,
            verified_medicine_records=registered_drugs,
            successfully_processed_documents=processed_docs,
            published_user_reviews=published_reviews,
            average_user_rating=avg_rating,
            calculated_at=now_iso,
            is_zero_state=is_zero_state,
            registered_drugs_count=registered_drugs,
            dietary_supplements_count=dietary_supplements,
            cosmetics_count=cosmetics,
            medical_devices_count=medical_devices,
            hidden_review_count=hidden_count,
            total_catalog_records=total_records,
            linked_monographs_count=linked_monographs
        )
