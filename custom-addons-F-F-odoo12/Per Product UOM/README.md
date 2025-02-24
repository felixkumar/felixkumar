# Per Product UOM

   This module will allow you to create a Unit of Measure class per product.  

# Contact

   electronic mail: nick (at) theserverexpert (dot) com
   website: https://github.com/nicknomo/local_addons_odoo

# Installation

   Please ensure you've configured a location for Odoo to locally load apps.  Copy this folder into there. Go to your odoo web interface, and go into the Apps tab. Click on "Update module list". Then search for "Per Product UoM" within your App list, and then install.

# Prerequisites

   You must be using Odoo v10 or possibly higher.  This module is only confirmed with v10. It will most likely not work with earlier versions, due to changes in the Odoo menu system.  

# Usage

   The intention of this module is to help you reuse similarly named units of measure in an organized way.  Using this module, you can create a units of measure assign it to a UoM class. You can then assign this class to a product. This is useful if 1 box of Product A is 4 LB, but 1 box of product B is 20 LB.  As long as product A and Product B are assigned a different UoM class, they may use the same unit of measure names, but the correct box to LB conversions can be maintained.
   
   Your first step is to enable different units of measure in Odoo.  Go into Inventory->settings.  Go to the "Products" section of the page, and choose the option "Some products may be sold/purchased in different units of measure (advanced)"

   After this is done, you must first enter the "Per Product Mod" tab.  Click on the menu seletion for "Product UOM Class".  You must then create a Product UOM Class. At this point, only a name is required. This class will later be assigned to a Product.  The product will then be restricted to UoM's within that class/category.  Units of measure must be unique to that UoM class. 

  After the class is created, you must select the menu entry for "Local UOM Entries".  Here, you create a unit of measure and assign it to a UOM class. You can create multiple units of measure and assign them to a class.  

  After the UoM class, and units of measure are assigned to it, you can edit a product and assign this UoM class to the product.  The sale and purchasing UoM can then be selected from this UoM class.  If multiple products use the same units of measure, this class can be assigned to other those other products as well.

# Known Issues
   
   An issue with Odoo prevents this module from properly removing this modules data.  If you intend to uninstall this module, I recommend you delete all UoM Classes first.  If this is not done, and you reinstall the module, then you will not be able to create records for any objects that were in the database before the module was removed.  
     