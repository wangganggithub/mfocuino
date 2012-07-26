#! /usr/bin/env python
# encoding: utf-8
# Christophe Duvernois, 2012

top = '.'
out = 'build'

import os, sys, glob, serial

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
		
		cpp.write('#include "Arduino.h"\n')
		cpp.write('void setup();')
		cpp.write('void loop();')

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
		if(size <= 32256):
			Logs.pprint('BLUE', 'Binary sketch size: %d bytes (of a 32256 byte maximum)' % size)
		else:
			Logs.pprint('RED', 'Binary sketch size: %d bytes (of a 32256 byte maximum)' % size)

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
		cmd += ['-p%s' % conf.env.MCU]
		cmd += ['-carduino']
		cmd += ['-P/dev/ttyACM0']
		cmd += ['-b115200']
		cmd += ['-D']
		cmd += ['-Uflash:w:%s:i' % hexnode.abspath()]
		subprocess.call(cmd)


def options(opt):
	opt.load('compiler_c')
	opt.load('compiler_cxx')
	opt.add_option('--upload', action='store_true', default=False, help='Upload on target', dest='upload')
	opt.add_option('--path', action='store', default='', help='path of the arduino ide', dest='idepath')
	opt.add_option('--arduino', action='store', default='uno', help='Arduino Board (uno, mega, ...)', dest='board')
	

def configure(conf):
	searchpath = []
	relBinPath = ['hardware/tools/', 'hardware/tools/avr/bin/']
	relIncPath = ['hardware/arduino/cores/arduino/', 'hardware/arduino/variants/standard/']
	if os.path.exists(Options.options.idepath):
		for p in relBinPath:
			path = os.path.abspath(Options.options.idepath + '/' + p)
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
	conf.env.F_CPU = '16000000L'
	if Options.options.board.lower() == "uno":
		conf.env.MCU = 'atmega328p'
		conf.msg('Arduino ', 'Uno')
	elif Options.options.board.lower() == "mega":
		conf.env.MCU = 'atmega1280'
		conf.msg('Arduino ', 'Mega')
	elif Options.options.board.lower() == "mega2650":
		conf.env.MCU = 'atmega2650'
		conf.msg('Arduino ', 'Mega 2650')
	
	
	flags = ['-g', '-Os' , '-w' , '-Wall', '-fno-exceptions', '-ffunction-sections' , '-fdata-sections', '-mmcu=%s' % conf.env.MCU, '-MMD']
	conf.env.CFLAGS = flags
	conf.env.CXXFLAGS = flags
	conf.env.DEFINES = ['F_CPU=%s' % conf.env.F_CPU, 'USB_VID=null', 'USB_PID=null', 'ARDUINO=101'] #todo get the version of the arduino ide
	conf.env.LINKFLAGS = ['-Wl,--gc-sections', '-mmcu=%s' % conf.env.MCU]
	
	conf.env.INCLUDES += ['libraries']
	conf.env.ARDUINO_SRC_CORE = glob.glob('%s/hardware/arduino/cores/arduino/*.c' % Options.options.idepath)
	conf.env.ARDUINO_SRC_CORE += glob.glob('%s/hardware/arduino/cores/arduino/*.cpp' % Options.options.idepath)
	


def build(bld):
	#build arduino core library
	#todo build the core library from anywhere ...
	core = bld.path.ant_glob(['ext/arduino-1.0.1/hardware/arduino/cores/arduino/*.c', 'ext/arduino-1.0.1/hardware/arduino/cores/arduino/*.cpp'])
	bld(features='c cxx cxxstlib', source=core, target='core', lib='m')

	#build arduino user project
	src = bld.path.ant_glob(['src/**/*.pde', 'src/**/*.c', 'src/**/*.cpp', 'libraries/PN532/*.cpp'])
	bld(features = 'c cxx cxxprogram',
		includes = 'src',
		source = src, 
		target = 'test.elf',
		lib = 'm',
		use = 'core',
	)
	
def openSerial(ctx):
	#wait serial is available
	try:
		#ser = serial.Serial("/dev/ttyACM0", 115200)
		ser = serial.Serial('/dev/ttyACM0', 9600)
		while 1:
			print ser.readline()
		ser.close()
	except Exception, e:
		Logs.pprint('RED', e)
	  

