from typing import Any, Callable, Dict, List, Optional
import stripe
import logging
from .models import StripeEvent, ProductModel, PriceModel

default_logger = logging.getLogger(__name__)


class StripeHandler:
    """
    A single interface to the Stripe API.

    Provides a convenience wrapper for Stripe operations, hiding the mechanics
    of working with JSON responses and providing webhook handling.
    """

    def __init__(
        self,
        api_key: str,
        logger: Optional[logging.Logger] = None,
        webhook_secret: str | None = None,
    ) -> None:
        """
        Initialize the StripeHandler with the necessary keys.

        Args:
            api_key: The Stripe API key (secret key).
            logger: Optional logger instance. If not provided, a default logger is created.
            webhook_secret: The Stripe Webhook secret for signature verification.
        """
        self.api_key = api_key
        self.logger = logger or self._setup_default_logger()
        self.webhook_secret = webhook_secret
        self._event_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

    def _setup_default_logger(self) -> logging.Logger:
        """Sets up a basic console logger if none is provided."""
        logger = logging.getLogger("eldercrank.stripe")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def add_event_handler(
        self, event_name: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Registers a function to handle a specific Stripe event.

        Args:
            event_name: The name of the Stripe event (e.g., 'subscription-completed').
            handler: A function reference that will be called when the event occurs.
        """
        self._event_handlers[event_name] = handler

    def remove_event_handler(self, event_name: str) -> None:
        """
        Removes a registered function for a specific Stripe event.

        Args:
            event_name: The name of the Stripe event to remove.
        """
        if event_name in self._event_handlers:
            del self._event_handlers[event_name]

    def process_webhook(self, payload: str, sig_header: str) -> StripeEvent:
        """
        Verifies the signature and dispatches events to registered handlers.

        Args:
            payload: Raw webhook payload from Stripe.
            sig_header: Signature header from Stripe.

        Returns:
            StripeEvent object representing the processed event.

        Raises:
            stripe.error.SignatureVerificationError: If signature verification fails.
            ValueError: If payload parsing fails.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            self.logger.info(f"Received Stripe event: {event['type']} [{event['id']}]")
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}")
            raise e

        event_model = StripeEvent(**event)
        event_type = event_model.type
        handlers = self._event_handlers.get(event_type, [])

        if not handlers:
            self.logger.warning(f"No handlers registered for event: {event_type}")

        handlers += self._event_handlers.get("*", [])

        for handler in handlers:
            try:
                handler(event_model.event_object)
                self.logger.debug(
                    f"Handler {handler.__name__} executed successfully for {event_type}"
                )
            except Exception as e:
                self.logger.exception(
                    f"Error in handler {handler.__name__} for event {event_type}: {str(e)}"
                )

        return event_model

    def create_subscription_product(
        self, name: str, amount: int, currency: str = "usd", interval: str = "month"
    ) -> Dict[str, str]:
        """
        Creates a product and a recurring price in one go.

        Args:
            name: Name of the product.
            amount: Price amount in cents (e.g., 1000 for $10.00).
            currency: Currency code (default: 'usd').
            interval: Billing interval (default: 'month').

        Returns:
            Dictionary with 'product_id' and 'price_id'.
        """
        stripe.api_key = self.api_key
        product = stripe.Product.create(name=name)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=currency,
            recurring={"interval": interval},
        )
        return {"product_id": product.id, "price_id": price.id}

    def list_active_products(self, limit: int = 10) -> List[ProductModel]:
        """
        Retrieves active products along with their recurring prices.

        Args:
            limit: Maximum number of products to retrieve.

        Returns:
            List of ProductModel objects.
        """
        stripe.api_key = self.api_key
        products = stripe.Product.list(active=True, limit=limit)

        result = []
        for p in products:
            prices = stripe.Price.list(product=p.id, active=True)

            price_models = [
                PriceModel(
                    id=pr.id,
                    unit_amount=pr.unit_amount,
                    currency=pr.currency,
                    interval=pr.recurring.get("interval") if pr.recurring else None,
                )
                for pr in prices
            ]

            result.append(
                ProductModel(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    active=p.active,
                    prices=price_models,
                )
            )
        return result

    def deactivate_product(self, product_id: str) -> None:
        """
        Sets a product to inactive so it cannot be used for new subscriptions.

        Args:
            product_id: ID of the product to deactivate.
        """
        stripe.api_key = self.api_key
        stripe.Product.modify(product_id, active=False)

    def deactivate_price(self, price_id: str) -> None:
        """
        Sets a price to inactive.

        Args:
            price_id: ID of the price to deactivate.
        """
        stripe.api_key = self.api_key
        stripe.Price.modify(price_id, active=False)
