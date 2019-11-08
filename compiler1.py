import sys, os, re, string
from pathlib import Path

# take care of lines 74,78,92,96,110,114
class_symbol_table={}
static_count=0
field_count=0
class_total=0
subroutine_table={}
argument_count=0
local_count=0
subroutine_total=0
currentClassName=""
currentSubroutineType=""
currentSubroutineName=""
types = ['int','char','boolean']
statements = {'letStatement','ifStatement','whileStatement','doStatement','returnStatement'}
op = {'+','-','*','/','&amp;','|','&lt;','&gt;','='}
op_code = {'+':'add\n','-':'sub\n','&amp;':'and\n','|':'or\n','&gt;':'gt\n','&lt;':'lt\n','=':'eq\n','*':'call Math.multiply 2\n','/':'call Math.divide 2\n'}
unaryOp = {'-','~'}
unary_code={'-':'neg\n','~':'not\n'}
keywordConstant = {'true','false','null','this'}
index = 0
labelNum=0

def initialize_subroutine_table():    
    global subroutine_table
    global argument_count
    global local_count
    global subroutine_total
    subroutine_table={}
    argument_count=0
    local_count=0
    subroutine_total=0

def compileTerm(token_list,outfile):
    global index
    assert token_list[index][0][1:-1]=='term'
    index+=1
    if token_list[index][1] in unaryOp:
        curr_op=token_list[index][1]
        index+=1
        assert token_list[index][0][1:-1]=='term'
        compileTerm(token_list,outfile)
        assert token_list[index][0]=='</term>'
        index+=1
        outfile.write(unary_code[curr_op])
    elif token_list[index][1]=='(':
        index+=1
        compileExpression(token_list,outfile)
        assert token_list[index][0]=='</expression>'
        index+=1
        assert token_list[index][1]==')'
        index+=1
    elif token_list[index][0][1:-1]=='integerConstant':
        outfile.write("push constant " + token_list[index][1] + "\n")
        index+=1
    elif token_list[index][1] in keywordConstant:
        valu = token_list[index][1]
        if valu=='true':
            outfile.write("push constant 0\nnot\n")
        elif valu =='false' or valu == 'null':
            outfile.write("push constant 0\n")
        else:
            outfile.write("push pointer 0\n")
        index+=1
    elif token_list[index][0][1:-1]=='identifier':
        varName=token_list[index][1]
        id1=varName
        a = (len(token_list[index+1])>1  and token_list[index+1][1] not in ['(','[','.'])
        b = len(token_list[index+1])<=1
        if a or b:
            if varName not in subroutine_table and varName not in class_symbol_table:
                print("Declaration error: " + varName + " undeclared.")
            elif varName in subroutine_table:
                kind = subroutine_table[id1][0]
                typee = str(subroutine_table[id1][2])
                if kind == "field":
                    kind="this"
                outfile.write("push " + kind + " " + typee + "\n")
            elif varName in class_symbol_table:
                kind = class_symbol_table[id1][0]
                typee = str(class_symbol_table[id1][2])
                if kind == "field":
                    kind="this"
                outfile.write("push " + kind + " " + typee + "\n")
            index+=1
        elif token_list[index+1][1] =='[':
            index+=2
            compileExpression(token_list,outfile)
            assert token_list[index][0]=='</expression>'
            index+=1
            assert token_list[index][1]==']'
            index+=1
            if varName not in subroutine_table and varName not in class_symbol_table:
                print("Declaration error: " + varName + " undeclared.")
            elif varName in subroutine_table:
                kind = subroutine_table[id1][0]
                typee = subroutine_table[id1][1]
                ind = str(subroutine_table[id1][2])
                if kind == "field":
                    kind="this"
                outfile.write("push " + kind + " " + ind + "\n")
            elif varName in class_symbol_table:
                kind = class_symbol_table[id1][0]
                typee = class_symbol_table[id1][1]
                ind = str(class_symbol_table[id1][2])
                if kind == "field":
                    kind="this"
                outfile.write("push " + kind + " " + ind + "\n")
            outfile.write("add\npop pointer 1\npush that 0\n")
        else:
            index+=1
            #id1=varName
            if token_list[index][1]=='.':
                index+=1
                assert token_list[index][0][1:-1]=='identifier'
                id2=token_list[index][1]
                index+=1
                typee=""
                if id1 in subroutine_table:
                    kind = subroutine_table[id1][0]
                    typee = subroutine_table[id1][1]
                    ind = str(subroutine_table[id1][2])
                    if kind == "field":
                        kind="this"
                    outfile.write("push " + kind + " " + ind + "\n")
                elif id1 in class_symbol_table:            
                    kind = class_symbol_table[id1][0]
                    typee = class_symbol_table[id1][1]
                    ind = str(class_symbol_table[id1][2])
                    if kind == "field":
                        kind="this"
                    outfile.write("push " + kind + " " + ind + "\n")
                assert token_list[index][1]=='('
                index+=1
                nP = compileExpressionList(token_list,outfile)
                assert token_list[index][0]=='</expressionList>'
                index+=1
                assert token_list[index][1]==')'
                index+=1
                #assert token_list[index][1]==';'
                #index+=1
                if id1 in class_symbol_table or id1 in subroutine_table:
                    outfile.write("call " + typee + "." + id2 + " " + str(nP+1) + "\n")
                else:
                    outfile.write("call " + id1 + "." + id2 + " " + str(nP) + "\n")
            else:
                outfile.write("push pointer 0\n")
                assert token_list[index][1]=='('
                index+=1
                nP = compileExpressionList(token_list,outfile)
                assert token_list[index][0]=='</expressionList>'
                index+=1
                assert token_list[index][1]==')'
                index+=1
                #assert token_list[index][1]==';'
                #index+=1
                outfile.write("call " + currentClassName + "." + id1 + " " + str(nP+1) + "\n")

    elif token_list[index][0][1:-1]=='stringConstant':
        s=' '.join(token_list[index][1:-1])
        s+=" "
        index+=1
        outfile.write("push constant " + str(len(s)) + "\ncall String.new 1\n")
        for i in s:
            outfile.write("push constant " + str(ord(i)) + "\ncall String.appendChar 2\n")
    else: 
        pass


