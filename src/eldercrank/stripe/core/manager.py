"""
StripeManager class for handling all Stripe data operations.

This class focuses solely on data operations and does not handle webhooks.
For webhook handling, use StripeHandler instead.
"""

from typing import Any, Callable, Dict, List, Optional
import stripe
import logging
from .models import StripeEvent


class StripeManager:
    """
    A manager class focused on Stripe data operations.

    This class handles all Stripe API interactions except webhook processing.
    Use StripeHandler for webhook-related functionality.
    """

    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the StripeManager with the necessary keys.

        Args:
            api_key: The Stripe API key (secret key).
            logger: Optional logger instance. If not provided, a default logger is created.
        """
        self.api_key = api_key
        stripe.api_key = self.api_key
        self.logger = logger or self._setup_default_logger()
        self._webhook_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

    def _setup_default_logger(self) -> logging.Logger:
        """Sets up a basic console logger if none is provided."""
        logger = logging.getLogger("eldercrank.stripe.manager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def add_webhook_handler(
        self, event_name: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Registers a function to handle a specific Stripe webhook event.

        Args:
            event_name: The name of the Stripe event.
            handler: A function reference that will be called when the event occurs.
        """
        self._webhook_handlers[event_name] = handler
        self.logger.info(f"Added webhook handler for event: {event_name}")

    def remove_webhook_handler(self, event_name: str) -> None:
        """
        Removes a registered function for a specific Stripe webhook event.

        Args:
            event_name: The name of the Stripe event to remove.
        """
        if event_name in self._webhook_handlers:
            del self._webhook_handlers[event_name]
            self.logger.info(f"Removed webhook handler for event: {event_name}")
        else:
            self.logger.warning(f"No webhook handler found for event: {event_name}")

    def process_webhook_payload(
        self, payload: str, sig_header: str, webhook_secret: str
    ) -> Optional[StripeEvent]:
        """
        Verifies the webhook signature and processes the payload.

        Args:
            payload: Raw webhook payload from Stripe.
            sig_header: Signature header from Stripe.
            webhook_secret: Secret used to verify the webhook.

        Returns:
            StripeEvent object if processing is successful.

        Raises:
            stripe.error.SignatureVerificationError: If signature verification fails.
            ValueError: If payload parsing fails.
        """
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            self.logger.info(f"Received Stripe event: {event['type']} [{event['id']}]")
        except ValueError as e:
            self.logger.error(f"Webhook payload parsing failed: {str(e)}")
            raise e
        except stripe.error.SignatureVerificationError as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}")
            raise e

        event_model = StripeEvent(**event)
        event_type = event_model.type
        handlers = self._webhook_handlers.get(event_type, [])

        if not handlers:
            self.logger.warning(f"No handlers registered for event: {event_type}")

        handlers += self._webhook_handlers.get("*", [])

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

    # PRODUCT OPERATIONS

    def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        active: bool = True,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new product in Stripe."""
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
                active=active,
                metadata=metadata or {},
            )
            self.logger.info(f"Created product: {product.id}")
            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "active": product.active,
                "created": product.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error creating product: {str(e)}")
            raise e

    def retrieve_product(self, product_id: str) -> Dict[str, Any]:
        """Retrieve a product from Stripe."""
        try:
            product = stripe.Product.retrieve(product_id)
            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "active": product.active,
                "created": product.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error retrieving product {product_id}: {str(e)}")
            raise e

    def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Update an existing product in Stripe."""
        try:
            update_params = {}
            if name is not None:
                update_params["name"] = name
            if description is not None:
                update_params["description"] = description
            if active is not None:
                update_params["active"] = active
            if metadata is not None:
                update_params["metadata"] = metadata

            product = stripe.Product.modify(product_id, **update_params)
            self.logger.info(f"Updated product: {product.id}")
            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "active": product.active,
                "created": product.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error updating product {product_id}: {str(e)}")
            raise e

    def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Delete (deactivate) a product in Stripe."""
        try:
            product = stripe.Product.modify(product_id, active=False)
            self.logger.info(f"Deactivated product: {product.id}")
            return {"id": product.id, "deleted": True, "active": product.active}
        except stripe.error.StripeError as e:
            self.logger.error(f"Error deleting product {product_id}: {str(e)}")
            raise e

    def list_products(
        self, active: Optional[bool] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List products in Stripe."""
        try:
            params = {"limit": limit}
            if active is not None:
                params["active"] = active

            products = stripe.Product.list(**params)
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "active": p.active,
                    "created": p.created,
                }
                for p in products
            ]
        except stripe.error.StripeError as e:
            self.logger.error(f"Error listing products: {str(e)}")
            raise e

    # PRICE OPERATIONS

    def create_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str = "usd",
        recurring: Optional[Dict[str, str]] = None,
        nickname: Optional[str] = None,
        active: bool = True,
    ) -> Dict[str, Any]:
        """Create a new price in Stripe."""
        try:
            price_data = {
                "product": product_id,
                "unit_amount": unit_amount,
                "currency": currency,
                "active": active,
            }

            if recurring:
                price_data["recurring"] = recurring
            if nickname:
                price_data["nickname"] = nickname

            price = stripe.Price.create(**price_data)
            self.logger.info(f"Created price: {price.id}")
            return {
                "id": price.id,
                "product_id": price.product,
                "unit_amount": price.unit_amount,
                "currency": price.currency,
                "recurring": price.recurring,
                "active": price.active,
                "created": price.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error creating price: {str(e)}")
            raise e

    def retrieve_price(self, price_id: str) -> Dict[str, Any]:
        """Retrieve a price from Stripe."""
        try:
            price = stripe.Price.retrieve(price_id)
            return {
                "id": price.id,
                "product_id": price.product,
                "unit_amount": price.unit_amount,
                "currency": price.currency,
                "recurring": price.recurring,
                "active": price.active,
                "created": price.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error retrieving price {price_id}: {str(e)}")
            raise e

    def update_price(
        self,
        price_id: str,
        active: Optional[bool] = None,
        nickname: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing price in Stripe."""
        try:
            update_params = {}
            if active is not None:
                update_params["active"] = active
            if nickname is not None:
                update_params["nickname"] = nickname

            price = stripe.Price.modify(price_id, **update_params)
            self.logger.info(f"Updated price: {price.id}")
            return {
                "id": price.id,
                "product_id": price.product,
                "unit_amount": price.unit_amount,
                "currency": price.currency,
                "recurring": price.recurring,
                "active": price.active,
                "created": price.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error updating price {price_id}: {str(e)}")
            raise e

    def delete_price(self, price_id: str) -> Dict[str, Any]:
        """Delete (deactivate) a price in Stripe."""
        try:
            price = stripe.Price.modify(price_id, active=False)
            self.logger.info(f"Deactivated price: {price.id}")
            return {"id": price.id, "deleted": True, "active": price.active}
        except stripe.error.StripeError as e:
            self.logger.error(f"Error deleting price {price_id}: {str(e)}")
            raise e

    def list_prices(
        self,
        active: Optional[bool] = None,
        product_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List prices in Stripe."""
        try:
            params = {"limit": limit}
            if active is not None:
                params["active"] = active
            if product_id is not None:
                params["product"] = product_id

            prices = stripe.Price.list(**params)
            return [
                {
                    "id": p.id,
                    "product_id": p.product,
                    "unit_amount": p.unit_amount,
                    "currency": p.currency,
                    "recurring": p.recurring,
                    "active": p.active,
                    "created": p.created,
                }
                for p in prices
            ]
        except stripe.error.StripeError as e:
            self.logger.error(f"Error listing prices: {str(e)}")
            raise e

    # CUSTOMER OPERATIONS

    def create_customer(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        description: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new customer in Stripe."""
        try:
            customer_data = {}
            if name:
                customer_data["name"] = name
            if email:
                customer_data["email"] = email
            if description:
                customer_data["description"] = description
            if phone:
                customer_data["phone"] = phone
            if address:
                customer_data["address"] = address
            if metadata:
                customer_data["metadata"] = metadata

            customer = stripe.Customer.create(**customer_data)
            self.logger.info(f"Created customer: {customer.id}")
            return {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "description": customer.description,
                "phone": customer.phone,
                "address": customer.address,
                "created": customer.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error creating customer: {str(e)}")
            raise e

    def retrieve_customer(self, customer_id: str) -> Dict[str, Any]:
        """Retrieve a customer from Stripe."""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "description": customer.description,
                "phone": customer.phone,
                "address": customer.address,
                "created": customer.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            raise e

    def update_customer(
        self,
        customer_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        description: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Update an existing customer in Stripe."""
        try:
            update_params = {}
            if name is not None:
                update_params["name"] = name
            if email is not None:
                update_params["email"] = email
            if description is not None:
                update_params["description"] = description
            if phone is not None:
                update_params["phone"] = phone
            if address is not None:
                update_params["address"] = address
            if metadata is not None:
                update_params["metadata"] = metadata

            customer = stripe.Customer.modify(customer_id, **update_params)
            self.logger.info(f"Updated customer: {customer.id}")
            return {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "description": customer.description,
                "phone": customer.phone,
                "address": customer.address,
                "created": customer.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error updating customer {customer_id}: {str(e)}")
            raise e

    def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        """Delete a customer in Stripe."""
        try:
            customer = stripe.Customer.delete(customer_id)
            self.logger.info(f"Deleted customer: {customer.id}")
            return {"id": customer.id, "deleted": customer.deleted}
        except stripe.error.StripeError as e:
            self.logger.error(f"Error deleting customer {customer_id}: {str(e)}")
            raise e

    def list_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List customers in Stripe."""
        try:
            customers = stripe.Customer.list(limit=limit)
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "description": c.description,
                    "phone": c.phone,
                    "address": c.address,
                    "created": c.created,
                }
                for c in customers
            ]
        except stripe.error.StripeError as e:
            self.logger.error(f"Error listing customers: {str(e)}")
            raise e

    # SUBSCRIPTION OPERATIONS

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_period_days: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new subscription in Stripe."""
        try:
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
            }

            if trial_period_days:
                subscription_data["trial_period_days"] = trial_period_days
            if metadata:
                subscription_data["metadata"] = metadata

            subscription = stripe.Subscription.create(**subscription_data)
            self.logger.info(f"Created subscription: {subscription.id}")
            return {
                "id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "created": subscription.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error creating subscription: {str(e)}")
            raise e

    def retrieve_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve a subscription from Stripe."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "created": subscription.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(
                f"Error retrieving subscription {subscription_id}: {str(e)}"
            )
            raise e

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription in Stripe."""
        try:
            subscription = stripe.Subscription.cancel(subscription_id)
            self.logger.info(f"Cancelled subscription: {subscription.id}")
            return {
                "id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at,
            }
        except stripe.error.StripeError as e:
            self.logger.error(
                f"Error cancelling subscription {subscription_id}: {str(e)}"
            )
            raise e

    def list_subscriptions(
        self, customer_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List subscriptions in Stripe."""
        try:
            params = {"limit": limit}
            if customer_id:
                params["customer"] = customer_id

            subscriptions = stripe.Subscription.list(**params)
            return [
                {
                    "id": s.id,
                    "customer_id": s.customer,
                    "status": s.status,
                    "current_period_start": s.current_period_start,
                    "current_period_end": s.current_period_end,
                    "created": s.created,
                }
                for s in subscriptions
            ]
        except stripe.error.StripeError as e:
            self.logger.error(f"Error listing subscriptions: {str(e)}")
            raise e

    # CHECKOUT SESSION OPERATIONS

    def create_checkout_session(
        self,
        customer_id: str,
        line_items: List[Dict[str, Any]],
        success_url: str,
        cancel_url: str,
        mode: str = "subscription",
        metadata: Optional[Dict[str, str]] = None,
        billing_address_collection: Optional[str] = None,
        payment_method_types: Optional[List[str]] = None,
        allow_promotion_codes: bool = False,
        expires_at: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session.

        Args:
            customer_id: The ID of the customer.
            line_items: List of line items (each with 'price' and 'quantity').
            success_url: URL to redirect after successful checkout.
            cancel_url: URL to redirect after cancelled checkout.
            mode: Payment mode ('subscription', 'payment', or 'setup').
            metadata: Optional metadata for the session.
            billing_address_collection: Whether to collect billing address.
            payment_method_types: List of payment method types to accept.
            allow_promotion_codes: Whether to allow promotion codes.
            expires_at: Unix timestamp when the session expires.

        Returns:
            Dictionary with checkout session details including 'url' and 'id'.
        """
        try:
            session_data = {
                "customer": customer_id,
                "mode": mode,
                "line_items": line_items,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "allow_promotion_codes": allow_promotion_codes,
            }

            if metadata:
                session_data["metadata"] = metadata
            if billing_address_collection:
                session_data["billing_address_collection"] = billing_address_collection
            if payment_method_types:
                session_data["payment_method_types"] = payment_method_types
            if expires_at:
                session_data["expires_at"] = expires_at

            session = stripe.checkout.Session.create(**session_data)
            self.logger.info(f"Created checkout session: {session.id}")
            return {
                "id": session.id,
                "url": session.url,
                "customer_id": session.customer,
                "mode": session.mode,
                "status": session.status,
                "expires_at": session.expires_at,
                "created": session.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error creating checkout session: {str(e)}")
            raise e

    def retrieve_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a checkout session by ID.

        Args:
            session_id: The checkout session ID.

        Returns:
            Dictionary with checkout session details.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "url": session.url,
                "customer_id": session.customer,
                "mode": session.mode,
                "status": session.status,
                "expires_at": session.expires_at,
                "created": session.created,
            }
        except stripe.error.StripeError as e:
            self.logger.error(
                f"Error retrieving checkout session {session_id}: {str(e)}"
            )
            raise e

    # BILLING PORTAL OPERATIONS

    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: Optional[str] = None,
        flow_data: Optional[Dict[str, Any]] = None,
        flow_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Billing Portal session for customer management.

        Args:
            customer_id: The ID of the customer.
            return_url: URL to redirect after portal session ends.
            flow_data: Optional flow data for pre-configured flows.
            flow_type: Optional flow type (e.g., 'subscription_update').

        Returns:
            Dictionary with portal session details including 'url'.
        """
        try:
            portal_data = {"customer": customer_id}

            if return_url:
                portal_data["return_url"] = return_url
            if flow_data:
                portal_data["flow_data"] = flow_data
            if flow_type:
                portal_data["flow_type"] = flow_type

            session = stripe.billing_portal.Session.create(**portal_data)
            self.logger.info(f"Created billing portal session: {session.id}")
            return {
                "id": session.id,
                "url": session.url,
                "customer_id": session.customer,
                "created": session.created,
                "expires_at": session.expires_at,
            }
        except stripe.error.StripeError as e:
            self.logger.error(f"Error creating billing portal session: {str(e)}")
            raise e
