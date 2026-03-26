"""
Financial utilities for CapitalSense.
"""

def categorize_description(description: str, vendor_name: str = "") -> str:
    """Infer obligation category from description or vendor name."""
    text = (f"{description} {vendor_name}").lower()
    
    if any(k in text for k in ["gst", "tax", "tds", "vat", "government", "income tax", "provident fund", "pf"]):
        return "Tax"
    if any(k in text for k in ["salary", "wage", "payroll", "employee", "stipend"]):
        return "Payroll"
    if any(k in text for k in ["loan", "emi", "interest", "mortgage", "credit card", "principal"]):
        return "Loan"
    if any(k in text for k in ["rent", "lease", "office rent"]):
        return "Rent"
    if any(k in text for k in ["electricity", "water", "internet", "broadband", "phone", "utility", "gas"]):
        return "Utilities"
    if any(k in text for k in ["insurance", "policy", "premium"]):
        return "Insurance"
        
    return "Supplier"

def is_must_pay_in_full(category: str) -> bool:
    """Check if category is high-priority and resists partial payment."""
    return category.lower() in ["tax", "payroll", "loan"]
