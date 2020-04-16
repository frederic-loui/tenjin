import tenjin
from tenjin.helpers import *
engine = tenjin.Engine(layout='layout.pyhtml', trace=True)
output = engine.render('main.pyhtml', {'items': ['A','B','C']})
print(output)
