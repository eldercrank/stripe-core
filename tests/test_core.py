"""Tests for the eldercrank-stripe-core package."""

from eldercrank_stripe_core import StripeHandler, StripeManager
from eldercrank_stripe_core.models import StripeEvent, ProductModel, PriceModel


class TestStripeHandler:
    """Tests for the StripeHandler class."""

    def test_init(self):
        """Test StripeHandler initialization."""
        handler = StripeHandler(api_key="sk_test_123", webhook_secret="whsec_123")
        assert handler.api_key == "sk_test_123"
        assert handler.webhook_secret == "whsec_123"

    def test_init_with_custom_logger(self):
        """Test StripeHandler initialization with custom logger."""
        import logging

        custom_logger = logging.getLogger("custom")
        handler = StripeHandler(api_key="sk_test_123", logger=custom_logger)
        assert handler.logger is custom_logger

    def test_add_event_handler(self):
        """Test adding an event handler."""
        handler = StripeHandler(api_key="sk_test_123")

        def my_handler(event_data):
            pass

        handler.add_event_handler("payment_intent.succeeded", my_handler)
        assert "payment_intent.succeeded" in handler._event_handlers
        assert handler._event_handlers["payment_intent.succeeded"] == my_handler

    def test_remove_event_handler(self):
        """Test removing an event handler."""
        handler = StripeHandler(api_key="sk_test_123")

        def my_handler(event_data):
            pass

        handler.add_event_handler("payment_intent.succeeded", my_handler)
        handler.remove_event_handler("payment_intent.succeeded")
        assert "payment_intent.succeeded" not in handler._event_handlers

    def test_remove_nonexistent_event_handler(self):
        """Test removing a nonexistent event handler."""
        handler = StripeHandler(api_key="sk_test_123")
        # Should not raise an error
        handler.remove_event_handler("nonexistent.event")


class TestStripeManager:
    """Tests for the StripeManager class."""

    def test_init(self):
        """Test StripeManager initialization."""
        manager = StripeManager(api_key="sk_test_123")
        assert manager.api_key == "sk_test_123"

    def test_init_with_custom_logger(self):
        """Test StripeManager initialization with custom logger."""
        import logging

        custom_logger = logging.getLogger("custom_manager")
        manager = StripeManager(api_key="sk_test_123", logger=custom_logger)
        assert manager.logger is custom_logger

    def test_add_webhook_handler(self):
        """Test adding a webhook handler."""
        manager = StripeManager(api_key="sk_test_123")

        def my_handler(event_data):
            pass

        manager.add_webhook_handler("payment_intent.succeeded", my_handler)
        assert "payment_intent.succeeded" in manager._webhook_handlers
        assert manager._webhook_handlers["payment_intent.succeeded"] == my_handler

    def test_remove_webhook_handler(self):
        """Test removing a webhook handler."""
        manager = StripeManager(api_key="sk_test_123")

        def my_handler(event_data):
            pass

        manager.add_webhook_handler("payment_intent.succeeded", my_handler)
        manager.remove_webhook_handler("payment_intent.succeeded")
        assert "payment_intent.succeeded" not in manager._webhook_handlers


class TestStripeEvent:
    """Tests for the StripeEvent model."""

    def test_stripe_event_creation(self):
        """Test creating a StripeEvent."""
        event = StripeEvent(
            id="evt_123",
            type="payment_intent.succeeded",
            data={"object": {"id": "pi_123"}},
        )
        assert event.id == "evt_123"
        assert event.type == "payment_intent.succeeded"
        assert event.event_object == {"id": "pi_123"}

    def test_stripe_event_with_optional_fields(self):
        """Test creating a StripeEvent with optional fields."""
        event = StripeEvent(
            id="evt_123",
            type="payment_intent.succeeded",
            data={"object": {}},
            api_version="2024-01-01",
        )
        assert event.api_version == "2024-01-01"

    def test_stripe_event_empty_object(self):
        """Test StripeEvent with empty event object."""
        event = StripeEvent(id="evt_123", type="payment_intent.succeeded", data={})
        assert event.event_object == {}


class TestProductModel:
    """Tests for the ProductModel."""

    def test_product_model_creation(self):
        """Test creating a ProductModel."""
        product = ProductModel(id="prod_123", name="Test Product", active=True)
        assert product.id == "prod_123"
        assert product.name == "Test Product"
        assert product.active is True
        assert product.prices == []

    def test_product_model_with_prices(self):
        """Test creating a ProductModel with prices."""
        price = PriceModel(
            id="price_123", unit_amount=1999, currency="usd", recurring_interval="month"
        )
        product = ProductModel(
            id="prod_123", name="Test Product", active=True, prices=[price]
        )
        assert len(product.prices) == 1
        assert product.prices[0].id == "price_123"


class TestPriceModel:
    """Tests for the PriceModel."""

    def test_price_model_creation(self):
        """Test creating a PriceModel."""
        price = PriceModel(id="price_123", unit_amount=1999, currency="usd")
        assert price.id == "price_123"
        assert price.unit_amount == 1999
        assert price.currency == "usd"

    def test_price_model_with_interval(self):
        """Test creating a PriceModel with recurring interval."""
        price = PriceModel(
            id="price_123", unit_amount=1999, currency="usd", recurring_interval="year"
        )
        assert price.recurring_interval == "year"

    def test_price_model_interval_alias(self):
        """Test that 'interval' alias works for recurring_interval."""
        price = PriceModel(
            id="price_123", unit_amount=1999, currency="usd", interval="week"
        )
        assert price.recurring_interval == "week"
