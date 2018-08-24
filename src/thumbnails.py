#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2015 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-10-19
#

"""Generate thumbnails in the background."""

from __future__ import print_function, unicode_literals, absolute_import

import logging
from glob import glob
import hashlib
import os
import subprocess
import sys

from workflow import Workflow
from workflow.workflow import LockFile, atomic_writer


log = logging.getLogger('workflow.thumbnails')


class Thumbs(object):
    """Thumbnail generator."""

    def __init__(self, cachedir):
        """Create new `Thumbs` object.

        Args:
            cachedir (str): Path to directory to save thumbnails in.

        """
        self._cachedir = os.path.abspath(cachedir)
        self._img_dir = os.path.join(self._cachedir, 'img')
        self._queue_dir = os.path.join(self._cachedir, 'jobs')
        self._queue = []

        try:
            os.makedirs(self._img_dir)
            os.makedirs(self._queue_dir)
        except (IOError, OSError):
            pass

    @property
    def cachedir(self):
        """Where thumbnails are saved.

        Returns:
            str: Directory path.

        """
        return self._cachedir

    def thumbnail_path(self, img_path):
        """Return appropriate path for thumbnail.

        Args:
            img_path (str): Path to image file.

        Returns:
            str: Path to thumbnail.

        """
        h = self.job_name(img_path)
        dirpath = os.path.join(self._img_dir, h[:2], h[2:4])
        return os.path.join(dirpath, h + '.png')

    def job_path(self, img_path):
        """Return job file path for image."""
        h = self.job_name(img_path)
        return os.path.join(self._queue_dir, h + '.txt')

    def job_name(self, img_path):
        """Return job name for image.

        Args:
            img_path (str): Path to image file.

        Returns:
            str: Name of job file.

        """
        if isinstance(img_path, unicode):
            img_path = img_path.encode('utf-8')
        elif not isinstance(img_path, str):
            img_path = str(img_path)

        return hashlib.sha256(img_path).hexdigest()

    def thumbnail(self, img_path):
        """Return resized thumbnail for `img_path`.

        Args:
            img_path (str): Path to original images.

        Returns:
            str: Path to thumbnail image.

        """
        thumb_path = self.thumbnail_path(img_path)

        if os.path.exists(thumb_path):
            return thumb_path
        else:
            self.queue_thumbnail(img_path)
            return None

    def queue_thumbnail(self, img_path):
        """Add `img_path` to queue for later thumbnail generation.

        Args:
            img_path (str): Path to image file.

        """
        self._queue.append(img_path)

    def save_queue(self):
        """Save queued files."""
        if not self._queue:
            return

        for p in self._queue:
            if isinstance(p, unicode):
                p = p.encode('utf-8')

            if os.path.exists(self.thumbnail_path(p)):
                log.debug('thumb already exists: %r', p)
                continue

            job_path = self.job_path(p)
            if os.path.exists(job_path):
                # log.debug('job already queued: %r', p)
                continue

            with open(job_path, 'wb') as fp:
                fp.write(p)

            log.debug('queued for thumbnail generation : %r', p)

        self._queue = []

    @property
    def queue_size(self):
        """Return length of queue.

        Returns:
            int: Number of thumbnails queued for generation.

        """
        return len(glob(os.path.join(self._queue_dir, '*.txt')))

    def process_queue(self):
        """Generate thumbnails for queued files."""
        queue = glob(os.path.join(self._queue_dir, '*.txt'))

        success = True
        for i, job_path in enumerate(queue):
            with open(job_path) as fp:
                img_path = fp.read().strip()

            if not os.path.exists(img_path):
                log.warning('queued image does not exist: %r', img_path)
                continue

            log.debug('[%d/%d] generating thumbnail for %r ...',
                      i + 1, len(queue), img_path)
            if not self.generate_thumbnail(img_path):
                success = False
            else:
                os.unlink(job_path)

        return success

    def generate_thumbnail(self, img_path):
        """Generate and save thumbnail for `img_path`.

        Args:
            img_path (str): Path to image file.

        Returns:
            bool: `True` if generation succeeded, else `False`.

        """
        thumb_path = self.thumbnail_path(img_path)
        dirpath = os.path.dirname(thumb_path)
        try:
            os.makedirs(dirpath)
        except OSError:  # path exists
            pass

        cmd = [
            '/usr/local/bin/gm',
            'convert',
            '-thumbnail', '256x256>',
            '-background', 'transparent',
            '-gravity', 'center',
            '-extent', '256x256',
            img_path, thumb_path
        ]

        retcode = subprocess.call(cmd)

        if retcode:
            log.error('convert exited with %d : %s', retcode, img_path)
            return False

        log.debug('wrote thumbnail for %r to %r', img_path, thumb_path)

        return True


def main(wf):
    """Generate any thumbnails pending in the queue.

    Args:
        wf (Workflow): Current workflow instance.

    """
    t = Thumbs(wf.cachefile('thumbs'))
    t.process_queue()


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
