import tenjin
template = tenjin.Template('views/page.pyhtml')
print(template.script)

### or:
#template = tenjin.Template()
#with open('views/page.pyhtml') as f:
#    print(template.convert(f.read(), 'views/page.pyhtml'))

### or:
#engine = tenjin.Engine(path=['views'])
#print(engine.get_template('page.pyhtml').script)
