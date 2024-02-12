# SchemToVox
Converts WorldEdit `.schem` files into MagicaVoxel `.vox` models.  
You can make schematic files by creating a selection with the wand (or `//pos1`-`//pos2`), running `//copy` and then `//schem save <schematic_filename>`.  
The saved `.schem` file will be in your `.minecraft/config/worldedit/schematics` directory. 
Models are capped at 256x256x256.  

Requires the [NBT package](https://pypi.org/project/NBT/).

Usage: `python schem2vox.py schem_file`  
You can also drag the schematic file onto the script. 

There is an optional `-c` or `-compression` argument, from 0 to 10:  
`python schem2vox.py -c 1 example.vox` will merge similar colours - a higher value means a lower threshold for merging.

I haven't tested every block's colour - some may look strange; should be an easy fix.

## Examples

<img src="images/mansion.png" width="60%">
<br>
<img src="images/bastion.png" width="60%">
<br>
<img src="images/lake.png" width="60%">
<br>
<img src="images/village.png" width="60%">
<br>
<img src="images/nether.png" width="60%">