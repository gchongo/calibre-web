# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2018-2019 OzzieIsaacs, cervinko, jkrehm, bodybybuddha, ok11,
#                            andy29485, idalin, Kyosfonica, wuqi, Kennyl, lemmsh,
#                            falgh1, grunjol, csitko, ytils, xybydy, trasba, vrabe,
#                            ruben-herold, marblepebble, JackED42, SiphonSquirrel,
#                            apetresc, nanu-c, mutschler, GammaC0de, vuolter
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from flask import current_app, session

from .cw_login import LoginManager
from .cw_login.config import SESSION_KEYS
from .cw_login.signals import session_protected


class MyLoginManager(LoginManager):
    def _session_protection_failed(self):
        sess = session._get_current_object()
        ident = self._session_identifier_generator()
        # Skip empty / csrf-only sessions (anonymous)
        if not (sess and not (len(sess) == 1 and sess.get('csrf_token', None))
                and ident != sess.get('_id', None)):
            return False

        app = current_app._get_current_object()
        mode = app.config.get("SESSION_PROTECTION", self.session_protection)

        if not mode or mode not in ["basic", "strong"]:
            return False

        if mode == "basic" or sess.permanent:
            if sess.get("_fresh") is not False:
                sess["_fresh"] = False
            session_protected.send(app)
            return False

        # Strong: drop ephemeral session keys, but keep the remember-me cookie.
        # Upstream flask-login also sets sess["_remember"] = "clear", which logs
        # users out on mobile / Cloudflare when the client IP changes between
        # requests — that looks like "refresh drops login".
        for k in SESSION_KEYS:
            sess.pop(k, None)
        session_protected.send(app)
        return True
