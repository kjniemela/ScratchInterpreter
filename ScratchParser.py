import json
from zipfile import ZipFile
from time import time
from svg_to_png import *
import math

def sin(x):
    return math.sin(math.radians(x))
def cos(x):
    return math.cos(math.radians(x))
def tan(x):
    return math.tan(math.radians(x))
def number(x):
    try:
        n = float(x)
        if n == round(n):
            n = round(n)
    except ValueError:
        n = 0
    except TypeError:
        n = 0
    return n

working_dir = "working_dir"

import os
import sys
if len(sys.argv) > 1:
    projectName = sys.argv[1].replace('.sb3', '')
else:
    #projectName = "..\..\Downloads\Mirror Number Finder"
    projectName = "Scratch Project"
if len(sys.argv) > 2:
    headless = sys.argv[2] == "-headless"
else:
    headless = False
with ZipFile(projectName + '.sb3', 'r') as zipObj:
   zipObj.extractall(working_dir)
f = open(working_dir + "/project.json")
data = json.loads(f.read())

#headless = True
doStdinEvents = True

if not headless:
    import pygame

class Project:
    def __init__(self, data, path, headless=False, doStdinEvents=False):
        self.headless = headless
        self.doStdinEvents = doStdinEvents
        self.sprites = []
        self.callstack = []
        self.waitstack = []
        self.message_recievers = {}
        self.path = path
        if not headless:
            (width, height) = (480, 360)
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.flip()
            pygame.display.set_caption(path[:-1])
            self.clock = pygame.time.Clock()

        
        self.answer = ""
        self.vars = []
        
        for target in data['targets']:
            self.sprites.append(Sprite(target, self))
##        for monitor in data['monitors']:
##            if monitor['opcode'] == 'data_variable':
##                self.vars.append(Variable(monitor, self))
##            elif monitor['opcode'] == 'data_listcontents':
##                self.vars.append(List(monitor, self))
    def trigger_event(self, event):
        for sprite in self.sprites:
            sprite.trigger_event(event)
    def add_message_reciever(self, message, recv, context):
        if not message in self.message_recievers:
            self.message_recievers[message] = []
        self.message_recievers[message].append((recv, context))
    def get_sprite_by_name(self, name):
        for sprite in self.sprites:
            if sprite.name == name:
                return sprite
        return None
    def get_var_by_ID(self, ID):
        for var in self.vars:
            if var.ID == ID:
                return var
        return None
    def get_recievers_by_message(self, message):
        return self.message_recievers[message]
    def step(self):
        #print("###STEP###")
        #print(self.callstack)
        if len(self.callstack) > 0:
            for i in range(len(self.callstack)):
                self.callstack[0][0].do_run(self.callstack[0][1])
                del self.callstack[0]
        if len(self.waitstack) > 0:
            for block, context, t in self.waitstack:
                if time() > t:
                    #print(self.waitstack)
                    block.do_run(context)
                    del self.waitstack[self.waitstack.index([block, context, t])]
                    
    def run(self):
        running = True
        while running:
            if len(self.callstack) > 0 or len(self.waitstack) > 0:
                self.step()

                if not self.headless:

                    self.screen.fill((255,255,255))

                    for sprite in self.sprites:
                        sprite.draw(self.screen)
                    pygame.display.flip()
            elif self.headless:
                running = False
                break
            if not self.headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        pygame.quit()
                        break
                    #elif event.type == pygame.KEYDOWN and not self.doStdinEvents:
                        #self.trigger_event("whenkeypressed")
                self.clock.tick(30)

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
        #print(data)
        self.path = self.sprite.project.path + data['assetId'] + "." + data['dataFormat']
        if data['dataFormat'] == 'png':
            self.image = pygame.image.load(self.path)
        elif data['dataFormat'] == 'svg':
            self.image = pygame.image.load(svg_to_png(self.path, self.path[:-4]))
    def apply_costume(self):
        #print(self.path)
        self.sprite.lastDir = 90
        self.sprite.spriteObject.image = self.image
        self.sprite.spriteObject.rect = self.sprite.spriteObject.image.get_rect(center=(240, 180))
        self.sprite.rect = self.sprite.spriteObject.rect

