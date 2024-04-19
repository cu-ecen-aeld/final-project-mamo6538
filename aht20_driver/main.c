/**
 * @file aht20.c
 * @brief Functions and data related to the AHT20 i2c driver implementation
 *
 * Based on the implementation of the "bme280" i2c driver, found in
 * cu-ecen-aeld/final-project-ritikar97 project.
 *
 * @author Madeleine Monfort
 * @date 2024-04-16
 * 
 * @ref AHT20 datasheet
 *      BME280 Github repo by Ritikar97
 *      AESDCHAR project from my assignment3-and-later repo
 *
 */

#include <linux/module.h>
#include <linux/init.h>
#include <linux/printk.h>
#include <linux/types.h>
#include <linux/cdev.h>
#include <linux/fs.h> // file_operations
#include <linux/slab.h> /* kmalloc() */
#include <linux/delay.h> //msleep
#include "aht20.h"

int aht20_major =   0; // use dynamic major
int aht20_minor =   0;

MODULE_AUTHOR("Madeleine Monfort");
MODULE_LICENSE("Dual BSD/GPL");

struct aht20_dev aht20_device; //allocated in init function

//define i2c_driver struct
static struct i2c_driver aht20_i2c_driver = 
{
    .driver = {
        .name = "aht20",
        .owner = THIS_MODULE,
    },
};

//define board info for the AHT20 device
struct i2c_board_info aht20_i2c_board = {
    .type = "aht20",           // set device type to aht20
    .addr = AHT20_SENSOR_ADDR, // I2C address!
    .flags = 0, 
    .platform_data = NULL,
};

static int aht20_init_sensor(void)
{
    int retval = 0;
    uint8_t data_byte = 0;
       
    //check calibration bit 
    data_byte = i2c_smbus_read_byte_data(aht20_device.aht20_client, STATUS_ADDR);
    uint8_t cal_bit = (data_byte >> CAL_BIT) & 0x01;
    if(!cal_bit) {
        PDEBUG("starting calibration.");
        //send init command
        int result = i2c_smbus_write_word_data(aht20_device.aht20_client, INIT_ADDR, INIT_DATA);
        if(result < 0) {
            printk(KERN_ERR "Couldn't initialize sensor.");
            retval = -1;
        }
    } 

    return retval;
}

int aht20_open(struct inode *inode, struct file *filp)
{
    PDEBUG("open");
    
    //use container_of to find the aht20_dev from the inode's cdev field
    struct aht20_dev* dev;
    dev = container_of(inode->i_cdev, struct aht20_dev, cdev);
    
    //set the file pointer to the aht20_dev struct found from the inode
    filp->private_data = dev;
    
    //Run the init for the AHT20 -- needed to wait 40ms upon startup, so this was better. 
    int retval = aht20_init_sensor();
    
    return retval;
}

int aht20_release(struct inode *inode, struct file *filp)
{
    PDEBUG("release");
    //shouldn't need to do anything since I didn't malloc in open
    return 0;
}

