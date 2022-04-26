#!/usr/bin/env python3

# Copyright © 2022 Yannick Gingras <ygingras@ygingras.net>

# This file is part of Revengate.

# Revengate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Revengate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Revengate.  If not, see <https://www.gnu.org/licenses/>.

""" Top-level Android entry point """

import os
from pprint import pprint


def show_all_files():
    for d in os.environ["PYTHONPATH"].split(":"):
        print(os.system(f"ls -R {d}"))

def main():
    show_all_files()

    from revengate.governor import Governor
    gov = Governor()
    gov.start()


if __name__ == "__main__":
    main()
