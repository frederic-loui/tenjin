value = 'My Great Example'

## create engine object with preprocessing enabled
import tenjin
from tenjin.helpers import *
engine = tenjin.Engine(path=['views'], preprocess=True)

## print Python script code
print("------ converted script ------")
print(engine.get_template('pp-example1.pyhtml').script)

## render html
html = engine.render('pp-example1.pyhtml', {})
print("------ rendered html ------")
print(html)
