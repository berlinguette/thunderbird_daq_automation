# read header (16 bits)
# fail if not 0xCAEx
# read last bits to get signal save settings
#   bit 0: Energy saved
#   bit 1: Calib_energy saved
#   bit 2: Energyshort saved
#   bit 3: Waveform samples saved
# create struct/np_array for non-sample data
# create 
# calculate total bit size of these fields:
#   board, channel, timestamp, energy, calib_energy, energyshort, flags, waveform code
# read non-sample bits, decode to struct, add to list
# read n_samples, decode
# use n_samples to read/decode samples, add to list
# convert to DataFrame every X records, add to list
# concat DataFrames every N DataFrame conversions

