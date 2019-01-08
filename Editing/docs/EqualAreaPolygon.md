# Create Building Assessment Feature Class
Splits a polygon into two equal North South areas.

# USAGE

### Input
1. **Polygon Layer** - POLYGON - A layer containing the polygon to be split. Feature classes with
multiple polygons are merged into a single polygon. This tools honors selected fields. If the user
has selected fields, only those fields are extracted and merged into one polygon before the analysis. 
2. **Tolerance** - DOUBLE - A value between 0 and 1. The tool will keep running until the desired
tolerance is met. Tolerance is calculated as ```polygon_X / polygon_Y = tolarance``` where `polygon_X`
is the split polygon with the lowest area and `polygon_Y` is the split polygon with the highest
area. _Note, the closer the tolerance is to 1 the longer the processing time. The tolerance should never
be more than 0.99999999_
   
