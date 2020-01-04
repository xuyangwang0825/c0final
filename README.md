### README

#### 使用说明

![](https://tva1.sinaimg.cn/large/006tNbRwly1ga8u1dztf7j30i605gdgn.jpg)

- '-h' 显示帮助
- -s 将.c0源文件输出到文本汇编文件.s0
- -c 将.c0源文件输出到二进制目标文件.o0
- -i 设置输入文件
- -o 设置输出文件

#### 项目说明

​		实现了基础C0 ✅

​		类型转换 ✅ 

​		double ✅ 10	

       注释 ✅ 1

       字符字面量和字符串字面量 ✅ 2

       作用域与生命周期 ✅ 3

       do while ✅ 3
#### C0语法

```bash
<digit> ::= 
    '0'|<nonzero-digit>
<nonzero-digit> ::= 
    '1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9'
<hexadecimal-digit> ::=
    <digit>|'a'|'b'|'c'|'d'|'e'|'f'|'A'|'B'|'C'|'D'|'E'|'F'

<integer-literal> ::= 
    <decimal-literal>|<hexadecimal-literal>
<decimal-literal> ::= 
    '0'|<nonzero-digit>{<digit>}
<hexadecimal-literal> ::= 
    ('0x'|'0X')<hexadecimal-digit>{<hexadecimal-digit>}


<nondigit> ::=    'a'|'b'|'c'|'d'|'e'|'f'|'g'|'h'|'i'|'j'|'k'|'l'|'m'|'n'|'o'|'p'|'q'|'r'|'s'|'t'|'u'|'v'|'w'|'x'|'y'|'z'|'A'|'B'|'C'|'D'|'E'|'F'|'G'|'H'|'I'|'J'|'K'|'L'|'M'|'N'|'O'|'P'|'Q'|'R'|'S'|'T'|'U'|'V'|'W'|'X'|'Y'|'Z'

<identifier> ::= 
    <nondigit>{<nondigit>|<digit>}
<reserved-word> ::= 
     'const'
    |'void'   |'int'    |'char'   |'double'
    |'struct'
    |'if'     |'else'   
    |'switch' |'case'   |'default'
    |'while'  |'for'    |'do'
    |'return' |'break'  |'continue' 
    |'print'  |'scan'


<char-liter> ::= 
    "'" (<c-char>|<escape-seq>) "'" 
<string-literal> ::= 
    '"' {<s-char>|<escape-seq>} '"'
<escape-seq> ::=  
      '\\' | "\'" | '\"' | '\n' | '\r' | '\t'
    | '\x'<hexadecimal-digit><hexadecimal-digit>

    
<sign> ::= 
    '+'|'-'
<digit-seq> ::=
    <digit>{<digit>}
<floating-literal> ::= 
     [<digit-seq>]'.'<digit-seq>[<exponent>]
    |<digit-seq>'.'[<exponent>]
    |<digit-seq><exponent>
<exponent> ::= 
    ('e'|'E')[<sign>]<digit-seq>
   
    
<unary-operator>          ::= '+' | '-'
<additive-operator>       ::= '+' | '-'
<multiplicative-operator> ::= '*' | '/'
<relational-operator>     ::= '<' | '<=' | '>' | '>=' | '!=' | '=='
<assignment-operator>     ::= '='   

    
<single-line-comment> ::=
    '//'{<any-char>}<LF>
<multi-line-comment> ::= 
    '/*'{<any-char>}'*/'  
    
    
<type-specifier>         ::= <simple-type-specifier>
<simple-type-specifier>  ::= 'void'|'int'|'char'|'double'
<const-qualifier>        ::= 'const'
    
    
<C0-program> ::= 
    {<variable-declaration>}{<function-definition>}


<variable-declaration> ::= 
    [<const-qualifier>]<type-specifier><init-declarator-list>';'
<init-declarator-list> ::= 
    <init-declarator>{','<init-declarator>}
<init-declarator> ::= 
    <identifier>[<initializer>]
<initializer> ::= 
    '='<expression>    

    
<function-definition> ::= 
    <type-specifier><identifier><parameter-clause><compound-statement>

<parameter-clause> ::= 
    '(' [<parameter-declaration-list>] ')'
<parameter-declaration-list> ::= 
    <parameter-declaration>{','<parameter-declaration>}
<parameter-declaration> ::= 
    [<const-qualifier>]<type-specifier><identifier>

    
<compound-statement> ::= 
    '{' {<variable-declaration>} <statement-seq> '}'
<statement-seq> ::= 
	{<statement>}
<statement> ::= 
     <compound-statement>
    |<condition-statement>
    |<loop-statement>
    |<jump-statement>
    |<print-statement>
    |<scan-statement>
    |<assignment-expression>';'
    |<function-call>';'
    |';'   
    
    
<condition> ::= 
     <expression>[<relational-operator><expression>] 
   
<condition-statement> ::= 
     'if' '(' <condition> ')' <statement> ['else' <statement>]
    |'switch' '(' <expression> ')' '{' {<labeled-statement>} '}'

<labeled-statement> ::= 
     'case' (<integer-literal>|<char-literal>) ':' <statement>
    |'default' ':' <statement>

    
<loop-statement> ::= 
    'while' '(' <condition> ')' <statement>
   |'do' <statement> 'while' '(' <condition> ')' ';'
   |'for' '('<for-init-statement> [<condition>]';' [<for-update-expression>]')' <statement>

<for-init-statement> ::= 
    [<assignment-expression>{','<assignment-expression>}]';'
<for-update-expression> ::=
    (<assignment-expression>|<function-call>){','(<assignment-expression>|<function-call>)}


<jump-statement> ::= 
     'break' ';'
    |'continue' ';'
    |<return-statement>
<return-statement> ::= 'return' [<expression>] ';'
    
    
<scan-statement> ::= 
    'scan' '(' <identifier> ')' ';'
<print-statement> ::= 
    'print' '(' [<printable-list>] ')' ';'
<printable-list>  ::= 
    <printable> {',' <printable>}
<printable> ::= 
    <expression> | <string-literal>

<assignment-expression> ::= 
    <identifier><assignment-operator><expression>
    
   
  
<expression> ::= 
    <additive-expression>
<additive-expression> ::= 
     <multiplicative-expression>{<additive-operator><multiplicative-expression>}
<multiplicative-expression> ::= 
     <cast-expression>{<multiplicative-operator><cast-expression>}
<cast-expression> ::=
    {'('<type-specifier>')'}<unary-expression>
<unary-expression> ::=
    [<unary-operator>]<primary-expression>
<primary-expression> ::=  
     '('<expression>')' 
    |<identifier>
    |<integer-literal>
    |<char-literal>
    |<floating-literal>
    |<function-call>

<function-call> ::= 
    <identifier> '(' [<expression-list>] ')'
<expression-list> ::= 
    <expression>{','<expression>}
```



