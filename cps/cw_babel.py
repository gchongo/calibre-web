from babel import negotiate_locale
from flask_babel import Babel, Locale
from babel.core import UnknownLocaleError
from flask import request
from .cw_login import current_user

from . import logger

log = logger.create()

babel = Babel()

# Map common browser / short locale codes to Calibre-Web translation folders
_LOCALE_ALIASES = {
    'zh': 'zh_Hans_CN',
    'zh_CN': 'zh_Hans_CN',
    'zh_SG': 'zh_Hans_CN',
    'zh_Hans': 'zh_Hans_CN',
    'zh_TW': 'zh_Hant_TW',
    'zh_HK': 'zh_Hant_TW',
    'zh_Hant': 'zh_Hant_TW',
}


def _normalize_locale(locale_code):
    if not locale_code:
        return None
    locale_code = str(locale_code).replace('-', '_')
    return _LOCALE_ALIASES.get(locale_code, locale_code)


def get_locale():
    # if a user is logged in, use the locale from the user settings
    if current_user is not None and hasattr(current_user, "locale"):
        # if the account is the guest account bypass the config lang settings
        if current_user.name != 'Guest':
            locale = _normalize_locale(current_user.locale)
            if locale:
                return locale

    preferred = list()
    if request.accept_languages:
        for x in request.accept_languages.values():
            try:
                preferred.append(_normalize_locale(str(Locale.parse(x.replace('-', '_')))))
            except (UnknownLocaleError, ValueError) as e:
                log.debug('Could not parse locale "%s": %s', x, e)

    # Prefer configured default UI language when browser does not match a translation
    try:
        from . import config
        default_locale = _normalize_locale(getattr(config, 'config_default_locale', None))
        if default_locale and default_locale != 'en':
            preferred = [default_locale] + (preferred or [])
    except Exception:
        pass

    return negotiate_locale(preferred or ['en'], get_available_translations()) or 'en'


def get_user_locale_language(user_language):
    return Locale.parse(user_language).get_language_name(get_locale())


def get_available_locale():
    return sorted(babel.list_translations(), key=lambda x: x.display_name.lower())


def get_available_translations():
    return set(str(item) for item in get_available_locale())
