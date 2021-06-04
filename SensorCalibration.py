import Adafruit_ADS1x15

class Calibration:
    def __init__(self):
        self.adc = Adafruit_ADS1x15.ADS1115(address=0x48)
        
    def pressure_calibration(self):
        volt_list = []
        for i in range(20):
            self.data = self.adc.read_adc(0, gain=1)
            volt = self.data/8000
            volt = round(volt,1)
            volt_list.append(volt)
            voltage = sum(volt_list)/len(volt_list)
            voltage = round(voltage,1)
            #print('adc_val',voltage)      
        return voltage
    def oxygen_calibration(self):
        volt_list = []
        for i in range(200):
            self.data = self.adc.read_adc(2, gain=1)
            volt = self.data
            volt = round(volt,1)
            volt_list.append(volt)
            voltage = sum(volt_list)/len(volt_list)
            voltage = round(voltage,1)
            volt_factor = voltage-117
            #print('adc_val',voltage)      
        return volt_factor

#a = Calibration()
#v = a.oxygen_voltage()
#v_c = v-117
#oxy = v-v_c
#v = v*0.1875
#print('voltage>>',v)
#print('Calibrated_voltage>>',v_c)