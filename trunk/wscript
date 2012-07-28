#! /usr/bin/env python
# encoding: utf-8
# Christophe Duvernois, 2012

top = '.'
out = 'build'

import os, sys, platform, serial

from waflib import Task, Options, Logs
from waflib.TaskGen import feature, after
from waflib.TaskGen import extension

@extension('.pde')
def process_pde(self, node):
	if 'cxx' in self.features:
		cppnode = node.change_ext('.cpp');
		self.create_task('pde', node, cppnode)
		self.source.append(cppnode)
		
class pde(Task.Task):
	color = 'GREEN'
	
	def run(self):
		pde = open(self.inputs[0].abspath(), "r");
		cpp = open(self.outputs[0].abspath(), 'w')
		
		cpp.write('#if defined(ARDUINO) && ARDUINO >= 100\n')
		cpp.write('#include "Arduino.h"\n')
		cpp.write('#else\n')
		cpp.write('#include "WProgram.h"\n')
		cpp.write('#endif\n')
		cpp.write('void setup();\n')
		cpp.write('void loop();\n')

		for l in pde:
			cpp.write(l)
			
		pde.close()
		cpp.close()
	
class eep(Task.Task):
	color = 'YELLOW'
	run_str = '${OBJ_COPY} -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --no-change-warnings --change-section-lma .eeprom=0 ${SRC} ${TGT}'
	
class hex(Task.Task):
	color = 'YELLOW'
	#run_str = '${OBJ_COPY} -O ihex -R .eeprom ${SRC} ${TGT}'
	
	def run(self):
		env = self.env
		bld = self.generator.bld
		wd = bld.bldnode.abspath()

		def to_list(xx):
			if isinstance(xx, str): return [xx]
			return xx		
		
		lst = []
		lst.extend(to_list(env['OBJ_COPY']))
		lst.extend(['-O'])
		lst.extend(['ihex'])
		lst.extend(['-R'])
		lst.extend(['.eeprom'])
		lst.extend([self.inputs[0].abspath()])
		lst.extend([self.outputs[0].abspath()])
		lst = [x for x in lst if x]
		
		self.generator.bld.cmd_and_log(lst, cwd=wd, env=env.env or None, output=0, quiet=0)
		
		lst = []
		lst.extend(to_list(env['AVR_SIZE']))
		lst.extend([self.outputs[0].abspath()])
		lst = [x for x in lst if x]
		
		out = self.generator.bld.cmd_and_log(lst, cwd=wd, env=env.env or None, output=0, quiet=0)[0]
		size = int(out.splitlines()[1].split('\t')[1].strip())
		maxsize = int(env.ARDUINO['upload.maximum_size'])
		if(size <= maxsize):
			Logs.pprint('BLUE', 'Binary sketch size: %d bytes (of a %s byte maximum)' % (size, maxsize))
		else:
			Logs.pprint('RED', 'Binary sketch size: %d bytes (of a %s byte maximum)' % (size, maxsize))

@feature('cxxprogram', 'cprogram') 
@after('apply_link') 
def makeUploadArduinoProgram(self): 
	elfnode = self.link_task.outputs[0]
	eepnode = elfnode.change_ext(".eep")
	hexnode = elfnode.change_ext(".hex")
	self.create_task('eep', elfnode, eepnode)
	self.create_task('hex', elfnode, hexnode)
	if Options.options.upload:
		import subprocess
	
		cmd = [self.env.AVRDUDE]
		cmd += ['-C%s' % self.env.AVRDUDECONF]
		cmd += ['-v']
		cmd += ['-p%s' % self.env.ARDUINO['build.mcu']]
		cmd += ['-carduino']
		cmd += ['-P/dev/ttyACM0']
		cmd += ['-b%s' % self.env.ARDUINO['upload.speed']]
		cmd += ['-D']
		cmd += ['-Uflash:w:%s:i' % hexnode.abspath()]
		subprocess.call(cmd)


def getAvailableBoards(ctx):
	boardsfile = os.path.abspath(ctx.env.ARDUINO_PATH + '/hardware/arduino/boards.txt')
	try:
		brd = open(boardsfile, "r");
		boards = {}
		for l in brd:
			l = l.strip()
			if len(l) == 0 or l.startswith('#'):
				continue
			property = l.split('=')
			value = property[1]
			property = property[0].split('.', 1)
			board = property[0]
			if not board in boards:
				boards[board] = {}
			boards[board][property[1]] = value
		return boards
	except Exception, e:
		print e;

def options(opt):
	opt.load('compiler_c')
	opt.load('compiler_cxx')
	opt.add_option('--upload', action='store_true', default=False, help='Upload on target', dest='upload')
	opt.add_option('--path', action='store', default='', help='path of the arduino ide', dest='idepath')
	opt.add_option('--arduino', action='store', default='uno', help='Arduino Board (uno, mega, ...)', dest='board')

def boards(ctx):
	"""display available arduino boards """
	arduinos = getAvailableBoards(ctx)
	Logs.pprint('BLUE', "Arduino boards available :")
	for b in arduinos:
		Logs.pprint('NORMAL', "%s : %s" % (b.ljust(max(15, len(b))), arduinos[b]['name']))


