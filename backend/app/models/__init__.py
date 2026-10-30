"""SQLAlchemy 모델. Alembic autogenerate 가 테이블을 인식하도록 여기서 모두 불러온다."""

from app.models.appointment import Appointment
from app.models.answer import Answer, AnswerRecommendedDepartment, HelpfulVote
from app.models.department import Department
from app.models.hospital_cache import HospitalCache
from app.models.medication import MedicationCheck
from app.models.notification import Notification
from app.models.payment import Payment, PharmacyOrder
from app.models.prescription import Drug, Prescription, PrescriptionItem
from app.models.question import Question, QuestionImage
from app.models.review import Review
from app.models.schedule import DoctorSchedule
from app.models.user import DoctorDocument, DoctorProfile, User

__all__ = [
    "Appointment",
    "Answer",
    "AnswerRecommendedDepartment",
    "Department",
    "DoctorDocument",
    "DoctorProfile",
    "DoctorSchedule",
    "Drug",
    "HelpfulVote",
    "HospitalCache",
    "MedicationCheck",
    "Notification",
    "Payment",
    "PharmacyOrder",
    "Prescription",
    "PrescriptionItem",
    "Question",
    "QuestionImage",
    "Review",
    "User",
]
