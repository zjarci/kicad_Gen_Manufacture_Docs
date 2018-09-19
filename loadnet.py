import sexpdata as sexp
import pcbnew as pn
import io

def loadNet(brd = None):
    if not brd:
        brd = pn.GetBoard()
    name = brd.GetFileName()
    name = name[0:name.rindex('.')] + '.net'
    return loadNetFile(name)

def toStr(v):
    if type(v) == str :
        return v
    return v.value()
    
def parseComp(comp):
    r = {}
    if comp[0].value() != "comp":
        print "Parse comp error"
        return None
    for i in range(1, len(comp)):
        key = comp[i][0].value()
        if key == "value":
            r['value'] = toStr(comp[i][1])
        if key == "footprint":
            fp = toStr(comp[i][1])
            pos = fp.rfind(':')
            if pos != -1:
                fp = fp[pos+1:]
            r['footprint'] = fp
        if key == "datasheet":
            r['datasheet'] = toStr(comp[i][1])
        if key == "fields":
            fields = comp[i]
            for j in range(1, len(fields)):
                field = fields[j]
                fkey = toStr(field[1][1])
                if fkey == "SuppliersPartNumber":
                    r['partNumber'] = toStr(field[2])
                if fkey == "Comment":
                    r['comment'] = toStr(field[2])
                if fkey == "description":
                    r['description'] = toStr(field[2])
    return r
    
def loadNetFile(fileName):
    f = io.open(fileName, "rb")
    nets = sexp.loads(f.read())
    if nets[3][0].value() != "components":
        return None
    comps = nets[3]
    r = {}
    for i in range(1, len(comps)):
        comp = comps[i]
        c = parseComp(comp)
        r[c['value'] + "&" + c['footprint']] = c
    return r
            
            
            