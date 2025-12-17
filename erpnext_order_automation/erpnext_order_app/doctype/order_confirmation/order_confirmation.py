import requests
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


def shorten_url(long_url):
    """
    Shorten a URL using is.gd or da.gd (free, no API key required)
    """
    try:
        # Try is.gd first
        # response = requests.get(
        #     "https://is.gd/create.php",
        #     params={"format": "simple", "url": long_url},
        #     timeout=5
        # )
        # if response.status_code == 200:
        #     return response.text.strip()
        
        # Fallback to da.gd if is.gd fails
        response = requests.get(
            "https://da.gd/s",
            params={"url": long_url},
            timeout=5
        )
        if response.status_code == 200:
            return response.text.strip()

        # If all fail, return the original URL
        return long_url

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
