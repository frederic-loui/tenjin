import tenjin
from tenjin.helpers import *
from tenjin.html import text2html
engine = tenjin.Engine(path=['views'])
context = {
    'title': 'Blog Post Test',
    'post_content': "Foo\nBar\nBaz",
}
html = engine.render('blog_post.pyhtml', context)
print(html)