def compileExpression(token_list,outfile):
    global index
    assert token_list[index][0][1:-1]=='expression'
    index+=1
    if token_list[index][0][1:-1]=='term':        
        compileTerm(token_list,outfile)
        assert token_list[index][0]=='</term>'
        index+=1
        while token_list[index][0]=='<symbol>' and token_list[index][1] in op:
            curr_op = token_list[index][1]
            index+=1
            assert token_list[index][0][1:-1]=='term'
            compileTerm(token_list,outfile)
            assert token_list[index][0]=='</term>'
            index+=1
            outfile.write(op_code[curr_op])

def compileExpressionList(token_list,outfile):
    global index
    nP=0
    assert token_list[index][0][1:-1]=='expressionList'
    index+=1
    if token_list[index][0]!='</expressionList>':
        compileExpression(token_list,outfile)
        nP+=1
        assert token_list[index][0]=='</expression>'
        index+=1
        while(token_list[index][0] == '<symbol>' and token_list[index][1]==','):
            index+=1
            compileExpression(token_list,outfile)
            nP+=1
            assert token_list[index][0]=='</expression>'
            index+=1
    return nP

def compileDo(token_list,outfile):
    global index
    global subroutine_table
    global class_symbol_table
    assert token_list[index][0]=='<doStatement>'
    index+=1
    assert token_list[index][1]=='do'
    index+=1
    assert token_list[index][0][1:-1]=='identifier'
    id1=token_list[index][1]
    index+=1
    if token_list[index][1]=='.':
        index+=1
        assert token_list[index][0][1:-1]=='identifier'
        id2=token_list[index][1]
        index+=1
        typee=""
        if id1 in subroutine_table:
            kind = subroutine_table[id1][0]
            typee = subroutine_table[id1][1]
            ind = str(subroutine_table[id1][2])
            if kind == "field":
                kind="this"
            outfile.write("push " + kind + " " + ind + "\n")
        elif id1 in class_symbol_table:            
            kind = class_symbol_table[id1][0]
            typee = class_symbol_table[id1][1]
            ind = str(class_symbol_table[id1][2])
            if kind == "field":
                kind="this"
            outfile.write("push " + kind + " " + ind + "\n")
        assert token_list[index][1]=='('
        index+=1
        nP = compileExpressionList(token_list,outfile)
        assert token_list[index][0]=='</expressionList>'
        index+=1
        assert token_list[index][1]==')'
        index+=1
        assert token_list[index][1]==';'
        index+=1
        if id1 in class_symbol_table or id1 in subroutine_table:
            outfile.write("call " + typee + "." + id2 + " " + str(nP+1) + "\npop temp 0\n")
        else:
            outfile.write("call " + id1 + "." + id2 + " " + str(nP) + "\npop temp 0\n")
    else:
        outfile.write("push pointer 0\n")
        assert token_list[index][1]=='('
        index+=1
        nP = compileExpressionList(token_list,outfile)
        assert token_list[index][0]=='</expressionList>'
        index+=1
        assert token_list[index][1]==')'
        index+=1
        assert token_list[index][1]==';'
        index+=1
        outfile.write("call " + currentClassName + "." + id1 + " " + str(nP+1) + "\npop temp 0\n")
        

