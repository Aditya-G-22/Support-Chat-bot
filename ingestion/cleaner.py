import re

PII_PATTERNS = [
    (["name", "nom", "benutzer", "support", "team", "customer",
      "recipient", "company", "organization", "agent"],       "<NAME>"),
    (["tel", "phone", "telefon"],                              "<PHONE>"),
    (["acc", "konto", "kunden", "account"],                    "<ACCOUNT>"),
    (["ref", "invoice", "rechnung", "case"],                   "<REF>"),
    (["email", "mail"],                                        "<EMAIL>"),
    (["url", "link", "website"],                               "<URL>"),
    (["date", "datum"],                                        "<DATE>"),
    (["time", "uhrzeit", "zeit"],                              "<TIME>"),
    (["price", "amount", "betrag"],                            "<MONEY>"),
]

def strip_html(text: str) -> str:
    return re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def normalize_pii(text: str) -> str:
    def replace(match):
        inner = match.group(1).lower()
        for keywords, canonical in PII_PATTERNS:
            if any(kw in inner for kw in keywords):
                return canonical
        return match.group(0)

    return re.sub(r"[<\[]([A-Za-z][\w ]*)[>\]]", replace, text)

def clean_text(text: str) -> str:
    return normalize_whitespace(normalize_pii(strip_html(text)))
