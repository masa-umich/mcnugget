# TODO

- explain how thermistors work
- explain what the SF coefficients are and where to find them + alternative methods like beta value or lookup tables
- explain concept of CJC junction
- explain how awesome Evan Eidt is
- explain specifics of converting thermistor voltage different into a resistance
- explain linear offset of thermocouples
- explain converting mv <-> celsius

# Breakdown of Channels

`gse_ai_time` - time channel to index all analog input channels (PTs, TCs, LCs)
`gse_state_time` - time channel to index all digital input channels (state channels)
`gse_vlv_{i}` - command channel for a valve, virtual -> no index
`gse_state{i}` - state channel for a valve, indexed by `gse_state_time`
`gse_pt_{i}` - pressure transducer channel, indexed by `gse_ai_time`
`gse_tc_{i}` - thermocouple channel, indexed by `gse_ai_time`
`gse_thermistor_supply` - needed for TC calculations, indexed by `gse_ai_time`
`gse_thermistor_signal` - needed for TC calculations, indexed by `gse_ai_time`
`gse_lc_{i}` - load cells, indexed by `gse_ai_time`