class Variable:
    def __init__(self, ID, data, project, spriteName):
        print(data)
        self.ID = ID
        self.project = project
        self.value = data[1]
        self.name = data[0]
        self.spriteName = spriteName
    def __repr__(self):
        return "Variable<%s>: [%s: %s]" % (self.spriteName, self.name, str(self.value))

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
        self.force_step_on_return = True
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
        self.name = self.data['name']
        self.project = project
        self.blocks = []
        self.costumes = {}
        self.costume = None
        self.procs = {}
        self.defaultContext = Context([])
        self.rect = None
        self.vars = self.data['variables']
        self.lists = self.data['lists']
        self.isStage = data['isStage']
        for blockID in data['blocks']:
            b = data['blocks'][blockID]
            if type(b) == dict:
                self.blocks.append(Block(self, blockID, b['parent'], b['next'], b['opcode'], b['inputs'], b['fields'], self.defaultContext, b))

        if not self.project.headless:
            for cost in data['costumes']:
                self.costumes[cost['name']] = Costume(self, cost)

        #if self.isStage:
        for ID in self.vars:
            project.vars.append(Variable(ID, self.vars[ID], self.project, self.name))

        self.x = 0
        self.y = 0
        self.direction = 90
        self.lastDir = 90
        self.scale = 100
        self.lastScale = 100

        if not self.project.headless:
            self.spriteObject = pygame.sprite.Sprite()
            #self.spriteObject.rect = project.screen.get_rect(center=(240, 180))

            self.renderObject = pygame.sprite.RenderPlain(self.spriteObject)

            self.set_costume(self.costumes[list(self.costumes.keys())[0]])
            
            self.spriteObject.image, self.spriteObject.rect = self.rotate(self.costume.image, self.rect, -(self.direction-90))
            self.spriteObject.image, self.spriteObject.rect = self.rescale(self.spriteObject.image, self.spriteObject.rect, self.scale)
            self.spriteObject.mask = pygame.mask.from_surface(self.spriteObject.image)
    def set_costume(self, costume):
        costume.apply_costume()
        self.costume = costume
        self.lastScale = None
        self.lastDir = None
    def __repr__(self):
        return "Sprite<%s>" % (self.name)
    def add_proc(self, proccode, block, varnames):
        self.procs[proccode] = {'id': block, 'varnames': varnames}
    def get_block_by_ID(self, ID):
        for block in self.blocks:
            if block.ID == ID:
                return block
        return None
    def get_local_var_by_ID(self, ID):
        return None
    def get_costume_by_name(self, name):
        return self.costumes[name]
    def trigger_event(self, event):
        for block in self.blocks:
            if block.opcode == "event_" + event:
                block.do_run(self.defaultContext)
    def touching(self, other):
        #print(self, other)
        #print(self.spriteObject.mask.overlap(other.spriteObject.mask, (int(abs(self.x-other.x)), int(abs(self.y-other.y)))))
        return not self.spriteObject.mask.overlap(other.spriteObject.mask, (int(abs(self.x-other.x)), int(abs(self.y-other.y)))) == None
    def draw(self, screen):
        if not self.direction == self.lastDir:
            self.spriteObject.image, self.spriteObject.rect = self.rotate(self.costume.image, self.rect, -(self.direction-90))
            self.spriteObject.image, self.spriteObject.rect = self.rescale(self.spriteObject.image, self.spriteObject.rect, self.scale)
            self.lastDir = self.direction
            self.spriteObject.mask = pygame.mask.from_surface(self.spriteObject.image)
        if not self.scale == self.lastScale:
            self.spriteObject.image, self.spriteObject.rect = self.rescale(self.costume.image, self.rect, self.scale)
            self.spriteObject.image, self.spriteObject.rect = self.rotate(self.spriteObject.image, self.spriteObject.rect, -(self.direction-90))
            self.lastScale = self.scale
            self.spriteObject.mask = pygame.mask.from_surface(self.spriteObject.image)
        self.spriteObject.rect = self.spriteObject.image.get_rect(center=(self.x+240, 360-(self.y+180)))
        self.renderObject.draw(screen)
    def rescale(self, image, rect, scale):
        new_image = pygame.transform.scale(image, (round(rect.width*(scale/200)), round(rect.height*(scale/200))))
        new_rect = new_image.get_rect(center=rect.center)
        return new_image, new_rect
    def rotate(self, image, rect, angle):
        """Rotate the image while keeping its center."""
        # Rotate the original image without modifying it.
        new_image = pygame.transform.rotate(image, angle)
        # Get a new rect with the center of the old rect.
        rect = new_image.get_rect(center=rect.center)
        return new_image, rect

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
        #print(self.opcode, ' - ', inputs, ' - ', child, ' - ', self.sprite)
        
        if self.opcode == 'operator_divide':
            try:
                return number(inputs['NUM1']) / number(inputs['NUM2'])
            except ZeroDivisionError:
                return 'Infinity'
        elif self.opcode == 'operator_multiply':
            return number(inputs['NUM1']) * number(inputs['NUM2'])
        elif self.opcode == 'operator_subtract':
            return number(inputs['NUM1']) - number(inputs['NUM2'])
        elif self.opcode == 'operator_add':
            return number(inputs['NUM1']) + number(inputs['NUM2'])
        elif self.opcode == 'operator_round':
            return number(float(inputs['NUM']))
        elif self.opcode == 'operator_mathop':
            if inputs['OPERATOR'] == 'sin':
                return sin(number(inputs['NUM']))
            if inputs['OPERATOR'] == 'cos':
                return cos(number(inputs['NUM']))
            if inputs['OPERATOR'] == 'tan':
                return tan(number(inputs['NUM']))
            if inputs['OPERATOR'] == 'ceiling':
                return math.ceil(number(inputs['NUM']))
            if inputs['OPERATOR'] == 'floor':
                return math.floor(float(inputs['NUM']))
        elif self.opcode == 'operator_join':
            return str(inputs['STRING1']) + str(inputs['STRING2'])
        elif self.opcode == 'operator_gt':
            return float(inputs['OPERAND1']) > number(inputs['OPERAND2'])
        elif self.opcode == 'operator_lt':
            return float(inputs['OPERAND1']) < number(inputs['OPERAND2'])
        elif self.opcode == 'operator_equals':
            return str(inputs['OPERAND1']) == str(inputs['OPERAND2'])
        elif self.opcode == 'operator_not':
            if 'OPERAND' in inputs:
                if not inputs['OPERAND'] == None:
                    return not inputs['OPERAND'].do_run(context)
                else:
                    return True
            else:
                return True
        elif self.opcode == 'operator_length':
            return len(inputs['STRING'])
        elif self.opcode == 'operator_letter_of':
            return inputs['STRING'][int(inputs['LETTER'])-1]

        elif self.opcode == 'sensing_keypressed':
            if self.sprite.project.headless:
                return False
            else:
                keys = pygame.key.get_pressed()
                pressed_keys = []
                for key in range(len(keys)):
                    if keys[key] == 1:
                        pressed_keys.append(pygame.key.name(key).replace('up', 'up arrow').replace('down', 'down arrow').replace('right', 'right arrow').replace('left', 'left arrow'))
                #print(pressed_keys, self.sprite.get_block_by_ID(inputs['KEY_OPTION']).data['fields']['KEY_OPTION'][0])
                return self.sprite.get_block_by_ID(inputs['KEY_OPTION']).data['fields']['KEY_OPTION'][0] in pressed_keys
        elif self.opcode == 'sensing_askandwait':
            if not inputs['QUESTION'] == "":
                sys.stdout.write(inputs['QUESTION'])
            self.sprite.project.answer = sys.stdin.readline().replace('\n', '')
            if not child == None:
                child.run(context)
        elif self.opcode == 'sensing_answer':
            return self.sprite.project.answer
        elif self.opcode == 'sensing_touchingcolor':
            return False
        elif self.opcode == 'sensing_touchingobject':
            return self.sprite.get_block_by_ID(inputs['TOUCHINGOBJECTMENU']).do_run(context)
        elif self.opcode == 'sensing_touchingobjectmenu':
            if inputs['TOUCHINGOBJECTMENU'] == '_edge_':
                return False
            else:
                return self.sprite.touching(self.sprite.project.get_sprite_by_name(inputs['TOUCHINGOBJECTMENU']))

        elif self.opcode == 'looks_sayforsecs':
            sys.stdout.write(str(inputs['MESSAGE']) + '\n')
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_say':
            sys.stdout.write(str(inputs['MESSAGE']) + '\n')
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_thinkforsecs':
            sys.stderr.write(str(inputs['MESSAGE']) + '\n')
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_think':
            sys.stderr.write(str(inputs['MESSAGE']) + '\n')
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_setsizeto':
            self.sprite.scale = number(inputs['SIZE'])
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_switchcostumeto':
            self.sprite.set_costume(self.sprite.get_costume_by_name(self.sprite.get_block_by_ID(inputs['COSTUME']).do_run(context)))
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_costume':
            return inputs['COSTUME']

        elif self.opcode == 'motion_gotoxy':
            self.sprite.x, self.sprite.y = number(inputs['X']), number(inputs['Y'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_changexby':
            self.sprite.x += number(inputs['DX'])
            #print("X += %s" % (inputs['DX']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_changeyby':
            self.sprite.y += number(inputs['DY'])
            if not child == None:
                child.do_run(context)
            #print("Y += %s" % (inputs['DY']))
        elif self.opcode == 'motion_movesteps':
            self.sprite.x += number(inputs['STEPS'])*sin(self.sprite.direction)
            self.sprite.y += number(inputs['STEPS'])*cos(self.sprite.direction)
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_pointindirection':
            self.sprite.direction = number(inputs['DIRECTION'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_turnright':
            self.sprite.direction += number(inputs['DEGREES'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_turnleft':
            self.sprite.direction -= number(inputs['DEGREES'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_xposition':
            return self.sprite.x
        elif self.opcode == 'motion_yposition':
            return self.sprite.y

        elif self.opcode == 'data_setvariableto':
            #print("SET VAR %s TO %s" % (self.sprite.project.get_var_by_ID(inputs['VARIABLE']), inputs['VALUE']))
            self.sprite.project.get_var_by_ID(inputs['VARIABLE']).value = inputs['VALUE']
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_changevariableby':
            self.sprite.project.get_var_by_ID(inputs['VARIABLE']).value = number(self.sprite.project.get_var_by_ID(inputs['VARIABLE']).value) + number(inputs['VALUE'])
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

        elif self.opcode == 'event_whenkeypressed':
            keys = pygame.key.get_pressed()
            pressed_keys = []
            for key in range(len(keys)):
                if keys[key] == 1:
                    pressed_keys.append(pygame.key.name(key))
            if inputs['KEY_OPTION'] in pressed_keys:
                if not child == None:
                    child.do_run(context)
        elif self.opcode == 'event_broadcast':
            for recvBlock, recvContext in self.sprite.project.get_recievers_by_message(inputs['BROADCAST_INPUT']):
                recvBlock.run(recvContext)
        elif self.opcode == 'event_whenbroadcastreceived':
            project.add_message_reciever(project.sprites[0].data['broadcasts'][inputs['BROADCAST_OPTION']], self.sprite.get_block_by_ID(self.child), context)

        elif self.opcode == 'control_wait':
            self.sprite.project.waitstack.append([self.sprite.get_block_by_ID(self.child), context, time()+float(inputs['DURATION'])])
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
        elif self.opcode == 'control_forever':
            if 'SUBSTACK' in inputs:
                if not inputs['SUBSTACK'] == None:
                    c = context.clone(self)
                    inputs['SUBSTACK'].do_run(c)
                else:
                    if not child == None:
                        child.run(context)
            else:
                if not child == None:
                    child.do_run(context)
        elif self.opcode == 'control_if':
            if inputs['CONDITION'].do_run(context):
                if not inputs['SUBSTACK'] == None:
                    if child == None:
                        c = context.clone(context.return_block)
                        c.parent = context.parent
                    else:
                        c = context.clone(child)
                        c.force_step_on_return = False #this MUST NOT be set to false if the block is at the end of a loop. garuantee this by requiring the block to have a child.
                    inputs['SUBSTACK'].do_run(c)
                    return
                else:
                    if not child == None:
                        child.do_run(context)
            else:
                if not child == None:
                    child.do_run(context)
        elif self.opcode == 'control_if_else':
            if inputs['CONDITION'].do_run(context):
                if not inputs['SUBSTACK'] == None:
                    if child == None:
                        c = context.clone(context.return_block)
                        c.parent = context.parent
                    else:
                        c = context.clone(child)
                        c.force_step_on_return = False
                    inputs['SUBSTACK'].do_run(c)
                    return
                else:
                    if not child == None:
                        child.run(context)
            else:
                if not inputs['SUBSTACK2'] == None:
                    if child == None:
                        c = context.clone(context.return_block)
                        c.parent = context.parent
                    else:
                        c = context.clone(child)
                        c.force_step_on_return = False
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
            if context.force_step_on_return:
                #print("RETURNED FROM", self, context)
                self.sprite.project.callstack.append([context.return_block, context.parent])
            else:
                #print("FORCED RETURNED FROM", self, context)
                context.return_block.do_run(context.parent)
            #context.return_block.run(context.parent)

project = Project(data, working_dir + '/', headless, doStdinEvents)
project.trigger_event("whenbroadcastreceived")
project.trigger_event("whenflagclicked")
project.run()
#print(project.vars)