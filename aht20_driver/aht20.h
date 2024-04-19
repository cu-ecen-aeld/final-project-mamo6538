/*
 * aht20.h
 *
 *  Created on: Apr 16, 2024
 *      Author: Madeleine Monfort
 */

#ifndef AHT20_DRIVER_H_
#define AHT20_DRIVER_H_

#define AHT20_DEBUG 1  //Remove comment on this line to enable debug
#include <linux/i2c.h>

#undef PDEBUG             /* undef it, just in case */
#ifdef AHT20_DEBUG
#  ifdef __KERNEL__
     /* This one if debugging is on, and kernel space */
#    define PDEBUG(fmt, args...) printk( KERN_DEBUG "aht20: " fmt, ## args)
#  else
     /* This one for user space */
#    define PDEBUG(fmt, args...) fprintf(stderr, fmt, ## args)
#  endif
#else
#  define PDEBUG(fmt, args...) /* not debugging: nothing */
#endif

#define AHT20_SENSOR_ADDR 0x38
#define INIT_ADDR 0xBE
#define MEAS_TRIG_ADDR 0xAC
#define REST_ADDR 0xBA
#define STATUS_ADDR 0x71  //reading from this should also give humidity and temp data

#define INIT_DATA 0x0008
#define TRIG_DATA 0x0033

#define CAL_BIT 3
#define BUSY_BIT 7

#define BUFF_LEN 22

struct aht20_dev
{
    struct cdev cdev;     /* Char device structure      */
    struct i2c_adapter* aht20_adapter;
    struct i2c_client* aht20_client;
    //any other needed data
};


#endif /* AHT20_DRIVER_H_ */
