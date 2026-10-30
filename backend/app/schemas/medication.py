"""오늘 복용표 스키마 (P-1, P-2)."""

from typing import Literal

from pydantic import BaseModel

Slot = Literal["morning", "lunch", "evening", "bedtime"]


class DoseDrug(BaseModel):
    name: str
    dose: str
    instruction: str | None


class DoseSlot(BaseModel):
    slot: Slot
    label: str  # 아침
    time: str  # 08:00 (한국 시간, 권장 시각)
    taken: bool
    drugs: list[DoseDrug]


class MedicationPlan(BaseModel):
    prescription_id: int
    appointment_id: int
    doctor_name: str
    note: str | None  # 전체 복용 안내
    day: int  # 오늘이 며칠째 (1부터)
    total_days: int
    slots: list[DoseSlot]


class CheckIn(BaseModel):
    prescription_id: int
    slot: Slot
    taken: bool
