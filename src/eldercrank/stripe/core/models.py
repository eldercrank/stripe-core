from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import Any, Dict, Optional, List


class StripeEvent(BaseModel):
    """Model representing a Stripe webhook event."""

    id: str
    type: str
    data: Dict[str, Any]
    api_version: Optional[str] = None

    @property
    def event_object(self) -> Dict[str, Any]:
        """Returns the object contained in the event data."""
        return self.data.get("object", {})


class PriceModel(BaseModel):
    """Model representing a Stripe price."""

    id: str
    unit_amount: int
    currency: str
    recurring_interval: Optional[str] = Field(None, alias="interval")

    model_config = ConfigDict(populate_by_name=True)


class ProductModel(BaseModel):
    """Model representing a Stripe product with its prices."""

    id: str
    name: str
    description: Optional[str] = None
    active: bool
    prices: List[PriceModel] = []
