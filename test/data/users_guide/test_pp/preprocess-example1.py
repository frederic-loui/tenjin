import tenjin
from tenjin.helpers import *
pp = [
  tenjin.TemplatePreprocessor(),      # same as preprocess=True
  tenjin.TrimPreprocessor(),          # trim spaces before tags
  tenjin.PrefixedLinePreprocessor(),  # convert ':: ...' into '<?py ... ?>'
  tenjin.JavaScriptPreprocessor(),    # allow to embed client-side template
]
engine = tenjin.Engine(pp=pp)
context = {'items': ["Haruhi", "Mikuru", "Yuki"]}
html = engine.render('example.pyhtml', context)
