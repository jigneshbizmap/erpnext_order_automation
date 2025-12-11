import frappe

def send_confirmation_email(order_conf_name):
    """
    Sends an order confirmation email to the customer
    """
    order_conf = frappe.get_doc("Order Confirmation", order_conf_name)
    
    # Make sure customer email exists
    if not order_conf.customer_email:
        frappe.log_error(f"No email found for Order Confirmation {order_conf_name}", "Order Confirmation Email")
        return

    # Email subject and message
    subject = f"Order Confirmation for {order_conf.name}"
    message = f"""
    Dear {order_conf.customer_name or 'Customer'},
    
    Your order has been placed successfully.
    
    Thank you for choosing our service!
    
    Regards,
    Your Company
    """
    
    # Send email
    frappe.sendmail(
        recipients=[order_conf.customer_email],
        subject=subject,
        message=message,
        reference_doctype=order_conf.doctype,
        reference_name=order_conf.name
    )
    
    frappe.msgprint(f"Confirmation email sent to {order_conf.customer_email}")