def compileReturn(token_list,outfile):
    global index
    assert token_list[index][0]=='<returnStatement>'
    index+=1
    assert token_list[index][1]=='return'
    index+=1
    if token_list[index][0][1:-1]=='expression':
        compileExpression(token_list,outfile)
        assert token_list[index][0]=='</expression>'
        index+=1
        outfile.write("return\n")
    else:
        outfile.write("push constant 0\nreturn\n")
    assert token_list[index][1]==';'
    index+=1


def compileWhile(token_list,outfile):
    global index
    global labelNum
    TlabelNum=labelNum
    labelNum+=2
    assert token_list[index][0]=='<whileStatement>'
    index+=1
    assert token_list[index][1]=='while'
    index+=1
    assert token_list[index][1]=='('
    index+=1
    outfile.write("label "+currentClassName+"."+str(TlabelNum)+"\n")
    compileExpression(token_list,outfile)
    assert token_list[index][0]=='</expression>'
    index+=1
    assert token_list[index][1]==')'
    index+=1
    outfile.write("not\nif-goto "+currentClassName+"."+str(TlabelNum+1)+"\n")
    assert token_list[index][1]=='{'
    index+=1
    assert token_list[index][0][1:-1]=='statements'
    compileStatements(token_list,outfile)
    assert token_list[index][0]=='</statements>'
    index+=1
    assert token_list[index][1]=='}'
    index+=1
    outfile.write("goto "+currentClassName+"."+str(TlabelNum)+"\n"+"label "+currentClassName+"."+str(TlabelNum+1)+"\n")    


def compileIf(token_list,outfile):
    global index
    global labelNum
    TlabelNum=labelNum
    labelNum+=2
    assert token_list[index][0][1:-1]=='ifStatement'
    index+=1
    assert token_list[index][1]=='if'
    index+=1
    assert token_list[index][1]=='('
    index+=1
    compileExpression(token_list,outfile)
    assert token_list[index][0]=='</expression>'
    index+=1
    assert token_list[index][1]==')'
    index+=1
    assert token_list[index][1]=='{'
    index+=1
    outfile.write("not\nif-goto "+currentClassName+"."+str(TlabelNum)+"\n")
    assert token_list[index][0][1:-1]=='statements'
    compileStatements(token_list,outfile)
    assert token_list[index][0]=='</statements>'
    index+=1
    assert token_list[index][1]=='}'
    index+=1
    outfile.write("goto "+currentClassName+"."+str(TlabelNum+1)+"\n"+"label "+currentClassName+"."+str(TlabelNum)+"\n")
    if token_list[index][0]=='<keyword>' and token_list[index][1]=='else':
        index+=1
        assert token_list[index][1]=='{'
        index+=1
        assert token_list[index][0][1:-1]=='statements'
        compileStatements(token_list,outfile)
        assert token_list[index][0]=='</statements>'
        index+=1
        assert token_list[index][1]=='}'
        index+=1
    outfile.write("label "+currentClassName+"."+str(TlabelNum+1)+"\n")


