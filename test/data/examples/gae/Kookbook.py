##
## requires PyKook
## http://www.kuwata-lab.com/kook/
##

GAE_HOME = prop("GAE_HOME", "/usr/local/google_appengine")
dev_appserver_py = GAE_HOME + "/dev_appserver.py"

@recipe
@ingreds("lib/tenjin.py")
@spices("-p PORT: port number (default 8080)")
def server(c, *args, **kwargs):
    """start server"""
    port = kwargs.get("port", "8080")
    system(c%"python $(dev_appserver_py) -p $(port) .")

@recipe
@product("lib/tenjin.py")
@ingreds("../../lib2/tenjin.py")
def file_lib_tenjin_py(c):
    """copy tenjin.py into lib"""
    mkdir_p("lib")
    cp_p(c.ingred, c.product)
