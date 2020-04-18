import json
from zipfile import ZipFile
from turtle import *
from time import time
import math

def sin(x):
    return math.sin(math.radians(x))
def cos(x):
    return math.cos(math.radians(x))
def tan(x):
    return math.tan(math.radians(x))

import sys
if len(sys.argv) > 1:
    projectName = sys.argv[1].replace('.sb3', '')
else:
    projectName = "Scratch Project"
with ZipFile(projectName + '.sb3', 'r') as zipObj:
   zipObj.extractall(projectName)
f = open(projectName + "/project.json")
data = json.loads(f.read())
mode('logo')
tracer(n=None, delay=None)

class Project:
    def __init__(self, data, path):
        self.sprites = []
        self.callstack = []
        self.path = path
        self.screen = Screen()
        self.answer = ""
        self.vars = []
        
        for target in data['targets']:
            self.sprites.append(Sprite(target, self))
        for monitor in data['monitors']:
            if monitor['opcode'] == 'data_variable':
                self.vars.append(Variable(monitor, self))
            elif monitor['opcode'] == 'data_listcontents':
                self.vars.append(List(monitor, self))
    def trigger_event(self, event):
        for sprite in self.sprites:
            sprite.trigger_event(event)
    def get_sprite_by_name(self, name):
        for block in self.blocks:
            if block.ID == ID:
                return block
        return None
    def get_var_by_ID(self, ID):
        for var in self.vars:
            if var.ID == ID:
                return var
        return None
    def step(self):
        #print("###STEP###")
        #print(self.callstack)
        self.callstack[0][0].do_run(self.callstack[0][1])
        del self.callstack[0]
    def run(self):
        while len(self.callstack) > 0:
            self.step()

class Wait:
    def __init__(self, until, block):
        self.until = until
        self.block = block
    def do_run(self, context):
        if not self.block == None:
            if time() >= self.until:
                self.block.do_run(context)
            else:
                self.block.sprite.project.callstack.append([self, context])

class Costume:
    def __init__(self, sprite, data):
        self.sprite = sprite
        self.data = data
        self.path = self.sprite.project.path + data['md5ext']
    def apply_costume(self):
        #self.sprite.project.screen.addshape('Scratch Project/cf57fd9a0e0f018965a147e62471c9c2.png')
        #self.sprite.t.shape('Scratch Project/cf57fd9a0e0f018965a147e62471c9c2.png')
        pass

class Variable:
    def __init__(self, data, project):
        self.data = data
        self.ID = self.data['id']
        self.project = project
        self.value = self.data['value']
        self.name = self.data['params']['VARIABLE']
        self.spriteName = self.data['spriteName']
    def __repr__(self):
        return "Variable: [" + self.name + ": " + str(self.value) + "]"

class List:
    def __init__(self, data, project):
        self.data = data
        self.ID = self.data['id']
        self.project = project
        self.value = self.data['value']
        self.name = self.data['params']['LIST']
        self.spriteName = self.data['spriteName']
    def __repr__(self):
        return "List: [" + self.name + ": [" + ", ".join(self.value) + "]]"

class Context:
    def __init__(self, varnames, parent=None, values=None, return_block=None):
        if values == None:
            self.vars = {name: "" for name in varnames}
        else:
            self.vars = {varnames[i]: values[i] for i in range(len(varnames))}
        self.UID = str(time())
        self.return_block = return_block
        self.parent = parent
    def clone(self, return_block):
        c = Context([])
        c.vars = self.vars
        c.return_block = return_block
        c.UID = str(time())
        c.parent = self
        return c
    def __repr__(self):
        return "Context: " + self.UID + str(self.vars) + str(self.return_block)

class Sprite:
    def __init__(self, data, project):
        self.data = data
        self.project = project
        self.blocks = []
        self.costumes = {}
        self.procs = {}
        self.defaultContext = Context([])
        for blockID in data['blocks']:
            b = data['blocks'][blockID]
            self.blocks.append(Block(self, blockID, b['parent'], b['next'], b['opcode'], b['inputs'], b['fields'], self.defaultContext, b))

        for cost in data['costumes']:
            self.costumes[cost['name']] = Costume(self, cost)

        self.t = Turtle()
        self.t.penup()
        self.set_costume(self.costumes[list(self.costumes.keys())[0]])
    def set_costume(self, costume):
        costume.apply_costume()
    def __repr__(self):
        return self.data['name']
    def add_proc(self, proccode, block, varnames):
        self.procs[proccode] = {'id': block, 'varnames': varnames}
    def get_block_by_ID(self, ID):
        for block in self.blocks:
            if block.ID == ID:
                return block
        return None
    def trigger_event(self, event):
        for block in self.blocks:
            if block.opcode == "event_" + event:
                block.run(self.defaultContext)