def compileLet(token_list,outfile):
    global index
    global subroutine_table
    assert token_list[index][0][1:-1]=='letStatement'
    index+=1
    assert token_list[index][1]=='let'
    index+=1
    assert token_list[index][0][1:-1]=='identifier'
    varName = token_list[index][1]
    index+=1
    if token_list[index][1]!='[':
        assert token_list[index][1] == '='
        index+=1
        compileExpression(token_list,outfile)
        assert token_list[index][0]=='</expression>'
        index+=1
        if varName in subroutine_table:
            outfile.write("pop " + subroutine_table[varName][0] + " " + str(subroutine_table[varName][2]) + "\n")
        elif varName in class_symbol_table:
            if class_symbol_table[varName][0]=="field":
                outfile.write("pop this " + str(class_symbol_table[varName][2]) + "\n")
            else:
                outfile.write("pop " + class_symbol_table[varName][0] + " " + str(class_symbol_table[varName][2]) + "\n")
        else:
            print("Declaration error: " + varName + " undeclared.")            
        assert token_list[index][1]==';'
        index+=1
    else:
        index+=1
        assert token_list[index][0][1:-1]=='expression'
        compileExpression(token_list,outfile)
        assert token_list[index][0]=='</expression>'
        index+=1
        assert token_list[index][1]==']'
        index+=1
        outfile.write("push " + subroutine_table[varName][0] + " " + str(subroutine_table[varName][2]) + "\n" + "add\n")
        assert token_list[index][1] == '='
        index+=1
        compileExpression(token_list,outfile)
        assert token_list[index][0]=='</expression>'
        index+=1
        outfile.write("pop temp 0\npop pointer 1\npush temp 0\npop that 0\n")
        assert token_list[index][1]==';'
        index+=1


def compileStatements(token_list,outfile):
    global index
    assert token_list[index][0][1:-1]=='statements'
    index+=1
    while(token_list[index][0]!="</statements>"):
        assert token_list[index][0][1:-1] in statements
        statement_type = token_list[index][0][1:-1]
        f[statement_type](token_list,outfile)
        assert token_list[index][0][2:-1]==statement_type
        index+=1
     

def compileVarDec(token_list,outfile):
    global index
    global subroutine_table
    global local_count
    global subroutine_total
    assert token_list[index][0]=='<varDec>'
    index+=1
    assert token_list[index][1]=='var'
    index+=1
    kind='local'
    assert token_list[index][1] in ['int','char','boolean'] or token_list[index][0][1:-1]=='identifier'
    if token_list[index][1] in ['int','char','boolean']:
        typee=token_list[index][1]
    else:
        typee=token_list[index][1]
    index+=1
    assert token_list[index][0][1:-1]=='identifier'
    name = token_list[index][1]
    index+=1    
    subroutine_table[name]=[kind,typee,local_count]
    local_count+=1
    subroutine_total+=1
    while(token_list[index][1]==','):
        index+=1
        assert token_list[index][0][1:-1]=='identifier'
        name = token_list[index][1]
        index+=1
        subroutine_table[name]=[kind,typee,local_count]
        local_count+=1
        subroutine_total+=1
    assert token_list[index][1]==';'
    index+=1
    #print(subroutine_table)


def compileSubroutineBody(token_list,outfile):
    global index
    global currentSubroutineName
    global local_count
    global currentClassName
    assert token_list[index][0][1:-1]=='subroutineBody'
    index+=1
    assert token_list[index][1]=='{'
    index+=1
    while(token_list[index][0]=='<varDec>'):
        compileVarDec(token_list,outfile)
        assert token_list[index][0]=='</varDec>'
        index+=1
    outfile.write("function " + currentClassName + "." + currentSubroutineName + " " + str(local_count) + "\n")
    if currentSubroutineType=='constructor':
        outfile.write("push constant " + str(field_count) + "\n")
        outfile.write("call Memory.alloc 1\npop pointer 0\n")
    if currentSubroutineType=='method':
        outfile.write("push argument 0\npop pointer 0\n")
    assert token_list[index][0][1:-1]=='statements'
    #index+=1
    compileStatements(token_list,outfile)
    assert token_list[index][0]=='</statements>'
    index+=1
    assert token_list[index][1]=='}'
    index+=1


def compileParameterList(token_list,outfile):
    global index
    global subroutine_table
    global argument_count
    global local_count
    global subroutine_total
    assert token_list[index][0][1:-1]=='parameterList'
    index+=1
    if token_list[index][0] != '</parameterList>':
        if token_list[index][1] in types:
            typee = token_list[index][1]
            index+=1
        elif token_list[index][0][1:-1]=='identifier':
            typee = token_list[index][1]
            index+=1
        else:
            assert False, "Illegal Type"
        assert token_list[index][0][1:-1]=='identifier'
        varname = token_list[index][1]
        index+=1
        subroutine_table[varname]=['argument',typee,argument_count]
        argument_count+=1
        subroutine_total+=1
        while(token_list[index][0]=='<symbol>' and token_list[index][1]==','):
            index+=1
            if token_list[index][1] in types:
                typee = token_list[index][1]
                index+=1
            elif token_list[index][0][1:-1]=='identifier':
                typee = token_list[index][1]
                index+=1
            else:
                assert False, "Illegal Type"
            assert token_list[index][0][1:-1]=='identifier'
            varname = token_list[index][1]
            index+=1
            subroutine_table[varname]=['argument',typee,argument_count]
            argument_count+=1
            subroutine_total+=1


