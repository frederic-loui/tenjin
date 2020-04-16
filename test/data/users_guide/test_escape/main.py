import tenjin
from tenjin.helpers import *
import cgi
engine = tenjin.Engine(path=['views'], escapefunc="cgi.escape", tostrfunc="str")
print(engine.get_template('page.pyhtml').script)
