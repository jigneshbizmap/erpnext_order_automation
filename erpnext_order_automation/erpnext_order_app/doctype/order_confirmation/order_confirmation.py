import requests
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
import pyshorteners

# BITLY_TOKEN = "527220ad35b032e9ece229594da72f7f168c3811"


# def shorten_url(long_url):
#     if not BITLY_TOKEN:
#         frappe.log_error("Missing Bitly token", "Bitly Error")
#         return long_url

#     url = "https://api-ssl.bitly.com/v4/shorten"
#     headers = {
#         "Authorization": f"Bearer {BITLY_TOKEN}",
#         "Content-Type": "application/json",
#     }

#     data = {"long_url": long_url}

#     try:
#         response = requests.post(url, json=data, headers=headers)

#         if response.status_code in (200, 201):
#             return response.json().get("link", long_url)

#         frappe.log_error(
#             f"Bitly error {response.status_code}",
#             "Bitly URL Error"
#         )
#         return long_url

#     except Exception as e:
#         frappe.log_error(str(e)[:140], "Bitly Exception")
#         return long_url



def shorten_url(long_url):
    try:
        shortener = pyshorteners.Shortener()
        return shortener.tinyurl.short(long_url)
    except Exception as e:
        frappe.log_error(str(e)[:140], "Shorten URL Error")
        return long_url
    
class OrderConfirmation(Document):
    pass


def create_order_confirmation(doc, method):

    def postprocess(source_doc, target_doc, source_parent):
        if hasattr(target_doc, "items"):
            for row in target_doc.items:
                row.conversion_factor = 1

    order_conf = get_mapped_doc(
        "Sales Order",
        doc.name,
        {
            "Sales Order": {
                "doctype": "Order Confirmation",
                "field_map": {"customer": "customer"},
                "postprocess": postprocess
            }
        },
        ignore_permissions=True
    )

    order_conf.insert()
    frappe.db.commit()

    base_url = frappe.utils.get_url()   # MUST include :8003
    long_url = f"{base_url}/order-confirmation/{order_conf.name}"

    short_url = shorten_url(long_url)

    order_conf.confirmation_url = short_url
    order_conf.save(ignore_permissions=True)
