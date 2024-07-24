"""LDAP Authentication Setup.

Modification of Flask-SimpleLDAP script by https://github.com/alexferl/flask-simpleldap.
"""

# mypy: ignore-errors
import re

import ldap
from ldap import filter as ldap_filter


class LDAPException(RuntimeError):
    """LDAP Exception."""

    message = None

    # pylint: disable=W0231
    def __init__(self, message):
        """Init class."""
        self.message = message

    def __str__(self):
        """Set default string."""
        return self.message


class LDAP:
    """LDAP Authentication class.

    Attempts to bind user and get user groups.

    :param flask.Flask app: the application to configure for use with this class.
    """

    def __init__(self, app):
        """Init class."""
        self.app = app
        if app is not None:
            app.config.setdefault("LDAP_HOST", "localhost")
            app.config.setdefault("LDAP_PORT", 389)
            app.config.setdefault("LDAP_SCHEMA", "ldap")
            app.config.setdefault("LDAP_USERNAME", None)
            app.config.setdefault("LDAP_PASSWORD", None)
            app.config.setdefault("LDAP_TIMEOUT", 10)
            app.config.setdefault("LDAP_USE_SSL", False)
            app.config.setdefault("LDAP_USE_TLS", False)
            app.config.setdefault("LDAP_REQUIRE_CERT", False)
            app.config.setdefault("LDAP_CERT_PATH", "/path/to/cert")
            app.config.setdefault("LDAP_BASE_DN", None)
            app.config.setdefault("LDAP_OBJECTS_DN", "distinguishedName")
            app.config.setdefault("LDAP_USER_FIELDS", [])
            app.config.setdefault(
                "LDAP_USER_OBJECT_FILTER",
                "(|(sAMAccountName=%s)(userPrincipalName=%s))",
            )
            app.config.setdefault("LDAP_USER_GROUPS_FIELD", "memberOf")
            app.config.setdefault("LDAP_GROUP_FIELDS", [])
            app.config.setdefault(
                "LDAP_GROUP_OBJECT_FILTER",
                "(&(objectclass=Group)(userPrincipalName=%s))",
            )
            app.config.setdefault("LDAP_GROUP_MEMBERS_FIELD", "member")
            app.config.setdefault("LDAP_REALM_NAME", "LDAP authentication")
            app.config.setdefault("LDAP_OPENLDAP", False)
            app.config.setdefault("LDAP_GROUP_MEMBER_FILTER", "*")
            app.config.setdefault("LDAP_GROUP_MEMBER_FILTER_FIELD", "*")
            app.config.setdefault("LDAP_CUSTOM_OPTIONS", None)

            if app.config["LDAP_USE_SSL"] or app.config["LDAP_USE_TLS"]:
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

            if app.config["LDAP_REQUIRE_CERT"]:
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
                ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, app.config["LDAP_CERT_PATH"])

            for option in ["USERNAME", "PASSWORD", "BASE_DN"]:
                if app.config["LDAP_{0}".format(option)] is None:
                    raise LDAPException("LDAP_{0} cannot be None!".format(option))

    def _set_custom_options(self, conn):
        options = self.app.config["LDAP_CUSTOM_OPTIONS"]
        if options:
            for key, value in options.items():
                conn.set_option(key, value)
        return conn

    @property
    def initialize(self):
        """Initialize a connection to the LDAP server.

        :return: LDAP connection object.
        """
        try:
            conn = ldap.initialize(
                "{0}://{1}:{2}".format(
                    self.app.config["LDAP_SCHEMA"],
                    self.app.config["LDAP_HOST"],
                    self.app.config["LDAP_PORT"],
                )
            )
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, self.app.config["LDAP_TIMEOUT"])
            conn = self._set_custom_options(conn)
            conn.protocol_version = ldap.VERSION3
            conn.set_option(ldap.OPT_REFERRALS, 0)
            if self.app.config["LDAP_USE_TLS"]:
                conn.start_tls_s()
            return conn
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args)) from e

    @property
    def bind(self):
        """Attempt to bind to the LDAP server using the credentials of the service account.

        :return: Bound LDAP connection object if successful or ``None`` if unsuccessful.
        """
        conn = self.initialize
        try:
            conn.simple_bind_s(self.app.config["LDAP_USERNAME"], self.app.config["LDAP_PASSWORD"])
            return conn
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args)) from e

    # pylint: disable=R1710
    def bind_user(self, username, password):
        """Attempt to bind a user to the LDAP server using the credentials supplied.

        Many LDAP servers will grant anonymous access if ``password`` is
        the empty string, causing this method to return :obj:`True` no
        matter what username is given. If you want to use this method to
        validate a username and password, rather than actually connecting
        to the LDAP server as a particular user, make sure ``password`` is
        not empty.

        :param str username: The username to attempt to bind with.
        :param str password: The password of the username we're attempting to bind with.
        :return: Returns ``True`` if successful or ``None`` if the credentials are invalid.
        """
        user_dn = self.get_object_details(user=username, dn_only=True)

        if user_dn is None:
            return
        try:
            conn = self.initialize
            _user_dn = user_dn.decode("utf-8") if isinstance(user_dn, bytes) else user_dn
            conn.simple_bind_s(_user_dn, password)
            return self.get_object_details(user=username)  # True
        except ldap.LDAPError:
            return

    def get_object_details(self, user=None, group=None, query_filter=None, dn_only=False):
        """Return a ``dict`` with the object's (user or group) details.

        :param str user: Username of the user object you want details for.
        :param str group: Name of the group object you want details for.
        :param str query_filter: If included, will be used to query object.
        :param bool dn_only: If we should only retrieve the object's distinguished name or not.
        """
        query = None
        fields = None
        if user is not None:
            if not dn_only:
                fields = self.app.config["LDAP_USER_FIELDS"]
            query_filter = query_filter or self.app.config["LDAP_USER_OBJECT_FILTER"]
            query = ldap_filter.filter_format(
                query_filter,
                (
                    user,
                    user,
                ),
            )
        elif group is not None:
            if not dn_only:
                fields = self.app.config["LDAP_GROUP_FIELDS"]
            query_filter = query_filter or self.app.config["LDAP_GROUP_OBJECT_FILTER"]
            query = ldap_filter.filter_format(query_filter, (group,))
        conn = self.bind
        try:
            records = conn.search_s(
                self.app.config["LDAP_BASE_DN"], ldap.SCOPE_SUBTREE, query, fields
            )
            conn.unbind_s()
            result = {}
            if records:
                if dn_only:
                    if self.app.config["LDAP_OPENLDAP"]:
                        if records:
                            return records[0][0]
                    else:
                        if self.app.config["LDAP_OBJECTS_DN"] in records[0][1]:
                            # pylint: disable=C0103
                            dn = records[0][1][self.app.config["LDAP_OBJECTS_DN"]]
                            return dn[0]
                for key, value in list(records[0][1].items()):
                    result[key] = value

                return result
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args)) from e

    def get_user_groups(self, user):
        """Return a ``list`` with the user's groups or ``None`` if unsuccessful.

        :param str user: User we want groups for.
        """
        conn = self.bind
        try:
            if self.app.config["LDAP_OPENLDAP"]:
                fields = [str(self.app.config["LDAP_GROUP_MEMBER_FILTER_FIELD"])]
                records = conn.search_s(
                    self.app.config["LDAP_BASE_DN"],
                    ldap.SCOPE_SUBTREE,
                    ldap_filter.filter_format(
                        self.app.config["LDAP_GROUP_MEMBER_FILTER"],
                        (
                            self.get_object_details(user, dn_only=True),
                            self.get_object_details(user, dn_only=True),
                        ),
                    ),
                    fields,
                )
            else:
                records = conn.search_s(
                    self.app.config["LDAP_BASE_DN"],
                    ldap.SCOPE_SUBTREE,
                    ldap_filter.filter_format(
                        self.app.config["LDAP_USER_OBJECT_FILTER"],
                        (
                            user,
                            user,
                        ),
                    ),
                    [self.app.config["LDAP_USER_GROUPS_FIELD"]],
                )

            conn.unbind_s()
            if records:
                if self.app.config["LDAP_OPENLDAP"]:
                    group_member_filter = self.app.config["LDAP_GROUP_MEMBER_FILTER_FIELD"]
                    groups = [
                        (record[1][group_member_filter][0]).decode("utf-8") for record in records
                    ]
                    return groups

                if self.app.config["LDAP_USER_GROUPS_FIELD"] in records[0][1]:
                    groups = records[0][1][self.app.config["LDAP_USER_GROUPS_FIELD"]]
                    result = [re.findall(b"(?:cn=|CN=)(.*?),", group)[0] for group in groups]
                    return [x.decode("utf-8") for x in result]
        except ldap.LDAPError as e:
            raise LDAPException(self.error(e.args)) from e

    @staticmethod
    def error(error_message):
        """Get error string from message."""
        error_message = error_message[0]
        if "desc" in error_message:
            return error_message["desc"]

        return error_message
