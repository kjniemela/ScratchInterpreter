import json
from zipfile import ZipFile
from time import time
from random import randint
# from svg_to_png import *
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

help_text = f"""usage: {sys.executable} {os.path.basename(__file__)} <project> [options]
Options:
    -h, --help            Show help.
    -n, --no-display      Run project without displaying a screen.
    -d, --debug           Run project in debug mode.
    -p, --pretty-print    Pretty print project code instead of running.
    -s, --strict          Run in strict mode, meaning any use of unsupported blocks will cause a crash.
    --headless            Run project without pygame (this will break some features).
"""

if '-h' in sys.argv or '--help' in sys.argv:
    sys.exit(help_text)

if len(sys.argv) > 1:
    projectName = sys.argv[1]
else:
    sys.stderr.write('project path required\n')
    sys.exit(help_text)

arguments = sys.argv[2:]

no_display = '-n' in arguments or '--no-display' in arguments
debug = '-d' in arguments or '--debug' in arguments
pretty_print = '-p' in arguments or '--pretty-print' in arguments
strict_mode = '-s' in arguments or '--strict' in arguments
headless = '--headless' in arguments or pretty_print

if no_display and headless:
    sys.exit('\'--no-display\' option not allowed in headless mode')

with ZipFile(projectName, 'r') as zipObj:
   zipObj.extractall(working_dir)
f = open(working_dir + "/project.json")
data = json.loads(f.read())

doStdinEvents = True

import os
if no_display:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

if not headless:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
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
    def print(self):
        print('Variables:')
        for var in self.vars:
            print(var)
        print('\nSprites:')
        for sprite in self.sprites:
            sprite.print()
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
        # print("###STEP###")
        # print(self.callstack)
        if len(self.callstack) > 0:
            for i in range(len(self.callstack)):
                self.callstack[0][0].do_run(self.callstack[0][1])
                del self.callstack[0]
        if len(self.waitstack) > 0:
            for block, context, t in self.waitstack:
                if time() > t:
                    # print(self.waitstack)
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
                        for clone in sprite.clones:
                            clone.draw(self.screen)
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
        # print(data)
        self.path = self.sprite.project.path + data['assetId'] + "." + data['dataFormat']
        if data['dataFormat'] == 'png':
            self.image = pygame.image.load(self.path)
        elif data['dataFormat'] == 'svg':
            # self.image = pygame.image.load(svg_to_png(self.path, self.path[:-4]))
            self.image = pygame.Surface((0, 0))
    def apply_costume(self):
        # print(self.path)
        self.sprite.lastDir = 90
        self.sprite.spriteObject.image = self.image
        self.sprite.spriteObject.rect = self.sprite.spriteObject.image.get_rect(center=(240, 180))
        self.sprite.rect = self.sprite.spriteObject.rect

