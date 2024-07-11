from pyvium import Pyvium as iv
from time import sleep


try:
    # Check for open instances 
    iv.open_driver()
    # sleep for 1 second
    sleep(1)
    instances = iv.get_active_iviumsoft_instances()
except:
    instances = []
    pass

if not instances:
    print("No instances found")
    sleep(1)
    status_list = []

else:
    # Check the device status of all instances
    status_list = []
    for i in instances:
        iv.select_iviumsoft_instance(i)
        # Make a list of pairs of serial number and status
        try:
            status_list.append([iv.get_device_serial_number(), iv.get_device_status()[0]])
        except:
            pass
    # Close driver
    iv.close_driver()
    # sleep for 1 second
    sleep(1)

# Print list
print(status_list)

