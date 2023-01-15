/*
 * Copyright (c) 2022, Silvano Cortesi
 * Copyright (c) 2022, ETH Zürich
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include <src/main.h>
#include <zephyr/drivers/gpio.h>

K_MUTEX_DEFINE(charging_state_mutex);
K_CONDVAR_DEFINE(charging_state_change);

/* charging interrupt pin */
#define CHARGING DT_PATH(charging)

static struct gpio_dt_spec charging_int =
    GPIO_DT_SPEC_GET(CHARGING, charging_gpios);

static struct gpio_callback charging_cb_data;
static struct k_msgq *charging_state_queue;
static volatile gpio_flags_t trigger_level = 0;

void charging_status_change(const struct device *dev, struct gpio_callback *cb,
                            uint32_t pins) {
  uint8_t charging_state = gpio_pin_get_dt(&charging_int);

  /* write value to queue */
  while (k_msgq_put(charging_state_queue, &charging_state, K_NO_WAIT) != 0) {
    /* message queue is full: purge old data & try again */
    k_msgq_purge(charging_state_queue);
  }

  trigger_level = trigger_level == GPIO_INT_EDGE_TO_ACTIVE
                      ? GPIO_INT_EDGE_TO_INACTIVE
                      : GPIO_INT_EDGE_TO_ACTIVE;
  gpio_pin_interrupt_configure_dt(&charging_int, trigger_level);
}

int charging_int_init(struct k_msgq *charging_state_queue_param) {
  int ret = 0;

  printk("POWER_MGMT: Starting Charging (Init)");

  charging_state_queue = charging_state_queue_param;

  if (!device_is_ready(charging_int.port)) {
    printk("POWER_MGMT: Error: charging gpio device is not ready");
    return -EIO;
  }

  ret = gpio_pin_configure_dt(&charging_int, GPIO_INPUT);
  if (ret < 0) {
    printk("POWER_MGMT: Failed to configure charging interrupt pin %d (err %d)",
            charging_int.pin, ret);
    return ret;
  }

  trigger_level = GPIO_INT_EDGE_TO_ACTIVE;
  ret = gpio_pin_interrupt_configure_dt(&charging_int, trigger_level);
  if (ret < 0) {
    printk(
        "POWER_MGMT: Failed to configure interrupt on charging interrupt pin %d (err %d)",
        charging_int.pin, ret);
    return ret;
  }

  gpio_init_callback(&charging_cb_data, charging_status_change,
                     BIT(charging_int.pin));
  ret = gpio_add_callback(charging_int.port, &charging_cb_data);
  if (ret < 0) {
    printk("POWER_MGMT: Failed to add callback to charging interrupt pin (err %d)", ret);
    return ret;
  }

  printk("POWER_MGMT: Set up charging interrupt pin %d", charging_int.pin);

  return ret;
}
