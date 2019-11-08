import sys, os, re
from pathlib import Path

keyword = {'class','constructor','function','method','field','static','var','int','char','boolean','void','true','false','null','this','let','do','if','else','while','return'}
symbol = {'{','}','(',')','[',']','.',',',';','+','-','*','/','&','|','<','>','=','~'}
special = {'<','>','&','"'}
types = {'int','char','boolean'}
function_types = {'constructor','function','method'}
statements = {'let','if','while','do','return'}
op = {'+','-','*','/','&amp;','|','&lt;','&gt;','='}
unaryOp = {'-','~'}
keywordConstant = {'true','false','null','this'}

index=0

def remove_comments(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " " # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)

def JackTokenizer(infile,outfile):
    infile = remove_comments(infile).strip()
    SCANNER = re.compile(r'''
        (\s+) |                      # whitespace
        (//)[^\n]* |                 # comments
        0[xX]([0-9A-Fa-f]+) |        # hexadecimal integer literals
        (\d+) |                      # integer literals
        (<<|>>) |                    # multi-char punctuation
        ([][(){}<>=,;:*+-/|~&]) |       # punctuation
        ([A-Za-z_][A-Za-z0-9_]*) |   # identifiers
        """(.*?)""" |                # multi-line string literal
        "((?:[^"\n\\]|\\.)*)" |      # regular string literal
        (.)                          # an error!
    ''', re.DOTALL | re.VERBOSE)
    for match in re.finditer(SCANNER,infile):
        _, __, ___, integer, ____, punct, word, _____, stringlit, ______ = match.groups()
        #print(match.group())
        if integer:
            outfile.write("<integerConstant> "+match.group()+" </integerConstant>\n")
        if stringlit:
            outfile.write("<stringConstant> "+match.group()[1:-1]+" </stringConstant>\n")
        if word:
            if match.group() in keyword:
                outfile.write("<keyword> "+match.group()+" </keyword>\n")
            else:
                assert match.group()[0].isdigit() == False, "Illegal Identifier Error"
                outfile.write("<identifier> "+match.group()+" </identifier>\n")
        if punct:
            if match.group() not in special:
                outfile.write("<symbol> "+match.group()+" </symbol>\n")
            elif match.group()=='<':
                outfile.write("<symbol> "+"&lt;"+" </symbol>\n")
            elif match.group()=='>':
                outfile.write("<symbol> "+"&gt;"+" </symbol>\n")
            elif match.group()=='&':
                outfile.write("<symbol> "+"&amp;"+" </symbol>\n")
            elif match.group()=='"':
                outfile.write("<symbol> "+"&quot;"+" </symbol>\n")

def compileExpressionList(token_list,outfile):
    global index
    if token_list[index][1]!=')':
        outfile.write("<expression>\n")
        compileExpression(token_list,outfile)
        outfile.write("</expression>\n")
        while token_list[index][1]==',':
            outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
            index+=1
            outfile.write("<expression>\n")
            compileExpression(token_list,outfile)
            outfile.write("</expression>\n")

def compilesubroutineCall(token_list,outfile):
    global index
    assert token_list[index][0][1:-1]=='identifier',"No function name"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    if token_list[index][1]=='(':
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        outfile.write("<expressionList>\n")
        compileExpressionList(token_list,outfile)
        outfile.write("</expressionList>\n")
        assert token_list[index][1]==')',"Missing closing bracket"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
    elif token_list[index][1]=='.':
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        assert token_list[index][0][1:-1]=='identifier',"No function name"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        assert token_list[index][1]=='(',"Missing opening bracket"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        outfile.write("<expressionList>\n")
        compileExpressionList(token_list,outfile)
        outfile.write("</expressionList>\n")
        assert token_list[index][1]==')',"Missing closing bracket"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1

def compileExpression(token_list,outfile):
    global index
    compileTerm(token_list,outfile)
    while(token_list[index][1] in op):
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        compileTerm(token_list,outfile)

def compileTerm(token_list,outfile):
    global index
    if index <len(token_list):
        outfile.write("<term>\n")
        if(token_list[index][1]=='('):
            outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
            index+=1
            outfile.write("<expression>\n")
            compileExpression(token_list,outfile)
            outfile.write("</expression>\n")
            assert token_list[index][1]==')',"Missing closing bracket"
            outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
            index+=1
        else:
            if token_list[index][0][1:-1] in ['integerConstant']:
                outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                index+=1
            elif token_list[index][1] in keywordConstant:
                outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                index+=1

            elif token_list[index][0][1:-1] == 'stringConstant':
                outfile.write(' '.join(token_list[index]))
                outfile.write('\n')
                index+=1
            elif token_list[index][0][1:-1]=='identifier':                
                if(token_list[index+1][1]=='(' or token_list[index+1][1]=='.'):
                    compilesubroutineCall(token_list,outfile)
                elif token_list[index+1][1]=='[':
                    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                    index+=1
                    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                    index+=1
                    outfile.write("<expression>\n")
                    compileExpression(token_list,outfile)
                    outfile.write("</expression>\n")
                    assert token_list[index][1]==']',"Missing ] bracket"
                    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                    index+=1
                else:
                    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                    index+=1
            elif token_list[index][1] in unaryOp:
                outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
                index+=1
                compileTerm(token_list,outfile)
        outfile.write("</term>\n")                


def compileLet(token_list,outfile):
    global index
    assert token_list[index][1]=='let',"wrong keyword"
    outfile.write("<letStatement>\n")
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][0][1:-1]=='identifier',"No variable name"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    if token_list[index][1]=='[':
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        outfile.write("<expression>\n")
        compileExpression(token_list,outfile)
        outfile.write("</expression>\n")
        assert token_list[index][1]==']',"Missing closing array bracket"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
    assert token_list[index][1]=='=',"Equal symbol missing"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<expression>\n")
    compileExpression(token_list,outfile)
    outfile.write("</expression>\n")
    assert token_list[index][1]==';',"Semicolon missing"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("</letStatement>\n")