ssize_t aht20_read(struct file *filp, char __user *buf, size_t count,
                loff_t *f_pos)
{
    ssize_t retval = 0;
    char data_bytes[8];
    char buffer[BUFF_LEN];
    int temp = 0;
    int humidity = 0;
    PDEBUG("read %zu bytes with offset %lld",count,*f_pos);
    
    //error checking
    if(count == 0) goto exit;
    
    //get the circular buffer (get device struct)
    struct aht20_dev* dev = filp->private_data;
    
    //trigger measuring
    int result = i2c_smbus_write_word_data(aht20_device.aht20_client, MEAS_TRIG_ADDR, TRIG_DATA);
    if(result < 0) {
        printk(KERN_ERR "Couldn't trigger measuring.");
        retval = -1;
        goto exit;
    }
    
    //wait 80 ms
    msleep(80);  
    
    //read temp and humidity data
    int num_read = i2c_smbus_read_block_data(aht20_device.aht20_client, STATUS_ADDR, 6, &data_bytes);
    if(!num_read) {
        printk(KERN_ERR "Couldn't read the data.");
    }
    
    //check that status was good
    uint8_t status = (data_bytes[0] >> BUSY_BIT) & 0x01;
    if(status) {
        PDEBUG("data not ready.");
        goto send;
    }
    
    //convert the data
    //below calculations come from the datasheet and Adafruit's CircuitPython_AHTx0 library code
    humidity = (data_bytes[1] << 12) | (data_bytes[2] << 4) | (data_bytes[3] >> 4);
    temp = ((data_bytes[3] & 0x0F) << 16) | (data_bytes[4] << 8) | data_bytes[5];

    humidity = (humidity * 100) / 0x100000; //it is a percent
    temp = ((temp * 200) / 0x100000) - 50; //in degrees celsius


send:
    //format the converted data
    memset(buffer, 0, BUFF_LEN);
    snprintf(buffer, BUFF_LEN, "temp:%dC, humid:%d%", temp, humidity);

    //copy to user
    if(copy_to_user(buf, buffer, BUFF_LEN)) {
        retval = -EFAULT;
        goto exit;
    }
    
    retval = BUFF_LEN;
    
    
exit:
    return retval;
}


struct file_operations aht20_fops = {
    .owner =    THIS_MODULE,
    .read =     aht20_read,
    .open =     aht20_open,
    .release =  aht20_release,
};

static int aht20_setup_cdev(struct aht20_dev *dev)
{
    int err, devno = MKDEV(aht20_major, aht20_minor);

    cdev_init(&dev->cdev, &aht20_fops);
    dev->cdev.owner = THIS_MODULE;
    dev->cdev.ops = &aht20_fops;
    err = cdev_add (&dev->cdev, devno, 1);
    if (err) {
        printk(KERN_ERR "Error %d adding aht20 cdev", err);
    }
    return err;
}

int aht20_init_module(void)
{
    dev_t dev = 0;
    int result;
    result = alloc_chrdev_region(&dev, aht20_minor, 1,
            "aht20");
    aht20_major = MAJOR(dev);
    if (result < 0) {
        printk(KERN_WARNING "Can't get major %d\n", aht20_major);
        return result;
    }

    //Get I2C adapter master handle
    aht20_device.aht20_adapter = i2c_get_adapter(1);
    if(aht20_device.aht20_adapter == NULL) {
    	printk(KERN_ERR "Failed to get I2C adapter.\n");
    	result = -ENODEV;
    	goto safe_exit;
    }
    
    //Setup I2C client
    aht20_device.aht20_client = i2c_new_client_device(aht20_device.aht20_adapter, &aht20_i2c_board);
    if(aht20_device.aht20_client == NULL) {
    	printk(KERN_ERR "Failed to register I2C device.\n");
    	result = -ENODEV;
    	goto safe_exit;
    }
    
    //add the driver
    result = i2c_add_driver(&aht20_i2c_driver);
    if(result) {
    	printk(KERN_ERR "Error %d adding i2c driver", result);
    	goto safe_exit;
    }

    result = aht20_setup_cdev(&aht20_device);

    if( result ) {
        unregister_chrdev_region(dev, 1);
    }
    
    goto exit;
    
safe_exit:
    unregister_chrdev_region(dev, 1);
exit:
    if(aht20_device.aht20_adapter != NULL)
    	i2c_put_adapter(aht20_device.aht20_adapter);
    return result;

}

void aht20_cleanup_module(void)
{
    dev_t devno = MKDEV(aht20_major, aht20_minor);

    cdev_del(&aht20_device.cdev);

    //remove i2c client
    i2c_unregister_device(aht20_device.aht20_client);
    
    //delete driver
    i2c_del_driver(&aht20_i2c_driver);

    unregister_chrdev_region(devno, 1);
}



module_init(aht20_init_module);
module_exit(aht20_cleanup_module);
