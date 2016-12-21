#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2016 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-10-19
#

"""Search GIFs"""

from __future__ import print_function, unicode_literals, absolute_import

from collections import namedtuple
from operator import attrgetter
import os
import sys
from urllib import quote

from thumbnails import Thumbs
from workflow import Workflow3, ICON_WARNING
from workflow.background import is_running, run_in_background

log = None

HELP_URL = 'https://github.com/deanishe/alfred-gifs'
GITHUB = 'deanishe/alfred-gifs'

# Local GIF directory
GIF_DIR = os.path.expanduser(os.getenv('GIF_DIR'))
# Remote URL that corresponds to above
GIF_URL = os.getenv('GIF_URL')


Gif = namedtuple('Gif', 'name url path icon')

thumbs = None


def load_gifs():
    """Return list of `Gif` objects."""
    gifs = []
    for fn in os.listdir(GIF_DIR):
        if fn.lower().endswith('.gif'):
            name = os.path.splitext(fn)[0]
            path = os.path.join(GIF_DIR, fn)
            icon = thumbs.thumbnail(path)
            url = os.path.join(GIF_URL, quote(fn))
            gif = Gif(name, url, path, icon)
            gifs.append(gif)

    log.debug('%d GIFs in %s', len(gifs), GIF_DIR)
    return gifs


def bb_image(url):
    """BB Code image markup for `url`."""
    return '[img]{}[/img]'.format(url)


def markdown_image(url):
    """Markdown image markup for `url`."""
    return '![]({})'.format(url)


def main(wf):
    """Run Script Filter."""
    global thumbs
    # Initialise thumbnail generator
    thumbs = Thumbs(wf.cachefile('thumbs'))

    query = None
    if len(wf.args):
        query = wf.args[0].strip()

    gifs = load_gifs()

    if query:
        gifs = wf.filter(query, gifs, key=attrgetter('name'), min_score=30)

    if not gifs:
        wf.add_item('No matching GIFs',
                    'Try a different query',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return

    # Display results
    for gif in gifs:
        it = wf.add_item(gif.name,
                         'Copy URL to clipboard',
                         arg=gif.url,
                         quicklookurl=gif.url,
                         icon=gif.icon,
                         valid=True)

        # Alternate actions
        mod = it.add_modifier('cmd', 'Open in Browser', arg=gif.url)
        mod.setvar('action', 'browse')

        mod = it.add_modifier('alt', 'Copy as BB Code',
                              arg=bb_image(gif.url))
        mod.setvar('action', 'bbcode')

        mod = it.add_modifier('ctrl', 'Copy as Markdown',
                              arg=markdown_image(gif.url))
        mod.setvar('action', 'markdown')

    wf.send_feedback()

    # Generate thumbnails if necessary
    thumbs.save_queue()
    if thumbs.has_queue and not is_running('generate_thumbnails'):
        run_in_background('generate_thumbnails', ['/usr/bin/python',
                          wf.workflowfile('thumbnails.py')])

    return 0


if __name__ == '__main__':
    wf = Workflow3(help_url=HELP_URL,
                   update_settings={'github_slug': GITHUB})
    log = wf.logger
    sys.exit(wf.run(main))
