# eldercrank-stripe-core

A no-nonsense Stripe integration library that provides a clean, Pythonic interface to the Stripe API.

## Features

- **StripeHandler**: High-level interface for common Stripe operations including webhook handling
- **StripeManager**: Comprehensive CRUD operations for products, prices, customers, and subscriptions
- **Pydantic Models**: Type-safe models for Stripe events, products, and prices
- **Clean API**: Hides the complexity of working with raw Stripe JSON responses

## Installation

```bash
pip install eldercrank-stripe-core
```

## Quick Start

### Using StripeHandler

```python
from eldercrank.stripe.core import StripeHandler

handler = StripeHandler(
    api_key="sk_test_...",
    webhook_secret="whsec_..."
)

# Register a webhook handler
def handle_payment_success(event_data):
    print(f"Payment successful for customer: {event_data}")

handler.add_event_handler("payment_intent.succeeded", handle_payment_success)

# Process a webhook
event = handler.process_webhook(payload, signature)

# Create a subscription product
result = handler.create_subscription_product(
    name="Premium Plan",
    amount=1999,  # $19.99
    currency="usd",
    interval="month"
)
```

### Using StripeManager

```python
from eldercrank.stripe.core import StripeManager

manager = StripeManager(api_key="sk_test_...")

# Create a customer
customer = manager.create_customer(
    name="John Doe",
    email="john@example.com"
)

# Create a product
product = manager.create_product(
    name="Basic Plan",
    description="Basic subscription plan"
)

# Create a price
price = manager.create_price(
    product_id=product["id"],
    unit_amount=999,
    currency="usd",
    recurring={"interval": "month"}
)

# Create a subscription
subscription = manager.create_subscription(
    customer_id=customer["id"],
    price_id=price["id"]
)
```

## Framework Integrations

- **FastAPI**: See [eldercrank-stripe-fastapi](https://pypi.org/project/eldercrank-stripe-fastapi/)
- **Flask**: See [eldercrank-stripe-flask](https://pypi.org/project/eldercrank-stripe-flask/)

## License

MIT
