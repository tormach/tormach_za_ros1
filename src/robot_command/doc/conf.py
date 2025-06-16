# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
from pathlib import Path
import sys
import catkin_pkg.package

catkin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
catkin_package = catkin_pkg.package.parse_package(
    os.path.join(catkin_dir, catkin_pkg.package.PACKAGE_MANIFEST_FILENAME)
)
sys.path.insert(0, os.path.join(catkin_dir, 'src'))
sys.path.insert(0, os.path.join(catkin_dir, 'doc'))

from generate_stubs import generate_stubs  # noqa: E402

output_stub_path = Path(catkin_dir) / 'doc' / 'stubs' / 'robot_command-stubs'
package_namespace = Path('robot_command-stubs')
output_package_path = Path(catkin_dir) / 'doc'
generate_stubs(output_stub_path, package_namespace, output_package_path)

# -- Project information -----------------------------------------------------

project = 'Tormach Robot Programming Language (TRPL)'
copyright = '2023, Tormach Inc.'
author = 'Tormach Inc.'

# The full version, including alpha/beta/rc tags
version = catkin_package.version
release = catkin_package.version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.confluencebuilder',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']


# -- Options for Confluence ---------------------------------------------------
confluence_publish = True
confluence_page_hierarchy = True
confluence_server_url = 'https://tormach.atlassian.net/wiki/'
confluence_ask_user = True
# confluence_server_user = 'alexander@roessler.systems'
confluence_ask_password = True  # note: use API key, password does not work

if os.environ.get('RELEASE_DOCS', 'false') == 'true':
    print("Release mode")
    # publish release to https://tormach.atlassian.net/wiki/spaces/ROBO/pages/1930690719/Tormach+Robot+Programming+Language
    confluence_space_key = 'ROBO'
    confluence_parent_page = 'Creating Robot Programs'
else:
    print("Prerelease mode")
    # publish prerelease to https://tormach.atlassian.net/wiki/spaces/ROB/pages/3248914435/Tormach+Robot+Programming+Language
    confluence_space_key = 'ROB'
    confluence_parent_page = 'TRPL Docs Prerelease'
