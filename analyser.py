from dataStruct import const
from dataStruct import reservers
from dataStruct import V
from dataStruct import VT
from dataStruct import VN
from dataStruct import InstructionStream
from dataStruct import Instruction
from dataStruct import SymbolTable
from dataStruct import Error
from dataStruct import tableitem
from dataStruct import func
class analyser:
    def __init__(self,file, start, end, symbolTable, instructionStream):
        self.file = file
        self.start = start
        self.end = end
        self.pointer = self.start
        self.errors = []
        self.program = None
        self.symbolTable = symbolTable
        self.instructionStream = instructionStream
        self.level = 0 # 作用域level

    def emit(self, instruction):
        if not instruction:
            return
        assert isinstance(instruction,Instruction)
        self.instructionStream.append(instruction)
    # 为overlookSet添加一个元素
    def overlookSetAdd(self, overlookSet, item):
        if not item in overlookSet:
            overlookSet.append(item)
        return overlookSet
    # 跳过单词直到下一个指定符号集,取出的单词是指定符号集中任意符号
    def overlookToMarks(self, marks):
        while True:
            for mark in marks:
                if self.pointer.isType(mark) or self.isEnd():
                    return
            self.getsym()
    # 判断给定Vn是否是空节点，如果子节点为0，则返回空节点
    def checkEmpty(self, Vn):
        if len(Vn.children) == 0 :
            Vn.vtype = const.EMPTY
        return Vn
    # 获取下一个单词，即Vt
    def getsym(self):
        if not self.isEnd():
            self.pointer = self.pointer.next
        else :
            print("to End！\n")
    # 判断语法分析是否结束
    def isEnd(self):
        return self.pointer.isEOF()
    def hasError(self):
        return len(self.errors) > 0
    # 退格，还原上一个单词的状态
    def retrace(self):
        self.pointer = self.pointer.previous
    # 设置sym状态为指定状态
    def setsymat(self, pointer):
        self.pointer = pointer
    def scan(self):
        # 进入程序是当前单词已经是链表的第一个单词
        self.program = self.C0_program()
        return self.program
    # 检查作用域
    def checkexist(self,text,level):
        varexist = self.symbolTable.getVar(text)
        funcexistnum = self.symbolTable.getFunc(text)
        if funcexistnum == None:
            funcexist = None
        else:
            funcexist = self.symbolTable.funcs[funcexistnum]
        if ((not varexist == None and varexist.level < level) or varexist == None) and ((not funcexist == None and funcexist.level-1 < level) or funcexist == None):
            return True
        else:
            return False
    # 查询break和continue地址
    def find_bnc(self,start):
        flag1 = False
        flag2 = False
        for index1 in range(len(self.instructionStream.instructions)-1,start,-1):
            if self.instructionStream.instructions[index1].instruction == Instruction.loop_break:
                flag1 = True
                break
        for index2 in range(len(self.instructionStream.instructions)-1,start,-1):
            if self.instructionStream.instructions[index2].instruction == Instruction.loop_continue:
                flag2 = True
                break
        if flag1 == False and flag2 == False:
            return None,None
        elif flag1 == True and flag2 == False:
            return index1,None
        elif flag1 == False and flag2 == True:
            return None,index2
        else:
            return index1,index2

    # <C0-program> ::= {<variable-declaration>}{<function-definition>}
    def C0_program(self):
        overlookSet = [const.CONST, const.INT, const.VOID,const.DOUBLE]
        V_program = VN.create(const.C0PROGRAM,self.level)
        flag = 0
        # {<variable-declaration>}
        while True:
            # 如果是const，<常量分析>
            if self.pointer.isR_Const():
                V_program.append(self.const_declaration(overlookSet))
            # void 直接进void
            elif self.pointer.isR_Void() or self.pointer.isR_Int() or self.pointer.isR_Double():
                tempPointer = self.pointer
                self.getsym()
                if self.pointer.isID():
                    if self.pointer.text == "main":
                        flag = 1
                    self.getsym()
                    # 如果是左括号,那就是函数定义了，其它情况都交给变量定义来做
                    if self.pointer.isL_Parenthesis():
                        self.setsymat(tempPointer)
                        break
                    else:
                        self.setsymat(tempPointer)
                        V_program.append(self.variable_declaration(overlookSet))
                        flag = 0
            elif self.isEnd():
                break
            else :
                self.error(Error.AN_ILLEGAL_INPUT,self.pointer,msg="input should be var-dec or func-dec")
                self.overlookToMarks(overlookSet)
        # {<function-definition>}
        while True:
            tempPointer = self.pointer
            # int or double只能是变量定义 或 函数
            if self.pointer.isR_Int() or self.pointer.isR_Double() or self.pointer.isR_Void():
                self.getsym()
                if self.pointer.isID():
                    if self.pointer.text == "main":
                        flag = 1
                    self.getsym()
                    # 如果是左括号,那就是函数定义了，其它情况都交给变量定义来做
                    if self.pointer.isL_Parenthesis():
                        self.setsymat(tempPointer)
                        self.level += 1
                        #记录局部变量个数
                        varnum = len(self.symbolTable.var)
                        V_program.append(self.function_definition(overlookSet))
                        self.level -= 1
                        #删除局部变量
                        self.symbolTable.var = self.symbolTable.var[:varnum]
                    else:
                        self.error(Error.AN_MISS_L_PARENTHESIS,self.pointer.previous)
                        self.overlookToMarks(overlookSet)
                else :
                    self.error(Error.AN_ILLEGAL_INPUT,self.pointer.previous,msg="missing identifier")
                    self.overlookToMarks(overlookSet)
            # 因为文件终结符而结束
            elif self.isEnd():
                index1,index2 = self.find_bnc(-1)
                if not(index1 == None and index2 == None):
                    self.error(Error.AN_ILLEGAL_INPUT,self.pointer,msg="break or continue can only use in loop")
                break
            # 什么都识别不出来，只有报错跳过了
            else:
                self.error(Error.AN_ILLEGAL_INPUT,self.pointer)
                self.overlookToMarks([const.DOUBLE,const.INT,const.VOID])
        if not flag == 1:
            self.error(Error.AN_MISS_MAIN_FUNCTION,self.pointer.previous)
        return V_program

    #<const-declaration> ::= <const-qualifier><type-specifier><init-declarator-list>';'
    #<init-declarator-list> ::= <init-declarator>{','<init-declarator>}
    # type : int -> 0 , double -> 1
    def const_declaration(self, overlookSet=None):
        var_type = 0
        if overlookSet is None:
            overlookSet = [const.CONST, const.INT, const.VOID]
        downoverlookSet = overlookSet[:]
        self.overlookSetAdd(downoverlookSet, const.SEMICOLON)
        V_const_declaration = VN.create(const.CON_DEC,self.level)
        # 此处为第一个常量定义处理，如果只有空const,报错！
        # 进入函数的时候已经检验了存在 const标识符,不用重复检查
        V_const_declaration.append(self.pointer)
        self.getsym()
        if self.pointer.isR_Double():
            var_type = 1
            V_const_declaration.append(self.pointer)
        elif self.pointer.isR_Int():
            var_type = 0 
            V_const_declaration.append(self.pointer)
        else:
            self.error(Error.AN_ILLEGAL_INPUT,self.pointer.previous,msg = "type should be int or double")
            self.overlookToMarks(overlookSet)
        self.getsym()
        init_dec,init_type = self.init_declarator(downoverlookSet,flag=1,type = var_type)
        V_const_declaration.append(init_dec)
        while(self.pointer.isComma()):
            comma = self.pointer
            self.getsym()
            init_dec,init_type = self.init_declarator(downoverlookSet,flag=1,type = var_type)
            V_const_declaration.append(comma).append(init_dec)
        #如果读到分号，结束返回,记得多读一个！
        if self.pointer.isSemicolon():
            V_const_declaration.append(self.pointer)
            self.getsym()
        else:
            # 如果没有分号，报错！但是别多读一个了
            # 已经读的仍然保留
            self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        # 防止只有 const 保留字和/或 ; 被读入了
        if not V_const_declaration.hasVn():
            V_const_declaration.empty()
        return self.checkEmpty(V_const_declaration)

    #<variable-declaration> ::= <type-specifier><init-declarator-list>';'
    def variable_declaration(self, overlookSet=None):
        var_type = 0
        if overlookSet is None:
            overlookSet = [const.CONST, const.INT, const.VOID]
        downoverlookSet = overlookSet[:]
        self.overlookSetAdd(downoverlookSet, const.SEMICOLON)
        V_variable_declaration = VN.create(const.VAR_DEC,self.level)
        if self.pointer.isR_Double():
            var_type = 1
        elif self.pointer.isR_Int():
            var_type = 0
        else:
            self.error(Error.AN_ILLEGAL_INPUT,self.pointer.previous,msg = "type should be int or double")
            self.overlookToMarks(overlookSet)
        V_variable_declaration.append(self.pointer)
        self.getsym()
        init_dec,init_type = self.init_declarator(downoverlookSet,flag = 0,type = var_type)
        V_variable_declaration.append(init_dec)
        while(self.pointer.isComma()):
            comma = self.pointer
            self.getsym()
            V_variable_declaration.append(comma)
            init_dec,init_type = self.init_declarator(downoverlookSet,flag = 0,type = var_type)
            V_variable_declaration.append(init_dec)
        #如果读到分号，结束返回,记得多读一个！
        if self.pointer.isSemicolon():
            V_variable_declaration.append(self.pointer)
            self.getsym()
        else:
            # 如果没有分号，报错！但是别多读一个了
            # 已经读的仍然保留
            self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        if not V_variable_declaration.hasVn():
            V_variable_declaration.empty()
        return self.checkEmpty(V_variable_declaration)

    # <init-declarator> ::= <identifier>[<initializer>]
    def init_declarator(self,overlookSet = [const.SEMICOLON, const.ID, const.CONST, const.INT, const.VOID],flag = 1,type = 0):
        init_type =""
        V_init_declarator = VN.create(const.INIT_DEC,self.level)
        if self.pointer.isID():
            V_init_declarator.append(self.pointer)
            self.pointer.level = self.level
            if self.checkexist(self.pointer.text,self.level) == True:
                if flag == 1:
                    if type == 1:
                        self.symbolTable.var.append(tableitem("double",self.pointer.text,self.pointer.level,self.symbolTable.offset[self.pointer.level],flag))
                        self.symbolTable.offset[self.pointer.level] += 2
                    elif type == 0:
                        self.symbolTable.var.append(tableitem("int",self.pointer.text,self.pointer.level,self.symbolTable.offset[self.pointer.level],flag))
                        self.symbolTable.offset[self.pointer.level] += 1
                else:
                    if type == 1:
                        self.symbolTable.var.append(tableitem("double",self.pointer.text,self.pointer.level,self.symbolTable.offset[self.pointer.level],flag))
                        self.symbolTable.offset[self.pointer.level] += 2
                    elif type == 0:
                        self.symbolTable.var.append(tableitem("int",self.pointer.text,self.pointer.level,self.symbolTable.offset[self.pointer.level],flag))
                        self.symbolTable.offset[self.pointer.level] += 1
                var = self.symbolTable.getVar(self.pointer.text)
                self.getsym()
                # 去符号表中找这个ID，找不到记得报错
                if self.pointer.isAssign():
                    if type == 1:
                        self.emit(Instruction(Instruction.snew,2))
                    else:
                        self.emit(Instruction(Instruction.snew,1))
                    if var.level == 0 and self.level != var.level:
                        self.emit(Instruction(Instruction.loada, 1, var.offset))
                    else:
                        self.emit(Instruction(Instruction.loada, 0, var.offset))
                    init,init_type = self.initializer(overlookSet)
                    V_init_declarator.append(init)
                    if type == 1 and not init_type == "double":
                        self.emit(Instruction(Instruction.i2d))
                        self.emit(Instruction(Instruction.dstore))
                    elif type == 0 and init_type == "double":
                        self.emit(Instruction(Instruction.d2i))
                        self.emit(Instruction(Instruction.istore))
                    elif type == 0 and init_type == "int":
                        self.emit(Instruction(Instruction.istore))
                    elif type == 1 and init_type == "double":
                        self.emit(Instruction(Instruction.dstore))
                else :
                    if flag == 1 :
                        self.error(Error.AN_MISS_ASSIGN, self.pointer.previous, "Gramma Analysis Error: A \'=\'  is expected in const variables\' defination  .")
                        self.overlookToMarks(overlookSet)
                        V_init_declarator.empty()
                    else:
                        if type == 1:
                            self.emit(Instruction(Instruction.snew,2))
                        else:
                            self.emit(Instruction(Instruction.snew,1))
            else:
                self.error(Error.AN_ILLEGAL_INPUT,self.pointer,"can not define the var or const with used name")
                self.overlookToMarks(overlookSet)
                V_init_declarator.empty()
        else :
            self.error(Error.AN_MISS_IDENTIFIER,self.pointer.previous)
            self.overlookToMarks(overlookSet)
            V_init_declarator.empty()
        return V_init_declarator,init_type

    # <initializer> ::= '='<expression> 
    def initializer(self, overlookSet = [const.ASSIGN]):
        V_initializer = VN.create(const.INIT,self.level)
        #读入等于
        V_initializer.append(self.pointer)
        self.getsym()
        init,init_type = self.expression(overlookSet)
        V_initializer.append(init)
        return V_initializer,init_type

    # <expression> ::= <additive-expression>::= 
    # <multiplicative-expression>{<additive-operator><multiplicative-expression>}
    def expression(self,overlookset):
        exp_type = ""
        V_expression = VN.create(const.EXP,self.level)
        mul,exp_type = self.multiplicative_expression(overlookset)
        V_expression.append(mul)
        while self.pointer.isAdditiveOperator():
            sign = self.pointer
            V_expression.append(sign)
            # 加一个方便定位的指令 后面要删去
            self.emit(Instruction(Instruction.nop))
            self.getsym()
            tmp_mul,tmp_exp_type = self.multiplicative_expression(overlookset)
            for index in range(len(self.instructionStream.instructions)-1,-1,-1):
                if self.instructionStream.instructions[index].instruction == Instruction.nop:
                    break
            if tmp_exp_type == "double" and exp_type == "int":
                self.instructionStream.instructions[index] = Instruction(Instruction.i2d)
                if sign.vtype == const.PLUS:
                    self.emit(Instruction(Instruction.dadd))
                elif sign.vtype == const.MINUS:
                    self.emit(Instruction(Instruction.dsub))
                exp_type = "double"
            elif tmp_exp_type == "int" and exp_type == "double":
                del self.instructionStream.instructions[index]
                self.emit(Instruction(Instruction.i2d))
                if sign.vtype == const.PLUS:
                    self.emit(Instruction(Instruction.dadd))
                elif sign.vtype == const.MINUS:
                    self.emit(Instruction(Instruction.dsub))
                exp_type = "double"
            elif tmp_exp_type == "int" and exp_type == "int":
                del self.instructionStream.instructions[index]
                if sign.vtype == const.PLUS:
                    self.emit(Instruction(Instruction.iadd))
                elif sign.vtype == const.MINUS:
                    self.emit(Instruction(Instruction.isub))
                exp_type = "int"
            elif tmp_exp_type == "double" and exp_type == "double":  
                del self.instructionStream.instructions[index]
                if sign.vtype == const.PLUS:
                    self.emit(Instruction(Instruction.dadd))
                elif sign.vtype == const.MINUS:
                    self.emit(Instruction(Instruction.dsub))
                exp_type = "double"
            V_expression.append(tmp_mul)
            
        return self.checkEmpty(V_expression),exp_type

    # <multiplicative-expression> ::= 
    # <cast-expression>{<multiplicative-operator><cast-expression>}
    def multiplicative_expression(self,overlookset):
        exp_type = ""
        V_multiplicative_expression = VN.create(const.MUL_EXP,self.level)
        cast,exp_type = self.cast_expression(overlookset)
        V_multiplicative_expression.append(cast)
        while self.pointer.isMultiplicativeOperator():
            sign = self.pointer
            V_multiplicative_expression.append(sign)
             # 加一个方便定位的指令 后面要删去
            self.emit(Instruction(Instruction.nop))
            self.getsym()
            tmp_cast,tmp_exp_type = self.cast_expression(overlookset)
            for index in range(len(self.instructionStream.instructions)-1,-1,-1):
                if self.instructionStream.instructions[index].instruction == Instruction.nop:
                    break
            if tmp_exp_type == "double" and exp_type == "int":
                self.instructionStream.instructions[index] = Instruction(Instruction.i2d)
                if sign.vtype == const.SLASH:
                    self.emit(Instruction(Instruction.ddiv))
                elif sign.vtype == const.STAR:
                    self.emit(Instruction(Instruction.dmul))
                exp_type = "double"
            elif tmp_exp_type == "int" and exp_type == "double":
                del self.instructionStream.instructions[index]
                self.emit(Instruction(Instruction.i2d))
                if sign.vtype == const.SLASH:
                    self.emit(Instruction(Instruction.ddiv))
                elif sign.vtype == const.STAR:
                    self.emit(Instruction(Instruction.dmul))
                exp_type = "double"
            elif tmp_exp_type == "int" and exp_type == "int":
                del self.instructionStream.instructions[index]
                if sign.vtype == const.SLASH:
                    self.emit(Instruction(Instruction.idiv))
                elif sign.vtype == const.STAR:
                    self.emit(Instruction(Instruction.imul))
                exp_type = "int"
            elif tmp_exp_type == "double" and exp_type == "double":  
                del self.instructionStream.instructions[index]
                if sign.vtype == const.SLASH:
                    self.emit(Instruction(Instruction.ddiv))
                elif sign.vtype == const.STAR:
                    self.emit(Instruction(Instruction.dmul))
                exp_type = "double"
            V_multiplicative_expression.append(tmp_cast)
        return self.checkEmpty(V_multiplicative_expression),exp_type
            
    
    # <cast-expression> ::=
    # {'('<type-specifier>')'}<unary-expression>
    def cast_expression(self,overlookset):
        exp_type = ""
        sign = ""
        V_cast_expression = VN.create(const.CAST_EXP,self.level)
        if self.pointer.isL_Parenthesis():
            l = self.pointer
            self.getsym()
            if self.pointer.isR_Int():
                sign = "int"
            elif self.pointer.isR_Double():
                sign = "double"
            elif self.pointer.isR_Void():
                self.error(Error.AN_ILLEGAL_TYPE,self.pointer,msg="cast can not be void ")
                self.overlookToMarks(overlookset)
            else: #否则就说明没有cast，直接进unary-expression
                self.pointer = l
        #sign有东西就存
        if not sign == "":
            m = self.pointer
            self.getsym()
            if not self.pointer.isR_Parenthesis():
                self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(overlookset)
            else:
                V_cast_expression.append(l)            #左括号
                V_cast_expression.append(m)            #类型
                V_cast_expression.append(self.pointer) #右括号
                self.getsym()
        unary,exp_type = self.unary_expression(overlookset)
        V_cast_expression.append(unary)
        #sign有东西就转换
        if sign == "double" and exp_type == "int":
            self.emit(Instruction(Instruction.i2d))
        elif sign == "int" and exp_type == "double":
            self.emit(Instruction(Instruction.d2i))
        return self.checkEmpty(V_cast_expression),exp_type

    # <unary-expression> ::=
    # [<unary-operator>]<primary-expression>
    def unary_expression(self,overlookset):
        exp_type = ""
        V_unary_expression = VN.create(const.UNARY_EXP,self.level)
        sign = False
        if self.pointer.isAdditiveOperator():
            sign = self.pointer
            V_unary_expression.append(sign)
            self.getsym()
        prim,exp_type = self.primary_expression(overlookset)
        V_unary_expression.append(prim)
        if not sign == False and sign.vtype == const.MINUS:
            self.emit(Instruction(Instruction.ineg))
        return self.checkEmpty(V_unary_expression),exp_type
        
    # <primary-expression> ::= '('<expression>')' 
    # |<identifier>
    # |<integer-literal>
    # |<char-literal>
    # |<floating-literal>
    # |<function-call>
    def primary_expression(self,overlookset):
        exp_type =""
        downOverlookSet = overlookset[:]
        self.overlookSetAdd(downOverlookSet,const.R_PARENTHESIS)
        V_primary_expression = VN.create(const.PRIM_EXP,self.level)
        # 进入后先判断是哪种因子
        # 如果是ID，则可能是标识符或者调用函数
        if self.pointer.isID() and (not self.pointer.next.isL_Parenthesis()):
            var = self.symbolTable.getVar(self.pointer.text)
            # 去符号表中找这个ID，找不到记得报错
            if var:
                V_primary_expression.append(self.pointer)
                # 判断diff_level
                if var.level == 0 and self.level != var.level:
                    self.emit(Instruction(Instruction.loada, 1, var.offset))
                else:
                    self.emit(Instruction(Instruction.loada, 0, var.offset))

                if var.type == "double":
                    self.emit(Instruction(Instruction.dload))
                elif var.type == "int":
                    self.emit(Instruction(Instruction.iload))
                else:
                    self.error(Error.AN_ILLEGAL_TYPE, self.pointer,msg = "can not load void var")
                    self.overlookToMarks(overlookset)
                self.getsym()
                exp_type = var.type
            else:
                self.error(Error.ST_UNDEFINED_ID, self.pointer)
                self.overlookToMarks(overlookset)
        #函数调用
        elif self.pointer.isID() and self.pointer.next.isL_Parenthesis():
            funcnum = self.symbolTable.getFunc(self.pointer.text)
            if not funcnum == None:
                func = self.symbolTable.funcs[funcnum]
                if func.returntype == "VOID": #void型
                    self.error(Error.ST_UNDEFINED_ID, self.pointer,msg="can not call a void function")
                    self.overlookToMarks(overlookset)
                else:
                    V_primary_expression.append(self.function_call(overlookset))
                    if func.returntype == "INT":
                        exp_type = "int"
                    else:
                        exp_type = "double"
            else:
                self.error(Error.ST_UNDEFINED_ID, self.pointer,msg="can not call this func")
                self.overlookToMarks(overlookset)
        # 处理表达式
        elif self.pointer.isL_Parenthesis():
            l_parenthesis = self.pointer
            self.getsym()
            # 接着要进行进入表达式解析
            expression,exp_type = self.expression(downOverlookSet)
            if self.pointer.isR_Parenthesis():
                V_primary_expression.append(l_parenthesis).append(expression).append(self.pointer)
                self.getsym()
            else:
                self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(overlookset)
        # 处理整型字面量
        elif self.pointer.isInteger() or self.pointer.isHex():
            V_primary_expression.append(self.pointer)
            # 直接加到符号表
            if not self.symbolTable.isunique(self.pointer.text) :
                self.symbolTable.constant.append(tableitem('I',self.pointer.text,V_primary_expression.level,0,0))
            # 因为上面加了，所以全是loadc就行
            self.emit(Instruction(Instruction.loadc, self.symbolTable.getConstant_by_value(self.pointer.text)))
            exp_type = "int"
            self.getsym()
        # 处理浮点型字面量
        elif self.pointer.isDouble():
            V_primary_expression.append(self.pointer)
            if not self.symbolTable.isunique(self.pointer.text):
                self.symbolTable.constant.append(tableitem('D',self.pointer.text,V_primary_expression.level,0,0))
            self.emit(Instruction(Instruction.loadc, self.symbolTable.getConstant_by_value(self.pointer.text)))
            exp_type = "double"
            self.getsym()
        else:
            self.error(Error.AN_ILLEGAL_INPUT, self.pointer.previous, "Gramma Analysis Error: An expression, (exp), or integer or double or func or id is expeted")
            self.overlookToMarks(overlookset)
        return self.checkEmpty(V_primary_expression),exp_type

    # <function-call> ::= 
    # <identifier> '(' [<expression-list>] ')'
    def function_call(self,overlookset = [const.R_BRACE]):
        downOverlookSet = overlookset[:]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        V_function_call = VN.create(const.FUNC_CALL,self.level)
        func_pointer = self.pointer
        V_function_call.append(func_pointer)
        funcnum = self.symbolTable.getFunc(func_pointer.text)
        if funcnum == None or not self.symbolTable.getVar(self.pointer.text) == None:
            self.error(Error.ST_UNDEFINED_ID, self.pointer,msg="can not find this func")
            self.overlookToMarks(overlookset)
        self.getsym()
        if self.pointer.isL_Parenthesis():
            V_function_call.append(self.pointer)
            self.getsym()
            # 下一个如果不是右括号，才进入参数表分析
            if not self.pointer.isR_Parenthesis():
                paraValue = self.expression_list(downOverlookSet)
                V_function_call.append(paraValue)
            else:
                for func in self.symbolTable.funcs:
                    if func.name == func_pointer.text:
                        break
                if len(func.para) > 0:
                    self.error(Error.AN_ILLEGAL_INPUT,self.pointer.previous,msg="func should have some para")
                    self.overlookToMarks(overlookset)
            if self.pointer.isR_Parenthesis():
                V_function_call.append(self.pointer)
                self.getsym()
                self.emit(Instruction(Instruction.call,self.symbolTable.getFunc(func_pointer.text)))
            else:
                self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(overlookset)
        else:
            self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks(overlookset)
        return V_function_call 

    # <expression-list> ::= 
    # <expression>{','<expression>}
    def expression_list(self, overlookSet = [const.R_PARENTHESIS]):
        num = 0
        downOverlookSet = overlookSet[:]
        # id为函数名字
        id = self.pointer.previous.previous
        self.overlookSetAdd(downOverlookSet, const.COMMA)
        V_expression_list = VN.create(const.EXP_LIST,self.level)
        exp,exp_type = self.expression(downOverlookSet)
        # 找到符号表中的函数item
        for func in self.symbolTable.funcs:
            if func.name == id.text:
                break
        if len(func.para) > 0:
            if func.para[num] == "int" and exp_type == "double":
                self.emit(Instruction(Instruction.d2i))
                num += 1
            elif func.para[num] == "double" and exp_type == "int":
                self.emit(Instruction(Instruction.i2d))
                num += 1
            else:
                num += 1
        # 如果没有参数报错
        else:
            self.error(Error.AN_ILLEGAL_INPUT, id.next,msg="func don't have so much para")
            self.overlookToMarks(overlookSet)
        V_expression_list.append(exp)
        while self.pointer.isComma():
            V_expression_list.append(self.pointer)
            self.getsym()
            exp,exp_type = self.expression(downOverlookSet)
            if num < len(func.para):
                if func.para[num] == "int" and exp_type == "double":
                    self.emit(Instruction(Instruction.d2i))
                    num += 1
                elif func.para[num] == "double" and exp_type == "int":
                    self.emit(Instruction(Instruction.i2d))
                    num += 1
                else:
                    num += 1
                V_expression_list.append(exp)
            else:
                self.error(Error.AN_ILLEGAL_INPUT, id.next,msg="func don't have so much para")
                self.overlookToMarks(overlookSet)

        return self.checkEmpty(V_expression_list)

    # <function-definition> ::= 
    # <type-specifier><identifier><parameter-clause><compound-statement>

    def function_definition(self, overlookSet = [const.CONST, const.INT, const.VOID]):
        self.symbolTable.offset[self.level] = 0
        if self.pointer.next and self.pointer.next.text == "main":
            V_function_definition = VN.create(const.MAIN_FUNC,self.level)
        else: 
            V_function_definition = VN.create(const.FUNC_DEF,self.level)
        if self.pointer.isR_Int() or self.pointer.isR_Double():
            V_function_definition.append(self.pointer)
            self.getsym()
            if(self.pointer.isID()):
                V_function_definition.append(self.pointer)
                self.pointer.level = self.level
                id = self.pointer
                if not self.symbolTable.getConstant_by_value(id.text) == None or not self.symbolTable.getVar(id.text) == None:
                    self.error(Error.AN_ILLEGAL_INPUT, id,msg="can not define the function with used name")
                    self.overlookToMarks(overlookSet)
                else:
                    self.symbolTable.constant.append(tableitem('S',self.pointer.text,self.pointer.level,0,0))
                self.getsym()
            else:
                self.error(Error.AN_MISS_IDENTIFIER, self.pointer.previous)
                self.overlookToMarks(overlookSet)
            id = V_function_definition.findChild(const.ID)
        # 不是int，那就是void型咯！
        elif self.pointer.isR_Void():
            void = self.pointer
            self.getsym()
            # 还需要再来一个标识符!
            if self.pointer.isID() or self.pointer.isR_Main():
                V_function_definition.append(void)
                self.pointer.level = self.level
                id = self.pointer
                if not self.symbolTable.getConstant_by_value(id.text) == None or not self.symbolTable.getVar(id.text) == None:
                    self.error(Error.AN_ILLEGAL_INPUT, id,msg="can not define the function with used name")
                    self.overlookToMarks(overlookSet)
                else:
                    self.symbolTable.constant.append(tableitem('S',self.pointer.text,self.pointer.level,0,0))
                V_function_definition.append(self.pointer)
                self.getsym()
            # 标识符都没有，直接回上层
            else:
                self.error(Error.AN_MISS_IDENTIFIER, self.pointer.previous)
                self.overlookToMarks(overlookSet)
                return V_function_definition.empty()
        # 都不是，那就报"不认识"
        else:
            self.error(Error.AN_ILLEGAL_TYPE, self.pointer,msg="invalid function type")
            self.overlookToMarks(overlookSet)
            return V_function_definition.empty()
        
        # 接着是参数解析
        # 参数解析前加上函数名的 lab 标识，表示函数入口！
        self.instructionStream.setLab(id.text)
        if self.pointer.isL_Parenthesis():
            V_function_definition.append(self.parameter_clause())
        else:
            self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks([const.L_BRACE])
        # 头部定义结束，run一次
        self.run_functionDefine(V_function_definition)
        # 然后是复合语句解析
        if self.pointer.isL_Brace():
            V_function_definition.append(self.compound_statement())
        else:
            self.error(Error.AN_MISS_L_BRACE, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        self.run_functionDefineEnd(V_function_definition)
        return V_function_definition

    # <parameter-clause> ::= 
    # '(' [<parameter-declaration-list>] ')'
    def parameter_clause(self, lookoverSet = [const.L_BRACE]):
        downLookoverSet = lookoverSet[:]
        self.overlookSetAdd(downLookoverSet, const.R_PARENTHESIS)
        #进入时已经确认是(了，直接添加！
        V_parameter_clause = VN.create(const.PARA_CLA,self.level)
        V_parameter_clause.append(self.pointer)
        self.getsym()
        # 判断参数表是否为空,不为空则进入参数表解析
        if not self.pointer.isR_Parenthesis():
            # 添加参数表函数解析结果
            V_parameter_clause.append(self.parameter_declaration_list())
        if self.pointer.isR_Parenthesis():
            V_parameter_clause.append(self.pointer)
            self.getsym()
        else:
            self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks(lookoverSet)
        return self.checkEmpty(V_parameter_clause)

    # <parameter-declaration-list> ::= 
    # <parameter-declaration>{','<parameter-declaration>}
    def parameter_declaration_list(self, overlookSet = [const.R_PARENTHESIS]):
        V_parameter_declaration_list = VN.create(const.PARA_DEC_LIST,self.level)
        parameterNum = 0
        dec = self.parameter_declaration(overlookSet)
        if not dec.vtype == const.EMPTY :
            V_parameter_declaration_list.append(dec)
            parameterNum += 1
        while self.pointer.isComma():
            comma = self.pointer
            self.getsym() 
            dec = self.parameter_declaration(overlookSet)
            if not dec.vtype == const.EMPTY:
                V_parameter_declaration_list.append(comma)
                V_parameter_declaration_list.append(dec)
                parameterNum += 1
        if parameterNum == 0:
            V_parameter_declaration_list.empty()
        return self.checkEmpty(V_parameter_declaration_list)

    # <parameter-declaration> ::= 
    # [<const-qualifier>]<type-specifier><identifier>
    def parameter_declaration(self, overlookSet = [const.R_PARENTHESIS]):
        flag = 0
        V_parameter_declaration = VN.create(const.PARA_DEC,self.level)
        if self.pointer.isR_Const():
            V_parameter_declaration.append(self.pointer)
            self.getsym()
            flag == 1
        if self.pointer.isR_Int() or self.pointer.isR_Double():
            var_type = self.pointer
            V_parameter_declaration.append(self.pointer)
            self.getsym()
            if self.pointer.isID():
                V_parameter_declaration.append(self.pointer)
                self.pointer.level = self.level
                if var_type.isR_Double():
                    self.symbolTable.var.append(tableitem("double",self.pointer.text,self.pointer.level,self.symbolTable.offset[self.pointer.level],flag))
                    #funcitem.para.append("double")
                    self.symbolTable.offset[self.pointer.level] += 2
                else:
                    self.symbolTable.var.append(tableitem("int",self.pointer.text,self.pointer.level,self.symbolTable.offset[self.pointer.level],flag))
                    #funcitem.para.append("int")
                    self.symbolTable.offset[self.pointer.level] += 1
                self.getsym()
                return V_parameter_declaration
            else:
                self.error(Error.AN_MISS_IDENTIFIER, self.pointer,'Gramma Analysis Error: A identifier is expected after variables\' type.')
                self.overlookToMarks(overlookSet)
                return V_parameter_declaration.empty()
        else:
            self.error(Error.AN_ILLEGAL_TYPE, self.pointer,'Gramma Analysis Error: Type of parameter should not be \"const void\" or \"void\"')
            self.overlookToMarks(overlookSet)
        return V_parameter_declaration.empty()

    # <compound-statement> ::= 
    # '{' {<variable-declaration>} <statement-seq> '}'
    def compound_statement(self, overlookSet = [const.INT, const.CONST, const.ID]):
        downOverlookSet = [const.R_BRACE]
        selfOverlookSet = [const.R_BRACE]
        self.overlookSetAdd(downOverlookSet, const.R_BRACE)
        self.overlookSetAdd(downOverlookSet, const.INT)     # <variable-declaration>
        self.overlookSetAdd(downOverlookSet, const.CONST)   # <const-declaration> 
        self.overlookSetAdd(downOverlookSet, const.IF)      # <condition-statement>
        self.overlookSetAdd(downOverlookSet, const.WHILE)   # <loop1-statement>
        self.overlookSetAdd(downOverlookSet, const.RETURN)  # <return-statement>
        self.overlookSetAdd(downOverlookSet, const.L_BRACE) # <compound-statement>
        self.overlookSetAdd(downOverlookSet, const.SCAN)    # <scan-statement>
        self.overlookSetAdd(downOverlookSet, const.PRINT)   # <print-statement>
        self.overlookSetAdd(downOverlookSet, const.DO)      # <loop2-statement>
        self.overlookSetAdd(downOverlookSet, const.BREAK)   # <break-statement>
        self.overlookSetAdd(downOverlookSet, const.CONTINUE)# <continue-statement>

        # 进入则表示已经识别{,直接添加
        V_compound_statement = VN.create(const.COM_STATE,self.level)
        V_compound_statement.append(self.pointer)
        self.getsym()
        # 没有到函数末尾的}时，一直循环
        while not self.pointer.isR_Brace():
            # 如果读到Const,则是常量说明，
            if self.pointer.isR_Const():
                V_compound_statement.append(self.const_declaration(downOverlookSet))
            # 读到int，则是变量说明
            elif self.pointer.isR_Int() or self.pointer.isR_Double():
                V_compound_statement.append(self.variable_declaration(downOverlookSet))
            elif self.pointer.isR_Void():
                self.error(Error.AN_ILLEGAL_TYPE, self.pointer,'Gramma Analysis Error: Type of parameter should not be \"const void\" or \"void\"')
                self.overlookToMarks([const.SEMICOLON])
                self.getsym()
            else:
                break
        if self.pointer.isID() or self.pointer.isL_Brace() \
            or self.pointer.isR_If() or self.pointer.isR_While() or self.pointer.isR_Continue()\
            or self.pointer.isR_Return() or self.pointer.isR_Print() or self.pointer.isR_Break()\
            or self.pointer.isR_Scan() or self.pointer.isSemicolon() or self.pointer.isR_Do():
            V_compound_statement.append(self.statement_seq(downOverlookSet))
        else:
            self.error(Error.AN_ILLEGAL_INPUT, self.pointer.previous,msg="missing statement-seq")
            self.overlookToMarks(selfOverlookSet)
        # 复合语句的最后，因该是一个}，无则报错
        if self.pointer.isR_Brace():
            V_compound_statement.append(self.pointer)
            self.getsym()
        else:
            self.error(Error.AN_MISS_R_BRACE, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        return V_compound_statement

    # <statement-seq> ::= 
	# {<statement>}
    def statement_seq(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = overlookSet[:]
        self.overlookSetAdd(downOverlookSet, const.IF) #条件语句
        self.overlookSetAdd(downOverlookSet, const.WHILE) #循环语句
        self.overlookSetAdd(downOverlookSet, const.RETURN) #返回语句
        self.overlookSetAdd(downOverlookSet, const.L_BRACE) #语句序列
        self.overlookSetAdd(downOverlookSet, const.SCAN)
        self.overlookSetAdd(downOverlookSet, const.PRINT)
        self.overlookSetAdd(downOverlookSet, const.DO)      # <loop2-statement>
        self.overlookSetAdd(downOverlookSet, const.BREAK)   # <break-statement>
        self.overlookSetAdd(downOverlookSet, const.CONTINUE)# <continue-statement>
        V_statement_seq = VN.create(const.STAT_SEQ,self.level)
        # 对于是语句First集的单词，统统继续叠加语句
        while self.pointer.isID() or self.pointer.isR_If() \
            or self.pointer.isR_While() or self.pointer.isR_Return() or self.pointer.isR_Continue()\
            or self.pointer.isL_Brace() or self.pointer.isR_Scan() or self.pointer.isR_Break()\
            or self.pointer.isR_Print() or self.pointer.isSemicolon() or self.pointer.isR_Do():
            if self.pointer.isR_Return():
                V_statement_seq.append(self.statement(downOverlookSet))
                marks = [const.R_BRACE]
                self.overlookToMarks(marks)
                break
            else:
                V_statement_seq.append(self.statement(downOverlookSet))
        return self.checkEmpty(V_statement_seq)

    # <statement> ::= <compound-statement> | <condition-statement>
    # |<loop-statement> | <jump-statement> | <print-statement>
    # |<scan-statement> | <assignment-expression>';' | <function-call>';'
    # |';' 
    def statement(self, overlookSet = [const.R_BRACE]):
        sentenceListOverlookSet = []
        self.overlookSetAdd(sentenceListOverlookSet, const.R_BRACE)
        self.overlookSetAdd(sentenceListOverlookSet, const.CONST)
        self.overlookSetAdd(sentenceListOverlookSet, const.INT)
        sentenceOverlookSet = [const.R_BRACE]
        self.overlookSetAdd(sentenceOverlookSet, const.SEMICOLON)
        V_statement = VN.create(const.STAT,self.level)
        if self.pointer.isR_If():
            V_statement.append(self.condition_statement(overlookSet))
        elif self.pointer.isR_While():
            V_statement.append(self.loop1_statement(overlookSet))
        elif self.pointer.isR_Do():
            V_statement.append(self.loop2_statement(overlookSet))
        # 如果是{，就是处理语句序列
        elif self.pointer.isL_Brace():
            self.level += 1
            #记录局部变量个数
            varnum = len(self.symbolTable.var)
            V_statement.append(self.compound_statement(sentenceListOverlookSet))
            self.level -= 1
            #删除局部变量
            self.symbolTable.var = self.symbolTable.var[:varnum]
        elif self.pointer.isR_Return():
            V_statement.append(self.return_statement(sentenceOverlookSet))
        elif self.pointer.isR_Scan():
            V_statement.append(self.scan_statement(sentenceOverlookSet))
        elif self.pointer.isR_Print():
            V_statement.append(self.print_statement(sentenceOverlookSet))
        # 读到标识符，可能是函数调用或者赋值语句，
        elif self.pointer.isID() and self.pointer.next.isAssign():
            V_statement.append(self.assignment_expression(sentenceOverlookSet))
        elif self.pointer.isID() and self.pointer.next.isL_Parenthesis():
            id = self.pointer
            V_statement.append(self.function_call(sentenceOverlookSet))
            if self.pointer.isSemicolon():
                funcnum = self.symbolTable.getFunc(id.text)
                if funcnum == None:
                    self.error(Error.ST_UNDEFINED_ID, self.pointer,msg="can not find this func")
                    self.overlookToMarks(overlookSet)
                else:
                    func = self.symbolTable.funcs[funcnum]
                    if func.returntype == "INT":
                        self.emit(Instruction(Instruction.pop))
                    elif func.returntype == "DOUBLE":
                        self.emit(Instruction(Instruction.pop2))
                V_statement.append(self.pointer)
                self.getsym()
            else:
                self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
                self.overlookToMarks(overlookSet)
        elif self.pointer.isSemicolon():
            V_statement.append(self.pointer)
            self.getsym()
        elif self.pointer.isR_Continue():
            V_statement.append(self.pointer)
            self.emit(Instruction(Instruction.loop_continue))
            self.getsym()
        elif self.pointer.isR_Break():
            V_statement.append(self.pointer)
            self.emit(Instruction(Instruction.loop_break))
            self.getsym()
        else:
            self.error(Error.AN_ILLEGAL_INPUT)
            self.overlookToMarks(overlookSet)
        
        return self.checkEmpty(V_statement)

    # <condition-statement> ::= 
    # 'if' '(' <condition> ')' <statement> ['else' <statement>]
    def condition_statement(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = overlookSet[:]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        self.overlookSetAdd(downOverlookSet, const.ELSE)
        ifSentenceOverlookSet = overlookSet[:]
        self.overlookSetAdd(ifSentenceOverlookSet, const.ELSE)
        V_condition_statement = VN.create(const.COND_STATE,self.level)
        V_condition_statement.append(self.pointer)
        self.getsym()
        if self.pointer.isL_Parenthesis():
            V_condition_statement.append(self.pointer)
            self.getsym()
            cond,label1,relationOperator = self.condition(downOverlookSet)
            # condition后加一条nop指令 后面改为jcond to start of st2
            self.emit(Instruction(Instruction.nop))
            for base in range(len(self.instructionStream.instructions)-1,-1,-1):
                if len(self.instructionStream.instructions[base].lab) > 0:
                    break
            index1 = len(self.instructionStream.instructions)-1
            V_condition_statement.append(cond)
            if self.pointer.isR_Parenthesis():
                V_condition_statement.append(self.pointer)
                self.getsym()
                # first statement
                V_condition_statement.append(self.statement(ifSentenceOverlookSet))
                label2 = len(self.instructionStream.instructions)-base+1
                if self.pointer.isR_Else():
                    # 后面吧nop 改为 jmp to end of st2
                    self.emit(Instruction(Instruction.nop))
                    index2 = len(self.instructionStream.instructions)-1
                    V_condition_statement.append(self.pointer)
                    self.getsym()
                    #second statement
                    V_condition_statement.append(self.statement(overlookSet))
                    label3 = len(self.instructionStream.instructions)-base
                    # 分析
                    if not relationOperator == None:
                        if relationOperator.vtype == const.EQ:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jne,label2)
                        elif relationOperator.vtype == const.LE:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jg,label2)
                        elif relationOperator.vtype == const.LT:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jge,label2)
                        elif relationOperator.vtype == const.GE:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jl,label2)
                        elif relationOperator.vtype == const.GT:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jle,label2)
                        elif relationOperator.vtype == const.NE:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.je,label2)
                    else:
                        self.instructionStream.instructions[index1] = Instruction(Instruction.je,label2)
                    self.instructionStream.instructions[index2] = Instruction(Instruction.jmp,label3)
                else:
                    label2 -= 1
                    if not relationOperator == None:
                        if relationOperator.vtype == const.EQ:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jne,label2)
                        elif relationOperator.vtype == const.LE:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jg,label2)
                        elif relationOperator.vtype == const.LT:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jge,label2)
                        elif relationOperator.vtype == const.GE:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jl,label2)
                        elif relationOperator.vtype == const.GT:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.jle,label2)
                        elif relationOperator.vtype == const.NE:
                            self.instructionStream.instructions[index1] = Instruction(Instruction.je,label2)
                    else:
                        self.instructionStream.instructions[index1] = Instruction(Instruction.je,label2)
            else :
                self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(overlookSet)
        else:
            self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        return V_condition_statement

    # <condition> ::= 
    # <expression>[<relational-operator><expression>] 
    def condition(self, overlookSet = [const.R_BRACE]):
        label1 = 0
        V_condition = VN.create(const.CONDITION,self.level)
        posit = len(self.instructionStream.instructions)
        expression,tmp_exp_type = self.expression(overlookSet)
        base = 0
        for base in range(len(self.instructionStream.instructions)-1,-1,-1):
            if len(self.instructionStream.instructions[base].lab) > 0:
               break  
        label1 =  posit - base
        self.emit(Instruction(Instruction.nop))
        V_condition.append(expression)
        relationOperator = None
        index = len(self.instructionStream.instructions)-1
        if self.pointer.isRelationOperator():
            relationOperator = self.pointer
            V_condition.append(relationOperator)
            self.getsym()
            exp,exp_type = self.expression(overlookSet)
            V_condition.append(exp)
            if tmp_exp_type == "int" and exp_type == "double":
                self.instructionStream.instructions[index] = Instruction(Instruction.i2d)
                exp_type = "double"
                self.emit(Instruction(Instruction.dcmp))
            elif tmp_exp_type == "double" and exp_type == "int":
                del self.instructionStream.instructions[index]
                self.emit(Instruction(Instruction.i2d))
                exp_type = "double"
                self.emit(Instruction(Instruction.dcmp))
            elif tmp_exp_type == "int" and exp_type == "int":
                del self.instructionStream.instructions[index]
                exp_type = "int"
                self.emit(Instruction(Instruction.icmp))
            elif tmp_exp_type == "double" and exp_type == "double":  
                del self.instructionStream.instructions[index]
                exp_type = "double"
                self.emit(Instruction(Instruction.dcmp))
        else:
            del self.instructionStream.instructions[index]
            if not tmp_exp_type == "int":
                self.emit(Instruction(Instruction.d2i))
        # 这里结束后没有检查，直接返回
        return self.checkEmpty(V_condition),label1,relationOperator

    # <loop1-statement> ::= 
    # 'while' '(' <condition> ')' <statement>
    def loop1_statement(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = [const.R_BRACE]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        V_loop1_statement = VN.create(const.LOOP_STATE,self.level)
        V_loop1_statement.append(self.pointer)
        self.getsym()
        if self.pointer.isL_Parenthesis():
            V_loop1_statement.append(self.pointer)
            self.getsym()
            cond,label1,relationOperator = self.condition(downOverlookSet)
            V_loop1_statement.append(cond)
            if self.pointer.isR_Parenthesis():
                for base in range(len(self.instructionStream.instructions)-1,-1,-1):
                    if len(self.instructionStream.instructions[base].lab) > 0:
                        break
                V_loop1_statement.append(self.pointer)
                self.getsym()
                self.emit(Instruction(Instruction.nop))
                index = len(self.instructionStream.instructions) - 1
                V_loop1_statement.append(self.statement(overlookSet))
                label2 = len(self.instructionStream.instructions)-base+1
                if not relationOperator == None:
                    if relationOperator.vtype == const.EQ:
                        self.instructionStream.instructions[index] = Instruction(Instruction.jne,label2)
                    elif relationOperator.vtype == const.LE:
                        self.instructionStream.instructions[index] = Instruction(Instruction.jg,label2)
                    elif relationOperator.vtype == const.LT:
                        self.instructionStream.instructions[index] = Instruction(Instruction.jge,label2)
                    elif relationOperator.vtype == const.GE:
                        self.instructionStream.instructions[index] = Instruction(Instruction.jl,label2)
                    elif relationOperator.vtype == const.GT:
                        self.instructionStream.instructions[index] = Instruction(Instruction.jle,label2)
                    elif relationOperator.vtype == const.NE:
                        self.instructionStream.instructions[index] = Instruction(Instruction.je,label2)
                else:
                    self.instructionStream.instructions[index] = Instruction(Instruction.je,label2)
                self.emit(Instruction(Instruction.jmp,label1))
                # 加入对于break和continue的检查
                bbreak,ccontinue = self.find_bnc(index)
                if not bbreak == None:
                    self.instructionStream.instructions[bbreak] = Instruction(Instruction.jmp,label2)
                if not ccontinue == None:
                    self.instructionStream.instructions[ccontinue] = Instruction(Instruction.jmp,label2-1)
            else:
                self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(downOverlookSet)
        else:
            self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks(downOverlookSet)
        return self.checkEmpty(V_loop1_statement)

    # <loop2-statement> ::= 
    # ‘do' <statement> 'while' '(' <condition> ')' ';'
    def loop2_statement(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = [const.R_BRACE]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        V_loop2_statement = VN.create(const.LOOP_STATE,self.level)
        V_loop2_statement.append(self.pointer)
        self.getsym()
        start = len(self.instructionStream.instructions)-1
        V_loop2_statement.append(self.statement(overlookSet))
        for base in range(len(self.instructionStream.instructions)-1,-1,-1):
            if len(self.instructionStream.instructions[base].lab) > 0:
                break
        label2 = start-base+1
        if self.pointer.isR_While():
            V_loop2_statement.append(self.pointer)
            self.getsym()
            if self.pointer.isL_Parenthesis():
                V_loop2_statement.append(self.pointer)
                self.getsym()
                cond,label1,relationOperator = self.condition(downOverlookSet)
                V_loop2_statement.append(cond)
                if self.pointer.isR_Parenthesis():
                    V_loop2_statement.append(self.pointer)
                    if not relationOperator == None:
                        if relationOperator.vtype == const.EQ:
                            self.emit(Instruction(Instruction.je,label2))
                        elif relationOperator.vtype == const.LE:
                            self.emit(Instruction(Instruction.jle,label2))
                        elif relationOperator.vtype == const.LT:
                            self.emit(Instruction(Instruction.jl,label2))
                        elif relationOperator.vtype == const.GE:
                            self.emit(Instruction(Instruction.jge,label2))
                        elif relationOperator.vtype == const.GT:
                            self.emit(Instruction(Instruction.jg,label2))
                        elif relationOperator.vtype == const.NE:
                            self.emit(Instruction(Instruction.jne,label2))
                    else:
                        self.emit(Instruction(Instruction.jne,label2))
                    # 加入对于break和continue的检查
                    bbreak,ccontinue = self.find_bnc(start)
                    if not bbreak == None:
                        self.instructionStream.instructions[bbreak] = Instruction(Instruction.jmp,len(self.instructionStream.instructions)-base)
                    if not ccontinue == None:
                        self.instructionStream.instructions[ccontinue] = Instruction(Instruction.jmp,label1)
                    # 读分号
                    self.getsym()
                    if self.pointer.isSemicolon():
                        V_loop2_statement.append(self.pointer)
                        self.getsym()
                    else:
                        self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
                        self.overlookToMarks(overlookSet)
                else:
                    self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                    self.overlookToMarks(downOverlookSet)
            else:
                self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(downOverlookSet)
        else:
            self.error(Error.AN_ILLEGAL_INPUT, self.pointer,"missing while")
            self.overlookToMarks(downOverlookSet)
        return self.checkEmpty(V_loop2_statement)

    # <jump-statement> ::= 
    # 'break' ';'
    #|'continue' ';'
    #|<return-statement>
    
    # <return-statement> ::= 'return' [<expression>] ';'
    def return_statement(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = overlookSet[:]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        V_return_statement = VN.create(const.RET_STATE,self.level)
        V_return_statement.append(self.pointer)
        self.getsym()
        if not self.pointer.isSemicolon():
            exp,exp_type = self.expression(downOverlookSet)
            V_return_statement.append(exp)
            if exp_type == "double":
                self.emit(Instruction(Instruction.dret))
            else:
                self.emit(Instruction(Instruction.iret))
            if not self.pointer.isSemicolon():
                self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
                self.overlookToMarks(overlookSet)
            else:
                V_return_statement.append(self.pointer)
                self.getsym()
        else:
            V_return_statement.append(self.pointer)
            self.emit(Instruction(Instruction.ret))
            self.getsym()
        return V_return_statement

    # <scan-statement> ::= 'scan' '(' <identifier> ')' ';'
    def scan_statement(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = overlookSet[:]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        V_scan_statement = VN.create(const.SCAN_STATE,self.level)
        V_scan_statement.append(self.pointer)
        self.getsym()
        if self.pointer.isL_Parenthesis():
            V_scan_statement.append(self.pointer)
            self.getsym()
            if self.pointer.isID():
                id = self.pointer
                var = self.symbolTable.getVar(id.text)
                if var == None:
                    self.error(Error.ST_UNDEFINED_ID, self.pointer.previous)
                    self.overlookToMarks(overlookSet)
                # 找到标识符，先加载
                else:
                    if var.level == 0 and self.level != var.level:
                        self.emit(Instruction(Instruction.loada, 1, var.offset))
                    else:
                        self.emit(Instruction(Instruction.loada, 0, var.offset))
                V_scan_statement.append(self.pointer)
                self.getsym()
                if self.pointer.isR_Parenthesis():
                    V_scan_statement.append(self.pointer)
                    self.getsym()
                    # 添加赋值指令
                    if var.flag == 0: 
                        if var.type == "double":
                            self.emit(Instruction(Instruction.dscan))
                            self.emit(Instruction(Instruction.dstore))
                        elif var.type == "int":
                            self.emit(Instruction(Instruction.iscan))
                            self.emit(Instruction(Instruction.istore))
                    else:
                        self.error(Error.AN_ILLEGAL_TYPE, self.pointer.previous)
                        self.overlookToMarks(overlookSet)
                    if self.pointer.isSemicolon():
                        V_scan_statement.append(self.pointer)
                        self.getsym()
                    else:
                        self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
                        self.overlookToMarks(overlookSet)
                else:
                    self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                    self.overlookToMarks(overlookSet)
            else :
                self.error(Error.AN_MISS_IDENTIFIER, self.pointer.previous)
                self.overlookToMarks(overlookSet)
        else :
            self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        return V_scan_statement

    # <print-statement> ::= 'print' '(' [<printable-list>] ')' ';'
    def print_statement(self, overlookSet = [const.R_BRACE]):
        downOverlookSet = overlookSet[:]
        self.overlookSetAdd(downOverlookSet, const.R_PARENTHESIS)
        V_printable = VN.create(const.PRINT_STATE,self.level)
        V_printable.append(self.pointer)
        self.getsym()
        if self.pointer.isL_Parenthesis():
            V_printable.append(self.pointer)
            self.getsym()
            printable_list = self.printable_list(downOverlookSet)
            V_printable.append(printable_list)
            if self.pointer.isR_Parenthesis():
                V_printable.append(self.pointer)
                self.emit(Instruction(Instruction.printl))
                self.getsym()
                if self.pointer.isSemicolon():
                    V_printable.append(self.pointer)
                    self.getsym()
                else:
                    self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
                    self.overlookToMarks(overlookSet)
            else:
                self.error(Error.AN_MISS_R_PARENTHESIS, self.pointer.previous)
                self.overlookToMarks(overlookSet)
        else :
            self.error(Error.AN_MISS_L_PARENTHESIS, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        return V_printable

    # <printable-list>  ::= <printable> {',' <printable>}
    def printable_list(self,overlookSet):
        V_printable_list = VN.create(const.PRINT_LIST,self.level)
        printable = self.printable(overlookSet)
        while self.pointer.isComma():
            V_printable_list.append(self.pointer)
            self.getsym()
            self.emit(Instruction(Instruction.bipush,32))
            self.emit(Instruction(Instruction.cprint))
            printable = self.printable(overlookSet)
            V_printable_list.append(printable)
        return V_printable_list

    # <printable> ::= <expression> | <string-literal> |
    def printable(self,overlookSet):
        V_printable = VN.create(const.PRINTABLE,self.level)
        if self.pointer.isString():
            if not self.symbolTable.isunique(self.pointer.text[1:-1]) :
                self.symbolTable.constant.append(tableitem('S',self.pointer.text[1:-1],self.pointer.level,0,0))
            self.emit(Instruction(Instruction.loadc,self.symbolTable.getConstant_by_value(self.pointer.text[1:-1])))
            self.emit(Instruction(Instruction.sprint))
            V_printable.append(self.pointer)
            self.getsym()
        # 如果字符串后面不是有括号，那就解析表达式
        elif self.pointer.isChar():
            self.emit(Instruction(Instruction.bipush,self.pointer.text))
            self.emit(Instruction(Instruction.cprint))
            V_printable.append(self.pointer)
            self.getsym()
        else:
            printable,print_type = self.expression(overlookSet)
            V_printable.append(printable)
            if print_type == "double":
                self.emit(Instruction(Instruction.dprint))
            elif print_type == "int":
                self.emit(Instruction(Instruction.iprint))
        return V_printable
    # <assignment-expression> ::= 
    # <identifier> <assignment-operator> <expression>
    def assignment_expression(self,overlookSet = [const.R_BRACE]):
        #downOverlookSet = overlookSet[:]
        V_assignment_expression = VN.create(const.ASSIGN_EXP,self.level)
        var = self.symbolTable.getVar(self.pointer.text)
        if var:
            V_assignment_expression.append(self.pointer)
            if var.flag == 0:
                self.getsym()
                if var.level == 0 and self.level != var.level:
                    self.emit(Instruction(Instruction.loada, 1, var.offset))
                else:
                    self.emit(Instruction(Instruction.loada, 0, var.offset))
            else:
                self.error(Error.ST_ASSIGN_CONST, self.pointer.previous)
                self.getsym()
        else:
            self.error(Error.ST_UNDEFINED_ID, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        if self.pointer.isAssign():
            V_assignment_expression.append(self.pointer)
            self.getsym()
            exp,exp_type = self.expression(overlookSet)
            V_assignment_expression.append(exp)
            if var.type == "double":
                if not exp_type == "double":
                    self.emit(Instruction(Instruction.i2d))
                self.emit(Instruction(Instruction.dstore))
            elif var.type == "int":
                if not exp_type == "int":
                    self.emit(Instruction(Instruction.d2i))
                self.emit(Instruction(Instruction.istore))
        else:
            self.error(Error.AN_MISS_ASSIGN, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        if self.pointer.isSemicolon():
            V_assignment_expression.append(self.pointer)
            self.getsym()
        else:
            self.error(Error.AN_MISS_SEMICOLON, self.pointer.previous)
            self.overlookToMarks(overlookSet)
        return V_assignment_expression
    # 语义分析
    # <函数定义部分>
    def run_functionDefine(self, Vn):
        overlookSet = [const.CONST, const.INT, const.VOID]
        if Vn.hasChild(const.VOID):
            returnValue = "VOID"
        elif Vn.hasChild(const.INT):
            returnValue = "INT"
        elif Vn.hasChild(const.DOUBLE):
            returnValue = "DOUBLE"
        id = Vn.findChild(const.ID)
        if not id == None:
            name = id.text
            # 如果有参数表，记得加入参数到符号表中
            parameter = Vn.findChild(const.PARA_CLA)
            if not parameter == None:
                if parameter.hasChild(const.PARA_DEC_LIST):
                    para_list = []
                    parameterList = parameter.findChild(const.PARA_DEC_LIST)
                    paraslot = 0
                    ids = parameterList.findGrandChildren(const.ID)
                    for id in ids:
                        if id.previous.isR_Double():
                            paraslot += 2
                            para_list.append("double")
                        elif id.previous.isR_Int():
                            paraslot += 1
                            para_list.append("int")
                    self.symbolTable.funcs.append(func(name,self.symbolTable.getConstant_by_value(name),paraslot,parameter.level,para_list,returnValue))
                else:
                    para_list = []
                    self.symbolTable.funcs.append(func(name,self.symbolTable.getConstant_by_value(name),0,parameter.level,para_list,returnValue))
            
    # 语义分析
    # 函数定义结束后的符号表收尾动作
    def run_functionDefineEnd(self, Vn):
        if Vn.isEmpty():
            return
        #id = Vn.findChild(const.ID)
        if Vn.findChild(const.VOID):
            returnValue = const.VOID
        elif Vn.findChildren(const.DOUBLE):
            returnValue = const.DOUBLE
        else:
            returnValue = const.INT
        sentencelist = None
        if not Vn.findChild(const.COM_STATE) == None:
            if not Vn.findChild(const.COM_STATE).findChild(const.STAT_SEQ) == None:
                sentencelist = Vn.findChild(const.COM_STATE).findChild(const.STAT_SEQ)
        if sentencelist is None:
            self.error(Error.AN_MISS_SENTENCE, self.pointer.previous)
        else:
            sentences = sentencelist.findChildren(const.STAT)
            ret = False
            for sentence in sentences:
                if not sentence.findChild(const.RET_STATE) is None:
                    ret = True
                    break
            if ret == False:
                if returnValue == const.VOID:
                    self.emit(Instruction(Instruction.ret))
                else:
                    self.error(Error.AN_MISS_RET_STATEMENT, self.pointer.previous)
            else:
                #隐式转换返回类型
                early = self.instructionStream.instructions.pop() #double or int
                if returnValue == const.INT and early.instruction == Instruction.dret:
                    self.emit(Instruction(Instruction.d2i))
                    self.emit(Instruction(Instruction.iret))
                elif returnValue == const.INT and early.instruction == Instruction.iret:
                    self.emit(Instruction(Instruction.iret))
                elif returnValue == const.DOUBLE and early.instruction == Instruction.iret:
                    self.emit(Instruction(Instruction.i2d))
                    self.emit(Instruction(Instruction.dret))
                elif returnValue == const.DOUBLE and early.instruction == Instruction.dret:
                    self.emit(Instruction(Instruction.dret))
                elif early.instruction == Instruction.ret:
                    self.emit(Instruction(Instruction.ret))

                if returnValue == const.VOID and not early.instruction == Instruction.ret:
                    self.error(Error.AN_ILLEGAL_INPUT, self.pointer.previous,msg="can not return value in a void func")
                elif not returnValue == const.VOID and early.instruction == Instruction.ret:
                    self.error(Error.AN_ILLEGAL_INPUT, self.pointer.previous,msg="miss a return value")

    # 错误处理函数
    def error(self,errorNo = Error.AN_UNDEFINED, Vt = None, msg = ''):
        if Vt is None:
            Vt  = self.pointer
        err = Error(self.file, errorNo, Vt.line, msg, Vt.wordNo)
        self.errors.append(err)
        return
    def printAllVn(self):
        self.printVn(self.program)
    def printVn(self, V):
        if isinstance(V, VN):
            print('Vn.Type:' + V.msg() + '')
            for child in V.children:
                self.printVn(child)
        else:
            print('Vt.No' + str(V.vtype) + ' Text:' + V.msg() )
    def print_var_table(self):
        print(".var:")
        for i in range(0,len(self.symbolTable.var)):
            print("%-5d%-8s%-5d%-8s%-3d"%(i, self.symbolTable.var[i].type, self.symbolTable.var[i].level, self.symbolTable.var[i].value, self.symbolTable.var[i].offset))
