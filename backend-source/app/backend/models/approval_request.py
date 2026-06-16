from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from bson import ObjectId

class ApprovalRequestModel(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    sale_id: str
    cajero_id: str
    tipo: Literal["DESCUENTO_TARJETA", "ANULACION", "DEVOLUCION"]
    monto_afectado: float
    justificacion: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    token_autorizacion: Optional[str] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True,
        from_attributes=True,
    )