def compileIf(token_list,outfile):
    global index
    assert token_list[index][1]=='if',"wrong keyword"
    outfile.write("<ifStatement>\n")
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1]=='(',"No opening bracket"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<expression>\n")
    compileExpression(token_list,outfile)
    outfile.write("</expression>\n")
    assert token_list[index][1]==')',"No closing bracket"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1]=='{',"No opening parantheses"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<statements>\n")
    compileStatements(token_list,outfile)
    outfile.write("</statements>\n")
    assert token_list[index][1]=='}',"No closing parantheses"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    if(token_list[index][1]=='else'):
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        assert token_list[index][1]=='{',"No opening parantheses"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        outfile.write("<statements>\n")
        compileStatements(token_list,outfile)
        outfile.write("</statements>\n")
        assert token_list[index][1]=='}',"No closing parantheses"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
    outfile.write("</ifStatement>\n")

def compileDo(token_list,outfile):
    global index
    assert token_list[index][1]=='do',"wrong keyword"
    outfile.write("<doStatement>\n")
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1    
    compilesubroutineCall(token_list,outfile)   
    assert token_list[index][1]==';',"Semicolon missing"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("</doStatement>\n")    

def compileWhile(token_list,outfile):
    global index
    assert token_list[index][1]=='while',"wrong keyword"
    outfile.write("<whileStatement>\n")
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1]=='(',"No opening bracket"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<expression>\n")
    compileExpression(token_list,outfile)
    outfile.write("</expression>\n")
    assert token_list[index][1]==')',"No closing bracket"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1]=='{',"No opening parantheses"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<statements>\n")
    compileStatements(token_list,outfile)
    outfile.write("</statements>\n")
    assert token_list[index][1]=='}',"No closing parantheses"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1    
    outfile.write("</whileStatement>\n")

def compileReturn(token_list,outfile):
    global index
    assert token_list[index][1]=='return',"wrong keyword"
    outfile.write("<returnStatement>\n")
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    if(token_list[index][1]!=';'):
        outfile.write("<expression>\n")
        compileExpression(token_list,outfile)
        outfile.write("</expression>\n")    
    assert token_list[index][1]==';',"Semicolon missing"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("</returnStatement>\n")

def compileStatements(token_list,outfile):
    global index
    while(token_list[index][1]!='}'):
        assert token_list[index][1] in statements,"illegal keyword"
        f[token_list[index][1]](token_list,outfile)

def compileparameterList(token_list,outfile):
    global index
    assert token_list[index][1] in types or token_list[index][0][1:-1]=='identifier',"Illegal type"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][0][1:-1]=='identifier',"No variable name"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    while(token_list[index][1]==','):
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        assert token_list[index][1] in types or token_list[index][0][1:-1]=='identifier',"Illegal type"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        assert token_list[index][0][1:-1]=='identifier',"No variable name"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1

def compilesubroutineBody(token_list,outfile):
    global index
    if(len(token_list)>index):
        while token_list[index][1]=='var':
            outfile.write("<varDec>\n")
            compilevarDec(token_list,outfile)
            outfile.write("</varDec>\n")
        outfile.write("<statements>\n")
        if(token_list[index][1]!='}'):
            compileStatements(token_list,outfile)
        outfile.write("</statements>\n")

