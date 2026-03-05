# Generated for QuickFix provider payouts (Stripe Connect + PayPal Payouts)
import os
from src.response import ok, err
from src.event import get_jwt_sub
from src.db import get_conn
from src.http import post_form, get_json, basic_auth_header, HttpError
from src.sql_helpers import get_provider_id_by_sub, get_provider_email, get_provider_payout_method, upsert_provider_payout_method

def _stripe_base():
    return "https://api.stripe.com"

def _auth_headers(stripe_secret):
    # Stripe uses basic auth: <secret_key>:
    return {"Authorization": basic_auth_header(stripe_secret, "")}

def _norm_path(event):
    return (event.get("rawPath") or event.get("path") or "").lower()

def handler(event, context):
    if (event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "")).upper() == "OPTIONS":
        return ok({"ok": True})

    sub = get_jwt_sub(event)
    if not sub:
        return err("Unauthorized", 401)

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        return err("Missing STRIPE_SECRET_KEY", 500)

    return_url = os.getenv("STRIPE_CONNECT_RETURN_URL")
    refresh_url = os.getenv("STRIPE_CONNECT_REFRESH_URL")
    if not return_url or not refresh_url:
        return err("Missing STRIPE_CONNECT_RETURN_URL / STRIPE_CONNECT_REFRESH_URL", 500)

    path = _norm_path(event)

    conn = get_conn()
    try:
        provider_id = get_provider_id_by_sub(conn, sub)
        if not provider_id:
            return err("Provider not found for token", 403)

        pm = get_provider_payout_method(conn, provider_id) or {}
        acct = pm.get("stripe_account_id")

        # START onboarding: create account if missing, then account link
        if path.endswith("/providers/stripe/connect/start"):
            if not acct:
                sp = get_provider_email(conn, provider_id)
                email = (sp or {}).get("email") or None

                url = _stripe_base() + "/v1/accounts"
                headers = _auth_headers(stripe_key)

                # Express account for Canada; request transfers capability for payouts
                form = {
                    "type": "express",
                    "country": "CA",
                }
                if email:
                    form["email"] = email
                form["capabilities[transfers][requested]"] = "true"

                acct_resp = post_form(url, form, headers=headers, timeout=25)
                acct = acct_resp.get("id")
                if not acct:
                    return err("Stripe account creation failed", 502, acct_resp)

                upsert_provider_payout_method(conn, provider_id, "stripe_connect", stripe_account_id=acct, paypal_email=None, status="pending")

            link_url = _stripe_base() + "/v1/account_links"
            link_resp = post_form(
                link_url,
                {
                    "account": acct,
                    "refresh_url": refresh_url,
                    "return_url": return_url,
                    "type": "account_onboarding",
                },
                headers=_auth_headers(stripe_key),
                timeout=25
            )
            conn.commit()
            return ok({"provider_id": provider_id, "stripe_account_id": acct, "onboarding_url": link_resp.get("url")})

        # CHECK status: mark verified when payouts enabled (or details submitted)
        if path.endswith("/providers/stripe/connect/status"):
            if not acct:
                return err("No stripe_account_id on file. Start onboarding first.", 400)

            url = _stripe_base() + f"/v1/accounts/{acct}"
            acct_info = get_json(url, headers=_auth_headers(stripe_key), timeout=25)
            payouts_enabled = bool(acct_info.get("payouts_enabled"))
            details_submitted = bool(acct_info.get("details_submitted"))

            status = "verified" if payouts_enabled or details_submitted else "pending"
            upsert_provider_payout_method(conn, provider_id, "stripe_connect", stripe_account_id=acct, paypal_email=None, status=status)
            conn.commit()

            return ok({
                "provider_id": provider_id,
                "stripe_account_id": acct,
                "status": status,
                "stripe": {
                    "payouts_enabled": payouts_enabled,
                    "details_submitted": details_submitted,
                    "charges_enabled": acct_info.get("charges_enabled"),
                    "requirements": acct_info.get("requirements", {}),
                }
            })

        return err("Not found", 404)

    except HttpError as he:
        try:
            conn.rollback()
        except Exception:
            pass
        return err("Stripe error", 502, {"status": he.status, "body": he.body})
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return err("Server error", 500, str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
