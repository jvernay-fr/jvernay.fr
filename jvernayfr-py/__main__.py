# SPDX-FileCopyrightText: 2022 Julien Vernay <contact@jvernay.fr>
# SPDX-License-Identifier: GPL-3.0-or-later
# Part of jvernay.fr build scripts.

"""Python module to build, run and deploy the jvernay.fr website."""

import logging, argparse
from .Nginx import Nginx, Service, Protocol
from .Certbot import Certbot
from .Utility import *

parser = argparse.ArgumentParser(prog="python3 -m jvernayfr-py", description="Module to build, run and deploy the jvernay.fr website.")
parser.add_argument("--certify", action="store_true", default=False, help="Use certbot to create HTTPS certificates.")
parser.add_argument("--deploy", action="store_true", default=False, help="Deploy server on port 80 and 443")
parser.add_argument("--build-single-thread", action="store_true", default=False,
    dest="build_single_thread", help="If nginx must be built, do it single-threaded.")
parser.add_argument("--rebuild-nginx", action="store_true", default=False,
    dest="rebuild_nginx", help="Force nginx to be rebuilt.")
args = parser.parse_args()

services = [
    Service(["jvernay.fr", "www.jvernay.fr"], 12000, Protocol.HTTP, [
        "\troot " + ResolvePath("www.jvernay.fr/root") + ";",
        "\tinclude " + ResolvePath("www.jvernay.fr/nginx.conf") + ";",
    ])
]

logging.basicConfig(level=logging.INFO)

if args.certify:
    server_names = [n for s in services for n in s.server_names]
    certbot = Certbot()
    certbot.certify(server_names)
else:
    nginx = Nginx(args.rebuild_nginx, not args.build_single_thread)
    nginx.config(services, with_server_names=args.deploy)
    nginx.run()