# read header (16 bits)
# fail if not 0xCAEx
# read last bits to get signal save settings
#   bit 0: Energy saved
#   bit 1: Calib_energy saved
#   bit 2: Energyshort saved
#   bit 3: Waveform samples saved
# calculate