class Block:
    def __init__(self, sprite, ID, parent, child, opcode, inputs, fields, defaultContext, data):
        self.sprite = sprite
        self.ID = ID
        self.parent = parent
        self.child = child
        self.opcode = opcode
        self.inputs = inputs
        self.fields = fields
        self.data = data
        self.loopcount = 0
        self.context = defaultContext
        if self.opcode == 'procedures_prototype':
            self.sprite.add_proc(self.data['mutation']['proccode'], self.data['parent'], json.loads(self.data['mutation']['argumentnames']))
    def __repr__(self):
        return "Block: " + self.opcode
    def eval_inputs(self, context):
        inputs = {}
        #print(self.inputs, self.fields, self)
        for i in self.inputs:
            #print(i, self.inputs[i])
            if self.inputs[i][0] == 1:
                if self.inputs[i][1] == None:
                    inputs[i] = None
                else:
                    if type(self.inputs[i][1]) == str:
                        inputs[i] = self.inputs[i][1]
                    else:
                        inputs[i] = self.inputs[i][1][1]
            if self.inputs[i][0] == 2:
                inputs[i] = self.sprite.get_block_by_ID(self.inputs[i][1])
            if self.inputs[i][0] == 3:
                if self.inputs[i][1][0] == 12:
                    inputs[i] = self.sprite.project.get_var_by_ID(self.inputs[i][1][2]).value
                else:
                    inputs[i] = self.sprite.get_block_by_ID(self.inputs[i][1]).do_run(context)
        for i in self.fields:
            #print(i, self.fields[i])
            if len(self.fields[i]) > 1:
                inputs[i] = self.fields[i][1]
            else:
                inputs[i] = self.fields[i][0]
        return inputs
    def run(self, context):
        self.loopcount = 0
        self.sprite.project.callstack.append([self, context])
        #print(self.sprite.project.callstack)
    def do_run(self, context):
        child = self.sprite.get_block_by_ID(self.child)
        inputs = self.eval_inputs(context)
        #print(self.opcode, ' - ', inputs, ' - ', child)#, ' - ', context)
        
        if self.opcode == 'operator_divide':
            return float(inputs['NUM1']) / float(inputs['NUM2'])
        elif self.opcode == 'operator_multiply':
            return float(inputs['NUM1']) * float(inputs['NUM2'])
        elif self.opcode == 'operator_subtract':
            return float(inputs['NUM1']) - float(inputs['NUM2'])
        elif self.opcode == 'operator_add':
            return float(inputs['NUM1']) + float(inputs['NUM2'])
        elif self.opcode == 'operator_round':
            return round(float(inputs['NUM']))
        elif self.opcode == 'operator_mathop':
            if inputs['OPERATOR'] == 'sin':
                return sin(float(inputs['NUM']))
            if inputs['OPERATOR'] == 'cos':
                return cos(float(inputs['NUM']))
            if inputs['OPERATOR'] == 'tan':
                return tan(float(inputs['NUM']))
            if inputs['OPERATOR'] == 'ceiling':
                return math.ceil(float(inputs['NUM']))
            if inputs['OPERATOR'] == 'floor':
                return math.floor(float(inputs['NUM']))
        elif self.opcode == 'operator_join':
            return str(inputs['STRING1']) + str(inputs['STRING2'])
        elif self.opcode == 'operator_gt':
            return float(inputs['OPERAND1']) > float(inputs['OPERAND2'])
        elif self.opcode == 'operator_equals':
            return str(inputs['OPERAND1']) == str(inputs['OPERAND2'])
        elif self.opcode == 'operator_length':
            return len(inputs['STRING'])
        elif self.opcode == 'operator_letter_of':
            return inputs['STRING'][int(inputs['LETTER'])-1]

        elif self.opcode == 'sensing_askandwait':
            if not inputs['QUESTION'] == "":
                sys.stdout.write(inputs['QUESTION'] + '\n')
            self.sprite.project.answer = sys.stdin.readline().replace('\n', '')
            if not child == None:
                child.run(context)
        elif self.opcode == 'sensing_answer':
            return self.sprite.project.answer

        elif self.opcode == 'looks_sayforsecs':
            sys.stdout.write(str(inputs['MESSAGE']) + '\n')
            self.sprite.t.clear()
            self.sprite.t.write(str(inputs['MESSAGE']), align='left')
            #self.sprite.project.callstack.append(Wait(time() + float(inputs['SECS']), child))
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_say':
            sys.stdout.write(str(inputs['MESSAGE']) + '\n')
            self.sprite.t.clear()
            self.sprite.t.write(str(inputs['MESSAGE']), align='left')
            #self.sprite.project.callstack.append(Wait(time() + float(inputs['SECS']), child))
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_thinkforsecs':
            sys.stderr.write(str(inputs['MESSAGE']) + '\n')
            self.sprite.t.clear()
            self.sprite.t.write(str(inputs['MESSAGE']), align='left')
            #self.sprite.project.callstack.append(Wait(time() + float(inputs['SECS']), child))
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_think':
            sys.stderr.write(str(inputs['MESSAGE']) + '\n')
            self.sprite.t.clear()
            self.sprite.t.write(str(inputs['MESSAGE']), align='left')
            #self.sprite.project.callstack.append(Wait(time() + float(inputs['SECS']), child))
            if not child == None:
                child.run(context)

        elif self.opcode == 'motion_gotoxy':
            self.sprite.t.goto(float(inputs['X']), float(inputs['Y']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_changexby':
            self.sprite.t.setx(self.sprite.t.xcor() + float(inputs['DX']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_changeyby':
            self.sprite.t.sety(self.sprite.t.ycor() + float(inputs['DY']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_pointindirection':
            self.sprite.t.seth(float(inputs['DIRECTION']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_turnright':
            self.sprite.t.right(float(inputs['DEGREES']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_turnleft':
            self.sprite.t.left(float(inputs['DEGREES']))
            if not child == None:
                child.do_run(context)

        elif self.opcode == 'data_setvariableto':
            self.sprite.project.get_var_by_ID(inputs['VARIABLE']).value = inputs['VALUE']
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_changevariableby':
            self.sprite.project.get_var_by_ID(inputs['VARIABLE']).value = int(self.sprite.project.get_var_by_ID(inputs['VARIABLE']).value) + int(inputs['VALUE'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_lengthoflist':
            return len(self.sprite.project.get_var_by_ID(inputs['LIST']).value)
        elif self.opcode == 'data_itemoflist':
            return self.sprite.project.get_var_by_ID(inputs['LIST']).value[int(inputs['INDEX'])-1]
        elif self.opcode == 'data_deleteoflist':
            if inputs['INDEX'] == 'all':
                self.sprite.project.get_var_by_ID(inputs['LIST']).value = []
            else:
                del self.sprite.project.get_var_by_ID(inputs['LIST']).value[int(inputs['INDEX'])-1]
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_addtolist':
            self.sprite.project.get_var_by_ID(inputs['LIST']).value.append(str(inputs['ITEM']))
            if not child == None:
                child.do_run(context)

        elif self.opcode == 'argument_reporter_string_number':
            return context.vars[inputs['VALUE']]

        elif self.opcode == 'procedures_call':
            context = Context(self.sprite.procs[self.data['mutation']['proccode']]['varnames'], context, list(inputs.values()), child)
            self.sprite.get_block_by_ID(self.sprite.procs[self.data['mutation']['proccode']]['id']).do_run(context)
        
        elif self.opcode == 'control_repeat':
            if 'SUBSTACK' in inputs:
                if self.loopcount == 0:
                    self.loopcount = int(inputs['TIMES'])
                #print("LOOP COUNT:", self.loopcount)
                if self.loopcount > 1:
                    if not inputs['SUBSTACK'] == None:
                        c = context.clone(self)
                        inputs['SUBSTACK'].do_run(c)
                        self.loopcount -= 1
                    else:
                        if not child == None:
                            child.run(context)
                    #self.sprite.project.callstack.append([self, context])
                else:
                    if not inputs['SUBSTACK'] == None:
                        if child == None:
                            c = context.clone(context.return_block)
                        else:
                            c = context.clone(child)
                        inputs['SUBSTACK'].do_run(c)
                        self.loopcount -= 1
                    else:
                        if not child == None:
                            child.run(context)
                    #if not child == None:
                        #child.run(context)
                        
                    
##                for i in range(int(inputs['TIMES'])):
##                    if not inputs['SUBSTACK'] == None:
##                        inputs['SUBSTACK'].run(context)
##                if not child == None:
##                    child.run(context)
            else:
                if not child == None:
                    child.do_run(context)
        elif self.opcode == 'control_if':
            if inputs['CONDITION'].do_run(context):
                if not inputs['SUBSTACK'] == None:
                    if child == None:
                        c = context.clone(context.return_block)
                    else:
                        c = context.clone(child)
                    inputs['SUBSTACK'].do_run(c)
                    return
                else:
                    if not child == None:
                        child.run(context)
        elif self.opcode == 'control_if_else':
            if inputs['CONDITION'].do_run(context):
                if not inputs['SUBSTACK'] == None:
                    if child == None:
                        c = context.clone(context.return_block)
                    else:
                        c = context.clone(child)
                    inputs['SUBSTACK'].do_run(c)
                    return
                else:
                    if not child == None:
                        child.run(context)
            else:
                if not inputs['SUBSTACK'] == None:
                    if child == None:
                        c = context.clone(context.return_block)
                    else:
                        c = context.clone(child)
                    inputs['SUBSTACK2'].do_run(c)
                    return
                else:
                    if not child == None:
                        child.run(context)
        
        else:
            if not child == None:
                child.do_run(context)

        if child == None and not context == self.sprite.defaultContext and not context.return_block == None:
            #print(context, "===", self)
            self.sprite.project.callstack.append([context.return_block, context.parent])
            #context.return_block.run(context.parent)

project = Project(data, projectName + '/')
project.trigger_event("whenflagclicked")
project.run()
#print(project.vars)