def compileClassVarDec(token_list,outfile):
    global index
    global class_symbol_table
    global class_total
    global static_count
    global field_count

    assert token_list[index][0]=='<classVarDec>'
    index+=1
    assert token_list[index][1] in ['static','field']
    kind=token_list[index][1]
    index+=1
    assert token_list[index][1] in ['int','char','boolean'] or token_list[index][0][1:-1]=='identifier'
    if token_list[index][1] in ['int','char','boolean']:
        typee=token_list[index][1]
    else:
        typee=token_list[index][1]
    index+=1
    assert token_list[index][0][1:-1]=='identifier'
    name = token_list[index][1]
    index+=1
    class_total+=1
    if kind=='static':
        class_symbol_table[name]=[kind,typee,static_count]
        static_count+=1
    else:
        class_symbol_table[name]=[kind,typee,field_count]
        field_count+=1
    while(token_list[index][1]==','):
        index+=1
        assert token_list[index][0][1:-1]=='identifier'
        name = token_list[index][1]
        index+=1
        class_total+=1
        if kind=='static':
            class_symbol_table[name]=[kind,typee,static_count]
            static_count+=1
        else:
            class_symbol_table[name]=[kind,typee,field_count]
            field_count+=1
    assert token_list[index][1]==';'
    index+=1
    #print(class_symbol_table)


def compilesubroutineDec(token_list,outfile):
    global index
    global class_symbol_table
    global class_total
    global static_count
    global field_count
    global subroutine_table
    global argument_count
    global local_count
    global subroutine_total
    global currentSubroutineName
    global currentSubroutineType

    assert token_list[index][0]=='<subroutineDec>'
    index+=1
    initialize_subroutine_table()
    assert token_list[index][1] in ['constructor','function','method']
    currentSubroutineType=token_list[index][1]
    index +=1
    assert (token_list[index][1] in types) or (token_list[index][0][1:-1] == 'identifier') or (token_list[index][1]=='void')
    index+=1
    assert token_list[index][0][1:-1] == 'identifier'
    currentSubroutineName=token_list[index][1]
    index+=1
    if currentSubroutineType=='method':
        subroutine_table['this']=['argument',currentClassName,0]
        subroutine_total+=1
        argument_count+=1
    assert token_list[index][1]=='('
    index+=1
    compileParameterList(token_list,outfile)
    assert token_list[index][0]=='</parameterList>'
    index+=1
    assert token_list[index][1]==')'
    index+=1
    compileSubroutineBody(token_list,outfile)
    assert token_list[index][0]=='</subroutineBody>'
    index+=1


def compileClass(token_list,outfile):
    global index
    global currentClassName
    assert token_list[index][0][1:-1]=='class'
    index+=1
    index+=1
    assert token_list[index][0][1:-1]=='identifier'
    currentClassName=token_list[index][1]
    index+=1
    assert token_list[index][1]=='{'
    index+=1
    while(token_list[index][0]=='<classVarDec>'):
        compileClassVarDec(token_list,outfile)
        assert token_list[index][0]=='</classVarDec>'
        index+=1
    while(token_list[index][0]=='<subroutineDec>'):
        compilesubroutineDec(token_list,outfile)
        assert token_list[index][0]=='</subroutineDec>'
        index+=1
    assert token_list[index][1]=='}'
    index+=1

def CompilationEngine(infile,outfile):
    token_list=[]
    for line in infile:
        line=line.split()
        if(len(line)>0):
            token_list.append(line) 
            #print(line)   
    if(len(token_list)>0):        
        compileClass(token_list,outfile)
        assert token_list[index][0]=='</class>'

f = {"letStatement" : compileLet,"ifStatement" : compileIf,"doStatement" : compileDo,"whileStatement" : compileWhile, "returnStatement" : compileReturn}

def main():
    arg = sys.argv[1]
    global fileName    
    global index
    glob_path = Path(arg)
    file_list = [str(pp) for pp in glob_path.glob("**/*.xml")]    
    for file in file_list:
        fileName=os.path.basename(file)[:-4]
        index=0
        #print(fileName)
        infile=open(file)
        outfile = open(arg+"/"+fileName+ ".vm", "w")         
        CompilationEngine(infile,outfile)

if __name__=="__main__":
    main()

