"""
Code for implementing a python controller for Texas Instruments DLPLCR6500.
This code is based on the following project (https://github.com/csi-dcsc/Pycrafter6500 , by Paolo Pozzi).

Here we define the hardware class to be integrated in a ScopeFoundry app.

-Michele Castriotta (@mikics on github), MSc at Politecnico di Milano.
-Andrea Bassi;
-Gianmaria Calisesi;

12/12/18
"""
from threading import Thread
from ScopeFoundry import HardwareComponent
from qtpy import QtCore, QtWidgets
from TexasInstrumentsDMD_ScopeFoundry.DMDDeviceHID import DmdDeviceHID
import numpy
import os
import sys
import PIL.Image
import tifffile as tiff

class TexasInstrumentsDmdHW(HardwareComponent):
    
    name = "TexasInstrumentsDmdHW"
    
    def setup(self):
        
        self.mode = self.add_logged_quantity("mode", dtype = int, si = False, ro = 0,
                                             initial = 3, vmin = 0, vmax = 3)
        self.exposure = self.add_logged_quantity("exposure", dtype = int, si = False, ro = 0,
                                                 initial = 1000000, vmin = 1, spinbox_step = 50000, unit = "us") #the spinbox_step does not work since it only works with float
        self.dark_time = self.add_logged_quantity("dark_time", dtype = int, si = False, ro = 0,
                                                 initial = 0, vmin = 0, unit = "us")
        self.bit_depth = self.add_logged_quantity("bit_depth", dtype = int, ro = 1, initial = 1)
        self.trigger_input = self.add_logged_quantity("trigger_input", dtype = bool, si = False, ro = 0,
                                                      initial = False)
        self.trigger_output = self.add_logged_quantity("trigger_output", dtype = bool, si = False, ro = 0,
                                                      initial = True)
        self.pattern_num = self.settings.New(name='pattern_num', dtype=int, ro=False)
        self.select_frames = self.add_logged_quantity('select_frames', dtype=bool, initial=False)
        self.first_frame = self.settings.New(name='first_frame', dtype=int, initial=0,
                                             vmin=0, spinbox_step=1, ro=False, reread_from_hardware_after_write=True)
        self.last_frame = self.settings.New(name='last_frame', dtype=int, initial=0,
                                             vmin=0, spinbox_step=1, ro=False, reread_from_hardware_after_write=True)
        
        

        self.file_path = self.add_logged_quantity("file_path", dtype = 'file', is_dir = False, 
                                               initial = "D:\\LabPrograms\\ScopeFoundry_POLIMI\\DMD_Pattern\\Calibration_pattern\\Periodic Pattern\\modulated_lightsheet_32.png")
        
        self.add_operation("browser", self.file_browser)
        self.add_operation("encode", self.encode_sequence)
        self.add_operation("load_pattern", self.load_sequence) #self.load_sequence_threaded_mode)
        self.add_operation("start_pattern", self.start_sequence)
        self.add_operation("pause_pattern", self.pause_sequence)
        self.add_operation("stop_pattern", self.stop_sequence)

        
        
    def connect(self):
        
        self.dmd = DmdDeviceHID()
        self.dmd.stopsequence()
        
        self.mode.hardware_set_func = self.dmd.changemode(self.mode.val)
        t = Thread(target=self.load_start_stop)
        t.start()

    def disconnect(self):
        
        if hasattr(self, 'dmd'):
            #self.dmd.stopsequence()
            del self.dmd
            
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
    
    @QtCore.Slot()
    def load_sequence_threaded_mode(self):
        
        t = Thread(target=self.load_sequence)
        t.start()
    
    def load_start_stop(self):
        
        self.load_sequence()
        self.stop_sequence()
        self.start_sequence()
        self.stop_sequence()
     
        
    def encode_sequence(self):
        filename = self.settings['file_path']
        images = list(tiff.imread(filename))
        self.dmd.save_encoded_sequence(images, filename)
        print("****************\n\nEncoded image has been saved\n\n****************")
        
     
    # def load_sequence(self):
        
    #     images=[]
    
    #     file_path = os.fsdecode(self.file_path.val)
    #     arr = numpy.array(PIL.Image.open(file_path), dtype = numpy.bool)
    #     images.append(arr)
        
    #     self.settings['pattern_num'] = len(images)
    #     print("Number of patterns: ", self.settings['pattern_num'])
    #     fframe = self.first_frame.val
    #     lframe = self.last_frame.val
    #     if self.settings['select_frames']:
    #         images = images[fframe:lframe+1]
            
    #     exposure=[self.exposure.val]*len(images)
    #     dark_time=[self.dark_time.val]*len(images)
    #     trigger_input=[self.trigger_input.val]*len(images)
    #     trigger_output=[self.trigger_output.val]*len(images)
        
        
    #     self.dmd.defsequence(images,exposure,trigger_input,dark_time,trigger_output,0)
    #     print("****************\n\nStop Loading sequence!\n\n****************")
    
