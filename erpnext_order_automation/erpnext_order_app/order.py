import frappe
from frappe.utils import now_datetime, add_to_date
from otp_generation.api import send_otp
from otp_generation.api import validate_otp
from otp_generation.otp_generation.doctype.otp.otp import generate as generate_otp
from otp_generation.otp_generation.doctype.otp.otp import verify as verify_otp

# @frappe.whitelist(allow_guest=True)
# def store_otp(order_id):
#     order = frappe.get_doc("Order Confirmation", order_id)

#     # Block if already verified
#     if order.custom_verified:
#         return {"status": "failed", "message": "Order already verified"}


#     # 🔐 Send OTP using otp_generation
#     send_otp(
#         phone=order.contact_phone,
#         email=order.contact_email,
#         purpose=f"sign_up",
#     )


#     return {"status": "success", "message": "OTP sent"}

@frappe.whitelist(allow_guest=True)
def store_otp(order_id):
    import requests

    order = frappe.get_doc("Order Confirmation", order_id)

    if order.custom_verified:
        frappe.throw("Order already verified")

    #  Generate OTP (pure logic)
    otp_result = generate_otp(
        email=order.contact_email,
        phone=order.contact_phone,
        purpose="sign_up",
    )

    #  Send OTP to n8n
    requests.post(
        "https://roshan-n8n-1.app.n8n.cloud/webhook/generate-otp",
        json={
            "order_id": order.name,
            "phone": order.contact_phone,
            "otp": otp_result["otp_code"],
        },
        timeout=5
    )

    return {"status": "success", "message": "OTP sent"}



@frappe.whitelist(allow_guest=True)
def verify_order_otp(order_id, otp_code):
    from otp_generation.api import validate_otp

    order = frappe.get_doc("Order Confirmation", order_id)

    try:
        # 🔐 Validate OTP using otp_generation
        validate_otp(
            otp_code=otp_code,
            email=order.contact_email,
            phone=order.contact_phone,
            purpose="sign_up"
        )

        return {
            "status": "success",
            "verified": True
        }

    except frappe.ValidationError as e:
        return {
            "status": "failed",
            "verified": False,
            "message": str(e)
        }



@frappe.whitelist(allow_guest=True)
def mark_order_verified():
    import json

    order_id = frappe.request.headers.get("x-order-id")
    if not order_id:
        return {"status": "failed", "message": "Missing order ID"}


    payload = json.loads(frappe.request.get_data(as_text=True) or "{}")
    fraud = payload.get("fraud_data", {})

    order = frappe.get_doc("Order Confirmation", order_id)
    order.custom_verified = 1
    order.status = "Order Confirmed"
    order.save(ignore_permissions=True)

    frappe.db.commit()

    return {"status": "success", "message": "Order verified & confirmed"}



@frappe.whitelist()
def store_fraud_data(order_id, fraud_data):
    fraud_json = frappe.parse_json(fraud_data)

    # append as comment
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Order Confirmation",
        "reference_name": order_id,
        "content": f"Fraud Data Logged:\n{frappe.as_json(fraud_json, indent=2)}"
    }).insert(ignore_permissions=True)

    frappe.db.commit()

    return {"status": "success", "message": "Fraud data stored"}


