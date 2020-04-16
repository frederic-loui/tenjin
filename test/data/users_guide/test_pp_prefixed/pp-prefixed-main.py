import tenjin
from tenjin.helpers import *
pp = [ tenjin.PrefixedLinePreprocessor() ]
engine = tenjin.Engine(pp=pp)
context = { 'items': ["Haruhi", "Mikuru", "Yuki"] }
html = engine.render('example.pyhtml', context)
print(html)
