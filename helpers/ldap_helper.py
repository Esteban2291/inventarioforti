from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException

class LdapHelper:
    # Configuración LDAP
    LDAP_HOST = '10.201.0.7'
    LDAP_PORT = 3268
    LDAP_USER = 'FORTIVPN@gendarmeria.local'
    LDAP_PASSWORD = 'Qwerty2010'
    LDAP_DOMAIN = 'gendarmeria.local'
    BASE_DN = 'dc=gendarmeria,dc=local'

    @staticmethod
    def user_ldap(dni):
        try:
            server = Server(LdapHelper.LDAP_HOST, port=LdapHelper.LDAP_PORT, get_info=ALL)
            conn = Connection(server, user=LdapHelper.LDAP_USER, password=LdapHelper.LDAP_PASSWORD, authentication=NTLM, auto_bind=True)

            search_filter = f'(sAMAccountName={dni})'
            attributes = [
                "givenName", "sn", "mail", "title", "department", "displayName",
                "description", "ce", "jerarquia", "correo", "correoalternativo", "telefono"
            ]

            conn.search(search_base=LdapHelper.BASE_DN,
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes=attributes)

            if len(conn.entries) == 1:
                entry = conn.entries[0]
                return [{
                    'dni': dni,
                    'nombre': str(entry.givenName) if 'givenName' in entry else '',
                    'apellido': str(entry.sn) if 'sn' in entry else '',
                    'email': str(entry.mail) if 'mail' in entry else '',
                    'jerarquia': str(entry.jerarquia) if 'jerarquia' in entry else str(entry.title) if 'title' in entry else '',
                    'unidad': str(entry.department) if 'department' in entry else '',
                    'ce': str(entry.ce) if 'ce' in entry else '',
                    'telefono': str(entry.telefono) if 'telefono' in entry else '',
                    'correo': str(entry.correo) if 'correo' in entry else str(entry.mail) if 'mail' in entry else '',
                    'correoalt': str(entry.correoalternativo) if 'correoalternativo' in entry else '',
                }]
        except LDAPException as e:
            print(f"Error LDAP: {e}")
            return []
        return []

    @staticmethod
    def autenticar_ldap(dni, password):
        try:
            server = Server('10.201.0.7', port=3268, get_info=ALL)
            user_dn = f'{dni}@gendarmeria.local'
            conn = Connection(server, user=user_dn, password=password, auto_bind=True)
            return conn.bound
        except Exception as e:
            print("LDAP ERROR:", e)
            return False

    @staticmethod
    def user_exists(dni):
        return bool(LdapHelper.user_ldap(dni))
