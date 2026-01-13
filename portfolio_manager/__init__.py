from flask import Flask
import os

# Get the parent directory (project root) where templates is located
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
app = Flask(__name__, template_folder=template_dir)

from . import routes