"""Show all images in the "gallery" folder

Usage:

   .. simple_gallery::
      :dir: gallery

where "gallery" is relative to the folder containing conf.py.

Changelog:
0.1 (2019-10-24)
 - initial release
"""
import pathlib

from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive, directives
from sphinx.util.nodes import nested_parse_with_titles
from docutils import nodes


class SimpleGalleryDirective(Directive):
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        'dir': directives.unchanged,
    }

    def get_files(self):
        """This will return a list of files"""
        root = pathlib.Path(__file__).parent.parent
        gpath = root / self.options["dir"]
        files = []
        for ff in gpath.glob("*"):
            if ff.suffix in [".png", "*.jpg"]:
                files.append(ff.relative_to(root))
        return files

    def run(self):
        rst = []
        files = self.get_files()

        for ff in files:
            rst.append(".. image:: {}".format(ff))
            rst.append("    :target: _images/{}".format(ff.name))
            rst.append("    :scale: 25%")
            rst.append("    :align: left")
            rst.append("")

        vl = ViewList(rst, "fakefile.rst")
        # Create a node.
        node = nodes.section()
        node.document = self.state.document
        # Parse the rst.
        nested_parse_with_titles(self.state, vl, node)
        return node.children


def setup(app):
    app.add_directive('simple_gallery', SimpleGalleryDirective)
    return {'version': '0.1'}   # identifies the version of our extension
