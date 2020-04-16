import tenjin
from tenjin.helpers import *

## set logging object
import logging
logging.basicConfig(level=logging.INFO)
tenjin.logger = logging

engine = tenjin.Engine()
context = {'name': 'World'}
html = engine.render('example.pyhtml', context)
#print(html)
