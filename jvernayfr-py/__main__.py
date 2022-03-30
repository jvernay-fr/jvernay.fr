# SPDX-FileCopyrightText: 2022 Julien Vernay <contact@jvernay.fr>
# SPDX-License-Identifier: GPL-3.0-or-later
# Part of jvernay.fr build scripts.

"""Python module to build, run and deploy the jvernay.fr website."""

import logging, argparse
from .Nginx import Nginx, Service, Protocol, NGINX_CERTBOT_CHALLENGES
from .Certbot import Certbot
from .Utility import *

parser = argparse.ArgumentParser(prog="python3 -m jvernayfr-py", description="Module to build, run and deploy the jvernay.fr website.")
parser.add_argument("--certify", action="store_true", default=False, help="Use certbot to create HTTPS certificates.")
parser.add_argument("--deploy", action="store_true", default=False, help="Deploy server on port 80 and 443")
parser.add_argument("--build-single-thread", action="store_true", default=False,
    dest="build_single_thread", help="If nginx must be built, do it single-threaded.")
parser.add_argument("--rebuild-nginx", action="store_true", default=False,
    dest="rebuild_nginx", help="Force nginx to be rebuilt.")
parser.add_argument("--email", action="store", default=False, help="Email used to emit certificates")
parser.add_argument("--https-fullchain", action="store", default=False, dest="https_fullchain", help="/path/to/fullchain.pem")
parser.add_argument("--https-privkey", action="store", default=False, dest="https_privkey", help="/path/to/privkey.pem")
args = parser.parse_args()

services = [
    Service(["jvernay.fr", "www.jvernay.fr"], 12000, Protocol.HTTP, [
        "root " + ResolvePath("www.jvernay.fr/root") + ";",
        "include " + ResolvePath("www.jvernay.fr/nginx.conf") + ";",
    ])
]

logging.basicConfig(level=logging.INFO)

def ensure(cond, msg):
    if not cond:
        print(msg)
        exit()

if args.certify:
    ensure(args.email, "ERROR: you must pass --email when doing certificates.")
    server_names = [n for s in services for n in s.server_names]
    certbot = Certbot()
    certbot.certify(server_names, webroot=NGINX_CERTBOT_CHALLENGES, email=args.email)
else:
    using_https = bool(args.https_fullchain or args.https_privkey)
    if using_https:
        ensure(args.https_fullchain, "ERROR: You also must pass --https-fullchain when using HTTPS.")
        ensure(args.https_privkey, "ERROR: You also must pass --https-privkey when using HTTPS.")
    https = (args.https_fullchain, args.https_privkey) if using_https else None
    nginx = Nginx(args.rebuild_nginx, not args.build_single_thread)
    nginx.config(services, with_server_names=args.deploy, with_https=https)
    nginx.run()
