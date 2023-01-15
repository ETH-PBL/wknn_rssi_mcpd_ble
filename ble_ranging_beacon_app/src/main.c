/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

/** @file
 *  @brief Nordic Distance Measurement sample
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/printk.h>

#include <bluetooth/scan.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/gpio.h>

#include "peer.h"
#include <dm.h>
#include <src/main.h>

#define LED_BLUE_NODE DT_ALIAS(led2)
static const struct gpio_dt_spec led_blue =
    GPIO_DT_SPEC_GET(LED_BLUE_NODE, gpios);

/* message queue to share charging state with the main thread */
K_MSGQ_DEFINE(charging_state_queue, sizeof(uint8_t), 1, sizeof(uint8_t));
#define LED_RED_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led_red =
    GPIO_DT_SPEC_GET(LED_RED_NODE, gpios);

#define DESRIED_DM_RANGING_MODE DM_RANGING_MODE_MCPD

#define DEVICE_NAME CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN (sizeof(DEVICE_NAME) - 1)

#define COMPANY_CODE 0x0059
#define SUPPORT_DM_CODE 0xFF55AA5A

struct adv_mfg_data {
  uint16_t company_code;    /* Company Identifier Code. */
  uint32_t support_dm_code; /* To identify the device that supports distance
                               measurement. */
  uint32_t
      access_address; /* The access address used to measure the distance. */
} __packed;

static struct adv_mfg_data mfg_data;

struct bt_le_adv_param adv_param_noconn = BT_LE_ADV_PARAM_INIT(
    BT_LE_ADV_OPT_USE_IDENTITY | BT_LE_ADV_OPT_SCANNABLE |
        BT_LE_ADV_OPT_NOTIFY_SCAN_REQ,
    BT_GAP_ADV_FAST_INT_MIN_1, BT_GAP_ADV_FAST_INT_MAX_1, NULL);

struct bt_le_adv_param *adv_param = &adv_param_noconn;

// advertising data
static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA(BT_DATA_NAME_COMPLETE, DEVICE_NAME, DEVICE_NAME_LEN),
};

// scan response packet, needed for DM
static const struct bt_data sd[] = {
    BT_DATA(BT_DATA_MANUFACTURER_DATA, (unsigned char *)&mfg_data,
            sizeof(mfg_data)),
};

static struct bt_le_ext_adv *adv;

static void adv_scanned_cb(struct bt_le_ext_adv *adv,
                           struct bt_le_ext_adv_scanned_info *info) {
  struct dm_request req;

  bt_addr_t to_cmp = {0};
  bt_addr_from_str("EC:76:1F:F3:44:79", &to_cmp);

  if (bt_addr_cmp(&info->addr->a, &to_cmp) == 0) {
    bt_addr_le_copy(&req.bt_addr, info->addr);
    req.role = DM_ROLE_REFLECTOR;
    req.ranging_mode = peer_ranging_mode_get();
    req.access_address = peer_access_address_get();
    req.start_delay_us = 0;

    dm_request_add(&req);
  }
}

const static struct bt_le_ext_adv_cb adv_cb = {
    .scanned = adv_scanned_cb,
};

static int adv_start(void) {
  int err;
  struct bt_le_ext_adv_start_param ext_adv_start_param = {0};

  err = bt_le_ext_adv_create(adv_param, &adv_cb, &adv);
  if (err) {
    printk("MAIN: Failed to create advertising set (err %d)\n", err);
    return err;
  }

  err = bt_le_ext_adv_set_data(adv, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
  if (err) {
    printk("MAIN: Failed setting adv data (err %d)\n", err);
    return err;
  }

  err = bt_le_ext_adv_start(adv, &ext_adv_start_param);
  if (err) {
    printk("MAIN: Failed to start extended advertising  (err %d)\n", err);
    return err;
  }

  return err;
}

static int bt_sync_init(void) {
  /* Synchronisation is based on advertising and scanning modes.
   * It occurs when SCAN_REQ and SCAN_RESP packets are exchanged.
   */

  int err;

  printk("MAIN: DM Bluetooth LE Synchronization initialization\n");

  err = peer_access_address_prepare();
  if (err) {
    printk("MAIN: Failed to prepare access address (err %d)\n", err);
  }

  peer_ranging_mode_set(DESRIED_DM_RANGING_MODE);

  mfg_data.company_code = sys_cpu_to_le16(COMPANY_CODE);
  mfg_data.support_dm_code = sys_cpu_to_le32(SUPPORT_DM_CODE);
  mfg_data.access_address = sys_cpu_to_le32(peer_access_address_get());

  err = adv_start();
  if (err) {
    printk("MAIN: Failed to start advertising (err %d)\n", err);
    return err;
  }

  return err;
}

static void data_ready(struct dm_result *result) {
  // Do nothing, as this is reflector and not the initiator
}

static struct dm_cb dm_cb = {
    .data_ready = data_ready,
};

void main(void) {
  int err;

  struct dm_init_param init_param;

  printk("MAIN: Starting Distance Measurement example\n");

  init_param.cb = &dm_cb;

  err = dm_init(&init_param);
  if (err) {
    printk("MAIN: Distance measurement init failed (err %d)\n", err);
    return;
  }

  err = bt_enable(NULL);
  if (err) {
    printk("MAIN: Bluetooth init failed (err %d)\n", err);
    return;
  }

  err = bt_sync_init();
  if (err) {
    printk("MAIN: Synchronisation init failed (err %d)\n", err);
    return;
  }

  if (!device_is_ready(led_blue.port)) {
    printk("MAIN: Could not get LED blue Port");
  }
  err = gpio_pin_configure_dt(&led_blue, GPIO_OUTPUT_INACTIVE);
  if (err) {
    printk("MAIN: Couldn't configure LED blue (err %d)\n", err);
    return;
  }

  if (!device_is_ready(led_red.port)) {
    printk("MAIN: Could not get LED red Port");
  }
  err = gpio_pin_configure_dt(&led_red, GPIO_OUTPUT_INACTIVE);
  if (err) {
    printk("MAIN: Couldn't configure LED red (err %d)\n", err);
    return;
  }

  err = charging_int_init(&charging_state_queue);
  if (err < 0) {
    printk("MAIN: Failed setting up charging interrupt (err %d)", err);
  }

  uint8_t charging_state = 0;

  while (true) {
    k_msgq_get(&charging_state_queue, &charging_state, K_MSEC(4900));
    if (!charging_state) {
      gpio_pin_set_dt(&led_red, false);
      gpio_pin_set_dt(&led_blue, true);
      k_sleep(K_MSEC(100));
      gpio_pin_set_dt(&led_blue, false);
    } else {
      gpio_pin_set_dt(&led_red, true);
    }
  }
}
