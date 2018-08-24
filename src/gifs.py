#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2016 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-10-19
#

"""Search GIFs."""

from __future__ import print_function, unicode_literals, absolute_import

from collections import namedtuple
from operator import attrgetter
import os
import sys
from urllib import quote

from thumbnails import Thumbs
from workflow import Workflow3
from workflow.background import is_running, run_in_background

log = None

HELP_URL = 'https://github.com/deanishe/alfred-gifs'
GITHUB = 'deanishe/alfred-gifs'
ICON_UPDATE = 'update-available.png'

# Local GIF directory
GIF_DIR = os.path.expanduser(os.getenv('GIF_DIR')).decode('utf-8')
# Remote URL that corresponds to above
GIF_URL = os.getenv('GIF_URL').decode('utf-8')

# Whether scripts was called via Snippet Trigger
IS_SNIPPET = os.getenv('focusedapp') is not None

# Whether to Quicklook local files or URLs
PREVIEW_LOCAL = os.getenv('PREVIEW_LOCAL', '') not in ('', '0')

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

    show_uids = True
    query = None
    if len(wf.args):
        query = wf.args[0].strip()

    if wf.update_available and not query:
        show_uids = False  # force item to top
        wf.add_item('An Update is Available',
                    '↩ or ⇥ to install update',
                    valid=False,
                    autocomplete='workflow:update',
                    icon=ICON_UPDATE)

    gifs = load_gifs()

    if query:
        gifs = wf.filter(query, gifs, key=attrgetter('name'), min_score=30)

    # Display results
    for gif in gifs:
        action = 'copy'
        subtitle = 'Copy URL to clipboard'
        if IS_SNIPPET:
            action = 'paste'
            subtitle = 'Paste URL to active app'

        it = wf.add_item(gif.name,
                         subtitle,
                         arg=gif.url,
                         quicklookurl=gif.path if PREVIEW_LOCAL else gif.url,
                         uid=gif.url if show_uids else None,
                         icon=gif.icon,
                         valid=True)

        it.setvar('action', action)

        # Alternate actions
        mod = it.add_modifier('cmd', 'Open in Browser', arg=gif.url)
        mod.setvar('action', 'browse')

        mod = it.add_modifier('alt', action.title() + ' as BB Code',
                              arg=bb_image(gif.url))

        mod = it.add_modifier('ctrl', action.title() + ' as Markdown',
                              arg=markdown_image(gif.url))

        mod = it.add_modifier('shift', 'Paste URL in active app', arg=gif.url)
        mod.setvar('action', 'paste')

    # Generate thumbnails if necessary
    thumbs.save_queue()
    running = is_running('generate_thumbnails')
    if not running and thumbs.queue_size:
        run_in_background('generate_thumbnails', ['/usr/bin/python',
                          wf.workflowfile('thumbnails.py')])
        running = True

    if running:
        wf.rerun = 1

    wf.warn_empty('No matching GIFs', 'Try a different query?')
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(help_url=HELP_URL,
                   update_settings={'github_slug': GITHUB})
    log = wf.logger
    sys.exit(wf.run(main))
