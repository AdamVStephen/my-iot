# Digilent Pmod DA2 DAC Device RPI Interface

## Example Demos

## Lessons Learned

Prototype wiring can be susceptible to noise.  When monitoring a live circuit in 
parallel, it is not always clear if one part may impact the other.  Use of a 
circuit/logic analyzer to verify the driver software independent of the UUT is
a good strategy to divide the commissioning into two parts.

Keeping track of reliable components (e.g. breadboards of perhaps varying quality, age, reliability and so forth can help).  Be open to the usual possibility that particular contacts could have been damaged/corroded and might be making poor contact.

Find some kind of data sheet/advice as to which circuits are amenable to breadboarding and which are highly likely to give trouble.  This includes whether certain performance speeds are likely to be achievable or not.