#Elena   
    # def load_sequence(self):
        
    #     filename = self.file_path.val
    #     images = list(tiff.imread(filename)) # to load 3D stacks
        
    #   # This works only for 2D patterns:
    #   # images=[]
    #   # file_path = os.fsdecode(self.file_path.val)
    #   # arr = numpy.array(PIL.Image.open(file_path), dtype = numpy.bool)
    #   # images.append(arr)
        
    #     self.settings['pattern_num'] = len(images)
    #     print("Number of patterns: ", self.settings['pattern_num'])
    #     fframe = self.first_frame.val
    #     lframe = self.last_frame.val
    #     if self.settings['select_frames']:
    #         images = images[fframe:lframe+1]
            
    #     exposure=[self.exposure.val]*len(images)
    #     dark_time=[self.dark_time.val]*len(images)
    #     trigger_input=[self.trigger_input.val]*len(images)
    #     trigger_output=[self.trigger_output.val]*len(images)
        
        
    #     self.dmd.defsequence(images,exposure,trigger_input,dark_time,trigger_output,0)
    #     print("****************\n\nStop Loading sequence!\n\n****************")
    
#New:
    def load_sequence(self):
        
        filename = self.file_path.val
        
        file = os.fsdecode(filename)
        if file.endswith(".tif"):
            images = list(tiff.imread(filename)) # to load 3D stacks
            
            self.settings['pattern_num'] = len(images)
            print("Number of patterns: ", self.settings['pattern_num'])
            fframe = self.first_frame.val
            lframe = self.last_frame.val
            if self.settings['select_frames']:
                images = images[fframe:lframe+1]
            
            exposure=[self.exposure.val]*len(images)
            dark_time=[self.dark_time.val]*len(images)
            trigger_input=[self.trigger_input.val]*len(images)
            trigger_output=[self.trigger_output.val]*len(images)
            
            
            self.dmd.defsequence(images,exposure,trigger_input,dark_time,trigger_output,0)
            print("****************\n\nStop Loading sequence!\n\n****************")
        
        elif file.endswith(".encd"):
            exposure = [self.exposure.val]
            dark_time = [self.dark_time.val]
            trigger_input = [self.trigger_input.val]
            trigger_output = [self.trigger_output.val]
            
            self.dmd.def_sequence_by_file(filename,exposure,trigger_input,dark_time,trigger_output,0)
            print("****************\n\nStop Loading sequence!\n\n****************")


    
    
    @QtCore.Slot()
    def start_sequence(self):

        self.dmd.startsequence()
        print("****************\n\nThe sequence starts!\n\n****************")
    
    @QtCore.Slot()      
    def pause_sequence(self):

        self.dmd.pausesequence()
        print("****************\n\nThe sequence pauses!\n\n****************")
    
    @QtCore.Slot()    
    def stop_sequence(self):

        self.dmd.stopsequence()
        print("****************\n\nThe sequence stops!\n\n****************")
    
    @QtCore.Slot()    
    def file_browser(self):
        """
        Opens a dialog when click on browser, and update the value of the directory
        from which fetching patterns.
        """
        
        if self.file_path.is_dir:
            fname = QtWidgets.QFileDialog.getExistingDirectory(directory = self.file_path.val)
        else:
            fname, _ = QtWidgets.QFileDialog.getOpenFileName(directory = self.file_path.val)
            
        self.file_path.log.debug(repr(fname))
        self.file_path.update_value(fname)
    
#     @QtCore.Slot()    
#     def encode_sequence(self):
#         """
#         Encode the images in the selected folder and save them in another folder
#         """
#     
#     
#     def encode_image(self, image):
#         
#         encoded, size = self.dmd.new_encode(image)
        
            
    