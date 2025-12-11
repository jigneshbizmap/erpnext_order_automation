import frappe
from frappe.utils import now_datetime, add_to_date

@frappe.whitelist(allow_guest=True)
def store_otp(order_id, otp):
    order = frappe.get_doc("Order Confirmation", order_id)

    mobile = order.contact_phone or ""
    email = order.contact_email or ""

    # Check if there is already a Verified OTP for this order
    verified_otp = frappe.db.exists(
        "User OTP",
        {
            "reference_doctype": "Order Confirmation",
            "reference_docname": order_id,
            "otp_status": "Verified",
        }
    )

    if verified_otp:
        return {
            "status": "failed",
            "message": "OTP already verified for this order. No new OTP generated.",
            "mobile_no": mobile,
        }

    # Expire previous Active OTPs for this order
    frappe.db.set_value(
        "User OTP",
        {
            "reference_doctype": "Order Confirmation",
            "reference_docname": order_id,
            "otp_status": "Active",
        },
        "otp_status",
        "Expired",
    )

    expiry_time = add_to_date(now_datetime(), minutes=5)

    otp_doc = frappe.get_doc(
        {
            "doctype": "User OTP",
            "email": email,
            "mobile_no": mobile,
            "otp": otp,
            "otp_expiry": expiry_time,
            "otp_status": "Active",
            "reference_doctype": "Order Confirmation",
            "reference_docname": order_id,
            "generated_at": now_datetime(),
        }
    )

    otp_doc.insert(ignore_permissions=True)

    return {
        "status": "success",
        "message": "OTP Stored Successfully",
        "expires_in": "5 minutes",
        "mobile_no": mobile,
    }


# @frappe.whitelist(allow_guest=True)
# def mark_order_verified():
#     order_id = frappe.request.headers.get("x-order-id")

#     if not order_id:
#         return {"status": "failed", "message": "Missing order ID"}

#     order = frappe.get_doc("Order Confirmation", order_id)

#     order.db_set("status", "Order Confirmed")


#     frappe.db.commit()

#     return {"status": "success", "message": "Order verified successfully"}


@frappe.whitelist(allow_guest=True)
def mark_order_verified():
    import json

    order_id = frappe.request.headers.get("x-order-id")
    if not order_id:
        return {"status": "failed", "message": "Missing order ID"}

    data = frappe.request.get_data(as_text=True)
    payload = json.loads(data) if data else {}
    fraud = payload.get("fraud_data", {})

    # Mark order as confirmed
    order = frappe.get_doc("Order Confirmation", order_id)
    order.status = "Order Confirmed"
    order.custom_verified = 1
    order.save(ignore_permissions=True)

    # Get the latest active User OTP for this order
    otp_name = frappe.db.get_value(
        "User OTP",
        {"reference_doctype": "Order Confirmation", "reference_docname": order_id, "otp_status": "Active"},
        "name"
    )

    if otp_name:
        otp_doc = frappe.get_doc("User OTP", otp_name)

        # Save fraud fields
        otp_doc.ip_address         = fraud.get("ip")
        otp_doc.device_os          = fraud.get("device", {}).get("platform")
        otp_doc.timezone           = fraud.get("device", {}).get("timezone")
        otp_doc.language_setting   = fraud.get("device", {}).get("language")
        otp_doc.overall_risk_score = fraud.get("riskScore")

        geo = fraud.get("geo", {})
        otp_doc.approx_location = f"{geo.get('city')}, {geo.get('region')}, {geo.get('country')}".strip(", ")

        otp_doc.browser = fraud.get("device", {}).get("userAgent")

        screen = fraud.get("device", {}).get("screen", {})
        otp_doc.screen_resolution = f"{screen.get('width')}x{screen.get('height')}@{screen.get('colorDepth')}bit"

        otp_doc.device_id_hash = fraud.get("fingerprint")

        # Mark OTP as Verified to prevent reuse
        otp_doc.otp_status = "Verified"

        otp_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "message": "Order verified, OTP updated & fraud data saved"}
    else:
        return {"status": "failed", "message": "No active OTP found for this order"}


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
