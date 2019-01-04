# Create Building Assessment Feature Class
Create a feature class to evaluate damage after a natural disaster to qualify for FEMA aid.

This tool creates a feature class, which is intended to be published as a service on AGOL/Portal
and used in the Collector App for in field damage assessment - a digital ATC-45 Rapid Evaluation 
Safety Assessment From. 

The progress of field inspectors and 
extent of damage can be monitored through an Operational Dashboard. The information gathered by
field inspectors is then used to evaluate if the extent of damage qualifies for FEMA aid. 

The feature class is a snapshot of a parcel tax
information layer with added fields that are necessary for calculating the value of damage for 
the purpose of qualifying
for FEMA aid. In addition, the user has the option to include a Zoning and USGN layer to add additional fields, which
may be useful for reporting purposes.

The workflow in this script was derived by the City of Richardson's _Damage Assessment Walk Through_ authored by
Heather Scroggins.

# USAGE
###Requirements
The tool output must be saved to a geodatabase that supports subtypes and domains.

The tool output cannot be saved to a feature dataset. 
 

### Layers
1. **Tax Appraisal Layer** - POLYGON - A layer containing the tax information for each parcel in the disaster
area. At a mimimum, the layer should contain the tax value for the parcel _( The tax value is 
multiplied by the percent damaged to calculate the value of damage )_ and a unique Parcel ID field.
Other useful fields include: Owner Name, Owner Contact, Owner Address, and Parcel Address
2. **Zoning Layer (Optional)** - POLYGON - A zoning layer can be used to append the zoning type to the ZONE_FULL
field. This is useful for summarizing affected parcels by zoning type in reports and operational 
dashboards. The Zoning layer must share a unique id with the Tax Appraisal Layer. 
3. **USNG Layer (Optional)** - POLYGON - A U.S. National Grid layer can be used to append the grid
label to the USNGCoord field to aid in reporting.    

### Script Setup