def configure(conf):
	arduinoIdeVersion = '101' #todo get arduino ide version automatically
	
	searchpath = []
	relBinPath = ['hardware/tools/', 'hardware/tools/avr/bin/']
	relIncPath = ['hardware/arduino/cores/arduino/', 'hardware/arduino/variants/standard/']
	
	if os.path.exists(Options.options.idepath):
		conf.env.ARDUINO_PATH = os.path.abspath(Options.options.idepath)
	else:
		if platform.system() == "Windows":
			conf.fatal('you have to specify the arduino ide installation path with --path')
		else:
			#try package installation ... (will work on ubuntu ...)
			conf.env.ARDUINO_PATH = '/usr/share/arduino'
		
	for p in relBinPath:
		path = os.path.abspath(conf.env.ARDUINO_PATH + '/' + p)
		if os.path.exists(path):
			searchpath += [path]
		avrdudeconf = os.path.abspath(path + '/avrdude.conf')
		if os.path.exists(avrdudeconf):
			conf.env.AVRDUDECONF = avrdudeconf
	
	for p in relIncPath:
		path = os.path.abspath(Options.options.idepath + '/' + p)
		if os.path.exists(path):
			conf.env.INCLUDES += [path]

	
	searchpath += os.environ['PATH'].split(os.pathsep)
	searchpath = filter(None, searchpath)

	conf.find_program('avr-gcc', var='CC', path_list=searchpath)
	conf.find_program('avr-g++', var='CXX', path_list=searchpath)
	conf.find_program('avr-ar', var='AR', path_list=searchpath)
	conf.find_program('avr-objcopy', var='OBJ_COPY', path_list=searchpath)
	conf.find_program('avr-size', var='AVR_SIZE', path_list=searchpath)
	conf.find_program('avrdude', var='AVRDUDE', path_list=searchpath)
	
	if conf.env.AVRDUDECONF:
		conf.msg('Checking for avrdude.conf', conf.env.AVRDUDECONF)
	else:
		conf.msg('Checking for avrdude.conf', 'not found', 'YELLOW')
	
	conf.load('compiler_c')
	conf.load('compiler_cxx')

	# arduino board ...
	boardsfile = os.path.abspath(conf.env.ARDUINO_PATH + '/hardware/arduino/boards.txt')
	if os.path.exists(boardsfile):
		arduinos = getAvailableBoards(conf)
	else:
		conf.fatal('Can\'t find boards description file : %s' % boardsfile)
	
	if not Options.options.board in arduinos:
		conf.fatal('Arduino ', 'Unknown board %s!' % Options.options.board)
	arduino = arduinos[Options.options.board]
	conf.env.ARDUINO = arduino
	
	conf.msg('Arduino ', '%s' % arduino['name'], 'BLUE')
		
	flags = ['-g', '-Os' , '-w' , '-Wall', '-std=c99', '-fno-exceptions', '-ffunction-sections' , '-fdata-sections', '-mmcu=%s' % conf.env.ARDUINO['build.mcu'], '-MMD']
	conf.env.CFLAGS = flags
	conf.env.CXXFLAGS = flags
	conf.env.DEFINES = ['F_CPU=%s' % conf.env.ARDUINO['build.f_cpu'], 'USB_VID=null', 'USB_PID=null', 'ARDUINO=%s' % arduinoIdeVersion]
	conf.env.LINKFLAGS = ['-Wl,--gc-sections', '-mmcu=%s' % conf.env.ARDUINO['build.mcu']]
	
	conf.env.INCLUDES += ['libraries']
	conf.env.INCLUDES += ['%s/libraries' % conf.env.ARDUINO_PATH]
	
def buildArduinoCore(bld):
	#build arduino core library
	node = bld.root.ant_glob([
		'%s/hardware/arduino/cores/arduino/*.c' % bld.env.ARDUINO_PATH[1:],
		'%s/hardware/arduino/cores/arduino/*.cpp' % bld.env.ARDUINO_PATH[1:],
		#add extra libraries if needed ...
		])
	bld(features='c cxx cxxstlib', source=node, target='core', lib='m')      

def build(bld):
	#build arduino core library
	bld.add_pre_fun(buildArduinoCore)

	#build arduino project
	src = bld.path.ant_glob(['src/**/*.pde', 'src/**/*.c', 'src/**/*.cpp', 'libraries/**/*.cpp'])
	bld(features = 'c cxx cxxprogram',
		includes = 'src',
		source = src, 
		target = 'mfocuino.elf',
		lib = 'm',
		use = 'core',
	)
	
def monitor(ctx):
	"""Start `screen` on the serial device.  This is meant to be an equivalent to the Arduino serial monitor."""
	#todo
	#wait serial is available
	try:
		#ser = serial.Serial("/dev/ttyACM0", 115200)
		ser = serial.Serial('/dev/ttyACM0', 9600)
		while 1:
			print ser.readline()
		ser.close()
	except Exception, e:
		Logs.pprint('RED', e)


from waflib.Build import BuildContext
class boardslist(BuildContext):
	cmd = 'boards'
	fun = 'boards'
