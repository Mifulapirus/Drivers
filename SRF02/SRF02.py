def GetDistance():
    I2C_Bus.write_byte_data(SRF02_Write_Add, 0, SRF02_GetDistance_Cmd)
    time.sleep(0.08)
    range1 = I2C_Bus.read_byte_data(SRF02_Write_Add, 2) 
    range2 = I2C_Bus.read_byte_data(SRF02_Write_Add, 3) 
    range3 = (range1 << 8) + range2 
    return range3