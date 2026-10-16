import io
import json
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
stamp = int(time.time())
IMG = Path(__file__).resolve().parent.parent / "products" / "sofas" / "sofa_01.jpg"


def req(method, path, token=None, json_body=None, form=None, files=None):
    url = BASE + path
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body).encode()
        req_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req_obj) as resp:
            return resp.status, json.loads(resp.read().decode())
    if files is not None:
        boundary = "----DecoreBoundary"
        chunks = []
        for key, value in (form or {}).items():
            chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode())
        for key, (filename, content, ctype) in files.items():
            chunks.append(
                (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\n"
                    f"Content-Type: {ctype}\r\n\r\n"
                ).encode()
                + content
                + b"\r\n"
            )
        chunks.append(f"--{boundary}--\r\n".encode())
        body = b"".join(chunks)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        req_obj = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req_obj) as resp:
            return resp.status, json.loads(resp.read().decode())
    req_obj = urllib.request.Request(url, headers=headers, method=method)
    with urllib.request.urlopen(req_obj) as resp:
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}


def register(role, extra=None):
    payload = {
        "name": f"{role.title()} User",
        "email": f"{role}_{stamp}@decore.ai",
        "password": "Password123!",
        "role": role,
    }
    if extra:
        payload.update(extra)
    status, data = req("POST", "/api/auth/register", json_body=payload)
    assert status in (200, 201), data
    return data["access_token"], data["user"]


def main():
    print("TEST seller register")
    seller_token, seller = register("seller", {"business_name": "Oak Studio", "phone": "9999999999"})
    print("  seller", seller["user_id"], seller["role"])
    assert seller["role"] == "seller"

    print("TEST stats")
    status, stats = req("GET", "/api/seller/stats", token=seller_token)
    print("  stats", status, {k: stats[k] for k in stats if k != "recent_products"})
    assert "total_products" in stats

    print("TEST create product")
    img = IMG.read_bytes() if IMG.exists() else Path(__file__).read_bytes()
    status, created = req(
        "POST",
        "/api/seller/products",
        token=seller_token,
        form={
            "name": "Live Test Sofa",
            "category": "sofa",
            "subcategory": "loveseat",
            "description": "Ready to deliver sofa",
            "price": "29999",
            "currency": "INR",
            "color": "burgundy",
            "material": "fabric",
            "style": "modern, contemporary",
            "dimensions": "180x80x75 cm",
            "stock": "4",
            "is_active": "true",
        },
        files={"file": ("sofa.jpg", img, "image/jpeg")},
    )
    print("  created", status, created["product_id"], created["price"])
    pid = created["product_id"]

    print("TEST list")
    status, products = req("GET", "/api/seller/products", token=seller_token)
    print("  count", len(products))
    assert any(p["product_id"] == pid for p in products)

    print("TEST update")
    status, updated = req(
        "PUT",
        f"/api/seller/products/{pid}",
        token=seller_token,
        form={"price": "28999", "stock": "3"},
        files={},
    )
    print("  updated price", updated.get("price"), "status", status)

    print("TEST customer cannot use seller stats")
    cust_token, customer = register("customer")
    try:
        req("GET", "/api/seller/stats", token=cust_token)
        raise SystemExit("customer should be forbidden")
    except urllib.error.HTTPError as e:
        print("  customer stats", e.code)
        assert e.code == 403

    print("TEST admin register/login")
    admin_token, admin = register("admin")
    print("  admin", admin["role"], admin["user_id"])
    assert admin["role"] == "admin"

    print("TEST delete")
    status, deleted = req("DELETE", f"/api/seller/products/{pid}", token=seller_token)
    print("  deleted", deleted)

    print("ALL API CHECKS PASSED")


if __name__ == "__main__":
    import urllib.error
    main()
