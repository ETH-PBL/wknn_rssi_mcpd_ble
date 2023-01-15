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
#include <zephyr/sys/reboot.h>

#include <zephyr/drivers/uart.h>
#include <zephyr/usb/usb_device.h>

#include <bluetooth/scan.h>
#include <zephyr/bluetooth/bluetooth.h>

#include "peer.h"
#include <dm.h>

BUILD_ASSERT(DT_NODE_HAS_COMPAT(DT_CHOSEN(zephyr_console), zephyr_cdc_acm_uart),
             "Console device is not ACM CDC UART device");

#define DESRIED_DM_RANGING_MODE DM_RANGING_MODE_MCPD

#define DEVICE_NAME CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN (sizeof(DEVICE_NAME) - 1)

#define COMPANY_CODE 0x0059
#define SUPPORT_DM_CODE 0xFF55AA5A

static struct dm_cb dm_cb;

const static bt_addr_t devices[6] = {
    {.val = {0x31, 0x34, 0xA7, 0xEE, 0x6F, 0xEE}},
    {.val = {0x63, 0x8E, 0x3D, 0x59, 0x64, 0xDE}},
    {.val = {0x44, 0x56, 0xBE, 0xF2, 0x63, 0xF1}},
    {.val = {0x0F, 0xA1, 0x6D, 0x40, 0x6D, 0xDB}},
    {.val = {0xA2, 0x1B, 0xAB, 0x7D, 0xB4, 0xFF}},
    {.val = {0xDD, 0xA7, 0x54, 0x5D, 0x40, 0xFC}},
};
static int devices_counter = 0;

K_SEM_DEFINE(ble_mutex, 0, 1);

struct adv_mfg_data {
  uint16_t company_code;    /* Company Identifier Code. */
  uint32_t support_dm_code; /* To identify the device that supports distance
                               measurement. */
  uint32_t
      access_address; /* The access address used to measure the distance. */
} __packed;
static struct adv_mfg_data mfg_data;

// scan parameters
static struct bt_le_scan_param scan_param = {
    .type = BT_LE_SCAN_TYPE_ACTIVE, // to create scan requests
    .interval = BT_GAP_SCAN_FAST_INTERVAL,
    .window = BT_GAP_SCAN_FAST_WINDOW,
    .options = BT_LE_SCAN_OPT_NONE,
    .timeout = 0,
};

// scan init parameters
static struct bt_scan_init_param scan_init = {
    .connect_if_match = 0, .scan_param = &scan_param, .conn_param = NULL};

static struct bt_scan_manufacturer_data scan_mfg_data = {
    .data = (unsigned char *)&mfg_data,
    .data_len =
        sizeof(mfg_data.company_code) + sizeof(mfg_data.support_dm_code),
};

static bool data_cb(struct bt_data *data, void *user_data) {
  struct adv_mfg_data *recv_mfg_data;
  struct dm_request req;

  switch (data->type) {
  case BT_DATA_MANUFACTURER_DATA:
    if (sizeof(struct adv_mfg_data) == data->data_len) {
      recv_mfg_data = (struct adv_mfg_data *)data->data;

      bt_addr_le_copy(&req.bt_addr, user_data);
      req.role = DM_ROLE_INITIATOR;
      req.ranging_mode = peer_ranging_mode_get();
      req.access_address = sys_le32_to_cpu(recv_mfg_data->access_address);
      req.start_delay_us = 1000;

      dm_request_add(&req);
    }
    return false;
  default:
    return true;
  }
}

static void scan_filter_match(struct bt_scan_device_info *device_info,
                              struct bt_scan_filter_match *filter_match,
                              bool connectable) {
  static uint8_t reset_counter = 0;
  if (bt_addr_cmp(&devices[devices_counter],
                  &device_info->recv_info->addr->a)) {
    return;
  }

  if (k_sem_take(&ble_mutex, K_NO_WAIT)) {
    reset_counter++;
    if (reset_counter == 20) {
      struct dm_init_param init_param;
      init_param.cb = &dm_cb;
      printk("Reset\r\n");
      sys_reboot(SYS_REBOOT_COLD);
    }
    return;
  } else {
    devices_counter =
        (devices_counter + 1) % (sizeof(devices) / sizeof(bt_addr_t));
    reset_counter = 0;
  }
  bt_addr_le_t addr;

  bt_addr_le_copy(&addr, device_info->recv_info->addr);
  peer_supported_add(device_info->recv_info->addr);
  peer_update_rssi(device_info->recv_info->addr, device_info->recv_info->rssi);
  bt_data_parse(device_info->adv_data, data_cb, &addr);
}