class Variable:
    def __init__(self, ID, data, project, spriteName):
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
        self.costumes = []
        self.costume_names = {}
        self.costume = None
        self.costume_index = None
        self.procs = {}
        self.proc_codes = {}
        self.proc_defs = {}
        self.defaultContext = Context([])
        self.rect = None
        self.vars = self.data['variables']
        self.local_vars = []
        self.lists = self.data['lists']
        self.isStage = data['isStage']
        for blockID in data['blocks']:
            b = data['blocks'][blockID]
            if type(b) == dict:
                self.blocks.append(Block(
                    self,
                    blockID,
                    b.get('parent'),
                    b.get('next'),
                    b.get('opcode'),
                    b.get('inputs'),
                    b.get('fields'),
                    self.defaultContext,
                    b,
                ))

        if not self.project.headless:
            for cost in data['costumes']:
                self.costume_names[cost['name']] = len(self.costumes)
                self.costumes.append(Costume(self, cost))

        if self.isStage:
            for ID in self.vars:
                project.vars.append(Variable(ID, self.vars[ID], self.project, self.name))
        else:
            for ID in self.vars:
                self.local_vars.append(Variable(ID, self.vars[ID], self.project, self.name))


        self.clones = []
        self.parent = None
        
        self.x = 0 if self.isStage else data['x']
        self.y = 0 if self.isStage else data['y']
        self.direction = 90 if self.isStage else data['direction']
        self.lastDir = 90
        self.scale = 100 if self.isStage else data['size']
        self.lastScale = 100
        self.rotation_style = None if self.isStage else data['rotationStyle']

        if not self.project.headless:
            self.spriteObject = pygame.sprite.Sprite()
            #self.spriteObject.rect = project.screen.get_rect(center=(240, 180))

            self.renderObject = pygame.sprite.RenderPlain(self.spriteObject)

            self.set_costume_by_index(data['currentCostume'])
            
            self.spriteObject.image, self.spriteObject.rect = self.rotate(self.costume.image, self.rect, -(self.direction-90))
            self.spriteObject.image, self.spriteObject.rect = self.rescale(self.spriteObject.image, self.spriteObject.rect, self.scale)
            self.spriteObject.mask = pygame.mask.from_surface(self.spriteObject.image)
    def print(self):
        print(f"  {self.name}")
        print(f"  Blocks:")
        for block in self.blocks:
            if block.parent == None:
                block.print(indent=2)
                print()
    def clone(self):
        parent = self if self.parent is None else self.parent

        clone = Sprite(parent.data, parent.project)
        clone.parent = parent
        parent.clones.append(clone)

        # Copy data to new clone
        for i in range(len(self.local_vars)):
            clone.local_vars[i].value = self.local_vars[i].value
        clone.x = self.x
        clone.y = self.y
        clone.direction = self.direction
        clone.scale = self.scale
        clone.rotation_style = self.rotation_style
        clone.set_costume_by_index(self.costume_index)

        for block in clone.blocks:
            if block.opcode == 'control_start_as_clone':
                block.do_run(clone.defaultContext)
    def set_costume_by_index(self, index):
        costume = self.costumes[index]
        costume.apply_costume()
        self.costume = costume
        self.costume_index = index
        self.lastScale = None
        self.lastDir = None
    def __repr__(self):
        return "Sprite<%s>" % (self.name)
    def add_proc(self, prot_ID, proccode, block, varnames):
        self.proc_codes[prot_ID] = proccode
        if block is not None:
            def_ID = block
        elif prot_ID in self.proc_defs:
            def_ID = self.proc_defs[prot_ID]
        else:
            def_ID = None
        self.procs[proccode] = {'id': def_ID, 'varnames': varnames}
    def add_proc_def(self, def_ID, prot_ID):
        self.proc_defs[prot_ID] = def_ID
        if prot_ID in self.proc_codes:
            if self.procs[proccode]['id'] is None:
                self.procs[proccode]['id'] = def_ID
    def get_block_by_ID(self, ID):
        for block in self.blocks:
            if block.ID == ID:
                return block
        return None
    def get_var_by_ID(self, ID):
        for var in self.local_vars:
            if var.ID == ID:
                return var
        return self.project.get_var_by_ID(ID)
    def get_costume_index_by_name(self, name):
        return self.costume_names.get(name, self.costume_index)
    def trigger_event(self, event):
        for block in self.blocks:
            if block.opcode == "event_" + event:
                block.do_run(self.defaultContext)
    def touching(self, other):
        if other is None:
            return False
        return not self.spriteObject.mask.overlap(other.spriteObject.mask, (int(abs(self.x-other.x)), int(abs(self.y-other.y)))) == None
    def touching_edge(self):
        # TODO - actually make this
        return not (-240 <= self.x <= 240 and -180 <= self.y <= 180)
    def bounce_on_edge(self):
        # TODO - actually make this
        touch_top = self.y > 180
        touch_left = self.x < -240
        touch_right = self.x > 240
        touch_bottom = self.y < -180

        radians = math.radians(90 - self.direction)
        dx = math.cos(radians)
        dy = -math.sin(radians)
        if touch_left:
            dx = max(0.2, abs(dx))
        elif touch_top:
            dy = max(0.2, abs(dy))
        elif touch_right:
            dx = 0 - max(0.2, abs(dx))
        elif touch_bottom:
            dy = 0 - max(0.2, abs(dy))

        self.direction = math.degrees(math.atan2(dy, dx)) + 90

    def draw(self, screen):
        if self.rotation_style == 'left-right' or self.rotation_style == 'don\'t rotate':
            direction = 90
        else:
            direction = self.direction

        if not direction == self.lastDir:
            self.spriteObject.image, self.spriteObject.rect = self.rotate(self.costume.image, self.rect, -(direction-90))
            self.spriteObject.image, self.spriteObject.rect = self.rescale(self.spriteObject.image, self.spriteObject.rect, self.scale)
            if self.rotation_style == 'left-right' and ((self.direction + 180) % 360) - 180 < 0:
                self.spriteObject.image = pygame.transform.flip(self.spriteObject.image, True, True)
            self.lastDir = direction
            self.spriteObject.mask = pygame.mask.from_surface(self.spriteObject.image)
        if not self.scale == self.lastScale:
            self.spriteObject.image, self.spriteObject.rect = self.rescale(self.costume.image, self.rect, self.scale)
            self.spriteObject.image, self.spriteObject.rect = self.rotate(self.spriteObject.image, self.spriteObject.rect, -(direction-90))
            if self.rotation_style == 'left-right' and ((self.direction + 180) % 360) - 180 < 0:
                self.spriteObject.image = pygame.transform.flip(self.spriteObject.image, True, True)
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
        self.loopcount = -1
        self.context = defaultContext
        if self.opcode == 'procedures_prototype':
            self.sprite.add_proc(ID, self.data['mutation']['proccode'], self.data.get('parent'), json.loads(self.data['mutation']['argumentnames']))
        elif self.opcode == 'procedures_definition':
            self.sprite.add_proc_def(ID, inputs['custom_block'][1])
    def __repr__(self):
        return f"Block: {self.opcode}"
    def print(self, indent=0):
        child = self.sprite.get_block_by_ID(self.child)
        substack = None
        if 'SUBSTACK' in self.inputs:
            substack = self.sprite.get_block_by_ID(self.inputs['SUBSTACK'][1])

        print(f"{'  '*indent}{self.opcode}")
        if substack is not None:
            substack.print(indent=indent+1)
        if child is not None:
            child.print(indent=indent)
    def eval_inputs(self, context):
        inputs = {}
        # print(self, self.inputs, self.fields)
        for i in self.inputs:
            # print(i, self.inputs[i])
            # TODO - properly deserialize all of this
            if self.inputs[i][0] == 1:
                if self.inputs[i][1] == None:
                    inputs[i] = None
                else:
                    if type(self.inputs[i][1]) == str:
                        inputs[i] = self.inputs[i][1]
                    elif self.inputs[i][1][0] == 11:
                        inputs[i] = self.inputs[i][1][2]
                    else:
                        inputs[i] = self.inputs[i][1][1]
            if self.inputs[i][0] == 2:
                inputs[i] = self.sprite.get_block_by_ID(self.inputs[i][1])
            if self.inputs[i][0] == 3:
                if self.inputs[i][1][0] == 12:
                    inputs[i] = self.sprite.get_var_by_ID(self.inputs[i][1][2]).value
                else:
                    inputs[i] = self.sprite.get_block_by_ID(self.inputs[i][1]).do_run(context)
        for field in self.fields:
            # TODO - clean this mess up!
            if field == 'BROADCAST_OPTION':
                inputs[field] = self.fields[field][1]
            elif field == 'VARIABLE':
                inputs[field] = self.fields[field][1]
            elif len(self.fields[field]) > 1 and type(self.fields[field][0]) == int:
                inputs[field] = self.fields[field][1]
            else:
                inputs[field] = self.fields[field][0]
        return inputs
    def run(self, context):
        self.loopcount = -1
        self.sprite.project.callstack.append([self, context])
        # print(self.sprite.project.callstack)
    def do_run(self, context):
        child = self.sprite.get_block_by_ID(self.child)
        inputs = self.eval_inputs(context)
        if debug:
            print(self.ID, ' - ', self.opcode, ' - ', inputs, ' - ', child, ' - ', self.sprite,
            ' - ', None if context.return_block is None else context.return_block.ID)
            if self.sprite.project.headless:
                input()
            else:
                pygame.event.wait()
        
        
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
        elif self.opcode == 'operator_mod':
            return number(inputs['NUM1']) % number(inputs['NUM2'])
        elif self.opcode == 'operator_round':
            return number(round(float(inputs['NUM'])))
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
        elif self.opcode == 'operator_and':
            return inputs['OPERAND1'].do_run(context) and inputs['OPERAND2'].do_run(context)
        elif self.opcode == 'operator_or':
            return inputs['OPERAND1'].do_run(context) or inputs['OPERAND2'].do_run(context)
        elif self.opcode == 'operator_length':
            return len(inputs['STRING'])
        elif self.opcode == 'operator_letter_of':
            return inputs['STRING'][int(inputs['LETTER'])-1]
        elif self.opcode == 'operator_random':
            return randint(int(inputs['FROM']), int(inputs['TO']))

        elif self.opcode == 'sensing_keypressed':
            if self.sprite.project.headless:
                return False
            else:
                keys = pygame.key.get_pressed()
                pressed_keys = []
                for key in range(len(keys)):
                    if keys[key]:
                        pressed_keys.append(pygame.key.name(key))
                if keys[pygame.K_UP]: pressed_keys.append('up arrow')
                if keys[pygame.K_DOWN]: pressed_keys.append('down arrow')
                if keys[pygame.K_LEFT]: pressed_keys.append('left arrow')
                if keys[pygame.K_RIGHT]: pressed_keys.append('right arrow')
                # if len(pressed_keys) > 0:
                #     print(pressed_keys, self.sprite.get_block_by_ID(inputs['KEY_OPTION']).data['fields']['KEY_OPTION'][0])
                return self.sprite.get_block_by_ID(inputs['KEY_OPTION']).data['fields']['KEY_OPTION'][0] in pressed_keys
        elif self.opcode == 'sensing_askandwait':
            if not inputs['QUESTION'] == "":
                sys.stdout.write(inputs['QUESTION'])
                sys.stdout.flush()
            self.sprite.project.answer = sys.stdin.readline().replace('\n', '')
            if not child == None:
                child.run(context)
        elif self.opcode == 'sensing_answer':
            return self.sprite.project.answer
        elif self.opcode == 'sensing_touchingcolor':
            if strict_mode:
                sys.exit('unsupported opcode: sensing_touchingcolor')
            else:
                return False
        elif self.opcode == 'sensing_touchingobject':
            return self.sprite.get_block_by_ID(inputs['TOUCHINGOBJECTMENU']).do_run(context)
        elif self.opcode == 'sensing_touchingobjectmenu':
            if inputs['TOUCHINGOBJECTMENU'] == '_edge_':
                return self.sprite.touching_edge()
            elif inputs['TOUCHINGOBJECTMENU'] is None:
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
            if not self.sprite.project.headless:
                if type(inputs['COSTUME']) == int:
                    self.sprite.set_costume_by_index(inputs['COSTUME'])
                else:
                    block = self.sprite.get_block_by_ID(inputs['COSTUME'])
                    if block is None:
                        self.sprite.set_costume_by_index(
                            self.sprite.get_costume_index_by_name(inputs['COSTUME'])
                        )
                    else:
                        self.sprite.set_costume_by_index(
                            self.sprite.get_costume_index_by_name(block.do_run(context))
                        )
            if not child == None:
                child.run(context)
        elif self.opcode == 'looks_nextcostume':
            if not self.sprite.project.headless:
                self.sprite.set_costume_by_index(
                    (self.sprite.costume_index + 1) % len(self.sprite.costumes)
                )
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
            # print("X += %s" % (inputs['DX']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_changeyby':
            self.sprite.y += number(inputs['DY'])
            # print("Y += %s" % (inputs['DY']))
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_movesteps':
            self.sprite.x += number(inputs['STEPS'])*sin(self.sprite.direction)
            self.sprite.y += number(inputs['STEPS'])*cos(self.sprite.direction)
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_pointindirection':
            self.sprite.direction = number(inputs['DIRECTION'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_pointtowards':
            target = self.sprite.project.get_sprite_by_name(self.sprite.get_block_by_ID(inputs['TOWARDS']).do_run(context))
            self.sprite.direction = -(math.degrees(math.atan2(target.y - self.sprite.y, target.x - self.sprite.x)) - 90)
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_pointtowards_menu':
            return inputs['TOWARDS']
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
        elif self.opcode == 'motion_ifonedgebounce':
            self.sprite.bounce_on_edge()
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'motion_setrotationstyle':
            self.sprite.rotation_style = inputs['STYLE']
            if not child == None:
                child.do_run(context)

        elif self.opcode == 'data_setvariableto':
            # print("SET VAR %s TO %s" % (self.sprite.get_var_by_ID(inputs['VARIABLE']), inputs['VALUE']))
            self.sprite.get_var_by_ID(inputs['VARIABLE']).value = inputs['VALUE']
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_changevariableby':
            self.sprite.get_var_by_ID(inputs['VARIABLE']).value = number(self.sprite.get_var_by_ID(inputs['VARIABLE']).value) + number(inputs['VALUE'])
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_lengthoflist':
            return len(self.sprite.get_var_by_ID(inputs['LIST']).value)
        elif self.opcode == 'data_itemoflist':
            return self.sprite.get_var_by_ID(inputs['LIST']).value[int(inputs['INDEX'])-1]
        elif self.opcode == 'data_deleteoflist':
            if inputs['INDEX'] == 'all':
                self.sprite.get_var_by_ID(inputs['LIST']).value = []
            else:
                del self.sprite.get_var_by_ID(inputs['LIST']).value[int(inputs['INDEX'])-1]
            if not child == None:
                child.do_run(context)
        elif self.opcode == 'data_addtolist':
            self.sprite.get_var_by_ID(inputs['LIST']).value.append(str(inputs['ITEM']))
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
            project.add_message_reciever(inputs['BROADCAST_OPTION'], self.sprite.get_block_by_ID(self.child), context)

        elif self.opcode == 'control_wait':
            self.sprite.project.waitstack.append([self.sprite.get_block_by_ID(self.child), context, time()+float(inputs['DURATION'])])
        elif self.opcode == 'control_repeat':
            if 'SUBSTACK' in inputs:
                if self.loopcount == -1:
                    self.loopcount = int(inputs['TIMES'])
                # print("LOOP COUNT:", self.loopcount, self)
                if self.loopcount > 0:
                    if not inputs['SUBSTACK'] == None:
                        c = context.clone(self)
                        inputs['SUBSTACK'].do_run(c)
                        self.loopcount -= 1
                        return
                    else:
                        if not child == None:
                            child.run(context)
                else:
                    self.loopcount = -1
                    if not child == None:
                        child.run(context)
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
            if inputs['CONDITION'] is not None and inputs['CONDITION'].do_run(context):
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
            if inputs['CONDITION'] is not None and inputs['CONDITION'].do_run(context):
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
        elif self.opcode == 'control_repeat_until':
            # print(inputs)
            if 'SUBSTACK' in inputs:
                # print(inputs['CONDITION'].do_run(context), child, context.return_block, self)
                if inputs['CONDITION'] is not None and not inputs['CONDITION'].do_run(context):
                    if not inputs['SUBSTACK'] == None:
                        c = context.clone(self)
                        inputs['SUBSTACK'].do_run(c)
                        return
                    else:
                        if not child == None:
                            child.run(context)
                else:
                    if not child == None:
                        child.run(context)
            else:
                if not child == None:
                    child.do_run(context)
        elif self.opcode == 'control_create_clone_of':
            self.sprite.clone()
            if not child == None:
                child.run(context)
        elif self.opcode == 'control_start_as_clone':
            if not child == None:
                child.run(context)
        
        else:
            print("NOT IMPLEMENTED:", self.opcode)
            if not child == None:
                child.do_run(context)

        if child == None and not context == self.sprite.defaultContext and not context.return_block == None:
            # print(context, "===", self, child)
            if context.force_step_on_return:
                # print("RETURNED FROM", self, context, "TO", context.parent)
                self.sprite.project.callstack.append([context.return_block, context.parent])
            else:
                # print("FORCED RETURNED FROM", self, context, "TO", context.parent)
                context.return_block.do_run(context.parent)
            #context.return_block.run(context.parent)

project = Project(data, working_dir + '/', headless, doStdinEvents)
if pretty_print:
    project.print()
else:
    project.trigger_event("whenbroadcastreceived")
    project.trigger_event("whenflagclicked")
    project.run()