def compilevarDec(token_list,outfile):
    global index
    assert token_list[index][1]=='var',"var expected."
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1] in types or token_list[index][0][1:-1]=='identifier',"Illegal type"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][0][1:-1]=='identifier',"No variable name"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    while(token_list[index][1]==','):
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1        
        assert token_list[index][0][1:-1]=='identifier',"No variable name"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
    assert token_list[index][1]==";","semicolon missing"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1

def compileClassVarDec(token_list,outfile):
    global index
    assert token_list[index][1]=='static' or token_list[index][1]=='field',"Illegal function declaration"    
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1] in types or token_list[index][0][1:-1]=='identifier',"Illegal type"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][0][1:-1]=='identifier',"No variable name"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    while(token_list[index][1]==','):
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
        assert token_list[index][0][1:-1]=='identifier',"No variable name"
        outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
        index+=1
    assert token_list[index][1]==";","semicolon missing"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1

def compilesubroutineDec(token_list,outfile):
    global index
    assert token_list[index][1] in function_types,"wrong function type"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1] in types or token_list[index][1]=='void' or token_list[index][0][1:-1]=='identifier',"Illegal return type"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][0][1:-1]=='identifier',"No function name"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    assert token_list[index][1]=='(',"No opening bracket"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<parameterList>\n")
    if token_list[index][1] in types or token_list[index][0][1:-1]=='identifier':
        compileparameterList(token_list,outfile)
    outfile.write("</parameterList>\n")
    assert token_list[index][1]==')',"No closing bracket"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("<subroutineBody>\n")
    assert token_list[index][1]=='{',"Missing parantheses"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    if token_list[index][1]!='}':
        compilesubroutineBody(token_list,outfile)    
    assert token_list[index][1]=='}',"Missing close parantheses"
    outfile.write(token_list[index][0]+" "+token_list[index][1]+" "+token_list[index][2]+"\n")
    index+=1
    outfile.write("</subroutineBody>\n")

def compileClass(token_list,outfile):
    if len(token_list) == 0: 
        return
    assert token_list[0][1]=='class',"File should start with a Class"
    assert token_list[2][1]=='{',"No open parantheses for Class"
    assert token_list[1][0][1:-1]=='identifier',"No Class Name"
    assert token_list[-1][1]=='}',"No close parantheses for Class"
    outfile.write("<class>\n")
    outfile.write(token_list[0][0]+" "+token_list[0][1]+" "+token_list[0][2]+"\n")
    outfile.write(token_list[1][0]+" "+token_list[1][1]+" "+token_list[1][2]+"\n")
    outfile.write(token_list[2][0]+" "+token_list[2][1]+" "+token_list[2][2]+"\n")
    #call others
    token_list=token_list[3:-1]
    global index
    index = 0
    if(len(token_list))>0:
        while (token_list[index][1]=='static' or token_list[index][1]=='field'):
            outfile.write("<classVarDec>\n")
            compileClassVarDec(token_list,outfile)
            outfile.write("</classVarDec>\n")
        if(len(token_list) > index):
            while len(token_list) > index and token_list[index][1] in function_types:
                outfile.write("<subroutineDec>\n")
                compilesubroutineDec(token_list,outfile)
                outfile.write("</subroutineDec>\n")       

    outfile.write(token_list[-1][0]+" "+token_list[-1][1]+" "+token_list[-1][2]+"\n")
    outfile.write("</class>\n")

    
def CompilationEngine(infile,outfile):
    token_list=[]
    for line in infile:
        line=line.split()
        if(len(line)>1):
            token_list.append(line)    
    if(len(token_list)>0):
        compileClass(token_list,outfile)

f = {"let" : compileLet,"if" : compileIf,"do" : compileDo,"while" : compileWhile, "return" : compileReturn}
    
def main():
    arg = sys.argv[1]
    global fileName    
    glob_path = Path(arg)
    file_list = [str(pp) for pp in glob_path.glob("**/*.jack")]    
    for file in file_list:
        fileName=os.path.basename(file)[:-5]
        infile=open(file)
        outfile0 = open(arg+"/"+fileName+ "T.xml", "w")
        outfile1 = open(arg +"/"+fileName+ ".xml", "w")
        outfile0.write("<tokens>\n")
        JackTokenizer(infile.read(),outfile0)
        outfile0.write("</tokens>")
        outfile0.close()
        outfile0=open(arg+"/"+fileName+ "T.xml")   
        CompilationEngine(outfile0,outfile1)
   
if __name__=="__main__":
    main()