BT_SCAN_CB_INIT(scan_cb, scan_filter_match, NULL, NULL, NULL);

static int scan_start(void) {
  int err;

  bt_scan_init(&scan_init);
  bt_scan_cb_register(&scan_cb);

  err =
      bt_scan_filter_add(BT_SCAN_FILTER_TYPE_MANUFACTURER_DATA, &scan_mfg_data);
  if (err) {
    printk("Scanning filters cannot be set (err %d)\n", err);
    return err;
  }

  err = bt_scan_filter_enable(BT_SCAN_MANUFACTURER_DATA_FILTER, false);
  if (err) {
    printk("Filters cannot be turned on (err %d)\n", err);
    return err;
  }

  err = bt_scan_start(BT_SCAN_TYPE_SCAN_ACTIVE);
  if (err) {
    printk("Scanning failed to start (err %d)\n", err);
    return err;
  }

  return err;
}

static int bt_sync_init(void) {
  /* Synchronisation is based on advertising and scanning modes.
   * It occurs when SCAN_REQ and SCAN_RESP packets are exchanged.
   */

  int err;

  // printk("DM Bluetooth LE Synchronization initialization\n");

  err = peer_access_address_prepare();
  if (err) {
    printk("Failed to prepare access address (err %d)\n", err);
  }

  bt_addr_le_t addr = {0};
  size_t count = 1;
  bt_id_get(&addr, &count);
  char buf[BT_ADDR_LE_STR_LEN] = {0};
  bt_addr_le_to_str(&addr, buf, BT_ADDR_LE_STR_LEN);
  // printk("Device address: %s\r\n", buf);

  peer_ranging_mode_set(DESRIED_DM_RANGING_MODE);

  mfg_data.company_code = sys_cpu_to_le16(COMPANY_CODE);
  mfg_data.support_dm_code = sys_cpu_to_le32(SUPPORT_DM_CODE);
  mfg_data.access_address = sys_cpu_to_le32(peer_access_address_get());

  err = scan_start();
  if (err) {
    printk("Failed to start scanning (err %d)\n", err);
  }
  // print csv header
  /* printk("address,quality,rssi,"); */
  /* if (peer_ranging_mode_get() == DM_RANGING_MODE_RTT) { */
  /*   printk("rtt\n"); */
  /* } else { */
  /*   printk("mcpd_ifft,mcpd_phase_slope,rssi_openspace,best\n"); */
  /* } */
  return err;
}

static void data_ready(struct dm_result *result) {
  if (result->status) {
    peer_update(result);
  }
}

void main(void) {
  int err;
  dm_cb.data_ready = data_ready;
  struct dm_init_param init_param;

  const struct device *const dev = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
  uint32_t dtr = 0;

  if (usb_enable(NULL)) {
    return;
  }

  while (!dtr) {
    uart_line_ctrl_get(dev, UART_LINE_CTRL_DTR, &dtr);
    k_sleep(K_MSEC(100));
  }
  //printk("Starting Distance Measurement example\n");

  err = peer_init();
  if (err) {
    printk("Peer init failed (err %d)\n", err);
    return;
  }

  init_param.cb = &dm_cb;

  err = dm_init(&init_param);
  if (err) {
    printk("Distance measurement init failed (err %d)\n", err);
    return;
  }

  err = bt_enable(NULL);
  if (err) {
    printk("Bluetooth init failed (err %d)\n", err);
    return;
  }

  err = bt_sync_init();
  if (err) {
    printk("Synchronisation init failed (err %d)\n", err);
    return;
  }

  k_sem_give(&ble_mutex);
  for (;;) {
    k_sleep(K_FOREVER);
  }
}
