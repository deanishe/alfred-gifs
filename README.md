
Say it with GIFs (and Alfred)
=============================


A slightly more featureful version of [the GIF workflow from Destroy Today][orig].


Requirements
------------

You must have [GraphicsMagick][gm] installed at `/usr/local/bin/gm` to use this workflow (e.g. via [Homebrew][brew]).


Configuration
-------------

In the workflow configuration sheet (`[x]` icon):

1. Set `GIF_DIR` to the path to your local GIF hoard.
2. Set `GIF_URL` to the URL that corresponds to `GIF_DIR` in your Dropbox or on your webserver.


Usage
-----

- `gif [<query>]` — Filter your GIFs
	- `↩` — Copy the URL of the GIF to the clipboard
	- `⌘+↩` — Open the (remote) GIF in your browser
	- `⌥+↩` — Copy URL as BB Code markup
	- `^+↩` — Copy URL as Markdown markup


Licensing, thanks
-----------------

This workflow is released under the [MIT licence][mit].

It depends on [GraphicsMagick][gm] and the [Alfred-Workflow][aw] library, both also released under the [MIT licence][mit].

The icon if from the [Destroy Today][orig] workflow on which it's based.


[brew]: http://brew.sh
[gm]: http://www.graphicsmagick.org
[mit]: https://opensource.org/licenses/MIT
[orig]: http://destroytoday.com/writings/gif-workflow/
[aw]: http://www.deanishe.net/alfred-workflow/