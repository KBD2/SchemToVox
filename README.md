# SchemToVox
Converts WorldEdit schematic (`.schem`) files into MagicaVoxel voxel (`.vox`) models.  
You can make schematic files by creating a selection with the wand (or `//pos1`-`//pos2`), running `//copy` and then `//schem save <schematic_filename>`.  
The saved `.schem` file will be in your `.minecraft/config/worldedit/schematics` directory.  
Models are capped at 2000x2000x1000 voxels.  

Requires the [NBT package](https://pypi.org/project/NBT/).

Usage: `python schem2vox.py schem_file`  
You can also drag the schematic file onto the script. 

### Parameters
- `-c`, `--compression`, from 0 to 10:  
Will merge similar colours - a higher value means a lower threshold for merging.  
May be required for larger schematics.

- `--cull`:  
Will remove any invisible voxels (voxels with every face covered by an opaque voxel).  
Significantly decreases filesize for larger schematics, though will increase processing time.  

## Examples

<img src="images/norse_mythology.png" width="60%">
<br>
<img src="images/mansion.png" width="60%">
<br>
<img src="images/bastion.png" width="60%">
<br>
<img src="images/lake.png" width="60%">
<br>
<img src="images/village.png" width="60%">
<br>
<img src="images/nether.png" width="60%">