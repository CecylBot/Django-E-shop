import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY
def retrieve_existing_payment_intent(customer):
    try:
        # Use Stripe API or your data store to retrieve an existing payment intent
        # based on the customer or session identifier.
        # Return the existing payment intent if found, or None if not found.
        # You may need to customize this part based on your data storage mechanism.
        x=stripe.PaymentIntent.list(customer=customer, limit=1).data[0]
       
        return x
    except:
        return None



def get_create_customer(customer_identifier):
        customers = stripe.Customer.list(email=customer_identifier)
        # Check if a customer with the provided email exists
        if customers.data:
            # If the customer already exists, retrieve the first customer in the list
            customer=customers.data[0]
        else:
            # If the customer doesn't exist, create a new customer with the provided email
            customer = stripe.Customer.create(email=customer_identifier)
        return customer.id