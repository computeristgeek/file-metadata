# -*- coding: utf-8 -*-
"""
Utilities that help wikibot scripts. This script should be imported
in all scripts rather than directly importing pywikibot, as it handles
exceptions when importing pywikibot appropriately.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import logging
import os
import sys
import tempfile

from six import string_types

from file_metadata.utilities import download, retry

try:
    import pywikibot
except ImportError:
    logging.error("To run the script, pywikibot is required. Please install "
                  "it and try again. The nightly version of pywikibot can be "
                  "installed with `pip install git+https://"
                  "gerrit.wikimedia.org/r/pywikibot/core.git#egg=pywikibot`")
    sys.exit(1)
except RuntimeError as err:
    if (len(err.args) > 0 and
            "No user-config.py found in directory" in err.args[0]):
        logging.error("A user-config.py is require to run the pywikibot "
                      "script. To create the user-config.py run the "
                      "command `wikibot-create-config`.")
        sys.exit(1)
import pywikibot.editor
from pywikibot import textlib
from pywikibot.tools.formatter import color_format


def stringify(val):
    """
    Convert to val only if it is not already of type string. This is needed
    because strings like \xfa (ú) throw error when str() is used on them
    again.
    """
    return val if isinstance(val, string_types) else str(val)


@retry(IOError, tries=3)
def download_page(page, timeout=None, cache_dir=tempfile.gettempdir()):
    fname = page.title(as_filename=True).encode('ascii', 'replace')
    fpath = os.path.join(cache_dir, fname)
    download(page.fileUrl(), fpath, timeout=timeout)
    return fpath


def put_cats(page, new_cats, summary=None, always=False):
    line_sep = pywikibot.config.line_separator
    if not summary:
        summary = "Adding categories using catfiles"

    oldtext = page.get()
    old_cats = textlib.getCategoryLinks(oldtext)
    old_templates = textlib.extract_templates_and_params(oldtext)
    old_template_titles = [i[0].lower() for i in old_templates]

    templates, cats = [], []
    for val in new_cats:
        if val.lower().startswith('category:'):
            tmp_cat = pywikibot.Category(pywikibot.Link(val, page.site))
            if tmp_cat not in old_cats:
                cats.append(tmp_cat)
        elif val.lower().startswith('{{'):
            tmp_templates = textlib.extract_templates_and_params(val)
            if len(tmp_templates) != 1:
                logging.warn("There was an error when parsing the template "
                             "'{0}'. Contact the developer, skipping it for "
                             "now.".format(val))
            tmp_template = tmp_templates[0]
            if tmp_template[0].lower() not in old_template_titles:
                templates.append(val)

    # Add templates to the top, and the categories to the bottom.
    newtext = oldtext
    if len(templates) > 0:
        newtext = line_sep.join(templates) + line_sep + newtext
    if len(cats) > 0:
        newtext = (newtext + line_sep +
                   line_sep.join(c.title(asLink=True, underscore=False)
                                 for c in cats))

    if oldtext == newtext:
        pywikibot.output("No changes to the page need to be made.")
        return

    while True:
        # Show the diff that has been created
        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<',
            page.title(underscore=False)))
        pywikibot.showDiff(oldtext, newtext)

        if always:
            choice = 'y'
        else:
            # Ask user whether to accept
            choice = pywikibot.input_choice(
                'Do you want to accept these changes?',
                [('Yes', 'y'), ('No', 'n'), ('Edit', 'e'),
                 ('Open browser', 'b')],
                'n', automatic_quit=False)
        # Apply the choice from above
        if choice == 'n':
            break
        elif choice == 'b':
            pywikibot.bot.open_webbrowser(page)
        elif choice == 'e':
            editor = pywikibot.editor.TextEditor()
            as_edited = editor.edit(newtext)
            if as_edited and as_edited != newtext:
                newtext = as_edited
        elif choice == 'y':
            try:
                page.put_async(newtext, summary)
            except pywikibot.EditConflict:
                pywikibot.output('Edit conflict! Skipping')
            except pywikibot.ServerError:
                pywikibot.output('Server Error! Skipping')
            except pywikibot.SpamfilterError as e:
                pywikibot.output(
                    'Cannot change %s because of blacklist entry %s'
                    % (page.title(), e.url))
            except pywikibot.LockedPage:
                pywikibot.output('Skipping %s (locked page)' % page.title())
            except pywikibot.PageNotSaved as error:
                pywikibot.output('Error putting page: %s' % error.args)
            break
