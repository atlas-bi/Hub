"""SAML Login/Logout web views."""

import base64
import hashlib
import logging
import re
from urllib.parse import unquote

from defusedxml import ElementTree
from flask import (
    Blueprint,
    Flask,
    abort,
    flash,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from flask import current_app as app
from is_safe_url import is_safe_url
from saml2 import entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.metadata import entity_descriptor
from saml2.sigver import SignatureError
from werkzeug import Response

from web import db
from web.extensions import csrf
from web.model import User

login_bp = Blueprint("login_bp", __name__)

from flask_login import login_user

_ISSUER_TAG = "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer"
_CERT_TAG = "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"


def _posted_saml_response() -> str:
    """Read SAMLResponse without treating a literal '+' as a space.

    Flask's form decoder follows form-urlencoded rules. A reverse proxy that
    forwards a bare '+' would change the signed bytes and fail verification.
    """
    # Read the body before request.form, which consumes the stream.
    match = re.search(r"(?:^|&)SAMLResponse=([^&]*)", request.get_data(as_text=True))
    form_value = request.form.get("SAMLResponse", "")
    if not match:
        return form_value

    raw_value = unquote(match.group(1))
    if raw_value != form_value:
        logging.error(
            "SAMLResponse decoding changed the payload (raw length %s, form length %s)",
            len(raw_value),
            len(form_value),
        )
    return raw_value or form_value


def _fingerprint_b64(cert_text: str) -> str:
    """Return the SHA-256 fingerprint of a base64-encoded X509 certificate."""
    body = cert_text.replace("-----BEGIN CERTIFICATE-----", "")
    body = body.replace("-----END CERTIFICATE-----", "")
    return hashlib.sha256(base64.b64decode("".join(body.split()))).hexdigest()


def _signature_failure_detail(posted: str, saml_client: Saml2Client | None) -> str:
    """Compare the assertion certificate with the certificates loaded from metadata."""
    try:
        root = ElementTree.fromstring(base64.b64decode(posted))
    except Exception as exc:
        return f"SAMLResponse is not decodable XML ({exc.__class__.__name__})"

    issuers = []
    for node in root.iter(_ISSUER_TAG):
        issuer = (node.text or "").strip()
        if issuer and issuer not in issuers:
            issuers.append(issuer)

    response_certs = []
    for node in root.iter(_CERT_TAG):
        if not node.text:
            continue
        try:
            digest = _fingerprint_b64(node.text)
        except Exception:
            digest = "unreadable"
        if digest not in response_certs:
            response_certs.append(digest)

    metadata_certs = []
    metadata_error = ""
    if saml_client is not None:
        for issuer in issuers:
            try:
                found = saml_client.metadata.certs(issuer, "any", "signing")
            except Exception as exc:
                metadata_error = f"{issuer}: {exc.__class__.__name__}"
                continue
            for _name, cert in found:
                try:
                    digest = _fingerprint_b64(cert)
                except Exception:
                    digest = "unreadable"
                if digest not in metadata_certs:
                    metadata_certs.append(digest)

    overlap = sorted(set(response_certs) & set(metadata_certs))
    return (
        "SAML signature debug "
        f"issuers={issuers} response_certs={response_certs} "
        f"metadata_certs={metadata_certs} overlap={overlap} "
        f"metadata_error={metadata_error or 'none'}"
    )


class SAML:
    """SAML Authentication."""

    def __init__(self, flask_app: Flask) -> None:
        """Init class."""
        self.app = flask_app

    def saml_client_for(self) -> Saml2Client:
        """Build SAML client."""
        sp_config = Saml2Config()
        sp_config.load(app.config["SAML_CONFIG"])
        saml_client = Saml2Client(config=sp_config)

        return saml_client


@login_bp.route("/saml2/acs/", methods=["POST"])
@csrf.exempt
def idp_initiated() -> Response:
    """Get response from IDP."""
    saml_client = None
    posted_response = _posted_saml_response()
    try:
        saml = SAML(app)
        saml_client = saml.saml_client_for()
        authn_response = saml_client.parse_authn_request_response(
            posted_response, entity.BINDING_HTTP_POST
        )

        identity = authn_response.get_identity()

        groups = identity.get(app.config["SAML_ATTR_MAP"]["groups"]) or []

        if (
            "REQUIRED_GROUPS" in app.config
            and app.config["REQUIRED_GROUPS"]
            and not bool(set(app.config["REQUIRED_GROUPS"]) & set(groups))
        ):
            session.pop("_flashes", None)

            # user is not authorized.
            flash(
                "You must be part of the %s group(s) to use this site."
                % app.config["REQUIRED_GROUPS"]
            )
            return redirect(url_for(app.config["NOT_AUTHORIZED_URL"]))

        logging.warning(identity)

        if identity:
            account_name = identity.get(app.config["SAML_ATTR_MAP"]["account_name"])[0].lower()

            email = identity.get(app.config["SAML_ATTR_MAP"]["email"])[0].lower()

            user = User.query.filter(
                (User.account_name == account_name) | (User.email == email)
            ).first()

            # if user isn't existing, create
            if not user:
                user = User()

            # update user attributes
            user.account_name = account_name
            user.email = email

            user.full_name = "%s %s" % (
                identity.get(app.config["SAML_ATTR_MAP"]["first_name"])[0],
                identity.get(app.config["SAML_ATTR_MAP"]["last_name"])[0],
            )

            user.first_name = identity.get(app.config["SAML_ATTR_MAP"]["first_name"])[0]

            db.session.add(user)
            db.session.commit()

            login_user(user, remember=True)

            next_url = (
                request.args.get("next")
                or request.args.get("RelayState")
                or request.form.get("RelayState")
                or app.config["LOGIN_REDIRECT_URL"]
            )

            if not is_safe_url(next_url, app.config["ALLOWED_HOSTS"]):
                return abort(400)

            session.pop("_flashes", None)
            return redirect(next_url)
        return redirect(url_for(app.config["LOGIN_VIEW"]))

    except SignatureError as e:
        logging.exception("SAML signature verification failed")
        logging.error("%s", _signature_failure_detail(posted_response, saml_client))
        session.pop("_flashes", None)
        flash(str(e))
        return redirect(url_for(app.config["NOT_AUTHORIZED_URL"]))


@login_bp.route("/saml2/metadata/")
def build_metadata() -> Response:
    """Build saml metadata."""
    conf = Saml2Config()
    conf.load(app.config["SAML_CONFIG"])
    metadata = entity_descriptor(conf)
    response = make_response(str(metadata).encode("utf-8"))
    response.headers["content-type"] = "text/xml; charset=utf-8"
    return response
